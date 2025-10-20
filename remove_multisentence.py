import re
from pathlib import Path

AMR_FILE_PATH = "data/justice_AMR-500.amr"
OUTPUT_FILE_PATH = "data/justice_AMR-500.amr-flattened.amr"

def parse_amr_file(content):
    """
    Parse le fichier AMR en séparant chaque graphe AMR.
    Retourne une liste de dictionnaires contenant les métadonnées et le graphe.
    """
    # Séparer par lignes vides (chaque graphe AMR est séparé par des lignes vides)
    amr_blocks = re.split(r'\n\s*\n+', content.strip())
    
    amrs = []
    for block in amr_blocks:
        if not block.strip():
            continue
        
        # Extraire les métadonnées (lignes commençant par #)
        metadata_lines = []
        graph_lines = []
        
        for line in block.split('\n'):
            if line.strip().startswith('#'):
                metadata_lines.append(line)
            elif line.strip():
                graph_lines.append(line)
        
        # Extraire l'ID et la phrase
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

def is_multisentence(graph):
    """
    Vérifie si un graphe AMR contient une structure multi-sentence.
    """
    return bool(re.search(r'\(m\s*/\s*multi-sentence', graph, re.IGNORECASE))

def extract_subsentences(graph):
    """
    Extrait les sous-phrases d'une structure multi-sentence.
    Retourne une liste de tuples (label, sous-graphe).
    """
    subsentences = []
    
    # Pattern pour capturer :snt1, :snt2, etc.
    # On cherche :sntX suivi de son contenu entre parenthèses
    pattern = r':snt(\d+)\s+(\([^)]+(?:\([^)]*\))*[^)]*\))'
    
    # Méthode plus robuste : parcourir le graphe et extraire chaque :sntX
    lines = graph.split('\n')
    current_snt = None
    current_content = []
    indent_level = 0
    
    for line in lines:
        # Détecter le début d'une sous-phrase
        snt_match = re.search(r':snt(\d+)\s+(.+)', line)
        if snt_match:
            # Sauvegarder la sous-phrase précédente si elle existe
            if current_snt is not None and current_content:
                subsentences.append((current_snt, '\n'.join(current_content)))
            
            # Commencer une nouvelle sous-phrase
            current_snt = f"snt{snt_match.group(1)}"
            current_content = [snt_match.group(2)]
            indent_level = line.count('(') - line.count(')')
        elif current_snt is not None:
            # Continuer à accumuler le contenu de la sous-phrase
            current_content.append(line)
            indent_level += line.count('(') - line.count(')')
            
            # Si on revient au niveau 0, la sous-phrase est terminée
            if indent_level <= 0 and ':snt' in line:
                continue
    
    # Sauvegarder la dernière sous-phrase
    if current_snt is not None and current_content:
        subsentences.append((current_snt, '\n'.join(current_content)))
    
    return subsentences

def extract_subsentences_simple(graph):
    """
    Version simplifiée : extrait les sous-graphes en se basant sur l'indentation.
    """
    subsentences = []
    
    # Trouver toutes les balises :sntX
    snt_pattern = r':snt\d+'
    snt_matches = list(re.finditer(snt_pattern, graph))
    
    for i, match in enumerate(snt_matches):
        snt_label = match.group()
        start_pos = match.end()
        
        # Trouver la fin de cette sous-phrase (début de la prochaine ou fin du graphe)
        if i + 1 < len(snt_matches):
            end_pos = snt_matches[i + 1].start()
        else:
            end_pos = len(graph)
        
        # Extraire le contenu
        content = graph[start_pos:end_pos].strip()
        
        # Nettoyer le contenu (enlever les éventuels caractères de fermeture)
        if content:
            subsentences.append((snt_label, content))
    
    return subsentences

def flatten_amr(amr_data):
    """
    Aplatit un graphe AMR multi-sentence en plusieurs graphes simples.
    Retourne une liste de dictionnaires (un par sous-phrase).
    """
    if not is_multisentence(amr_data['graph']):
        # Pas de multi-sentence, retourner tel quel
        return [amr_data]
    
    subsentences = extract_subsentences_simple(amr_data['graph'])
    
    flattened = []
    for i, (snt_label, subgraph) in enumerate(subsentences, 1):
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
            
            # Écrire les métadonnées
            for meta in amr['metadata']:
                f.write(meta + '\n')
            
            # Écrire le graphe
            f.write(amr['graph'])

def main():
    # Vérification du fichier
    if not Path(AMR_FILE_PATH).exists():
        print(f"❌ Fichier introuvable : {AMR_FILE_PATH}")
        return
    
    # Lecture du fichier
    with open(AMR_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 80)
    print("APLATISSEMENT DES MULTI-SENTENCES AMR")
    print("=" * 80)
    
    # Parse le fichier
    amrs = parse_amr_file(content)
    print(f"\n📊 Statistiques du fichier source :")
    print(f"   • Nombre total de graphes AMR : {len(amrs)}")
    
    # Compter les multi-sentences
    multi_count = sum(1 for amr in amrs if is_multisentence(amr['graph']))
    print(f"   • Graphes multi-sentence : {multi_count}")
    print(f"   • Graphes simples : {len(amrs) - multi_count}")
    
    # Aplatir tous les AMR
    flattened_amrs = []
    for amr in amrs:
        flattened = flatten_amr(amr)
        flattened_amrs.extend(flattened)
    
    print(f"\n📈 Après aplatissement :")
    print(f"   • Nombre total de graphes AMR : {len(flattened_amrs)}")
    print(f"   • Graphes ajoutés : +{len(flattened_amrs) - len(amrs)}")
    
    # Afficher quelques exemples
    print(f"\n📋 Exemples de transformation :")
    for amr in amrs[:3]:
        if is_multisentence(amr['graph']):
            print(f"\n   Original (ID {amr['id']}) :")
            print(f"      • Phrase : {amr['sentence'][:60]}...")
            print(f"      • Type : multi-sentence")
            
            flattened = flatten_amr(amr)
            print(f"      → Divisé en {len(flattened)} sous-graphes :")
            for sub in flattened:
                print(f"         - ID {sub['id']}")
    
    # Sauvegarder le résultat
    write_amr_file(flattened_amrs, OUTPUT_FILE_PATH)
    print(f"\n✅ Fichier aplati sauvegardé : {OUTPUT_FILE_PATH}")
    
    print("\n" + "=" * 80)
    print("💡 UTILISATION :")
    print("   • Le fichier original est préservé")
    print("   • Chaque multi-sentence a été divisée en sous-graphes")
    print("   • Les IDs sont de la forme : ID_original.1, ID_original.2, etc.")
    print("   • Vous pouvez maintenant analyser les concepts 'justice' sur le fichier aplati")
    print("=" * 80)

if __name__ == "__main__":
    main()