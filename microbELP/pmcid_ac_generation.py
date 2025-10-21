import urllib.request as request
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError, Timeout
from urllib3.util import Retry
from urllib3.exceptions import NewConnectionError
import time
import os
import re
import nltk
from fuzzywuzzy import fuzz
import glob
import json
from datetime import datetime

from bs4 import BeautifulSoup, NavigableString, Tag

def get_request(input_id, http, base_url, headers):
    # for text retrieval its best to clear cookies before each request
    http.cookies.clear()
    
    # The response dictionary (r_d) will hold the output from our request, succeed or fail
    r_d = {}
    exception = None
    attempt = 1
    need_to_back_off = False
    while attempt <3:
        # we're going to set up a try except system so that we deal with the most common errors
        try:
            # send the request to the different APIs website
            base_url = f'{base_url}{input_id}&metadataPrefix=pmc'
            r = http.get(f'{base_url}', headers=headers, timeout = (20,120))
            
            # check for 200 response and raise exception if not so.
            if r.status_code != 200:
                print(f'Error {r.status_code} for {base_url}')
        
        #now we have a set of multiple exceptions that might occur
        except HTTPError as error:
            print(f"HTTP error occurred:\n{error}")
            if r.status_code == 429:
                need_to_back_off = True
            exception = error
            r = None
            attempt = 3
        except NewConnectionError as nce:
            print(f'New connection error occurred \n{nce}')
            exception = nce
            attempt = 3
            r = None
        except Timeout:
            print('Request timed out')
            exception = 'timeout'
            attempt = 3
            r= None
        except ConnectionError as ce:
            print(f'Max Retries error:\n{ce}')
            exception = ce
            attempt = 3
            r= None
        except Exception as err:
            print(f'Another sort of error occured: \n{err}')
            exception = err
            attempt = 3
            r= None
        else:
            # No Exceptions Occured
            # set the output variables from the response object
            exception = None
            status_code = r.status_code
            headers = r.headers
            text = r.text
            r_url = r.url
            content = r.content
            attempt = 3

        finally:
            
            if (r == None) or (r.status_code != 200):
                
                # set the default response_dict values before we parse
                status_code = None
                headers = None
                text = None
                r_url = None
                content = None
            else:
                pass
            
            r_d.update({'status_code':status_code,
                        'headers':headers,
                        'content':content,
                        'text':text,
                        'url':base_url,
                        'error':exception})
            
        # now we close the response objects to keep the number of open files to a minimum
        if r != None:
            r.close()
    
    if need_to_back_off == True:
        exit()
            
    return r_d, r

def get_iao_term_to_id_mapping(iao_term):
    """Map IAO terms to IAO IDs.

    Args:
        iao_term: IAO term to map to an IAO ID.

    Returns:
        A dictionary containing the IAO term and its corresponding ID
    """
    mapping_result_id_version = {'version number section': 'IAO:0000129',
                                 'patent section': 'IAO:0000313',
                                 'document part': 'IAO:0000314',
                                 'textual abstract section': 'IAO:0000315',
                                 'graphical abstract section': 'IAO:0000315',
                                 'introduction section': 'IAO:0000316',
                                 'methods section': 'IAO:0000317',
                                 'results section': 'IAO:0000318',
                                 'discussion section': 'IAO:0000319',
                                 'references section': 'IAO:0000320',
                                 'author list': 'IAO:0000321',
                                 'institution list': 'IAO:0000322',
                                 'author contributions section': 'IAO:0000323',
                                 'acknowledgements section': 'IAO:0000324',
                                 'footnote section': 'IAO:0000325',
                                 'supplementary material section': 'IAO:0000326',
                                 'copyright section': 'IAO:0000330',
                                 'abbreviations section': 'IAO:0000606',
                                 'author information section': 'IAO:0000607',
                                 'author summary section': 'IAO:0000609',
                                 'availability section': 'IAO:0000611',
                                 'case report section': 'IAO:0000613',
                                 'conclusion section': 'IAO:0000615',
                                 'conflict of interest section': 'IAO:0000616',
                                 'consent section': 'IAO:0000618',
                                 'ethical approval section': 'IAO:0000620',
                                 'figures section': 'IAO:0000622',
                                 'funding source declaration section': 'IAO:0000623',
                                 'future directions section': 'IAO:0000625',
                                 'genome announcement section': 'IAO:0000627',
                                 'keywords section': 'IAO:0000630',
                                 'study limitations section': 'IAO:0000631',
                                 'materials section': 'IAO:0000633',
                                 'notes section': 'IAO:0000634',
                                 'patients section': 'IAO:0000635',
                                 'pre-publication history section': 'IAO:0000637',
                                 'related work section': 'IAO:0000639',
                                 'requirements section': 'IAO:0000641',
                                 'statistical analysis section': 'IAO:0000644',
                                 'tables section': 'IAO:0000645',
                                 'descriptive data section': 'IAO:0000701',
                                 'document title': 'IAO:0000305',
                                 'disclosure section': 'IAO:CUIless',
                                 'highlights section': 'IAO:CUIless'}.get(iao_term, "")

    return {"iao_name": iao_term, "iao_id": mapping_result_id_version}

def get_iao_term_mapping(section_heading):
    """Get the IAO term mapping for a given section heading.

    Args:
        section_heading: The name of the section heading.

    Returns:
        The IAO term mapping for the section heading.
    """
    mapping_dict = {'references section': ['web resources',
                  'literature cited',
                  'methods only references',
                  'methods-only references',
                  'online methods references',
                  'reference',
                  'reference list',
                  'references',
                  'references and notes',
                  'selected references',
                  'urls',
                  'web resources',
                  'web site references'],
                 'keywords section': ['keywords'],
                 'abbreviations section': ['abbreviation and acronyms',
                  'abbreviation list',
                  'abbreviations',
                  'abbreviations and acronyms',
                  'abbreviations list',
                  'abbreviations used',
                  'abbreviations used in this paper',
                  'definitions for abbreviations',
                  'glossary',
                  'key abbreviations',
                  'list of abbreviations',
                  'non-standard abbreviations',
                  'nonstandard abbreviations',
                  'nonstandard abbreviations and acronyms'],
                 'textual abstract section': ['abstract',
                  'background and summary',
                  'etoc',
                  'etoc blurb',
                  'precis',
                  'toc'],
                 'availability section': ['accession',
                  'accession numbers',
                  'availability of data and materials',
                  'data archiving',
                  'data availability',
                  'data availability and accession code availability',
                  'data availability statement',
                  'data citations',
                  'data description',
                  'data records',
                  'data sharing statement',
                  'transparency document'],
                 'acknowledgements section': ['acknowledgement',
                  'acknowledgements',
                  'acknowledgment',
                  'acknowledgments',
                  'acknowledgments and disclaimer',
                  'acknowledgments and funding',
                  'disclaimer',
                  'funding summary and acknowledgments'],
                 'funding source declaration section': ['acknowledgments and funding',
                  'consortia',
                  'financial support',
                  'funding',
                  'funding and disclosure',
                  'funding information',
                  'funding statement',
                  'funding summary and acknowledgments',
                  'grants',
                  'sources of funding',
                  'study funding'],
                 'supplementary material section': ['addendum',
                  'additional file',
                  'additional files',
                  'additional information',
                  'additional information and declarations',
                  'additional information and declarations',
                  'additional points',
                  'appendix',
                  'appendix a',
                  'appendix a.  supplementary data',
                  'appendix a. supplementary data',
                  'appendix. authors',
                  'electronic supplementary material',
                  'electronic supplementary materials',
                  'extended data',
                  'online content',
                  'supplemental data',
                  'supplemental information',
                  'supplemental material',
                  'supplementary data',
                  'supplementary figures and tables',
                  'supplementary files',
                  'supplementary information',
                  'supplementary material',
                  'supplementary material 1.',
                  'supplementary materials',
                  'supplementary materials figures',
                  'supplementary materials figures and tables',
                  'supplementary materials table',
                  'supplementary materials tables',
                  'supporting information',
                  'supporting information available'],
                 'methods section': ['analytical methods',
                  'concise methods',
                  'data and methods',
                  'detailed methods',
                  'experimental',
                  'experimental design',
                  'experimental methods',
                  'experimental procedures',
                  'experimental section',
                  'material and method',
                  'material and methods',
                  'material and methods sample collection and reagents',
                  'materials & methods',
                  'materials and method',
                  'materials and methods',
                  'method',
                  'method validation',
                  'methodology',
                  'methods',
                  'methods and design',
                  'methods and materials',
                  'methods and procedures',
                  'methods and tools',
                  'methods summary',
                  'methods/design',
                  'online methods',
                  'participant and methods',
                  'participants and methods',
                  'patient and methods',
                  'patients and methods',
                  'research design and methods',
                  'sample & methods',
                  'star methods',
                  'study design',
                  'study design and methods',
                  'study groups and methods',
                  'study population and methods',
                  'subjects and methods'],
                 'highlights section': ['article highlights',
                  'author summary',
                  'central illustration',
                  'editor summary',
                  "editor's summary",
                  'editor’s summary',
                  'highlights',
                  'key messages',
                  'key points',
                  'one sentence summary',
                  'overview',
                  'research in context',
                  'significance',
                  'significance statement',
                  'study highlights'],
                 'information\tdocument part': ['article'],
                 'associated data section': ['associated data'],
                 'author contributions section': ['author contribution',
                  'author contribution (in alphabetic order)',
                  'author contributions',
                  'authors contributions',
                  "authors' contribution",
                  "authors' contributions",
                  'authors’ contribution',
                  'authors’ contributions',
                  'authors’ roles',
                  'contributorship',
                  'main authors by consortium and author contributions'],
                 'disclosure section': ['author disclosure statement',
                  'declarations',
                  'disclosure',
                  'disclosure statement',
                  'disclosures',
                  'funding and disclosure'],
                 'author information section': ['author present address',
                  "authors' information",
                  'authors’ information',
                  'authorship',
                  'biographies',
                  'contributor information'],
                 'conflict of interest section': ["authors' disclosures of potential conflicts of interest",
                  'competing financial interests',
                  'competing interests',
                  'conflict of interest',
                  'conflict of interest statement',
                  'conflict of interests',
                  'conflicts of interest',
                  'declaration of competing interest',
                  'declaration of interest',
                  'declaration of interests',
                  'disclosure of conflict of interest',
                  'disclosure of potential conflicts of interest',
                  'duality of interest',
                  'statement of interest'],
                 'introduction section': ['background',
                  'introduction',
                  'introductory paragraph',
                  'main text'],
                 'discussion section': ['clinical applicability',
                  'discussion',
                  'discussion and conclusions',
                  'discussions',
                  'result and discussion',
                  'results and discussion',
                  'strengths and limitations',
                  'study strengths and limitations'],
                 'document part': ['comment',
                  'comments',
                  'formats:',
                  'full text',
                  'nutritional status',
                  'share',
                  'simple ncbi directory'],
                 'ethical approval section': ['compliance with ethical standards',
                  'ethical approval',
                  'ethical requirements',
                  'ethics',
                  'ethics approval and consent to participate',
                  'ethics statement',
                  'research involving human participants'],
                 'conclusion section': ['concluding remarks',
                  'conclusion',
                  'conclusion and perspectives',
                  'conclusions',
                  'conclusions and expert recommendations',
                  'conclusions and future directions',
                  'discussion and conclusions',
                  'future directions and conclusions',
                  'perspectives',
                  'summary',
                  'summary and conclusion'],
                 'future directions section': ['conclusions and future directions',
                  'future directions and conclusions',
                  'outlook'],
                 'consent section': ['consent for publication',
                  'informed consent',
                  'patient consent for publication'],
                 'materials section': ['data',
                  'data and methods',
                  'experimental design',
                  'material and method',
                  'material and methods',
                  'material and methods sample collection and reagents',
                  'materials',
                  'materials & methods',
                  'materials and method',
                  'materials and methods',
                  'methods and design',
                  'methods and materials',
                  'methods/design',
                  'research design and methods',
                  'sample & methods',
                  'study design and methods',
                  'study groups and methods'],
                 'statistical analysis section': ['data analysis',
                  'power calculation',
                  'statistical analysis',
                  'statistical methods',
                  'statistical methods and analysis',
                  'statistics'],
                 'figures section': ['figures and tables', 'supplementary materials figures'],
                 'tables section': ['figures and tables',
                  'supplementary materials table',
                  'supplementary materials tables'],
                 'footnote section': ['footnotes'],
                 'graphical abstract section': ['graphical abstract',
                  'toc image',
                  'visual abstract'],
                 'study limitations section': ['limitations',
                  'strengths and limitations',
                  'study limitations',
                  'study strengths and limitations'],
                 'notes section': ['notes',
                  "publisher's note",
                  'publisher’s note',
                  'references and notes'],
                 'participants section': ['participant and methods',
                  'participants',
                  'participants and methods',
                  'research involving human participants',
                  'study population',
                  'study population and methods',
                  'subjects and methods',
                  'subjects'],
                 'patent section': ['patents'],
                 'patients section': ['patient and methods',
                  'patient selection',
                  'patients and methods'],
                 'pre-publication history section': ['pre-publication history'],
                 'results section': ['result and discussion',
                  'results',
                  'results and discussion'],
                 'funding source declaration section ': ['role of the funding source',
                  'role of the study sponsor'],
                 'version number section': ['version changes']}
    tokenized_section_heading = nltk.wordpunct_tokenize(section_heading)
    text = nltk.Text(tokenized_section_heading)
    words = [w.lower() for w in text]
    h2_tmp = " ".join(word for word in words)

    # TODO: check for best match, not the first
    mapping_result = []
    if h2_tmp != "":
        if any(x in h2_tmp for x in [" and ", "&", "/"]):
            h2_parts = re.split(r" and |\s?/\s?|\s?&\s?", h2_tmp)
            for h2_part in h2_parts:
                h2_part = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_part)
                for IAO_term, heading_list in mapping_dict.items():
                    if any(
                        fuzz.ratio(h2_part, heading) >= 80 for heading in heading_list
                    ):
                        mapping_result.append(get_iao_term_to_id_mapping(IAO_term))
                        break

        else:
            for IAO_term, heading_list in mapping_dict.items():
                h2_tmp = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_tmp)
                if any([fuzz.ratio(h2_tmp, heading) > 80 for heading in heading_list]):
                    mapping_result = [get_iao_term_to_id_mapping(IAO_term)]
                    break

    if mapping_result == []:
        return [{"iao_name": "document part", "iao_id": "IAO:0000314"}]

    return mapping_result

