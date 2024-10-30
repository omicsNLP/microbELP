import PySimpleGUI as sg
import glob
from microbELP.load_dic import load_dic
from microbELP.microbiomeAnnotator_condensed import Annotator as ann

def microbELP(input_directory, output_directory = './', count = 0, keyword = 'ALL', casesens = 'no'):
	result = ann(input_directory, output_directory, count, keyword, casesens)
	result.initialsteps()
