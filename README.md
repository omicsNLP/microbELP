[![DOI:10.1101/2021.01.08.425887](http://img.shields.io/badge/DOI-10.1101/2025.08.29.671515-BE2536.svg)](https://doi.org/10.1101/2025.08.29.671515)
[![DOI](https://zenodo.org/badge/407162055.svg)](https://zenodo.org/doi/10.5281/zenodo.17288827)

# 🦠 microbELP

**microbELP** is a text mining pipeline for automatic recognition and normalisation of microbiome-related entities in biomedical literature.  
It identifies microbial mentions (excluding viruses) in full-text scientific articles and links them to the **NCBI Taxonomy** identifiers.  

The system was developed to support large-scale microbiome curation and downstream text mining tasks by providing consistent and standardised microbial annotations in BioC-formatted JSON files (from [Auto-CORPus](https://github.com/omicsNLP/Auto-CORPus)).

---

## 🔍 Overview

The **microbELP** pipeline processes research articles encoded in **BioC JSON** format.  
It automatically detects mentions of microbiome entities — covering *archaea*, *bacteria*, and *fungi* — and attaches standardised taxonomy identifiers from NCBI.

Key features:
- **Automatic annotation** of microbiome mentions in BioC-formatted research articles.  
- **Entity normalisation** to **NCBI Taxonomy IDs**, providing consistent reference identifiers.  
- **Incremental annotation:** previously annotated files are skipped upon rerun.  
- **Standalone normalisation function:** converts a microbial name string to an NCBI Taxonomy identifier.  
- **Output in BioC JSON**, compatible with existing biomedical NLP pipelines.

---

## 🧩 Pipeline Overview

The pipeline consists of the following main stages:

1. **Input ingestion**  
   - Identifies all BioC JSON files from a specified input directory.  
   - Only files with `_bioc` in their names are processed.

2. **Named Entity Recognition (NER)**  
   - Recognised mentions are annotated with their text offsets and types (e.g. `bacteria_species`, `bacteria_genus`, etc.).

3. **Entity Normalisation**  
   - Each detected entity is mapped to an NCBI Taxonomy identifier using curated lexical resources.  

4. **Output generation**  
   - Annotated BioC JSON files are written to a new output directory.  
   - Each annotation includes:
     - The **text span** of the entity  
     - The **type** (e.g. `bacteria_species`)  
     - The **NCBI identifier**  
     - The **parent taxonomic identifier** (if available)  
     - Metadata: annotator name, date, and annotation ID  

5. **Incremental updates**  
   - On re-execution, files that already contain microbiome annotations are skipped, ensuring efficient updates.

---

## 📁 Input and Output Format

### Input  
A directory containing BioC JSON files (e.g. exported from [Auto-CORPus](https://github.com/omicsNLP/Auto-CORPus)).  

Example filename:  
```text
PMC92037_bioc.json
```

Each file contains a standard BioC structure:
```json
{
  "source": "Auto-CORPus (full-text)",
  "documents": [
    {
      "id": "PMC92037",
      "passages": [
        {
          "text": "Phylogenetic Relationships of Butyrate-Producing Bacteria from the Human Gut",
          "annotations": []
        }
      ]
    }
  ]
}
```
### Output 
A new directory (`microbELP_result`) is created, containing the same files with additional microbiome annotations:
```json
{
  "annotations": [
    {
      "text": "Eubacterium rectale",
      "infons": {
        "identifier": "NCBI:txid39491",
        "type": "bacteria_species",
        "annotator": "microbELP@omicsNLP.ic.ac.uk",
        "date": "2025-10-07 14:23:02",
        "parent_taxonomic_id": "NCBI:txid186928"
      },
      "locations": {"offset": 1418, "length": 19}
    }
  ]
}
```

---

## ⚙️ Installation
MicrobELP has a number of dependencies on other Python packages; it is recommended to install it in an isolated environment.

`git clone https://github.com/omicsNLP/microbELP.git`

`pip install ./microbELP`

---

## 🚀 Usage
### Main pipeline
Run the pipeline on a folder of BioC files:
```python
from microbELP import microbELP

microbELP('./$input_folder$')
```
Optional arguments:
```python 
from microbELP import microbELP

microbELP('./$input_folder$', output_directory='$output_path$')   # Provide the path to where the results should be saved. Default value is './'
```
### Normalisation Utility
The package includes a helper function for standalone microbial name normalisation:
```python
from microbELP import microbiome_normalisation

microbiome_normalisation('Eubacterium rectale') # NCBI:txid39491
```
If a match is found, it returns the NCBI Taxonomy identifier; otherwise `None`.

---

## ⚠️ Important - Please Read!
Published literature can be subject to copyright with restrictions on redistribution. Users need to be mindful of the data storage requirements and how the derived products are presented and shared. Many publishers provide guidance on the use of content for redistribution and use in research.

---

## 🤝 Acknowledgements
The microbELP pipeline was developed by Dhylan Patel ([icprofsensei](https://github.com/icprofsensei)) based on earlier work (without normalisation) by Nazanin Faghih-Mirzaei ([NazaninFaghih](https://github.com/NazaninFaghih)). The visualisation module was made by Avish Vijayaraghavan ([avishvj](https://github.com/avishvj)).

---

## 📝 Citing

Please indicate which version of microbELP you used.
```bibtex
@article {Patel2025.08.29.671515,
	author = {Patel, Dhylan and Lain, Antoine D. and Vijayaraghavan, Avish and Mirzaei, Nazanin Faghih and Mweetwa, Monica N. and Wang, Meiqi and Beck, Tim and Posma, Joram M.},
	title = {Microbial Named Entity Recognition and Normalisation for AI-assisted Literature Review and Meta-Analysis},
	elocation-id = {2025.08.29.671515},
	year = {2025},
	doi = {10.1101/2025.08.29.671515},
	publisher = {Cold Spring Harbor Laboratory},
	URL = {https://www.biorxiv.org/content/early/2025/08/30/2025.08.29.671515},
	eprint = {https://www.biorxiv.org/content/early/2025/08/30/2025.08.29.671515.full.pdf},
	journal = {bioRxiv}
}
```

---

## 🏷️ Version

### Version 0.2.0
-> First public release.