def replace_spaces_and_newlines(input_string: str) -> str:
    """Replace multiple spaces and newline characters in a string with a single space.

    Args:
        input_string: The input string.

    Returns:
        The updated string.
    """
    # Replace multiple spaces (2 or more) with a single space
    input_string = re.sub(r" {2,}", " ", input_string)

    # Replace newline characters ('\n') with spaces
    input_string = input_string.replace("\n", " ")

    # Return the result
    return input_string


def _replace_match(match: re.Match) -> str:  # type: ignore [type-arg]
    """Get the Unicode character corresponding to the escape sequence in a regex match.

    Args:
        match: The regular expression match object.
            Must contain a Unicode escape sequence.

    Returns:
        The unicode character corresponding to the escape sequence.
    """
    # Extract the Unicode escape sequence (e.g., \uXXXX)
    unicode_escape = match.group(0)

    # Decode the escape sequence to get the corresponding character
    unicode_char = bytes(unicode_escape, "utf-8").decode("unicode_escape")

    # Return the result
    return unicode_char


def replace_unicode_escape(input_string: str):
    """Find and replace unicode escape sequences with the actual characters in a string.

    Args:
        input_string: The input string containing Unicode escape sequences.

    Returns:
        The updated string with Unicode escape sequences replaced by actual characters.
    """
    # Use a regular expression to find all Unicode escape sequences (e.g., \uXXXX)
    pattern = re.compile(r"\\u[0-9a-fA-F]{4}")
    # Replace Unicode escape sequences with actual characters
    output_string = pattern.sub(_replace_match, input_string)

    # Return the result
    return output_string


def fix_mojibake_string(bad_string):
    """Fix common mojibake encoding issues safely."""
    for enc_pair in [
        ("latin1", "utf-8"),
        ("utf-8", "latin1"),
        ("windows-1252", "utf-8"),
        ("utf-8", "windows-1252")
    ]:
        src, dest = enc_pair
        try:
            return bad_string.encode(src).decode(dest)
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    # If none worked, return original
    return bad_string


def extract_section_content(
    section: BeautifulSoup,
    soup2: BeautifulSoup,
    ori_title: BeautifulSoup,
    tag_title,
    tag_subtitle,
    text_list,
):
    """Extract the content of a section and its subsections recursively.

    Args:
        section: A BeautifulSoup ResultSet object representing a section of the document.
        soup2: A BeautifulSoup object representing the entire document.
        ori_title: The original title of the section.
        tag_title: It contains all the parent titles of all the sections identified for
            the document. This list is being updated in this function.
        tag_subtitle: It contains all the current titles of all the sections identified
            for the document. This list is being updated in this function.
        text_list: It contains all the current text of all the sections identified for
            the document. This list is being updated in this function.
    """
    # Extract the current section's title, or use the original title if none is found
    current_title = section.find("title")
    if current_title is None:  # If no title is found, fall back to the original title
        current_title = ori_title

    # If a title is available, attempt to locate it in the soup2 object
    if current_title:
        target_title = soup2.find(
            "title", string=current_title.text
        )  # Find the exact title in the soup2 object

        if target_title is not None:
            # Find the hierarchy of parent titles for the current title
            parent_titles = find_parent_titles(target_title)
        else:
            parent_titles = []

        # If there are multiple parent titles, exclude the last one (likely redundant)
        if len(parent_titles) > 1:
            parent_titles = parent_titles[:-1]
    else:
        parent_titles = None  # If no current title, set parent titles to None

    # Extract the content within the current section, specifically paragraphs (`<p>` tags)
    content = BeautifulSoup(
        "<sec" + str(section).split("<sec")[1], features="xml"
    ).find_all("p")

    # If content is found, process each paragraph
    if content:
        for i in range(len(content)):
            # Avoid adding duplicate or null content
            if f"{content[i]}" not in text_list and content[i] is not None:
                # If no parent titles are found, tag the content with 'Unknown'
                if parent_titles:
                    tag_title.append(parent_titles)
                else:
                    # Otherwise, tag it with the identified parent titles
                    tag_title.append(["document part"])

                # Similarly, handle subtitle tagging
                if current_title:
                    tag_subtitle.append([current_title.text])
                else:
                    tag_subtitle.append(["document part"])

                # Add the processed content to the text list
                text_list.append(f"{content[i]}")

    # Recursively process any subsections within the current section
    subsections = section.find_all("sec")
    for subsection in subsections:
        extract_section_content(
            subsection, soup2, ori_title, tag_title, tag_subtitle, text_list
        )


def find_parent_titles(title_element):
    """Find the parent titles of a given title element in the document hierarchy.

    Args:
        title_element: A BeautifulSoup Tag or NavigableString object representing a
            title element.

    Returns:
        A list of parent titles in the document hierarchy.
    """
    # Initialize an empty list to store parent titles
    parent_titles: list[str] = []

    # Find the immediate parent <sec> element of the given title element
    parent = title_element.find_parent(["sec"])

    # Traverse up the hierarchy of <sec> elements
    while parent:
        # Look for a <title> within the current parent <sec>
        title = parent.find("title")
        if title:
            # If a title is found, add it to the beginning of the parent_titles list
            parent_titles.insert(0, title.text)

        # Move up to the next parent <sec> in the hierarchy
        parent = parent.find_parent(["sec"])

    # Return the list of parent titles, ordered from topmost to immediate parent
    return parent_titles


