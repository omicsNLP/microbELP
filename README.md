[![DOI:10.1101/2021.01.08.425887](http://img.shields.io/badge/DOI-10.1101/2025.08.29.671515-BE2536.svg)](https://doi.org/10.1101/2025.08.29.671515)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17305411.svg)](https://doi.org/10.5281/zenodo.17305411)
[![Hugging Face Models](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-microbELP_NER-FFD21E)](https://huggingface.co/omicsNLP/microbELP_NER)
[![Hugging Face Models](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-microbELP_NEN-FFD21E)](https://huggingface.co/omicsNLP/microbELP_NEN)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17288827.svg)](https://doi.org/10.5281/zenodo.17288827)
[![Codabench](http://img.shields.io/badge/Codabench-microbELP_benchmark-2C3F4C.svg)](https://www.codabench.org/competitions/10913/)
[![CoDiet](https://img.shields.io/badge/used_by:_%F0%9F%8D%8E_CoDiet-5AA764)](https://www.codiet.eu)

# 🦠 microbELP

**microbELP** is a text mining pipeline for automatic recognition and normalisation of microbiome-related entities in biomedical literature.  
It identifies microbial mentions (excluding viruses) in full-text scientific articles and links them to the **[NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy)** identifiers.  

The system was developed to support large-scale microbiome curation and downstream text mining tasks by providing consistent and standardised microbial annotations in BioC-formatted JSON files (from [Auto-CORPus](https://github.com/omicsNLP/Auto-CORPus)).

---

## 🔍 Overview

The **microbELP** pipeline processes research articles encoded in **BioC JSON** format.  
It automatically detects mentions of microbiome entities — covering *archaea*, *bacteria*, and *fungi* — and attaches standardised taxonomy identifiers from **NCBI**.

### Key Features
- **Automatic annotation** of microbiome mentions in BioC-formatted research articles.  
- **Entity normalisation** to **NCBI Taxonomy IDs**, providing consistent reference identifiers.  
- **Parallel processing:** leverages multiprocessing to distribute workloads across multiple CPU cores, reducing runtime on large datasets.  
- **Visualisation module:** generates interactive and comparative **phylogenetic trees** to explore microbial diversity and overlap across studies or datasets.  
- **Incremental annotation:** previously annotated files are automatically skipped on rerun.  
- **Standalone normalisation functions:** convert microbial name strings to **NCBI Taxonomy identifiers**, now available for both **CPU** and **GPU** usage.  
- **Standalone recognition function:** detect microbiome entities directly from **free text** using the **DL** version.  
- **Flexible pipelines:**  
  - A **non–DL pipeline** optimised for **CPU** processing.  
  - A **DL-based pipeline** optimised for **CPU** and **GPU** processing.  
- **OA article support:** includes an automatic **PMCID downloader and converter**, transforming Open Access PubMed Central articles into **BioC JSON** format.  
- **Output in BioC JSON**, ensuring full compatibility with existing biomedical NLP pipelines.  


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
   - Annotated BioC JSON files are written to a new output directory called `'microbELP_result/'`.  
   - Each annotation includes:
     - The **text span** of the entity  
     - The **type** (e.g. `bacteria_species`)  
     - The **NCBI identifier**  
     - The **parent taxonomic identifier** (if available)  
     - Metadata: annotator name, date, and annotation ID  

5. **Incremental updates**  
   - On re-execution, files that already contain microbiome annotations are skipped, ensuring efficient updates.

---

## ⚙️ Installation

MicrobELP has a number of dependencies on other Python packages; it is recommended to install it in an isolated environment.

`git clone https://github.com/omicsNLP/microbELP.git`

`pip install ./microbELP`

---

## 📁 Input and Output Format of the main functions (microbELP, parallel_microbELP, microbELP_DL)

### ↩️ Input  

A directory containing BioC JSON files (e.g. exported from [Auto-CORPus](https://github.com/omicsNLP/Auto-CORPus)).
E.g. the unannotated test set available from [Zenodo](https://zenodo.org/doi/10.5281/zenodo.17305411).

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
### ↪️ Output 

A new directory (`microbELP_result/`) is created, containing the same files with additional microbiome annotations:
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

## 🚀 Usage

### 🧰 Main pipeline - non–DL

Run the pipeline on a folder of BioC files with the name ending with `_bioc.json`:

```python
from microbELP import microbELP

microbELP('$input_folder$') #type str
```

Optional arguments:

```python 
from microbELP import microbELP

microbELP(
	'$input_folder$', #type str
	output_directory='$output_path$' #type str # The path to where the results should be saved. Default value is './'
)  
```

The `output_directory` parameter lets you specify where to save the results. By default, output files are stored in the current working directory (`'./'`) under `'microbELP_result/'`.

### 🧰 Main pipeline - DL

Run the pipeline on a folder of BioC files with the name ending with `_bioc.json`:

```python
from microbELP import microbELP_DL

microbELP_DL('$input_folder$') #type str
```

Optional arguments:

```python 
from microbELP import microbELP_DL

microbELP_DL(
	'$input_folder$', #type str
	output_directory='$output_path$', #type str # The path to where the results should be saved. Default value is './'
	cpu = False, # type bool # If True, the code runs on CPU, otherwise it will use a GPU if any available.
	normalisation = True # #type bool # If changed to False, will only perform NER instead of NER+NEN/EL. Default value is 'True'
)  
```

The `output_directory` parameter lets you specify where to save the results. By default, output files are stored in the current working directory (`'./'`) under `'microbELP_DL_result/'`. The `cpu` parameter lets you specify whether to perform Named Entity Normalisation / Entity Linking; using the CPU or the GPU. If using the CPU, the longest part is to load the vocabulary as opposed to a much faster loading on the GPU. The `normalisation` parameter lets you specify whether to perform Named Entity Normalisation / Entity Liking; when set to `False`, it only performs Named Entity Recognition.

---

### 🧾 PMCID retrieval and conversion to BioC

Retrieve Open Access publications from PubMed Central and automatically convert them into **BioC JSON** format:

```python
from microbELP import pmcid_to_microbiome

pmcid_to_microbiome(
	'$path_PMCID_text_file$', #type str
	'$email_address$' #type str
)
```

It takes 2 mandatory parameters:

- `pmcid_file` <class 'str'>: Path to a text file where each line contains a single PMCID.
- `email` <class 'str'>: An email address required by the NCBI API for query identification.

The function queries the NCBI API to retrieve all Open Access publications from the provided PMCID list and automatically converts them into BioC JSON format.

Optional argument:

```python
pmcid_to_microbiome(
	'$path_PMCID_text_file$', #type str
	'$email_address$', #type str
	output_directory = './'  #type str # Path to save the retrieved and converted files. Default is './'
)
```

By default, all results are saved in a new directory named `'microbELP_PMCID_microbiome/'`, which contains two subfolders:

- `PMCID_XML/` — raw XML files retrieved from NCBI.
- `bioc/` — BioC-converted versions of the publications, ready for downstream processing with `microbELP`, `parallel_microbELP` or `microbELP_DL`.

---

### 🤖 Microbiome Entity Recognition (DL)

The package includes a standalone function for **Microbiome Entity Recognition** using a **DL** model optimised for both **CPU** and **GPU**.

```python
from microbELP import microbiome_DL_ner

input_text = 'The first microbiome I learned about is called Helicobacter pylori.' #type str or list of str
print(microbiome_DL_ner(input_text))
```

Output:

`[{'Entity': 'Helicobacter pylori', 'locations': {'offset': 47, 'length': 19}}]`

If a match is found, the function returns a list of detected entities, each represented as a dictionary containing:

- `Entity`: the recognised microbiome name
- `locations`: the character offset and length of the entity within the text

You can also provide a list of text strings as input for batch processing to reduce loading overhead:

```python
from microbELP import microbiome_DL_ner

input_list = [
    'The first microbiome I learned about is called Helicobacter pylori.',
    'Then I learned about Eubacterium rectale.'
]
print(microbiome_DL_ner(input_list))
```

Output:

```
[
    [{'Entity': 'Helicobacter pylori', 'locations': {'offset': 47, 'length': 19}}],
    [{'Entity': 'Eubacterium rectale', 'locations': {'offset': 21, 'length': 19}}]
]
```

Each element in the output list corresponds to one input text, containing its recognised microbiome entities and their text locations. 

There is one optional parameter to this function called `cpu` <type 'bool'>, the default value is False, i.e. runs on a GPU if any available. If you want to force the usage of the CPU, you will need to use `microbiome_DL_ner(input_list, cpu = True)`.

---

### 🔗 Normalisation Utility

The package includes two helper functions for standalone **microbial name normalisation**, available for both **non–DL** and **DL** usage.


#### 📜 Non–DL Normalisation 

```python
from microbELP import microbiome_normalisation

microbiome_normalisation('Eubacterium rectale') #type str # Output: NCBI:txid39491
```

If a match is found, it returns the **NCBI Taxonomy identifier**; otherwise `None`.

For time efficiency (as loading the vocabulary requires the most time), you can provide a list of strings as input and receive a list of dictionaries as output in the format:
```
input = ['Eubacterium rectale', 'bacteria']
output = [{'Eubacterium rectale': 'NCBI:txid39491'}, {'bacteria': 'NCBI:txid2'}]
```

```python
from microbELP import microbiome_normalisation

microbiome_normalisation(['Eubacterium rectale', 'bacteria']) #type list # Output: [{'Eubacterium rectale': 'NCBI:txid39491'}, {'bacteria': 'NCBI:txid2'}]
```

#### ⚡ DL Normalisation 

For deep learning–based name normalisation using the BioSyn model, the package provides the following function:

```python
from microbELP import microbiome_biosyn_normalisation

input_list = ['bacteria', 'Eubacterium rectale', 'Helicobacter pylori'] # type list
print(microbiome_biosyn_normalisation(input_list))
```

Output:
```
[
  {'mention': 'bacteria', 'candidates': [
    {'NCBI:txid2': 'bacteria'},
    {'NCBI:txid2': 'Bacteria'},
    {'NCBI:txid1869227': 'bacteria bacterium'},
    {'NCBI:txid1869227': 'Bacteria bacterium'},
    {'NCBI:txid1573883': 'bacterium associated'}
  ]},
  {'mention': 'Eubacterium rectale', 'candidates': [
    {'NCBI:txid39491': 'eubacterium rectale'},
    {'NCBI:txid39491': 'Eubacterium rectale'},
    {'NCBI:txid39491': 'pseudobacterium rectale'},
    {'NCBI:txid39491': 'Pseudobacterium rectale'},
    {'NCBI:txid39491': 'e. rectale'}
  ]},
  {'mention': 'Helicobacter pylori', 'candidates': [
    {'NCBI:txid210': 'Helicobacter pylori'},
    {'NCBI:txid210': 'helicobacter pylori'},
    {'NCBI:txid210': 'Campylobacter pylori'},
    {'NCBI:txid210': 'campylobacter pylori'},
    {'NCBI:txid210': 'campylobacter pyloridis'}
  ]}
]
```

This function supports both single strings and lists of microbiome mentions as input.

```python
from microbELP import microbiome_biosyn_normalisation

input_text = 'Helicobacter pylori'
print(microbiome_biosyn_normalisation(input_text))

```

Output:
```
[{'mention': 'Helicobacter pylori', 'candidates': [
  {'NCBI:txid210': 'Helicobacter pylori'},
  {'NCBI:txid210': 'helicobacter pylori'},
  {'NCBI:txid210': 'Campylobacter pylori'},
  {'NCBI:txid210': 'campylobacter pylori'},
  {'NCBI:txid210': 'campylobacter pyloridis'}
]}]
```

Parameters:

- `to_normalise` <class 'str' or 'list['str']'>): Text or list of microbial names to normalise.
- `cpu` (<class 'bool'>, default=False): When set to `False`, it will run on any GPU available. The longest part for inference on the CPU is to load the vocabulary used to predict the identifier.
- `candidates_number` (<class 'int'>, default=5): Number of top candidate matches to return (from most to least likely).
- `max_lenght` (<class 'int'>, default=25): Maximum token length allowed for the model input.
- `ontology` (<class 'str'>, default=''): Path to a custom vocabulary text file in id||entity format. If left empty, the default curated NCBI Taxonomy vocabulary is used.
- `save` (<class 'bool'>, default=False): If True, saves results to `microbiome_biosyn_normalisation_output.json` in the current directory.
  
---

### 🌳 Visualisation Module

The library includes a visualisation module designed to generate phylogenetic trees of identified microbial taxa. This allows users to visually inspect the microbial composition of individual datasets or compare across different domains or study sections.

#### Single Phylogenetic Tree

To generate a single phylogenetic tree from the output of the pipeline or from a list of NCBI Taxonomy identifiers:

```python
from microbELP import phylogenetic_tree_microbiome

phylogenetic_tree_microbiome(
    input_path, #type str
    figure_text = '', #type str
    ioa_filter = [],  #type list
    output_image_path = './', #type str
    save = False, #type boolean
    verbose = False #type boolean
)
```

Parameters:

- `input_path` <class 'str'> Path to a `.csv`, `.tsv`, or `.txt` file containing a list of NCBI Taxonomy IDs, or a directory containing annotated files produced by the pipeline.
- `figure_text` <class 'str'> Optional text displayed in the centre of the generated figure (e.g., study or dataset name).
- `ioa_filter` <class 'list'> Only used when providing a directory as input. Enables filtering by specific sections of a paper (e.g., ['IAO:0000318'], ['IAO:0000318', 'IAO:0000319'] where `IAO:0000318` = results section and `IAO:0000319` = discussion section).
- `output_image_path` <class 'str'> Path where the output will be saved. The images are stored under a new subdirectory `microbiome_visualisation/`.
- `save` <class 'bool'> If `True`, saves the generated images automatically.
- `verbose` <class 'bool'> If `True`, displays detailed logs of the tree generation process.

This function produces a phylogenetic tree based on the counts of microbial taxa found in the provided dataset.

#### Comparative Phylogenetic Tree

To compare microbial profiles between two datasets or domains:

```python
from microbELP import comparative_phylogenetic_tree_microbiome

comparative_phylogenetic_tree_microbiome(
    back_input_path, #type str
    front_input_path, #type str
    ioa_filter = [], #type list
    back_text = '', #type str
    front_text = '', #type str
    overlap_text = '', #type str
    output_image_path = './', #type str
    save = False, #type boolean
    verbose = False #type boolean
)
```

Parameters:

- `back_input_path` <class 'str'> The reference dataset or domain to compare against.
- `front_input_path` <class 'str'> The dataset or domain to highlight over the reference.
- `ioa_filter` <class 'list'>, `output_image_path` <class 'str'>, `save` <class 'bool'>, and `verbose` <class 'bool'>: Same as in the previous function.
- `back_text` <class 'str'>, `front_text` <class 'str'>, `overlap_text` <class 'str'>: Optional labels to display in the generated figures (e.g., dataset names or conditions).

This function generates four comparative images:

1. Phylogenetic tree and counts for the `back_input_path`.
2. Phylogenetic tree and counts for the `front_input_path`.
3. Tree of `front_input_path` with q-values compared to `back_input_path`.
4. Overlay of `front_input_path` on top of `back_input_path`, showing comparative abundance.

---

## 🐧 Linux / 🍎 macOS / 💠 Cygwin (Linux-like on Windows)

To reduce processing time, microbELP leverages Python’s `multiprocessing` library. This allows the workload to be distributed across multiple CPU cores, significantly speeding up the overall execution of the pipeline.

### 🧰 Main pipeline - non–DL (CPU only)

Run the pipeline on a folder containing BioC files:

```python
from microbELP import parallel_microbELP

if __name__ == "__main__":
	parallel_microbELP(
		'$input_folder$', #type str
		NUMBER_OF_CORES_ALLOCATED #type int
	)
```

Optional arguments:

```python 
from microbELP import parallel_microbELP

if __name__ == "__main__":
	parallel_microbELP(
    	'$input_folder$', #type str
    	NUMBER_OF_CORES_ALLOCATED, #type int
    	output_directory='$output_path$' #type str # Default: './'
	)
```

The `output_directory` parameter lets you specify where to save the results. By default, output files are stored in the current working directory (`'./'`) under `'microbELP_result/'`.

---

## ⚠️ Important - Please Read!

Published literature can be subject to copyright with restrictions on redistribution. Users need to be mindful of the data storage requirements and how the derived products are presented and shared. Many publishers provide guidance on the use of content for redistribution and use in research.

---

## 🤝 Acknowledgements

The corpus was collected using [cadmus](https://github.com/biomedicalinformaticsgroup/cadmus) 
<a href="https://github.com/biomedicalinformaticsgroup/cadmus"><img src="https://img.shields.io/github/stars/biomedicalinformaticsgroup/cadmus.svg?logo=github&label=Stars" style="vertical-align:middle;"/></a>,
and the raw file formats were then standardised to BioC using [Auto-CORPus](https://github.com/omicsNLP/Auto-CORPus) 
<a href="https://github.com/omicsNLP/Auto-CORPus"><img src="https://img.shields.io/github/stars/omicsNLP/Auto-CORPus.svg?logo=github&label=Stars" style="vertical-align:middle;"/></a>.
The original weights before fine-tuning for named entity recognition and entity linking were obtained from 
[dmis-lab/biobert-base-cased-v1.1](https://huggingface.co/dmis-lab/biobert-base-cased-v1.1) 
<a href="https://huggingface.co/dmis-lab/biobert-base-cased-v1.1"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-biobert-FFD21E" style="vertical-align:middle;"/></a>.
Finally, the entity linking fine-tuning and inference scripts were obtained and modified from 
[BioSyn](https://github.com/dmis-lab/BioSyn) 
<a href="https://github.com/dmis-lab/BioSyn"><img src="https://img.shields.io/github/stars/dmis-lab/BioSyn.svg?logo=github&label=Stars" style="vertical-align:middle;"/></a>.

---

## 📝 Citing

If you find this repository useful, please consider giving a star ⭐ and citation 📝:

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

If you used `microbiome_biosyn_normalisation` or `microbELP_DL` with the normalisation module please also cite 📝:

```bibtex
@inproceedings{sung2020biomedical,
    title = {Biomedical Entity Representations with Synonym Marginalization},
    author = {Sung, Mujeen and Jeon, Hwisang and Lee, Jinhyuk and Kang, Jaewoo},
    booktitle = {ACL},
    year = {2020}
}
```

If you used `pmcid_to_microbiome` please also cite 📝:
```bibtex
@article {10.3389/fdgth.2022.788124,
author = {Beck, Tim  and Shorter, Tom  and Hu, Yan  and Li, Zhuoyu  and Sun, Shujian  and Popovici, Casiana M.  and McQuibban, Nicholas A. R.  and Makraduli, Filip  and Yeung, Cheng S.  and Rowlands, Thomas  and Posma, Joram M. },       
title = {Auto-CORPus: A Natural Language Processing Tool for Standardizing and Reusing Biomedical Literature},      
journal = {Frontiers in Digital Health},    
volume = {Volume 4 - 2022},
year = {2022},
url = {https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2022.788124},
doi = {10.3389/fdgth.2022.788124}
```


---

## 👥 Code Contributors

<p align="center">
  <kbd>
    <a href="https://github.com/icprofsensei">
      <img src="https://drive.google.com/uc?id=1XJsbe4yKy0ncKy8Q4YWoAJgJrs9Ej2C4" width="90" height="90" style="border-radius:50%;">
    </a><br>
    👉 <strong><a href="https://github.com/icprofsensei" style="text-decoration:none; color:inherit;">Dhylan</a></strong>
  </kbd>
  &nbsp;&nbsp;
  <kbd>
    <a href="https://github.com/Antoinelfr">
      <img src="https://drive.google.com/uc?id=1FH6XRJuam6eMuCzwWXBAIdDacIw8PFiu" width="90" height="90" style="border-radius:50%;">
    </a><br>
    👉 <strong><a href="https://github.com/Antoinelfr" style="text-decoration:none; color:inherit;">Antoine</a></strong>
  </kbd>
  &nbsp;&nbsp;
  <kbd>
    <a href="https://uk.linkedin.com/in/avish-vijayaraghavan">
      <img src="https://drive.google.com/uc?id=1DWL0azN6pn6HRHGQ0hSIoZYZLLG-F7wb" width="90" height="90" style="border-radius:50%;">
    </a><br>
    👉 <strong><a href="https://uk.linkedin.com/in/avish-vijayaraghavan" style="text-decoration:none; color:inherit;">Avish</a></strong>
  </kbd>
  &nbsp;&nbsp;
  <kbd>
    <a href="https://github.com/NazaninFaghih">
      <img src="https://drive.google.com/uc?id=1ILo7Fcp_qnSSFpHiMw-qo9kMPdfx41m0" width="90" height="90" style="border-radius:50%;">
    </a><br>
    👉 <strong><a href="https://github.com/NazaninFaghih" style="text-decoration:none; color:inherit;">Nazanin</a></strong>
  </kbd>
  &nbsp;&nbsp;
  <kbd>
    <a href="https://github.com/jmp111">
      <img src="https://drive.google.com/uc?id=1kgEK2yqJG-eQnHGYDUH7mL2QeLtar2ZC" width="90" height="90" style="border-radius:50%;">
    </a><br>
    👉 <strong><a href="https://github.com/jmp111" style="text-decoration:none; color:inherit;">Joram</a></strong>
  </kbd>
</p>

---

## 🏷️ Version

### Version 0.2.0
-> First public release.

