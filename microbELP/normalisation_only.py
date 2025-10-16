import json
from collections import Counter
from microbELP.load_dic import load_dic

def microbiome_normalisation(word):

    # Most up to date version of this dictionary. 
    dict_data = load_dic()
    CleanNames = [i['CleanName'].lower() for i in dict_data]

    #Used to produce the strains dictionary for duplicate taxa where clean names have multiple mentions. 
    cncounts = dict(Counter(CleanNames))
    strains = {key:value for key, value in cncounts.items() if value > 1}
    CleanNames =list(dict.fromkeys(CleanNames))
    lcCleanNames = [i['CleanName'].lower() for i in dict_data]

    if type(word) == str:
        if word.lower() in CleanNames: # Adjust to lcCleanNames if only using lower case values
            match = next((l for l in dict_data if l['CleanName'].lower() == word.lower()), None)
            normalised_identifier = match["TaxID"]
            return normalised_identifier
        else:
            return None
    elif type(word) == list:
        output_list = []
        for i in range(len(word)):
            if word[i].lower() in CleanNames: # Adjust to lcCleanNames if only using lower case values
                match = next((l for l in dict_data if l['CleanName'].lower() == word[i].lower()), None)
                normalised_identifier = match["TaxID"]
                output_list.append({word[i]: normalised_identifier})
            else:
                output_list.append({word[i]: None})
        return output_list
    else:
        return 'Input error, this function only accept one "str" or a list of "str" has input.'