def convert_xml_to_json(path):
    """This function takes a path to the XML file and convert it to BioC JSON.

    Args:
        path: The path to the xml file.

    Returns:
        A Dictionary in BioC format
    """
    # Open the XML file located at the specified path
    with open(path, encoding="utf-8") as xml_file:
        # Read the contents of the XML file into a string
        text = xml_file.read()

    # Parse the XML content using BeautifulSoup with the 'lxml' parser
    soup = BeautifulSoup(text, features="xml")

    # Clean unwanted tags
    tags_to_remove = [
        "table-wrap",
        "table",
        "table-wrap-foot",
        "inline-formula",
        "fig",
        "graphic",
        "inline-graphic",
        "inline-supplementary-material",
        "media",
        "tex-math",
        "sub-article",
    ]
    for tag in tags_to_remove:
        for element in soup.find_all(tag):
            element.extract()

    # Set the source method description for tracking
    source_method = "Auto-CORPus (XML)"

    # Get the current date in the format 'YYYYMMDD'
    date = datetime.now().strftime("%Y%m%d")

    # Check if the text content, after replacing the any characters contained between < >, of the 'license-p' tag within the 'front' section is not 'None'
    if re.sub("<[^>]+>", "", str(soup.find("front").find("license-p"))) != "None":
        # Extract the content of the 'license-p' tag and remove all the characters between < and >
        license_xml = re.sub("<[^>]+>", "", str(soup.find("license-p")))

        # Replace Unicode escape sequences in the extracted license content with the helper function defines above
        license_xml = replace_unicode_escape(license_xml)

        # Remove excess spaces and newlines from the processed license content with the helper function defines above
        license_xml = replace_spaces_and_newlines(license_xml)
    else:
        # If the 'license-p' tag is not found or has no content, assign an empty string
        license_xml = ""

    # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'pmid' exists in the soup
    ### no check for unicode or hexacode or XML tags
    if soup.find("article-id", {"pub-id-type": "pmid"}) is not None:
        # Extract the text content of the 'article-id' tag with 'pub-id-type' set to 'pmid'
        pmid_xml = soup.find("article-id", {"pub-id-type": "pmid"}).text
    else:
        # If the tag is not found, assign an empty string as the default value
        pmid_xml = ""

    # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'pmcid' exists in the soup
    ### no check for unicode or hexacode or XML tags
    if soup.find("article-id", {"pub-id-type": "pmcid"}) is not None:
        # Extract the text content of the 'article-id' tag and prepend 'PMC' to it
        pmcid_xml = "PMC" + soup.find("article-id", {"pub-id-type": "pmcid"}).text
        # Old PMC files does not include PMC when the new ones include PMC
        pmcid_xml = pmcid_xml.replace("PMCPMC", "PMC")

        # Construct the PMC article URL using the extracted PMCID
        pmc_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid_xml}/"
    else:
        # If the tag is not found, assign default empty strings for both variables
        pmcid_xml = ""
        pmc_link = ""

    # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'doi' exists in the soup
    ### no check for unicode or hexacode or XML tags
    if soup.find("article-id", {"pub-id-type": "doi"}) is not None:
        # Extract the text content of the 'article-id' tag with 'pub-id-type' set to 'doi'
        doi_xml = soup.find("article-id", {"pub-id-type": "doi"}).text
    else:
        # If the tag is not found, assign an empty string to the 'doi_xml' variable
        doi_xml = ""

    # Check if the 'journal-title' tag exists within 'front', and if it contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
    ### no check for unicode or hexacode
    if re.sub("<[^>]+>", "", str(soup.find("front").find("journal-title"))) != "None":
        # If valid text exists, remove XML tags and extract the content
        journal_xml = re.sub("<[^>]+>", "", str(soup.find("journal-title")))
    else:
        # If the tag is not found or contains no text, assign an empty string
        journal_xml = ""

    # Check if the 'subject' tag exists within 'article-categories', and if it contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
    if (
        re.sub("<[^>]+>", "", str(soup.find("article-categories").find("subject")))
        != "None"
    ):
        # If valid text exists, remove XML tags and extract the content
        pub_type_xml = re.sub("<[^>]+>", "", str(soup.find("subject")))
    else:
        # If the tag is not found or contains no text, assign an empty string
        pub_type_xml = ""

    # Check if the 'accepted' date is found within 'date', and if it contains a 'year' tag
    ### no check for unicode or hexacode or XML tags
    if soup.find("date", {"date-type": "accepted"}) is not None:
        if soup.find("date", {"date-type": "accepted"}).find("year") is not None:
            # Extract the text content of the 'year' tag if found
            year_xml = soup.find("date", {"date-type": "accepted"}).find("year").text
        else:
            # If 'year' is missing, assign an empty string
            year_xml = ""
    else:
        # If 'accepted' date is missing, assign an empty string
        year_xml = ""

    # Initialize variables to store the offset, text, and tag-related information
    offset = 0
    offset_list = []
    text_list = []
    tag_title = []
    tag_subtitle = []

    # Check if the 'article-title' tag exists and contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
    if re.sub("<[^>]+>", "", str(soup.find("article-title"))) != "None":
        # If valid text exists, remove XML tags and append it to text_list
        # > and <, some other special character, are actually present in the title they would be converted to their 'human' form, unicode and hexacode is check later
        text_list.append(re.sub("<[^>]+>", "", str(soup.find("article-title"))))
        # Append corresponding titles for the tag
        tag_title.append(["document title"])
        tag_subtitle.append(["document title"])

    # Check if the 'kwd-group' (keyword) tag exists and contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
    kwd_groups = soup.find_all("kwd-group")  # Store result to avoid repeated calls
    for kwd in kwd_groups:
        # Skip kwd-group if xml:lang is present and not 'en'
        if kwd.has_attr("xml:lang") and kwd["xml:lang"] != "en":
            continue
        # Find the title (if it exists)
        title_tag = kwd.find("title")
        if title_tag is None:
            # Extract text from each <kwd>, ensuring inline elements stay together
            kwd_texts = [
                kwd_item.get_text(separator="", strip=True)
                for kwd_item in kwd.find_all("kwd")
            ]

            # Join <kwd> elements with "; " while keeping inline formatting intact
            remaining_text = "; ".join(kwd_texts)

            if remaining_text:
                tag_title.append(["Keywords"])
                tag_subtitle.append(["Keywords"])
                text_list.append(
                    str(remaining_text)
                )  # Print remaining content only if it exists
        else:
            if "abbr" not in title_tag.text.lower():
                # Extract text from each <kwd>, ensuring inline elements stay together
                kwd_texts = [
                    kwd_item.get_text(separator="", strip=True)
                    for kwd_item in kwd.find_all("kwd")
                ]

                # Join <kwd> elements with "; " while keeping inline formatting intact
                remaining_text = "; ".join(kwd_texts)

                # If a title exists, remove it from the remaining text
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    remaining_text = remaining_text.replace(title_text, "", 1).strip()

                if remaining_text:
                    tag_title.append(["Keywords"])
                    tag_subtitle.append([str(title_tag.text)])
                    text_list.append(
                        str(remaining_text)
                    )  # Print remaining content only if it exists

    # Check if the 'abstract' tag exists and contains valid text (stripping XML tags if there any text left)
    # ALL ABSTRACT CODE: Special characters, i.e. < and >, are converted to human form and unicode and hexacode is replaced later
    if re.sub("<[^>]+>", "", str(soup.find("abstract"))) != "None":
        # If there is only one 'abstract' tag (often would be at the form of unstructured abstract)
        if len(soup.find_all("abstract")) == 1:
            # Check if the 'abstract' tag contains any 'title' elements (if 1 unstructured otherwise might be structured)
            if len(soup.find("abstract").find_all("title")) > 0:
                # Iterate over each 'title' found in the 'abstract' tag (create the passages with different abstract heading i.e structuring the abstract)
                for title in soup.find("abstract").find_all("title"):
                    title_text = title.text
                    p_tags = []

                    # Find all sibling 'p' (paragraph) tags following the title (merging the text with the same title)
                    next_sibling = title.find_next_sibling("p")
                    while (
                        next_sibling and next_sibling.name == "p"
                    ):  # Check for 'p' elements
                        p_tags.append(next_sibling)
                        next_sibling = next_sibling.find_next_sibling()  # Get next sibling until no more then None and leave the while loop

                    # Append the text of each 'p' tag to 'text_list' and assign titles/subtitles
                    for p_tag in p_tags:
                        tag_title.append(["Abstract"])
                        tag_subtitle.append(
                            [title_text]
                        )  # Title text from the 'title' tag
                        text_list.append(
                            p_tag.text
                        )  # Content of the 'p' tag (paragraph)

            else:
                # If no 'title' elements are found within the 'abstract', store the whole abstract text (100% unstructured abstract from publisher XML tags)
                text_list.append(str(re.sub("<[^>]+>", "", str(soup.abstract))))
                tag_title.append(["Abstract"])
                tag_subtitle.append(["Abstract"])

        # If there are multiple 'abstract' tags (structured abstract from the XML markup)
        elif len(soup.find_all("abstract")) > 1:
            # Iterate through all 'abstract' tags
            for notes in soup.find_all("abstract"):
                # Check if the 'abstract' tag contains any 'title' elements
                if len(notes.find_all("title")) > 0:
                    # Iterate over each 'title' found in the 'abstract' tag
                    for title in notes.find_all("title"):
                        title_text = title.text
                        p_tags = []

                        # Find all sibling 'p' (paragraph) tags following the title (merging the text with the same title)
                        next_sibling = title.find_next_sibling("p")
                        while (
                            next_sibling and next_sibling.name == "p"
                        ):  # Check for 'p' elements
                            p_tags.append(next_sibling)
                            next_sibling = next_sibling.find_next_sibling()  # Get next sibling until no more then None and leave the while loop

                        # Append the text of each 'p' tag to 'text_list' and assign titles/subtitles
                        for p_tag in p_tags:
                            tag_title.append(["Abstract"])
                            tag_subtitle.append(
                                [title_text]
                            )  # Title text from the 'title' tag
                            text_list.append(
                                p_tag.text
                            )  # Content of the 'p' tag (paragraph)

                else:
                    # If no 'title' elements are found, just append the whole 'abstract' text (becomes multiple pasages without structure)
                    text_list.append(notes)
                    tag_title.append(["Abstract"])
                    tag_subtitle.append(["Abstract"])

        else:
            # If there is no abstract or it doesn't match any conditions, do nothing
            pass

    ############### <p> outside of <sec>
    output_p = []  # Store the result for all documents

    with open(path, encoding="utf-8") as xml_file:
        text = xml_file.read()
        soup3 = BeautifulSoup(text, features="xml")

    # Clean unwanted tags
    tags_to_remove = [
        "table-wrap",
        "table",
        "table-wrap-foot",
        "inline-formula",
        "front",
        "back",
        "fig",
        "graphic",
        "inline-graphic",
        "inline-supplementary-material",
        "media",
        "tex-math",
        "sub-article",
        "def-list",
        "notes",
    ]
    for tag in tags_to_remove:
        for element in soup3.find_all(tag):
            element.extract()

    # Extract body
    body = soup3.body
    if not body:
        return

    # Identify all paragraphs inside and outside <sec>
    all_p_in_body = body.find_all("p")

    # Identify paragraphs inside <sec> and <boxed-text> to avoid duplication
    p_inside_sections = set()
    p_inside_boxed = set()

    for sec in body.find_all("sec"):
        p_inside_sections.update(sec.find_all("p"))

    for boxed in body.find_all("boxed-text"):
        p_inside_boxed.update(boxed.find_all("p"))

    # Filter paragraphs outside <sec> and <boxed-text>
    p_outside = [
        p
        for p in all_p_in_body
        if p not in p_inside_sections and p not in p_inside_boxed
    ]

    # Generate pairs without duplication
    pairs = []
    prev_group = []
    next_group = []

    i = 0
    while i < len(p_outside):
        next_group = []

        # Aggregate consecutive outside paragraphs
        while i < len(p_outside):
            next_group.append(p_outside[i])
            # Check if the next paragraph is also outside <sec> and <boxed-text>
            if (
                i + 1 < len(p_outside)
                and all_p_in_body.index(p_outside[i + 1])
                == all_p_in_body.index(p_outside[i]) + 1
            ):
                i += 1
            else:
                break
        i += 1

        # Append the pair
        pairs.append([prev_group, next_group])

        # Prepare for the next iteration
        prev_group = next_group

    # Store the result for the current file
    output_p.append({"file": str(path), "pairs": pairs})

    # Print the result
    for doc in output_p:
        if len(doc["pairs"]) == 1 and doc["pairs"][0][0] == []:
            current_intro_list = []
            for i in range(len(doc["pairs"][0][1])):
                if (
                    "boxed-text" not in str(doc["pairs"][0][1])
                    and len(doc["pairs"][0][1]) == 1
                    and "</sec>" not in str(doc["pairs"][0][1])
                ):
                    doc["pairs"][0][1][i] = re.sub(
                        "<p[^>]*>", "<p>", str(doc["pairs"][0][1][i])
                    )
                    for j in range(len(doc["pairs"][0][1][i].split("<p>"))):
                        # Check if the current section (split by <p>) is not empty after removing </p> tags
                        if (
                            doc["pairs"][0][1][i].split("<p>")[j].replace("</p>", "")
                            != ""
                        ):
                            # Remove all tags from the current p text from the current item of the text_list
                            new_text = str(
                                re.sub(
                                    "<[^>]+>",
                                    "",
                                    str(doc["pairs"][0][1][i].split("<p>")[j]),
                                )
                            )
                            # Replace unicode and hexacode, using the function introduced above
                            new_text = replace_unicode_escape(new_text)
                            # Replace spaces and newlines, using the function introduced above
                            new_text = replace_spaces_and_newlines(new_text)
                            # Clean up special characters
                            # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                            new_text = (
                                new_text.replace("</p>", "")
                                .replace("&lt;", "<")
                                .replace("&gt;", ">")
                                .replace("&amp;", "&")
                                .replace("&apos;", "'")
                                .replace("&quot;", '"')
                            )

                            if len(new_text) < 6:
                                pass
                            else:
                                current_intro_list.append(new_text)

                                # Update the offset list (keeps track of the position in the document)
                                # offset_list.append(offset)

                                # Increment the offset by the length of the new text + 1 (for spacing or next content)
                                # offset += len(new_text) + 1
                        else:
                            # If the current section is empty after removing </p>, skip it
                            pass

                elif (
                    "boxed-text" not in str(doc["pairs"][0][1])
                    and len(doc["pairs"][0][1]) > 1
                    and "</sec>" not in str(doc["pairs"][0][1])
                ):
                    doc["pairs"][0][1][i] = re.sub(
                        "<p[^>]*>", "<p>", str(doc["pairs"][0][1][i])
                    )
                    for j in range(len(doc["pairs"][0][1][i].split("<p>"))):
                        # Check if the current section (split by <p>) is not empty after removing </p> tags
                        if (
                            doc["pairs"][0][1][i].split("<p>")[j].replace("</p>", "")
                            != ""
                        ):
                            # Remove all tags from the current p text from the current item of the text_list
                            new_text = str(
                                re.sub(
                                    "<[^>]+>",
                                    "",
                                    str(doc["pairs"][0][1][i].split("<p>")[j]),
                                )
                            )
                            # Replace unicode and hexacode, using the function introduced above
                            new_text = replace_unicode_escape(new_text)
                            # Replace spaces and newlines, using the function introduced above
                            new_text = replace_spaces_and_newlines(new_text)
                            # Clean up special characters
                            # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                            new_text = (
                                new_text.replace("</p>", "")
                                .replace("&lt;", "<")
                                .replace("&gt;", ">")
                                .replace("&amp;", "&")
                                .replace("&apos;", "'")
                                .replace("&quot;", '"')
                            )

                            if len(new_text) < 6:
                                pass
                            else:
                                current_intro_list.append(new_text)

                                # Update the offset list (keeps track of the position in the document)
                                # offset_list.append(offset)

                                # Increment the offset by the length of the new text + 1 (for spacing or next content)
                                # offset += len(new_text) + 1
                        else:
                            # If the current section is empty after removing </p>, skip it
                            pass
                else:
                    if (
                        "<caption>" in str(doc["pairs"][0][1][i])
                        and len(doc["pairs"][0][1]) == 1
                    ):
                        if "</sec>" in str(doc["pairs"][0][1][i]):
                            for j in range(
                                len(
                                    str(doc["pairs"][0][1][i])
                                    .split("</caption>")[-1]
                                    .split("</sec>")
                                )
                                - 1
                            ):
                                if (
                                    re.sub(
                                        "<[^>]+>",
                                        "",
                                        str(doc["pairs"][0][1][i])
                                        .split("</caption>")[-1]
                                        .split("</sec>")[j]
                                        .split("</title>")[-1]
                                        .replace("\n", ""),
                                    )
                                    != ""
                                ):
                                    tag_title.append(
                                        [
                                            re.sub(
                                                "<[^>]+>",
                                                "",
                                                str(doc["pairs"][0][1][i])
                                                .split("<caption>")[-1]
                                                .split("</caption>")[0],
                                            )
                                        ]
                                    )
                                    tag_subtitle.append(
                                        [
                                            str(doc["pairs"][0][1][i])
                                            .split("</caption>")[-1]
                                            .split("</sec>")[j]
                                            .split("<title>")[-1]
                                            .split("</title>")[0]
                                        ]
                                    )
                                    text_list.append(
                                        re.sub(
                                            "<[^>]+>",
                                            " ",
                                            str(doc["pairs"][0][1][i])
                                            .split("</caption>")[-1]
                                            .split("</sec>")[j]
                                            .split("</title>")[-1]
                                            .replace("\n", ""),
                                        )
                                    )
                        else:
                            current_subtitle = ""
                            for j in range(
                                len(
                                    str(doc["pairs"][0][1][i])
                                    .split("</caption>")[-1]
                                    .split("</p>")
                                )
                            ):
                                if (
                                    re.sub(
                                        "<[^>]+>",
                                        "",
                                        str(doc["pairs"][0][1][i])
                                        .split("</caption>")[-1]
                                        .split("</p>")[j]
                                        .split("</title>")[-1]
                                        .replace("\n", ""),
                                    )
                                    != ""
                                ):
                                    tag_title.append(
                                        [
                                            re.sub(
                                                "<[^>]+>",
                                                "",
                                                str(doc["pairs"][0][1][i])
                                                .split("<caption>")[-1]
                                                .split("</caption>")[0],
                                            )
                                        ]
                                    )
                                    if current_subtitle == "":
                                        current_subtitle = re.sub(
                                            "<[^>]+>",
                                            "",
                                            str(doc["pairs"][0][1][i])
                                            .split("<caption>")[-1]
                                            .split("</caption>")[0],
                                        )
                                    if (
                                        "</title>"
                                        in str(doc["pairs"][0][1][i])
                                        .split("</caption>")[-1]
                                        .split("</p>")[j]
                                    ):
                                        tag_subtitle.append(
                                            [
                                                str(doc["pairs"][0][1][i])
                                                .split("</caption>")[-1]
                                                .split("</sec>")[j]
                                                .split("<title>")[-1]
                                                .split("</title>")[0]
                                            ]
                                        )
                                    else:
                                        tag_subtitle.append([current_subtitle])
                                    text_list.append(
                                        re.sub(
                                            "<[^>]+>",
                                            "",
                                            str(doc["pairs"][0][1][i])
                                            .split("</caption>")[-1]
                                            .split("</p>")[j]
                                            .split("</title>")[-1]
                                            .replace("\n", ""),
                                        )
                                    )
                    elif (
                        re.sub(
                            "<[^>]+>",
                            "",
                            "</title>".join(
                                str(doc["pairs"][0][1][i]).split("</title>")[:2]
                            )
                            .split("<title>")[1]
                            .split("</title>")[-1],
                        )
                        == ""
                        and len(doc["pairs"][0][1]) == 1
                        and "</sec>" not in str(doc["pairs"][0][1])
                    ):
                        curent_subtitle = ""
                        for j in range(
                            len(
                                "</title>".join(
                                    str(doc["pairs"][0][1][i]).split("</title>")[1:]
                                ).split("</p>")
                            )
                        ):
                            if (
                                re.sub(
                                    "<[^>]+>",
                                    "",
                                    "</title>".join(
                                        str(doc["pairs"][0][1][i]).split("</title>")[1:]
                                    )
                                    .split("</p>")[j]
                                    .split("</title>")[-1]
                                    .replace("\n", ""),
                                )
                                != ""
                            ):
                                tag_title.append(
                                    [
                                        "</title>".join(
                                            str(doc["pairs"][0][1][i]).split(
                                                "</title>"
                                            )[:2]
                                        )
                                        .split("<title>")[1]
                                        .split("</title>")[0]
                                    ]
                                )
                                if curent_subtitle == "":
                                    curent_subtitle = (
                                        "</title>".join(
                                            str(doc["pairs"][0][1][i]).split(
                                                "</title>"
                                            )[:2]
                                        )
                                        .split("<title>")[1]
                                        .split("</title>")[0]
                                    )
                                if (
                                    "<title>"
                                    in "</title>".join(
                                        str(doc["pairs"][0][1][i]).split("</title>")[1:]
                                    ).split("</p>")[j]
                                ):
                                    curent_subtitle = (
                                        "</title>".join(
                                            str(doc["pairs"][0][1][i]).split(
                                                "</title>"
                                            )[1:]
                                        )
                                        .split("</p>")[j]
                                        .split("<title>")[-1]
                                        .split("</title>")[0]
                                    )
                                tag_subtitle.append([curent_subtitle])
                                text_list.append(
                                    re.sub(
                                        "<[^>]+>",
                                        "",
                                        "</title>".join(
                                            str(doc["pairs"][0][1][i]).split(
                                                "</title>"
                                            )[1:]
                                        )
                                        .split("</p>")[j]
                                        .split("</title>")[-1]
                                        .replace("\n", ""),
                                    )
                                )
                    else:
                        if "</sec>" not in str(doc["pairs"][0][1]):
                            for pair in doc["pairs"]:
                                print("\nPrevious:", [str(p) for p in pair[0]])
                                print("\nNext:", [str(p) for p in pair[1]])
                                print("=" * 80)
            if len(current_intro_list) == 0:
                pass
            elif len(current_intro_list) == 1:
                # Append the corresponding tag title and tag subtitle for the section
                # corrected_section.append(tag_title[i])
                tag_title.append(["document part"])
                # corrected_subsection.append(tag_subtitle[i])
                tag_subtitle.append(["document part"])
                # Append the corrected text to the corrected_text list
                # corrected_text.append(new_text)
                text_list.append(current_intro_list[0])
            else:
                for j in range(len(current_intro_list)):
                    # Append the corresponding tag title and tag subtitle for the section
                    # corrected_section.append(tag_title[i])
                    tag_title.append(["introduction"])
                    # corrected_subsection.append(tag_subtitle[i])
                    tag_subtitle.append(["introduction"])
                    # Append the corrected text to the corrected_text list
                    # corrected_text.append(new_text)
                    text_list.append(current_intro_list[j])
        else:
            trigger_previous = True
            for z in range(1, len(doc["pairs"])):
                if (
                    doc["pairs"][z - 1][1] != doc["pairs"][z][0]
                    or doc["pairs"][0][0] != []
                ):
                    trigger_previous = False
            if trigger_previous:
                for z in range(len(doc["pairs"])):
                    current_intro_list = []
                    for i in range(len(doc["pairs"][z][1])):
                        if (
                            "boxed-text" not in str(doc["pairs"][z][1])
                            and len(doc["pairs"][z][1]) == 1
                            and "</sec>" not in str(doc["pairs"][z][1])
                        ):
                            doc["pairs"][z][1][i] = re.sub(
                                "<p[^>]*>", "<p>", str(doc["pairs"][z][1][i])
                            )
                            for j in range(len(doc["pairs"][z][1][i].split("<p>"))):
                                # Check if the current section (split by <p>) is not empty after removing </p> tags
                                if (
                                    doc["pairs"][z][1][i]
                                    .split("<p>")[j]
                                    .replace("</p>", "")
                                    != ""
                                ):
                                    # Remove all tags from the current p text from the current item of the text_list
                                    new_text = str(
                                        re.sub(
                                            "<[^>]+>",
                                            "",
                                            str(doc["pairs"][z][1][i].split("<p>")[j]),
                                        )
                                    )
                                    # Replace unicode and hexacode, using the function introduced above
                                    new_text = replace_unicode_escape(new_text)
                                    # Replace spaces and newlines, using the function introduced above
                                    new_text = replace_spaces_and_newlines(new_text)
                                    # Clean up special characters
                                    # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                                    new_text = (
                                        new_text.replace("</p>", "")
                                        .replace("&lt;", "<")
                                        .replace("&gt;", ">")
                                        .replace("&amp;", "&")
                                        .replace("&apos;", "'")
                                        .replace("&quot;", '"')
                                    )

                                    if len(new_text) < 6:
                                        pass
                                    else:
                                        current_intro_list.append(new_text)

                                        # Update the offset list (keeps track of the position in the document)
                                        # offset_list.append(offset)

                                        # Increment the offset by the length of the new text + 1 (for spacing or next content)
                                        # offset += len(new_text) + 1
                                else:
                                    # If the current section is empty after removing </p>, skip it
                                    pass

                        elif (
                            "boxed-text" not in str(doc["pairs"][z][1])
                            and len(doc["pairs"][z][1]) > 1
                            and "</sec>" not in str(doc["pairs"][z][1])
                        ):
                            doc["pairs"][z][1][i] = re.sub(
                                "<p[^>]*>", "<p>", str(doc["pairs"][z][1][i])
                            )
                            for j in range(len(doc["pairs"][z][1][i].split("<p>"))):
                                # Check if the current section (split by <p>) is not empty after removing </p> tags
                                if (
                                    doc["pairs"][z][1][i]
                                    .split("<p>")[j]
                                    .replace("</p>", "")
                                    != ""
                                ):
                                    # Remove all tags from the current p text from the current item of the text_list
                                    new_text = str(
                                        re.sub(
                                            "<[^>]+>",
                                            "",
                                            str(doc["pairs"][z][1][i].split("<p>")[j]),
                                        )
                                    )
                                    # Replace unicode and hexacode, using the function introduced above
                                    new_text = replace_unicode_escape(new_text)
                                    # Replace spaces and newlines, using the function introduced above
                                    new_text = replace_spaces_and_newlines(new_text)
                                    # Clean up special characters
                                    # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                                    new_text = (
                                        new_text.replace("</p>", "")
                                        .replace("&lt;", "<")
                                        .replace("&gt;", ">")
                                        .replace("&amp;", "&")
                                        .replace("&apos;", "'")
                                        .replace("&quot;", '"')
                                    )

                                    if len(new_text) < 6:
                                        pass
                                    else:
                                        current_intro_list.append(new_text)

                                        # Update the offset list (keeps track of the position in the document)
                                        # offset_list.append(offset)

                                        # Increment the offset by the length of the new text + 1 (for spacing or next content)
                                        # offset += len(new_text) + 1
                                else:
                                    # If the current section is empty after removing </p>, skip it
                                    pass
                        else:
                            if (
                                "<caption>" in str(doc["pairs"][z][1][i])
                                and len(doc["pairs"][z][1]) == 1
                            ):
                                if "</sec>" in str(doc["pairs"][z][1][i]):
                                    for j in range(
                                        len(
                                            str(doc["pairs"][z][1][i])
                                            .split("</caption>")[-1]
                                            .split("</sec>")
                                        )
                                        - 1
                                    ):
                                        if (
                                            re.sub(
                                                "<[^>]+>",
                                                "",
                                                str(doc["pairs"][z][1][i])
                                                .split("</caption>")[-1]
                                                .split("</sec>")[j]
                                                .split("</title>")[-1]
                                                .replace("\n", ""),
                                            )
                                            != ""
                                        ):
                                            tag_title.append(
                                                [
                                                    re.sub(
                                                        "<[^>]+>",
                                                        "",
                                                        str(doc["pairs"][z][1][i])
                                                        .split("<caption>")[-1]
                                                        .split("</caption>")[0],
                                                    )
                                                ]
                                            )
                                            tag_subtitle.append(
                                                [
                                                    str(doc["pairs"][z][1][i])
                                                    .split("</caption>")[-1]
                                                    .split("</sec>")[j]
                                                    .split("<title>")[-1]
                                                    .split("</title>")[0]
                                                ]
                                            )
                                            text_list.append(
                                                re.sub(
                                                    "<[^>]+>",
                                                    " ",
                                                    str(doc["pairs"][z][1][i])
                                                    .split("</caption>")[-1]
                                                    .split("</sec>")[j]
                                                    .split("</title>")[-1]
                                                    .replace("\n", ""),
                                                )
                                            )
                                else:
                                    current_subtitle = ""
                                    for j in range(
                                        len(
                                            str(doc["pairs"][z][1][i])
                                            .split("</caption>")[-1]
                                            .split("</p>")
                                        )
                                    ):
                                        if (
                                            re.sub(
                                                "<[^>]+>",
                                                "",
                                                str(doc["pairs"][z][1][i])
                                                .split("</caption>")[-1]
                                                .split("</p>")[j]
                                                .split("</title>")[-1]
                                                .replace("\n", ""),
                                            )
                                            != ""
                                        ):
                                            tag_title.append(
                                                [
                                                    re.sub(
                                                        "<[^>]+>",
                                                        "",
                                                        str(doc["pairs"][z][1][i])
                                                        .split("<caption>")[-1]
                                                        .split("</caption>")[0],
                                                    )
                                                ]
                                            )
                                            if current_subtitle == "":
                                                current_subtitle = re.sub(
                                                    "<[^>]+>",
                                                    "",
                                                    str(doc["pairs"][z][1][i])
                                                    .split("<caption>")[-1]
                                                    .split("</caption>")[0],
                                                )
                                            if (
                                                "</title>"
                                                in str(doc["pairs"][z][1][i])
                                                .split("</caption>")[-1]
                                                .split("</p>")[j]
                                            ):
                                                tag_subtitle.append(
                                                    [
                                                        str(doc["pairs"][z][1][i])
                                                        .split("</caption>")[-1]
                                                        .split("</sec>")[j]
                                                        .split("<title>")[-1]
                                                        .split("</title>")[0]
                                                    ]
                                                )
                                            else:
                                                tag_subtitle.append([current_subtitle])
                                            text_list.append(
                                                re.sub(
                                                    "<[^>]+>",
                                                    "",
                                                    str(doc["pairs"][z][1][i])
                                                    .split("</caption>")[-1]
                                                    .split("</p>")[j]
                                                    .split("</title>")[-1]
                                                    .replace("\n", ""),
                                                )
                                            )
                            elif (
                                re.sub(
                                    "<[^>]+>",
                                    "",
                                    "</title>".join(
                                        str(doc["pairs"][z][1][i]).split("</title>")[:2]
                                    )
                                    .split("<title>")[1]
                                    .split("</title>")[-1],
                                )
                                == ""
                                and len(doc["pairs"][z][1]) == 1
                                and "</sec>" not in str(doc["pairs"][z][1])
                            ):
                                curent_subtitle = ""
                                for j in range(
                                    len(
                                        "</title>".join(
                                            str(doc["pairs"][z][1][i]).split(
                                                "</title>"
                                            )[1:]
                                        ).split("</p>")
                                    )
                                ):
                                    if (
                                        re.sub(
                                            "<[^>]+>",
                                            "",
                                            "</title>".join(
                                                str(doc["pairs"][z][1][i]).split(
                                                    "</title>"
                                                )[1:]
                                            )
                                            .split("</p>")[j]
                                            .split("</title>")[-1]
                                            .replace("\n", ""),
                                        )
                                        != ""
                                    ):
                                        tag_title.append(
                                            [
                                                "</title>".join(
                                                    str(doc["pairs"][z][1][i]).split(
                                                        "</title>"
                                                    )[:2]
                                                )
                                                .split("<title>")[1]
                                                .split("</title>")[0]
                                            ]
                                        )
                                        if curent_subtitle == "":
                                            curent_subtitle = (
                                                "</title>".join(
                                                    str(doc["pairs"][z][1][i]).split(
                                                        "</title>"
                                                    )[:2]
                                                )
                                                .split("<title>")[1]
                                                .split("</title>")[0]
                                            )
                                        if (
                                            "<title>"
                                            in "</title>".join(
                                                str(doc["pairs"][z][1][i]).split(
                                                    "</title>"
                                                )[1:]
                                            ).split("</p>")[j]
                                        ):
                                            curent_subtitle = (
                                                "</title>".join(
                                                    str(doc["pairs"][z][1][i]).split(
                                                        "</title>"
                                                    )[1:]
                                                )
                                                .split("</p>")[j]
                                                .split("<title>")[-1]
                                                .split("</title>")[0]
                                            )
                                        tag_subtitle.append([curent_subtitle])
                                        text_list.append(
                                            re.sub(
                                                "<[^>]+>",
                                                "",
                                                "</title>".join(
                                                    str(doc["pairs"][z][1][i]).split(
                                                        "</title>"
                                                    )[1:]
                                                )
                                                .split("</p>")[j]
                                                .split("</title>")[-1]
                                                .replace("\n", ""),
                                            )
                                        )
                            else:
                                if "</sec>" not in str(doc["pairs"][z][1]):
                                    for pair in doc["pairs"]:
                                        print(
                                            "\nPrevious:",
                                            [str(p) for p in pair[0]],
                                        )
                                        print("\nNext:", [str(p) for p in pair[1]])
                                        print("=" * 80)
                    if len(current_intro_list) == 0:
                        pass
                    elif len(current_intro_list) == 1:
                        # Append the corresponding tag title and tag subtitle for the section
                        # corrected_section.append(tag_title[i])
                        tag_title.append(["document part"])
                        # corrected_subsection.append(tag_subtitle[i])
                        tag_subtitle.append(["document part"])
                        # Append the corrected text to the corrected_text list
                        # corrected_text.append(new_text)
                        text_list.append(current_intro_list[0])
                    else:
                        for j in range(len(current_intro_list)):
                            # Append the corresponding tag title and tag subtitle for the section
                            # corrected_section.append(tag_title[i])
                            tag_title.append(["introduction"])
                            # corrected_subsection.append(tag_subtitle[i])
                            tag_subtitle.append(["introduction"])
                            # Append the corrected text to the corrected_text list
                            # corrected_text.append(new_text)
                            text_list.append(current_intro_list[j])
            else:
                for pair in doc["pairs"]:
                    print("\nPrevious:", [str(p) for p in pair[0]])
                    print("\nNext:", [str(p) for p in pair[1]])
                    print("=" * 80)
    ################### <p> outside section

    # Create a second soup object to perform modification of its content without modify the original soup object where more information will be extracted later in the code
    soup2 = BeautifulSoup(text, features="xml")

    tableswrap_to_remove = soup2.find_all("table-wrap")
    # Iterate through the tables present in the 'table-wrap' tag and remove them from the soup object regardless of where in the soup the tag is present
    for tablewrap in tableswrap_to_remove:
        tablewrap.extract()

    tables_to_remove = soup2.find_all("table")
    # Iterate through the tables present in the 'table' tag and remove them from the soup object regardless of where in the soup the tag is present
    for table in tables_to_remove:
        table.extract()

    tablewrapfoot_to_remove = soup2.find_all("table-wrap-foot")
    # Iterate through the table footnotes present in the 'table-wrap-foot' tag and remove them from the soup object regardless of where in the soup the tag is present
    for tablewrapfoot in tablewrapfoot_to_remove:
        tablewrapfoot.extract()

    captions_to_remove = soup2.find_all("caption")
    # Iterate through the captions present in the 'caption' tag and remove them from the soup object regardless of where in the soup the tag is present
    for caption in captions_to_remove:
        caption.extract()

    formula_to_remove = soup2.find_all("inline-formula")
    # Iterate through the formulas present in the 'inline-formula' tag and remove them from the soup object regardless of where in the soup the tag is present
    for formula in formula_to_remove:
        formula.extract()

    front_to_remove = soup2.find_all("front")
    # Iterate through the front part of the document where metadata is saved as soup2 is used to extract the body of text present in the 'front' tag and remove them from the soup object regardless of where in the soup the tag is present
    for front in front_to_remove:
        front.extract()

    back_to_remove = soup2.find_all("back")
    # Iterate through the back part of the document where metadata is saved as soup2 is used to extract the body of text present in the 'back' tag and remove them from the soup object regardless of where in the soup the tag is present
    for back in back_to_remove:
        back.extract()

    fig_to_remove = soup2.find_all("fig")
    # Iterate through the figures present in the 'fig' tag and remove them from the soup object regardless of where in the soup the tag is present
    for fig in fig_to_remove:
        fig.extract()

    graphic_to_remove = soup2.find_all("graphic")
    # Iterate through the graphic elements present in the 'graphic' tag and remove them from the soup object regardless of where in the soup the tag is present
    for graphic in graphic_to_remove:
        graphic.extract()

    inlinegraphic_to_remove = soup2.find_all("inline-graphic")
    # Iterate through the graphic elements made as a one-liner present in the 'inline-graphic' tag and remove them from the soup object regardless of where in the soup the tag is present
    for inlinegraphic in inlinegraphic_to_remove:
        inlinegraphic.extract()

    inlinesupplementarymaterial_to_remove = soup2.find_all(
        "inline-supplementary-material"
    )
    # Iterate through the supplementary material elements made as a one-liner present in the 'inline-supplementary-material' tag and remove them from the soup object regardless of where in the soup the tag is present
    for inlinesupplementarymaterial in inlinesupplementarymaterial_to_remove:
        inlinesupplementarymaterial.extract()

    media_to_remove = soup2.find_all("media")
    # Iterate through the media elements present in the 'media' tag and remove them from the soup object regardless of where in the soup the tag is present
    for media in media_to_remove:
        media.extract()

    texmath_to_remove = soup2.find_all("tex-math")
    # Iterate through the math equations present in the 'tex-math' tag and remove them from the soup object regardless of where in the soup the tag is present
    for texmath in texmath_to_remove:
        texmath.extract()

    # Find all <sec> elements in the soup2 object
    sec_elements = soup2.find_all("sec")

    # Define a regular expression pattern to match XML tags, as < and > are replace in the text with a str
    pattern = r"</[^>]+>"

    # Iterate through each <sec> element found in the soup2 object, i.e in the body as front and back part have been removed
    for a in range(len(sec_elements)):
        # Convert the <sec> element to a string for manipulation
        text_test = str(sec_elements[a])

        # Find all the closing tags in the current <sec> element (e.g., </p>, </sec>, </title>), looking for opening is more difficult because of id and extra information never present in the closing, the logic is that each opening as a closing
        matches = re.findall(pattern, text_test)

        # Remove duplicate closing tags and create a list of unique matches
        good_matches = list(dict.fromkeys(matches))

        # Remove unwanted tags such as </p>, </sec>, and </title> from the list of matches, we need to keep these tag for later parsing the document, this manipulation is done to remove xref, italic, bold, ... tags
        if "</p>" in good_matches:
            good_matches.remove("</p>")
        if "</sec>" in good_matches:
            good_matches.remove("</sec>")
        if "</title>" in good_matches:
            good_matches.remove("</title>")

        # Iterate over the remaining tags to remove them from the soup2 object converted as a string
        for b in range(len(good_matches)):
            current_tag_remove = good_matches[b]  # Get the tag to remove
            # Create the corresponding opening tag pattern to match in the content
            opening = f"<{current_tag_remove.split('</')[1][:-1]}[^>]*>"

            # Remove both the opening and closing tags from the text
            text_test = re.sub(opening, "", text_test)
            text_test = re.sub(current_tag_remove, "", text_test)

        # After all unwanted tags are removed from the converted string, update the sec_elements list with the cleaned <sec> element by reconverting to string to a soup object
        sec_elements[a] = BeautifulSoup(text_test, features="xml").find_all("sec")[
            0
        ]  # we keep the 0 element because we want the paragraph as a all not specific section since the parsing is taking place after

    # Iterate through each <sec> element in the sec_elements list - extarct the main text of the body, all the <sec> from the soup2 object
    # modification of the extracted content is performed later
    for sec in sec_elements:
        # Check if the current <sec> element does not have a parent <sec> element
        if not sec.find_parent("sec"):
            # If the <sec> element does not have a parent <sec>, find its title
            ori_title = sec.find("title")

            # Call the function extract_section_content defined above, passing the <sec> element that is composed as a block paragraph containing one or more passages, the soup2 object, and the title of the main <sec> but the function will refine the title search
            ### Current function is based on global variable, in the future we might want to pass the values as argument and unpack them again - will not provoke an error but could be improve
            extract_section_content(
                sec, soup2, ori_title, tag_title, tag_subtitle, text_list
            )

    # Check if the text inside the <ack> (acknowledgement) tag, back to the main soup object, is not 'None' after removing anything present between < and >
    # the special characters, unicode and hexacode are check later
    if re.sub("<[^>]+>", "", str(soup.find("ack"))) != "None":
        # If there is only one <ack> tag
        if len(soup.find_all("ack")) == 1:
            if len(soup.find("back").find("ack").find_all("title")) > 0:
                # Loop through all <title> tags inside the first <ack> tag
                for title in soup.find("back").find("ack").find_all("title"):
                    title_text = title.text  # Extract the title text

                    # Initialize an empty list to hold the <p> tags
                    p_tags = []
                    # Find the <p> tags that follow the title
                    next_sibling = title.find_next_sibling("p")

                    # Loop through all <p> tags that follow the title tag
                    while next_sibling and next_sibling.name == "p":
                        p_tags.append(next_sibling)  # Add the <p> tag to the list
                        next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                    # Loop through the collected <p> tags and extract the text
                    for p_tag in p_tags:
                        # Append the title and subtitle (same as the title) to the respective lists
                        tag_title.append([title_text])
                        tag_subtitle.append([title_text])
                        # Append the text of the <p> tag to the text_list
                        text_list.append(p_tag.text)
            else:
                # Append the title and subtitle (same as the title) to the respective lists
                tag_title.append(["Acknowledgments"])
                tag_subtitle.append(["Acknowledgments"])
                # Append the text of the <p> tag to the text_list
                text_list.append(soup.find("back").find("ack").text)

        # If there are multiple <ack> tags
        elif len(soup.find_all("ack")) > 1:
            # Loop through all <ack> tags in the document
            for notes in soup.find_all("ack"):
                # Loop through all <title> tags inside each <ack> tag
                if len(notes.find_all("title")) > 0:
                    for title in notes.find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)
                else:
                    # Append the title and subtitle (same as the title) to the respective lists
                    tag_title.append(["Acknowledgments"])
                    tag_subtitle.append(["Acknowledgments"])
                    # Append the text of the <p> tag to the text_list
                    text_list.append(notes.text)
        else:
            pass  # If no <ack> tag is found, do nothing

    # Check if the content inside the <funding-statement> tag, from the main soup object, is not 'None' after removing the text between < and >
    # the special characters, unicode and hexacode are check later
    if re.sub("<[^>]+>", "", str(soup.find("funding-statement"))) != "None":
        # If there are any <title> tags inside the <funding-statement> tag
        if len(soup.find("funding-statement").find_all("title")) != 0:
            # Loop through all the <title> tags inside <funding-statement>
            for title in soup.find("funding-statement").find_all("title"):
                title_text = title.text  # Extract the title text

                # Initialize an empty list to hold the <p> tags
                p_tags = []
                # Find the <p> tags that follow the title
                next_sibling = title.find_next_sibling("p")

                # Loop through all <p> tags that follow the title tag
                while next_sibling and next_sibling.name == "p":
                    p_tags.append(next_sibling)  # Add the <p> tag to the list
                    next_sibling = (
                        next_sibling.find_next_sibling()
                    )  # Move to the next sibling until None and get out of the while

                # Loop through the collected <p> tags and extract the text
                for p_tag in p_tags:
                    # Append the title and subtitle (same as the title) to the respective lists
                    tag_title.append([title_text])
                    tag_subtitle.append([title_text])
                    # Append the text of the <p> tag to the text_list
                    text_list.append(p_tag.text)

        # If there are no <title> tags but the <funding-statement> tag exists and is not 'None'
        elif re.sub("<[^>]+>", "", str(soup.find("funding-statement"))) != "None":
            # Append 'Funding Statement' as both the title and subtitle to the lists
            tag_title.append(["Funding Statement"])
            tag_subtitle.append(["Funding Statement"])
            # Append the content inside the <funding-statement> tag (without XML tags) to text_list
            text_list.append(re.sub("<[^>]+>", "", str(soup.find("funding-statement"))))
        else:
            pass  # If no <funding-statement> tag exists, do nothing

    # Check if the content inside the <fn-group> tag (footnotes), from the main soup object, is not 'None' after removing XML tags
    # the special characters, unicode and hexacode are check later
    if re.sub("<[^>]+>", "", str(soup.find("fn-group"))) != "None":
        # If there are any <title> tags inside the <fn-group> tag
        if len(soup.find("fn-group").find_all("title")) != 0:
            # Loop through all the <title> tags inside <fn-group>
            for title in soup.find("fn-group").find_all("title"):
                title_text = title.text  # Extract the title text

                # Initialize an empty list to hold the <p> tags
                p_tags = []
                # Find the <p> tags that follow the title
                next_sibling = title.find_next_sibling("p")

                # Loop through all <p> tags that follow the title tag
                while next_sibling and next_sibling.name == "p":
                    p_tags.append(next_sibling)  # Add the <p> tag to the list
                    next_sibling = (
                        next_sibling.find_next_sibling()
                    )  # Move to the next sibling until None and get out of the while

                # Loop through the collected <p> tags and extract the text
                for p_tag in p_tags:
                    # Append the title and subtitle (same as the title) to the respective lists
                    tag_title.append([title_text])
                    tag_subtitle.append([title_text])
                    # Append the text of the <p> tag to the text_list
                    text_list.append(p_tag.text)

        # If there are no <title> tags but the <fn-group> tag exists and is not 'None'
        elif re.sub("<[^>]+>", "", str(soup.find("fn-group"))) != "None":
            # Append 'Footnotes' as both the title and subtitle to the lists
            tag_title.append(["Footnotes"])
            tag_subtitle.append(["Footnotes"])
            # Append the content inside the <fn-group> tag (without XML tags) to text_list
            text_list.append(re.sub("<[^>]+>", "", str(soup.find("fn-group"))))
        else:
            pass  # If no <fn-group> tag exists, do nothing

    # Check if the content inside the <app-group> tag is not 'None' after removing the XML tags
    # the special characters, unicode and hexacode are check later
    if re.sub("<[^>]+>", "", str(soup.find("app-group"))) != "None":
        # If there are any <title> tags inside the <app-group> tag
        if len(soup.find("app-group").find_all("title")) != 0:
            # Loop through all the <title> tags inside <app-group>
            for title in soup.find("back").find("app-group").find_all("title"):
                title_text = title.text  # Extract the title text

                # Initialize an empty list to hold the <p> tags
                p_tags = []
                # Find the <p> tags that follow the title
                next_sibling = title.find_next_sibling("p")

                # Loop through all <p> tags that follow the title tag
                while next_sibling and next_sibling.name == "p":
                    p_tags.append(next_sibling)  # Add the <p> tag to the list
                    next_sibling = (
                        next_sibling.find_next_sibling()
                    )  # Move to the next sibling until None and get out of the while

                # Loop through the collected <p> tags and extract the text
                for p_tag in p_tags:
                    # Append the title and subtitle (same as the title) to the respective lists
                    tag_title.append([title_text])
                    tag_subtitle.append([title_text])
                    # Append the text of the <p> tag to the text_list
                    text_list.append(p_tag.text)

        # If there are no <title> tags but the <app-group> tag exists and is not 'None'
        elif re.sub("<[^>]+>", "", str(soup.find("app-group"))) != "None":
            # Append 'Unknown' as both the title and subtitle to the lists
            tag_title.append(["document part"])
            tag_subtitle.append(["document part"])
            # Append the content inside the <app-group> tag (without XML tags) to text_list
            text_list.append(re.sub("<[^>]+>", "", str(soup.find("app-group"))))
        else:
            pass  # If no <app-group> tag exists, do nothing

    # Check if the content inside the <notes> tag is not 'None' after removing XML tags
    if re.sub("<[^>]+>", "", str(soup.find("notes"))) != "None":
        # If there is only one <notes> tag
        if len(soup.find_all("notes")) == 1:
            # Loop through all the <title> tags inside <notes>
            ### ERROR make the code in case there is no title
            for title in soup.find("notes").find_all("title"):
                title_text = title.text  # Extract the title text

                # Initialize an empty list to hold the <p> tags
                p_tags = []
                # Find the <p> tags that follow the title
                next_sibling = title.find_next_sibling("p")

                # Loop through all <p> tags that follow the title tag
                while next_sibling and next_sibling.name == "p":
                    p_tags.append(next_sibling)  # Add the <p> tag to the list
                    next_sibling = (
                        next_sibling.find_next_sibling()
                    )  # Move to the next sibling until None and get out of the while

                # Loop through the collected <p> tags and extract the text
                for p_tag in p_tags:
                    # Append the title and subtitle (same as the title) to the respective lists
                    tag_title.append([title_text])
                    tag_subtitle.append([title_text])
                    # Append the text of the <p> tag to the text_list
                    text_list.append(p_tag.text)

        # If there are multiple <notes> tags
        elif len(soup.find_all("notes")) > 1:
            # Loop through each <notes> tag
            for notes in soup.find_all("notes"):
                # Loop through all the <title> tags inside the current <notes> tag
                ### ERROR make the code in case there is no title
                for title in notes.find_all("title"):
                    title_text = title.text  # Extract the title text

                    # Initialize an empty list to hold the <p> tags
                    p_tags = []
                    # Find the <p> tags that follow the title
                    next_sibling = title.find_next_sibling("p")

                    # Loop through all <p> tags that follow the title tag
                    while next_sibling and next_sibling.name == "p":
                        p_tags.append(next_sibling)  # Add the <p> tag to the list
                        next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                    # Loop through the collected <p> tags and extract the text
                    for p_tag in p_tags:
                        # Append the title and subtitle (same as the title) to the respective lists
                        tag_title.append([title_text])
                        tag_subtitle.append([title_text])
                        # Append the text of the <p> tag to the text_list
                        text_list.append(p_tag.text)
        else:
            pass  # If no <notes> tag exists, do nothing

    # Initialize lists to store the reference data
    tag_title_ref = []
    tag_subtitle_ref = []
    text_list_ref = []
    source_list = []
    year_list = []
    volume_list = []
    doi_list = []
    pmid_list = []

    # Find all <ref> tags in the main soup object as present in the <back> tag
    ref_tags = soup.find_all("ref")

    # Loop through each <ref> tag to extract citation information
    for ref in ref_tags:
        # Check if the <ref> tag contains an 'element-citation' tag with a publication type of 'journal', we can parse this format one when the other citation formats will not be parsed
        if ref.find("element-citation", {"publication-type": "journal"}) is not None:
            # Extract the label, which may or may not exist
            label = ref.label.text if ref.label else ""

            # Extract the article title, which may or may not exist
            article_title = (
                ref.find("article-title").text if ref.find("article-title") else ""
            )

            # Extract the source (journal name), which may or may not exist
            source = ref.source.text if ref.source else ""

            # Extract the year of publication, which may or may not exist
            year = ref.year.text if ref.year else ""

            # Extract the volume of the publication, which may or may not exist
            volume = ref.volume.text if ref.volume else ""

            # Extract the DOI, if available
            doi = (
                ref.find("pub-id", {"pub-id-type": "doi"}).text
                if ref.find("pub-id", {"pub-id-type": "doi"})
                else ""
            )

            # Extract the PMID, if available
            pmid = (
                ref.find("pub-id", {"pub-id-type": "pmid"}).text
                if ref.find("pub-id", {"pub-id-type": "pmid"})
                else ""
            )

            # Initialize an empty list to store the authors
            authors = []

            # Check if there is a <person-group> tag for authors
            if ref.find("person-group", {"person-group-type": "author"}) is not None:
                author_group = ref.find("person-group", {"person-group-type": "author"})

                # Loop through all <name> tags in the author group
                if len(author_group.find_all("name")) > 0:
                    for name in author_group.find_all("name"):
                        surname = name.surname.text  # Extract the surname of the author
                        given_names = (
                            name.find("given-names").text
                            if name.find("given-names")
                            else ""
                        )  # Extract given names, if available
                        authors.append(
                            f"{given_names} {surname}"
                        )  # Append the author's name to the authors list

            # Check for the presence of <etal> (et al.)
            etal_tag = ref.find("etal")
            if etal_tag is not None:
                etal = "Et al."  # Add "Et al." if the tag is present
            else:
                etal = ""

            # If 'etal' is found, append it to the final authors list
            ### ERROR authors could be an empty list, need to figure out if the above tag is absent what to do
            if etal != "":
                final_authors = f"{', '.join(authors)} {etal}"
            else:
                final_authors = f"{', '.join(authors)}"

            # Append the reference data to the lists
            tag_title_ref.append(["References"])
            tag_subtitle_ref.append(["References"])
            ### Not checked for XML tags, special characters not converted to human readable format
            # unicode and hexa checked later
            ### might need to look at the conditional of this one again
            text_list_ref.append(
                f"{label}{' ' + final_authors if final_authors else ''}{', ' + article_title if article_title else ''}{', ' + source if source else ''}{', ' + year if year else ''}{';' + volume if volume and year else ''}{', ' + volume if volume and not year else ''}"
            )

            # Append additional citation details to the respective lists
            source_list.append(source)
            year_list.append(year)
            volume_list.append(volume)
            doi_list.append(doi)
            pmid_list.append(pmid)

        else:
            # If the <ref> tag does not contain an 'element-citation' tag, extract the text content as-is
            content = ref.get_text(separator=" ")

            # Append the content to the reference lists
            tag_title_ref.append(["References"])
            tag_subtitle_ref.append(["References"])

            ### Not checked for XML tags, special characters not converted to human readable format
            # unicode and hexa checked later
            text_list_ref.append(content)

            # can't be parsed because we don't know the formats used
            source_list.append("")
            year_list.append("")
            volume_list.append("")
            doi_list.append("")
            pmid_list.append("")

    # Iterate through each element in the 'tag_title' list from the <front>, <abstract>, all the extracted text from soup2 object, and some information from the <back> outside of references saved in a different list
    for i in range(len(tag_title)):
        # Clean 'tag_subtitle[i]' by removing XML tags and unwanted characters, this is the most recent heading for the text
        # Remove all XML tags using regex
        # Remove single quotes from the string, removing the list syntax from the string
        # Remove opening square brackets from the string, removing the list syntax from the string
        # Remove closing square brackets from the string, removing the list syntax from the string
        # Remove double quotes from the string, removing the list syntax from the string
        tag_subtitle[i] = [
            re.sub("<[^>]+>", "", str(tag_subtitle[i]))
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
        ]

        # Iterate through each sublist in 'tag_title[i]'
        for j in range(len(tag_title[i])):
            # Clean each element (title) in the sublist by removing XML tags and unwanted characters, this is all the parent headings for the text
            # Remove all XML tags using regex
            # Remove single quotes from the string, removing the list syntax from the string
            # Remove opening square brackets from the string, removing the list syntax from the string
            # Remove closing square brackets from the string, removing the list syntax from the string
            # Remove double quotes from the string, removing the list syntax from the string
            tag_title[i][j] = [
                re.sub("<[^>]+>", "", str(tag_title[i][j]))
                .replace("'", "")
                .replace("[", "")
                .replace("]", "")
                .replace('"', "")
            ]

    # Iterate through each element in the 'tag_title' list
    for i in range(len(tag_title)):
        # Iterate through each sublist in 'tag_title[i]'
        for j in range(len(tag_title[i])):
            # Check if the string in the first element of the current sublist has more than one word, i.e. a space is present
            if len(tag_title[i][j][0].split()) > 1:
                # Check if the first word ends with a period
                if tag_title[i][j][0].split()[0][-1] == ".":
                    # Check if the first word (excluding the period) is a number (ignoring commas and periods)
                    if (
                        tag_title[i][j][0]
                        .split()[0][:-1]
                        .replace(".", "")
                        .replace(",", "")
                        .isdigit()
                    ):
                        # Remove the first word (likely a number followed by a period) and join the remaining words
                        tag_title[i][j][0] = " ".join(tag_title[i][j][0].split()[1:])

    # Iterate through each element in the 'tag_subtitle' list
    for i in range(len(tag_subtitle)):
        # Check if the first element in the current sublist contains more than one word
        if len(tag_subtitle[i][0].split()) > 1:
            # Check if the first word ends with a period
            if tag_subtitle[i][0].split()[0][-1] == ".":
                # Check if the first word (excluding the period) is a number (ignoring commas and periods)
                if (
                    tag_subtitle[i][0]
                    .split()[0][:-1]
                    .replace(".", "")
                    .replace(",", "")
                    .isdigit()
                ):
                    # Remove the first word (likely a number followed by a period) and join the remaining words
                    tag_subtitle[i][0] = " ".join(tag_subtitle[i][0].split()[1:])

    # Iterate over all elements in 'text_list'
    for i in range(len(text_list)):
        # Remove anything from '<sec[^*]' until '/title>' str and '</sec>' str from each element of text_list
        text_list[i] = re.sub("<sec[^*]+/title>", "", str(text_list[i])).replace(
            "</sec>", ""
        )

    # Iterate over all elements in 'text_list'
    for i in range(len(text_list)):
        # Replace Unicode escape sequences with actual characters, from the function introduced above
        text_list[i] = replace_unicode_escape(text_list[i])

    # Iterate over all elements in 'text_list'
    for i in range(len(text_list)):
        # Replace multiple spaces and newlines in the text with single spaces, from the function introduced above
        text_list[i] = replace_spaces_and_newlines(text_list[i])

    # Define a pattern to match <xref> tags in the text (reference cross-references)
    ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
    pattern = r"(<xref[^>]*>)([^<]+)(</xref>)"

    # Iterate over all elements in 'text_list'
    for i in range(len(text_list)):
        # Apply regex pattern to reformat <xref> tags by adding a space between the tag content
        ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
        text_list[i] = re.sub(pattern, r"\1 \2 \3", text_list[i])

    # Iterate over all elements in 'text_list' again
    for i in range(len(text_list)):
        # Replace spaces and newlines in the text once more after the <xref> tags are modified, from the function introduced above
        ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
        text_list[i] = replace_spaces_and_newlines(text_list[i])

    # Initialize empty lists to store corrected sections, subsections, text, and offsets
    corrected_section = []
    corrected_subsection = []
    corrected_text = []

    # Iterate over each element in the 'text_list'
    for i in range(len(text_list)):
        # Check if the current element in text_list is not empty
        if text_list[i] != "":
            # Iterate over each section split by <p> tags in the current text
            for j in range(len(text_list[i].split("<p>"))):
                # Check if the current section (split by <p>) is not empty after removing </p> tags
                if text_list[i].split("<p>")[j].replace("</p>", "") != "":
                    # Append the corresponding tag title and tag subtitle for the section
                    # corrected_section.append(tag_title[i])
                    # corrected_subsection.append(tag_subtitle[i])

                    # Remove all tags from the current p text from the current item of the text_list
                    new_text = str(
                        re.sub("<[^>]+>", "", str(text_list[i].split("<p>")[j]))
                    )
                    # Replace unicode and hexacode, using the function introduced above
                    new_text = replace_unicode_escape(new_text)
                    # Replace spaces and newlines, using the function introduced above
                    new_text = replace_spaces_and_newlines(new_text)
                    # Clean up special characters
                    # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                    new_text = (
                        new_text.replace("</p>", "")
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                        .replace("&amp;", "&")
                        .replace("&apos;", "'")
                        .replace("&quot;", '"')
                        .replace("\xa0", " ")
                    )
                    if len(new_text) > 0:
                        if new_text[0] == " " and new_text[-1] == " ":
                            if new_text[1:-1] in corrected_text:
                                pass
                            else:
                                corrected_section.append(tag_title[i])
                                corrected_subsection.append(tag_subtitle[i])
                                corrected_text.append(new_text[1:-1])
                                offset_list.append(offset)
                                offset += len(new_text[1:-1]) + 1
                        # Append the corrected text to the corrected_text list
                        else:
                            if new_text in corrected_text:
                                pass
                            else:
                                corrected_section.append(tag_title[i])
                                corrected_subsection.append(tag_subtitle[i])
                                corrected_text.append(new_text)
                                offset_list.append(offset)
                                offset += len(new_text) + 1

                    # Update the offset list (keeps track of the position in the document)
                    # offset_list.append(offset)

                    # Increment the offset by the length of the new text + 1 (for spacing or next content)
                    # offset += len(new_text) + 1
                else:
                    # If the current section is empty after removing </p>, skip it
                    pass
        else:
            # If the current text list element is empty, skip it
            pass

    # Correct any missing section titles by copying the previous title if the current title is empty
    for i in range(len(corrected_section)):
        if len(corrected_section[i]) == 0:
            corrected_section[i] = corrected_section[i - 1]

    ### No XML tags remove here or special characters conversion
    # Initialize an empty list to store offsets for references
    offset_list_ref = []

    # Iterate over each element in the 'text_list_ref' (list containing reference texts)
    for i in range(len(text_list_ref)):
        # Replace unicode and hexacode, using the function introduced above
        text_list_ref[i] = replace_unicode_escape(text_list_ref[i])

    # Iterate over each element in the 'text_list_ref' (list containing reference texts)
    for i in range(len(text_list_ref)):
        # Replace spaces and newlines, using the function introduced above
        text_list_ref[i] = replace_spaces_and_newlines(text_list_ref[i])

    # Iterate over each element in the 'text_list_ref' to calculate and store offsets
    for i in range(len(text_list_ref)):
        # Append the current value of 'offset' to the offset list for the reference
        offset_list_ref.append(offset)

        # Update the 'offset', as it comes after the main text by adding the length of the current reference text + 1, the +1 accounts for a space or delimiter between references
        offset += len(text_list_ref[i]) + 1

    for i in range(len(corrected_section)):
        corrected_section[i][0][0] = fix_mojibake_string(
            corrected_section[i][0][0]
            .replace("\n", "")
            .replace("\\n", "")
            .replace("\\xa0", " ")
        )
    for i in range(len(corrected_subsection)):
        for y in range(len(corrected_subsection[i])):
            corrected_subsection[i][y] = fix_mojibake_string(
                corrected_subsection[i][y]
                .replace("\n", "")
                .replace("\\n", "")
                .replace("\\xa0", " ")
            )

    # Main body IAO allocation
    iao_list = []

    for y in range(len(corrected_section)):
        if corrected_section[y][0][0] == "document title":
            section_type = [{"iao_name": "document title", "iao_id": "IAO:0000305"}]
        else:
            mapping_result = get_iao_term_mapping(corrected_section[y][0][0])

            # if condition to add the default value 'document part' for passages without IAO
            if mapping_result == []:
                section_type = [
                    {
                        "iao_name": "document part",  # Name of the IAO term
                        "iao_id": "IAO:0000314",  # ID associated with the IAO term, or empty if not found
                    }
                ]
            else:
                section_type = mapping_result

        iao_list.append(list({v["iao_id"]: v for v in section_type}.values()))

    # References IAO allocation
    iao_list_ref = []

    for y in range(len(tag_title_ref)):
        section_type = [
            {
                "iao_name": "references section",  # Name of the IAO term
                "iao_id": "IAO:0000320",  # ID associated with the IAO term, or empty if not found
            }
        ]

        iao_list_ref.append(list({v["iao_id"]: v for v in section_type}.values()))

    # Initialize lists to store embedded data
    embeded_list = []  # Final list containing all embedded documents
    embeded_section_list = []  # Final list containing all the infons information, excluding reference
    embeded_section_ref_list = []  # Final list containing all the infons for the reference section

    # Loop through corrected_section to create embedded section dictionaries
    for i in range(len(corrected_section)):
        # Create a dictionary for the first-level section title
        embeded_dict = {
            "section_title_1": corrected_section[i][0][0]  # First section title
        }
        cont_section = 2  # Counter for additional section titles

        # If there are more levels in the section, add them to the dictionary, i.e. subheadings
        if len(corrected_section[i]) > 1:
            for imp in range(1, len(corrected_section[i])):
                embeded_dict[f"section_title_{cont_section}"] = corrected_section[i][
                    imp
                ][0]
                cont_section += 1

        # If the subsection is different from the main section, add it as well i.e. the last subheading if there is a main heading
        if corrected_subsection[i][0] != corrected_section[i][0][0]:
            embeded_dict[f"section_title_{cont_section}"] = corrected_subsection[i][0]

        # Add IAO data (if available) to the dictionary
        if len(iao_list[i]) > 0:
            for y in range(len(iao_list[i])):
                embeded_dict[f"iao_name_{y + 1}"] = iao_list[i][y].get("iao_name")
                embeded_dict[f"iao_id_{y + 1}"] = iao_list[i][y].get("iao_id")

        # Append the completed dictionary to the embedded section list
        embeded_section_list.append(embeded_dict)

    # Process reference sections (tag_title_ref) to create embedded reference dictionaries
    for i in range(len(tag_title_ref)):
        embeded_dict = {
            "section_title_1": fix_mojibake_string(
                tag_title_ref[i][0]
            )  # First section title i.e. 'Reference'
        }

        # Add IAO data (if available) for references
        if len(iao_list_ref[i]) > 0:
            for y in range(len(iao_list_ref[i])):
                embeded_dict[f"iao_name_{y + 1}"] = iao_list_ref[i][y].get("iao_name")
                embeded_dict[f"iao_id_{y + 1}"] = iao_list_ref[i][y].get("iao_id")

        # Add metadata from references if available
        if source_list[i] != "":
            embeded_dict["journal"] = source_list[i]
        if year_list[i] != "":
            embeded_dict["year"] = year_list[i]
        if volume_list[i] != "":
            embeded_dict["volume"] = volume_list[i]
        if doi_list[i] != "":
            embeded_dict["doi"] = doi_list[i]
        if pmid_list[i] != "":
            embeded_dict["pmid"] = pmid_list[i]

        # Append the completed dictionary to the embedded section reference list
        embeded_section_ref_list.append(embeded_dict)

    # Combine corrected text with embedded sections into final embedded list
    for i in range(len(corrected_text)):
        # If after cleaning the there is no more text or only a space, we don't keep them
        if corrected_text[i] == "" or corrected_text[i] == " ":
            pass
        else:
            embeded_dict = {
                "offset": offset_list[i],  # Offset for the text
                "infons": embeded_section_list[i],  # Section metadata
                "text": fix_mojibake_string(corrected_text[i]),  # Main text
                "sentences": [],  # Placeholder for sentences
                "annotations": [],  # Placeholder for annotations
                "relations": [],  # Placeholder for relations
            }
            # Populate the list of passages
            embeded_list.append(embeded_dict)

    # Add reference text with metadata to the embedded list
    for i in range(len(text_list_ref)):
        # If after cleaning the there is no more text or only a space, we don't keep them
        if text_list_ref[i] == "" or text_list_ref[i] == " ":
            pass
        else:
            embeded_dict = {
                "offset": offset_list_ref[i],  # Offset for reference text
                "infons": embeded_section_ref_list[i],  # Reference metadata
                "text": fix_mojibake_string(
                    replace_spaces_and_newlines(text_list_ref[i])
                    .replace(" ,", ",")
                    .replace(" .", ".")
                    .replace("..", ".")
                ),  # Reference text
                "sentences": [],  # Placeholder for sentences
                "annotations": [],  # Placeholder for annotations
                "relations": [],  # Placeholder for relations
            }
            # Populate the list of passages
            embeded_list.append(embeded_dict)

    # Create a dictionary for document metadata
    infons_dict_meta = {}
    if pmcid_xml != "":
        infons_dict_meta["pmcid"] = pmcid_xml
    if pmid_xml != "":
        infons_dict_meta["pmid"] = pmid_xml
    if doi_xml != "":
        infons_dict_meta["doi"] = doi_xml
    if pmc_link != "":
        infons_dict_meta["link"] = pmc_link
    if journal_xml != "":
        infons_dict_meta["journal"] = journal_xml
    if pub_type_xml != "":
        infons_dict_meta["pub_type"] = pub_type_xml
    if year_xml != "":
        infons_dict_meta["year"] = year_xml
    if license_xml != "":
        infons_dict_meta["license"] = license_xml

    # Create the final dictionary for the document
    my_dict = {}
    if source_method != "":
        my_dict["source"] = source_method
    if date != "":
        my_dict["date"] = date
    my_dict["key"] = "autocorpus_fulltext.key"
    my_dict["infons"] = infons_dict_meta  # Metadata for the document
    my_dict["documents"] = [
        {
            "id": pmcid_xml,  # Document ID
            "infons": {},  # Placeholder for additional document-level infons
            "passages": embeded_list,  # Embedded passages including sections and references
            "relations": [],  # Placeholder for relations at the document level
        }
    ]

    return my_dict

