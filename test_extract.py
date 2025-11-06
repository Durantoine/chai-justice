import os
import re
import pdfplumber
from bs4 import BeautifulSoup
import chardet

def extract_text(file_path):
    text = ""

    if file_path.lower().endswith('.pdf'):
        try:
            with pdfplumber.open('data/docs/' + file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "
        except Exception as e:
            print(f"Warning: Could not read PDF {file_path}: {e}")

    elif file_path.lower().endswith('.html'):
            encodings_to_try = ['utf-8', 'windows-1252', 'iso-8859-1']
            success = False
            for enc in encodings_to_try:
                try:
                    with open('data/docs/' + file_path, 'r', encoding=enc) as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        text += soup.get_text(separator=' ') + " "
                    success = True
                    break
                except UnicodeDecodeError:
                    continue

            # Try auto-detection if all known encodings fail
            if not success:
                with open('data/docs' + file_path, 'rb') as f:
                    raw = f.read()
                    detected = chardet.detect(raw)
                    encoding = detected.get('encoding', 'utf-8')
                    try:
                        text += BeautifulSoup(raw.decode(encoding, errors='ignore'), 'html.parser').get_text(separator=' ')
                    except Exception as e:
                        print(f"Could not decode {file_path} even after detection: {e}")


    elif file_path.lower().endswith('.txt'):
        try:
            with open('data/txts/' + file_path, 'r', encoding='utf-8') as f:
                text += f.read() + " "
        except Exception as e:
            print(f"Warning: Could not read TXT {file_path}: {e}")

    else:
        print(f"Skipping unsupported file type: {file_path}")
    return text

# Test
doc_folder = "data/docs"
text_folder = "data/txts"

files = [f for f in os.listdir(doc_folder) if os.path.isfile(os.path.join(doc_folder, f))]
text_files = [f for f in os.listdir(text_folder) if os.path.isfile(os.path.join(text_folder, f))]

print(f"Nombre de fichiers docs: {len(files)}")
print(f"Nombre de fichiers txts: {len(text_files)}")

file_list = files + text_files
print(f"Nombre total de fichiers: {len(file_list)}")
print(f"Exemples: {file_list[:5]}")

phrases_justice = []

print("\nTest sur les 5 premiers fichiers:")
for i, file in enumerate(file_list[:5]):
    print(f"\n--- Fichier {i+1}: {file} ---")
    current_text = extract_text(file)
    print(f"Longueur du texte extrait: {len(current_text)}")

    if len(current_text) > 0:
        print(f"Premiers 100 chars: {current_text[:100]}")
        sentences = re.split(r'(?<=[.!?])\s+', current_text)
        print(f"Nombre de phrases: {len(sentences)}")
        justice_sentences = [s for s in sentences if re.search(r'\bjustice\b', s, re.IGNORECASE)]
        print(f"Phrases avec 'justice': {len(justice_sentences)}")

        for sent in justice_sentences:
            sent_with_doc_id = sent + ' (extracted from ' + str(file) + ')'
            phrases_justice.append(sent_with_doc_id)

print(f"\n\n=== RESULTAT FINAL ===")
print(f"Total phrases avec 'justice': {len(phrases_justice)}")
if phrases_justice:
    print(f"Premiere phrase: {phrases_justice[0][:200]}")
