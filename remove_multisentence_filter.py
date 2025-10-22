import re
from pathlib import Path

AMR_FILE_PATH = "data/justice_AMR-500.amr"
OUTPUT_FILE_PATH = "data/justice_AMR-500.amr-flattened.amr"

def parse_amr_file(content):
    """
    Parse le fichier AMR en séparant chaque graphe AMR.
    Retourne une liste de dictionnaires contenant les métadonnées et le graphe.
    """
    amr_blocks = re.split(r'\n\s*\n+', content.strip())
    
    amrs = []
    for block in amr_blocks:
        if not block.strip():
            continue
        
        metadata_lines = []
        graph_lines = []
        
        for line in block.split('\n'):
            if line.strip().startswith('#'):
                metadata_lines.append(line)
            elif line.strip():
                graph_lines.append(line)
        
        amr_id = None
        sentence = None
        
        for meta in metadata_lines:
            if '::id' in meta:
                amr_id = meta.split('::id')[1].strip()
            elif '::snt' in meta:
                sentence = meta.split('::snt')[1].strip()
        
        graph = '\n'.join(graph_lines)
        
        amrs.append({
            'id': amr_id,
            'sentence': sentence,
            'metadata': metadata_lines,
            'graph': graph
        })
    
    return amrs

def contains_justice(graph, debug=False):
    """
    Vérifie si un graphe AMR contient 'justice' (concept, modifier ou name).
    """
    if not graph or not graph.strip():
        return False
    
    graph_lower = graph.lower()
    
    # Concept justice : / justice
    if re.search(r'/\s*justice\b', graph_lower):
        if debug:
            print(f"      [DEBUG] Trouvé concept /justice")
        return True
    
    # Dans les noms/wiki : "...justice..."
    if re.search(r'"[^"]*justice[^"]*"', graph_lower):
        if debug:
            print(f"      [DEBUG] Trouvé dans nom/wiki")
        return True
    
    # Recherche simple dans tout le texte (pour vérifier)
    if 'justice' in graph_lower:
        if debug:
            print(f"      [DEBUG] Mot 'justice' trouvé mais pas capturé par les patterns")
            print(f"      [DEBUG] Extrait : {graph_lower[:200]}")
    
    return False

def is_multisentence(graph):
    """
    Vérifie si un graphe AMR contient une structure multi-sentence.
    """
    return bool(re.search(r'\(m\s*/\s*multi-sentence', graph, re.IGNORECASE))

def extract_subsentences_simple(graph):
    """
    Extrait les sous-graphes d'une multi-sentence en comptant les parenthèses.
    """
    subsentences = []
    
    snt_pattern = r':snt\d+'
    snt_matches = list(re.finditer(snt_pattern, graph))
    
    for i, match in enumerate(snt_matches):
        snt_label = match.group()
        start_pos = match.end()
        
        # Trouver la fin du sous-graphe en comptant les parenthèses
        paren_count = 0
        in_subgraph = False
        end_pos = start_pos
        
        for j in range(start_pos, len(graph)):
            char = graph[j]
            
            if char == '(':
                paren_count += 1
                in_subgraph = True
            elif char == ')':
                paren_count -= 1
                
                # Quand on revient à 0, le sous-graphe est terminé
                if paren_count == 0 and in_subgraph:
                    end_pos = j + 1
                    break
        
        # Si on n'a pas trouvé de fermeture, prendre jusqu'à la prochaine :snt
        if end_pos == start_pos:
            if i + 1 < len(snt_matches):
                end_pos = snt_matches[i + 1].start()
            else:
                end_pos = len(graph)
        
        content = graph[start_pos:end_pos].strip()
        
        if content:
            subsentences.append((snt_label, content))
    
    return subsentences

def flatten_amr(amr_data, debug=False):
    """
    Aplatit un graphe AMR multi-sentence en plusieurs graphes simples.
    FILTRE : Ne garde que les sous-phrases contenant 'justice'.
    Retourne une liste de dictionnaires (un par sous-phrase filtrée).
    """
    if not is_multisentence(amr_data['graph']):
        # Pas de multi-sentence, vérifier si contient justice
        has_justice = contains_justice(amr_data['graph'], debug=debug)
        if debug:
            print(f"\n   Graphe simple {amr_data['id']} - Justice: {has_justice}")
        if has_justice:
            return [amr_data]
        else:
            return []  # Filtré
    
    subsentences = extract_subsentences_simple(amr_data['graph'])
    
    if debug:
        print(f"\n   Multi-sentence {amr_data['id']} - {len(subsentences)} sous-phrases")
    
    flattened = []
    for i, (snt_label, subgraph) in enumerate(subsentences, 1):
        # FILTRE : ne garder que si contient "justice"
        has_justice = contains_justice(subgraph, debug=debug)
        
        if debug:
            print(f"      {snt_label} - Justice: {has_justice}")
            if not has_justice:
                print(f"         → FILTRÉ")
        
        if not has_justice:
            continue
        
        new_amr = {
            'id': f"{amr_data['id']}.{i}",
            'sentence': f"[{snt_label}] {amr_data['sentence']}",
            'metadata': [
                f"# ::id {amr_data['id']}.{i}",
                f"# ::snt [{snt_label}] {amr_data['sentence']}"
            ],
            'graph': subgraph
        }
        flattened.append(new_amr)
    
    return flattened