def pmcid_to_microbiome(pmcid_list, email, output_directory = './'):
    if type(pmcid_list) != str:
        print('Parameter "pmcid_list": Input error, this function only accepts a string directory to a txt file composed of PMCIDs, where each line is one PMCID. For example, if your file is called "pmcid_list.txt" and is located in the current directory, you should give "./pmcid_list.txt".')
        return None
    else:
        pass
    if type(email) != str:
        print('Parameter "email": Input error, this function only accepts a string of a valid email address.')
        return None
    else:
        pass
    if type(output_directory) != str:
        print('Parameter "output_directory": Input error, this function only accepts a string directory to save the files, e.g. for "./microbiome/", the function will generate and save the output in "./microbiome/microbELP_PMCID_microbiome/".')
        return None
    else:
        pass

    if output_directory[-1] == '/':
        final_output = output_directory + 'microbELP_PMCID_microbiome' 
    else:
        final_output = output_directory + '/microbELP_PMCID_microbiome' 
        
    f = open(f"{pmcid_list}")
    data = f.read()
    f.close()
    data = data.split('\n')

    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
       'Accept-Language': "en,en-US;q=0,5",
       'Accept': "text/html,application/pdf,application/xhtml+xml,application/xml,text/plain,text/xml",
       'mailto':f'{email}',
       'Accept-Encoding': 'gzip, deflate, compress',
       'Accept-Charset': 'utf-8, iso-8859-1;q=0.5, *;q=0.1'}

    http = requests.Session()
    # set the base url, in this case it is the works url for the crossref api
    http.headers.update(headers)
    # set up a retry strategy
    retry_strategy = Retry(
            total=3,
            status_forcelist = [429, 500, 502, 503, 504],
            backoff_factor = 1
        )
    # add the retry strategy to the adapter for a session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    # mount these settings to our session
    http.mount('https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:', adapter)
    try:
        os.mkdir(final_output)
        os.mkdir(final_output + '/PMCID_XML')
    except:
        pass
    final_data = []
    previous_data = glob.glob(final_output + '/PMCID_XML/*.xml')
    for i in range(len(previous_data)):
        previous_data[i] = previous_data[i].split('/')[-1].split('.')[0]
    for i in range(len(data)):
        if data[i] not in previous_data:
            final_data.append(data[i])
    total = len(final_data)
    print('Starting the retrieval process.')
    for i in range(len(final_data)):
        print('Retrieving file: ' + str(i+1) + ' out of ' + str(total) + ' from the NCBI API.')
        r_d, r = get_request(final_data[i].replace('PMC', ''), http, 'https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:', headers,)
        if r_d['status_code'] == 429:
                print('"Too many requests error [429]" received')
                print('Risk of IP address block: stopping script')
                return None
        # code 200 everything works correctly
        elif r_d['status_code'] == 200:
            f = open(final_output + f"/PMCID_XML/{final_data[i]}.xml", "w")
            f.write(r_d.get('text'))
            f.close()
        else:
            # in case the status code is different than 200 or 429
            print('error with request')
            print(f'{r_d["error"]}')
        time.sleep(1)

    collected_files = glob.glob(final_output + f'/PMCID_XML/*.xml')
    try:
        os.mkdir(final_output + '/bioc')
    except:
        pass
    print('Starting the conversion process.')
    final_bioc = []
    previous_data = glob.glob(final_output + '/bioc/*.json')
    for i in range(len(previous_data)):
        previous_data[i] = previous_data[i].split('/')[-1].split('_')[0]
    for i in range(len(collected_files)):
        if collected_files[i].split('/')[-1].split('.')[0] not in previous_data:
            final_bioc.append(collected_files[i])
    total = len(final_bioc)
    for i in range(len(final_bioc)):
        print('Converting file: ' + str(i+1) + ' out of ' + str(total) + ' to BioC.')
        f = open(f"{final_bioc[i]}", "r")
        data = f.read()
        f.close()
        if '<body>' in data:
            try:
                my_dict = convert_xml_to_json(final_bioc[i])
                with open(
                    final_output + f"/bioc/{final_bioc[i].split('/')[-1].split('.')[0]}_bioc.json",
                    "w",
                    encoding="utf-8",
                ) as fp:
                    json.dump(my_dict, fp, indent=2, ensure_ascii=False)
            except:
                os.remove(collected_files[i])
        else:
            os.remove(collected_files[i])
    print('Process complete!')
