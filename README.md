# chai-justice

## Overview

- Natural language processing project exploring how the MapAIE corpus discusses justice and related ethical notions in AI charters and manifestos.
- Combines large scale text extraction (PDF, HTML, TXT) with lexical statistics, word clouds, and qualitative inspection inside the `chai-justice-final.ipynb` notebook.
- Provides utilities to flatten AMR graphs and to sanity check raw text extraction before deeper analysis.

## Repository Layout

- `chai-justice-final.ipynb` main research notebook (data audit, frequency analysis, contextual inspection, visuals).
- `data/` MapAIE resources and derivatives (`docs/`, `txts/`, `all_manifestos.csv`, AMR files).
- `remove_multisentence.py` script that splits multi-sentence AMR graphs into single sentence graphs for downstream AMR tooling.
- `test_extract.py` quick smoke test for the document extraction logic.
- `requirements.txt` Python dependencies used across notebooks and scripts.

## Environment Setup

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`
- Optional: `python -m spacy download en_core_web_sm` if additional spaCy models are required by custom experiments.

## Working With The Notebook

- Open `chai-justice-final.ipynb` in VS Code or JupyterLab.
- Run the first cell to load imports; the environment expects the `.venv` configured above.
- Data intensive cells (especially Section 1.3) stream through the corpus; progress prints appear every 50 documents.
- Plots render inline; SVG displays rely on IPython.display which is pulled in via the requirements list.
- Keep the `data/` folder structure unchanged so relative paths remain valid.

## AMR Flattening Utility

- `python remove_multisentence.py`
- Reads `data/justice_AMR-500.amr`, rewrites multi-sentence graphs into individual entries, and saves `data/justice_AMR-500.amr-flattened.amr`.
- Logs summary statistics (counts before/after, examples of rewritten IDs).

## Text Extraction Smoke Test

- `python test_extract.py`
- Processes a small sample of documents, prints lengths, sentence counts, and occurrences of the token "justice".
- Useful for quickly verifying dependencies such as `pdfplumber`, `BeautifulSoup`, and encoding handling.

## Data Notes

- MapAIE datasheet: [https://mapaie.telecom-paris.fr/mapaie-datasheet.pdf](https://mapaie.telecom-paris.fr/mapaie-datasheet.pdf)
- `data/docs/` mixes PDF and HTML originals; `data/txts/` contains plain text counterparts.
- `data/all_manifestos.csv` lists the canonical set of manifestos and their inclusion status (`Included`).

## License and Attribution

- Original documents are authored by their respective institutions; please respect their usage licenses.
- Analysis code in this repository is intended for academic exploration within the Telecom Paris IMT Atlantique ChAI program.
