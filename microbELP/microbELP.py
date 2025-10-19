import sys, io
_stdout = sys.stdout
_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
import PySimpleGUI as sg
sys.stdout = _stdout
sys.stderr = _stderr
import glob
from microbELP.load_dic import load_dic
from microbELP.microbiomeAnnotator_condensed import Annotator as ann

def microbELP(input_directory, output_directory = './', count = 0, keyword = 'ALL', casesens = 'no'):
    if type(input_directory) != str:
        print('Parameter "input_directory": Input error, this function only accepts a string directory with BioC files to be annotated with "*_bioc.json", e.g. for "./bioc/*_bioc.json", requires "./bioc" as input.')
        return None
    else:
        pass
    if type(output_directory) != str:
        print('Parameter "output_directory": Input error, this function only accepts a string directory to save the annotated files, e.g. for "./bioc_annotated/", the function will generate and save the output in "./bioc_annotated/microbELP_DL_result/".')
        return None
    else:
        pass
	result = ann(input_directory, output_directory, count, keyword, casesens)
	result.initialsteps()
