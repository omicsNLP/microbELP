import sys, io
_stdout = sys.stdout
_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
import PySimpleGUI as sg
sys.stdout = _stdout
sys.stderr = _stderr
import glob
import multiprocessing as mp
from datetime import datetime
from microbELP.load_dic import load_dic
from microbELP.parallel_microbiomeAnnotator_condensed import parallel_Annotator as ann

def run_ann_initialsteps(input_dir, output_dir, count, keyword, casesens, process_number):
    obj = ann(input_dir, output_dir, count, keyword, casesens, process_number)
    obj.initialsteps()  # call the method on the instance
    return True

def parallel_microbELP(input_directory, numbers_of_cores, output_directory = './', count = 0, keyword = 'ALL', casesens = 'no'):
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
    if type(numbers_of_cores) != int:
        print('Parameter "numbers_of_cores": Input error, this function only accepts int, it will request the equivalent number of cores to be used in parallelism.')
        return None
    else:
        pass
	if numbers_of_cores >= mp.cpu_count():
	    print('The number of cores you want to use is equal or greater than the numbers of cores in your machine. We stop the script now')
	    return None
	else:
	    par_core = numbers_of_cores

	if input_directory[-1] == '/':
		input_bioc = glob.glob(input_directory + '*_bioc.json')
	else:
		input_bioc = glob.glob(input_directory + '/*_bioc.json')

	if output_directory[-1] == '/':
		done = glob.glob(output_directory + 'microbELP_result' + '/*_bioc.json')
	else:
		done = glob.glob(output_directory + '/microbELP_result' + '/*_bioc.json')

	final_input_bioc = []
	for i in range(len(done)):
		done[i] = done[i].split('/')[-1]
	for i in range(len(input_bioc)):
		if input_bioc[i].split('/')[-1] not in done:
			final_input_bioc.append(input_bioc[i])

	if len(final_input_bioc) < par_core:
	        par_core = len(final_input_bioc)
	
	if len(final_input_bioc) == 0:
		print('No new document to annotate.')
        return None

	if par_core > 1:
	    data = []
	    for i in range(par_core):
	        if i == 0:
	            current_data = (final_input_bioc[:round(len(final_input_bioc)/par_core)], output_directory, count, keyword, casesens, i+1)
	            data.append(current_data)
	        elif i > 0 and i+1 != par_core:
	            current_data = (final_input_bioc[(round(len(final_input_bioc)/par_core))*i:(round(len(final_input_bioc)/par_core))*(i+1)], output_directory, count, keyword, casesens, i+1)
	            data.append(current_data)
	        else:
	            current_data = (final_input_bioc[round(len(final_input_bioc)/par_core)*i:], output_directory, count, keyword, casesens, i+1)
	            data.append(current_data)
	else:
	    data = [(final_input_bioc, output_directory, count, keyword, casesens, 1)]

	now = datetime.now()
	current_time = now.strftime("%d/%m/%Y, %H:%M:%S")
	print(str(current_time) + str(' Process starting'))

	with mp.Pool(par_core) as pool:
	    pool.starmap(run_ann_initialsteps, data)

	now = datetime.now()
	current_time = now.strftime("%d/%m/%Y, %H:%M:%S")
	print(str(current_time) + str(' Process complete'))