def write_amr_file(amrs, output_path):
    """
    Écrit les graphes AMR dans un fichier.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, amr in enumerate(amrs):
            if i > 0:
                f.write('\n\n')
            
            for meta in amr['metadata']:
                f.write(meta + '\n')
            
            f.write(amr['graph'])

def main():
    if not Path(AMR_FILE_PATH).exists():
        print(f"❌ Fichier introuvable : {AMR_FILE_PATH}")
        return
    
    with open(AMR_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 80)
    print("APLATISSEMENT DES MULTI-SENTENCES AMR + FILTRAGE 'JUSTICE'")
    print("=" * 80)
    
    amrs = parse_amr_file(content)
    print(f"\n📊 Statistiques du fichier source :")
    print(f"   • Nombre total de graphes AMR : {len(amrs)}")
    
    multi_count = sum(1 for amr in amrs if is_multisentence(amr['graph']))
    simple_count = len(amrs) - multi_count
    print(f"   • Graphes multi-sentence : {multi_count}")
    print(f"   • Graphes simples : {simple_count}")
    
    # Compter combien contiennent "justice" avant filtrage
    justice_before = sum(1 for amr in amrs if contains_justice(amr['graph']))
    print(f"   • Graphes contenant 'justice' : {justice_before}")
    
    # Aplatir et filtrer tous les AMR
    flattened_amrs = []
    filtered_out = 0
    
    # MODE DEBUG pour les 5 premiers
    print(f"\n🔍 MODE DEBUG - Analyse des 5 premiers graphes :")
    for i, amr in enumerate(amrs[:5]):
        print(f"\n{'='*60}")
        print(f"ID: {amr['id']}")
        print(f"Phrase: {amr['sentence'][:80]}...")
        print(f"Multi-sentence: {is_multisentence(amr['graph'])}")
        
        if is_multisentence(amr['graph']):
            subsentences = extract_subsentences_simple(amr['graph'])
            print(f"Sous-phrases trouvées: {len(subsentences)}")
            for snt_label, subgraph in subsentences:
                has_justice = contains_justice(subgraph, debug=False)
                print(f"  {snt_label}: justice={has_justice}")
                if not has_justice:
                    print(f"    → SERA FILTRÉ")
                    print(f"    Extrait: {subgraph[:100]}...")
    
    print(f"\n{'='*60}")
    print(f"Traitement de tous les graphes...")
    
    for amr in amrs:
        flattened = flatten_amr(amr, debug=False)
        if not flattened:
            filtered_out += 1
        flattened_amrs.extend(flattened)
    
    print(f"\n📈 Après aplatissement et filtrage :")
    print(f"   • Nombre total de graphes AMR : {len(flattened_amrs)}")
    print(f"   • Graphes conservés : {len(flattened_amrs)}")
    print(f"   • Graphes/sous-phrases filtrés (sans 'justice') : {filtered_out}")
    
    # Afficher quelques exemples
    print(f"\n📋 Exemples de transformation :")
    examples_shown = 0
    for amr in amrs:
        if is_multisentence(amr['graph']) and examples_shown < 3:
            print(f"\n   Original (ID {amr['id']}) :")
            print(f"      • Phrase : {amr['sentence'][:60]}...")
            print(f"      • Type : multi-sentence")
            
            flattened = flatten_amr(amr)
            subsentences = extract_subsentences_simple(amr['graph'])
            print(f"      → {len(subsentences)} sous-graphes trouvés, {len(flattened)} conservés")
            if flattened:
                for sub in flattened:
                    print(f"         ✓ Conservé : ID {sub['id']}")
            examples_shown += 1
    
    # Sauvegarder le résultat
    write_amr_file(flattened_amrs, OUTPUT_FILE_PATH)
    print(f"\n✅ Fichier aplati et filtré sauvegardé : {OUTPUT_FILE_PATH}")
    
    print("\n" + "=" * 80)
    print("💡 RÉSULTAT :")
    print("   • Le fichier original est préservé")
    print("   • Chaque multi-sentence a été divisée en sous-graphes")
    print("   • Seules les (sous-)phrases contenant 'justice' ont été conservées")
    print("   • Les IDs sont de la forme : ID_original.1, ID_original.2, etc.")
    print("=" * 80)

if __name__ == "__main__":
    main()