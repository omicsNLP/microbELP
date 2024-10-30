# microbELP 
This project aims to build an automated full-text retrieval system for the generation of large biomedical corpora from published literature for research purposes.
Cadmus has been developed for use in non-commercial research. Use out with this remit is not recommended nor is the intended purpose.


## Installation
Cadmus has a number of dependencies on other Python packages, it is recommended to install it in an isolated environment.

`git clone https://github.com/biomedicalinformaticsgroup/cadmus.git`

`pip install ./cadmus`

## Get started

The format we are using for the search term(s) is the same as the one for [PubMed](https://pubmed.ncbi.nlm.nih.gov/). You can first try your search term(s) on PubMed and then use the same search term(s) as input for cadmus `bioscraping`.

In order to create your corpora you are going to use the function called `bioscraping`. The function is taking the following required parameters:

1. A PubMed query string or a Python list of PubMed IDs
2. An email address
3. Your NCBI_API_KEY
   
The function can also receive optional parameters.

1. wiley_api_key parameter allows Wiley to identify which publications you or your institution have the right to access. It will give you access to the OA publications that without the key you would not get access to. RECOMMENDED
2. elsevier_api_key parameter allows Elsevier to identify which publications you or your institution have the right to access. It will give you access to the OA publications that without the key you would not get access to. RECOMMENDED
3. The "start" parameter tells the function at which service we were before failure (e.g. crossref, doi, PubMed Central API. . .).
4. The "idx" parameter tells the function what is the last saved row index (article).

Start and idx are designed to use when restarting cadmus after a program failure. When Cadmus is running, there is a repeated output feed at the top of the live output.  This line will show you the stage and index that your output dataframe was last saved in case of failure for whatever reason. By using these optional parameters, the program will take off where it left off, saving you from starting the process from the beginning again.

5. "full_search", in case you want to check if a document became available since the last time you tried. "full_search" has three predefined values:

    - The default value is 'None', the function only looks for the new articles since the last run.
    - 'light', the function looks for the new articles since the last run and re-tried the row where we did not get any format.
    - 'heavy', the function looks for the new articles since the last run and re-tried the row where it did not retrieve at least one tagged version (i.e. html or xml) in combination with the pdf format.  

6. The "keep_abstract" parameter has the default value 'True' and can be changed to 'False'. When set to 'True', our parsing will load any format from the beginning of the document. If changes to 'False', our parsing is trying to identify the abstract from any format and starts to extract the text after it. We are offering the option of removing the abstract but we can not guarantee that our approach is the more reliable for doing so. In case you would like to apply your own parsing method for removing the abstract feel free to load any file saved during the retrieval available in the output folder: 
```"output/formats/{format}s/{index}.{suffix}.zip"```.  

You need to set the export path before every use so that cadmus is able to retrieve more than 10 000 records from NCBI. For that, we offer a function called `display_export_path`. You just need to call this function and copy past the result into your terminal before calling `bioscraping`. 

```python
from cadmus import display_export_path
display_export_path()
```

The result should look like:
```python
export PATH=${PATH}:YOUR_WORKING_DIRECTORY/output/medline/edirect
```

After copying and pasting the above export into your terminal you can now run `bioscraping` with the following example:

**Minimum requirements:**
```python
from cadmus import bioscraping
bioscraping(
    INPUT, #type str
    EMAIL, #type str
    NCBI_API_KEY #type str
    )
```
**Minimum recommended requirements:**
```python
from cadmus import bioscraping
bioscraping(
    INPUT, #type str
    EMAIL, #type str
    NCBI_API_KEY, #type str
    wiley_api_key = YOUR_WILEY_API_KEY, #type str
    elsevier_api_key = YOUR_ELSEVIER_API_KEY #type str
    )
```

## Load the result

The output from cadmus is a directory with the content text of each retrieved publication saved as a zip file containing a txt file, you can find the files here: ```"./ouput/retrieved_parsed_files/content_text/*.txt.zip"```. It also provides the metadata saved as a zip file containing a JSON file and a zip file containing a tsv file. In order to load the metadata you can use the following lines of code.

```python
import zipfile
import json
import pandas as pd
with zipfile.ZipFile("./output/retrieved_df/retrieved_df2.json.zip", "r") as z:
    for filename in z.namelist():
        with z.open(filename) as f:
            data = f.read()
            data = json.loads(data)


f.close()
z.close()
metadata_retrieved_df = pd.read_json(data, orient='index')
metadata_retrieved_df.pmid = metadata_retrieved_df.pmid.astype(str)
```

Here is a helper function you can call to generate a DataFrame with the same index as the one used for the metadata and the content text. The content text is the "best" representation of full text from the available formats. XML, HTML, Plain text, and PDF in that order of cleanliness. It is advised to keep the result somewhere else than in the output directory, as the DataFrame gets bigger the function takes more time to run. 

```python
from cadmus import parsed_to_df
retrieved_df = parsed_to_df(path = './output/retrieved_parsed_files/content_text/')
```

As default we assume the directory to the files is ```"./ouput/retrieved_parsed_files/content_text/``` please change the parameter 'path' otherwise.

---
## Output details

**retrieved_df**

The Metadata output is a pandas dataframe saved as a zip containing a JSON file.  
This is stored in the directory ```"./ouput/retrieved_df/retrieved_df2.json.zip"```. 
The dataframe columns are:
- pmid <class 'int64'>
    - PubMed id. If you prefer to change the data type of PMIDs to <class 'str'> you can use the following example: `metadata_retrieved_df.pmid = metadata_retrieved_df.pmid.astype(str)`
- pmcid <class 'float'>
    - PubMed Central id.
- title <class 'str'>
- abstract <class 'str'>
  - Abstract (from PubMed metadata). 
- mesh <class 'list'>
  -  MeSH (Medical Subject Headings) provided by Medline.
- keywords <class 'list'>
  - This field contains largely non-MeSH subject terms that describe the content of an article. Beginning in January 2013, author-supplied keywords.
- authors <class 'list'>
- journal <class 'str'>
- pub_type <class 'list'>
    - Publication type (from PubMed metadata).
- pub_date <class 'str'>
    - Publication date (from PubMed metadata).  
- doi <class 'str'>
- issn <class 'str'>
- crossref <class 'numpy.int64'>
    - 1/0 for the presence of crossref record when searching on doi. 
- full_text_links <class 'dict'>
    - dict_keys:
        - 'cr_tdm' (list of crossref tdm links),
        - 'html_parse' (list of links parsed from html files),
        - 'pubmed_links' (list of links from "linkout" section on PubMed page, not including PMC).
- licenses <class 'list'>
- pdf <class 'numpy.int64'>
    - (1/0) for successful download of the pdf version. 
- xml <class 'numpy.int64'>
    - (1/0) for successful download of the xml version.
- html <class 'numpy.int64'>
    - (1/0) for successful download of the html version.
- plain <class 'numpy.int64'>
    - (1/0) for successful download of the plain text version. 
- pmc_tgz <class 'numpy.int64'>
    - (1/0) for successful download of Pubmed Central Tar g-zip. 
- xml_parse_d <class 'dict'>
- html_parse_d <class 'dict'>
- pdf_parse_d <class 'dict'>
- plain_parse_d <class 'dict'>
    - **all parse_d have the same structure to the dictionary**
    - dict_keys:
        - 'file_path' (string representation of the path to the raw file saved at ```"output/formats/{format}s/{index}.{suffix}.zip"```),
        - 'size' (file size - bytes),
        - 'wc' (rough word count based on string.split() for the content text (int)),
        - 'wc_abs' (rough word count based on string.split() for the abstract (int)),
        - 'url' (the url used to retrieve the file),
        - 'body_unique_score' 
            - Score based on union and difference in words between the abstract and parsed text. The higher the score, the more original content in the full text, max = 1, min = 0.
        - 'ab_sim_score'
            - Score based on the count of words in the intersection between the abstract and parsed text, divided by the total union of unique words in the abstract and parsed text, the higher the score, the more similar the abstract is to the parsed text, max = 1, min = 0.
- content_text <class 'int'>
    - 0 if not retrieved 1 otherwise.

The 'core' data and content text from the retrieved publications are stored here:
- **retrieved_parsed_files**
    - In this directory, you can find 5 sub-directories: content_text, pdfs, htmls, xmls, txts. Each format sub-directories contains the content of the files saved as a zip containing a txt file. 
    - The content_text sub-directory, ```"./ouput/retrieved_parsed_files/content_text/*.txt.zip"```, contains the "best" representation of full text from the available formats. XML, HTML, Plain text, and PDF in that order of cleanliness. It is the place where the output is saved.
---



## Important - Please Read!
 Published literature can be subject to copyright with restrictions on redistribution. Users need to be mindful of the data storage requirements and how the derived products are presented and shared. Many publishers provide guidance on the use of content for redistribution and use in research.


## Citing

Please indicate which version of microbELP you used.

Jamie Campbell, Antoine Lain, & Ian Simpson. (2021). biomedicalinformaticsgroup/cadmus: First Release of Cadmus (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.5618052


## Version

### Version 0.2.0
-> First public release.

