from microbELP import TextPreprocess
from microbELP import cache_or_load_dictionary
from microbELP import BioSyn
from microbELP import create_sublists
from microbELP import adjust_boudaries
from microbELP import adjust_abbr
from microbELP import adjust_wc
from microbELP import adjust_spp
from microbELP import remove_nested_annotations
from microbELP import merge_overlapping_annotations

import os
import glob
import json 
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

def microbELP_DL(input_directory, output_dir = './', normalisation = True):
    if type(input_directory) != str:
        print('Parameter "input_directory": Input error, this function only accepts a string directory with BioC files to be annotated with "*_bioc.json", e.g. for "./bioc/*_bioc.json", requires "./bioc" as input.')
        return None
    else:
        pass
    if type(output_dir) != str:
        print('Parameter "output_dir": Input error, this function only accepts a string directory to save the annotated files, e.g. for "./bioc_annotated/", the function will generate and save the output in "./bioc_annotated/microbELP_DL_result/".')
        return None
    else:
        pass
    if type(normalisation) != bool:
        print('Parameter "normalisation": Input error, this function only accepts "True" or "False", if "True", the entities are normalised and added to the annotations.')
        return None
    else:
        pass
    if input_directory[-1] == '/':
        input_list = glob.glob(input_directory + '*_bioc.json')
    else:
        input_list = glob.glob(input_directory + '/*_bioc.json')
    if output_dir[-1] == '/':
        output_directory = output_dir + 'microbELP_DL_result/'
    else:
        output_directory = output_dir + '/microbELP_DL_result/'
    try:
        os.mkdir(output_directory)
    except:
        pass
    done = glob.glob(output_directory + '*_bioc.json')
    final_input_bioc = []
    for i in range(len(done)):
        done[i] = done[i].split('/')[-1]
    for i in range(len(input_list)):
        if input_list[i].split('/')[-1] not in done:
            final_input_bioc.append(input_list[i])
    if len(final_input_bioc) == 0:
        print('No new document to annotate.')
        return None
    if normalisation:
        model_name_or_path = 'omicsNLP/microbELP_NEN'
        biosyn = BioSyn(
                    max_length=25,
                    use_cuda=True
                )
        biosyn.load_model(model_name_or_path=model_name_or_path)
        dictionary, dict_sparse_embeds, dict_dense_embeds = cache_or_load_dictionary(biosyn, model_name_or_path)
    model_name = 'omicsNLP/microbELP_NER'
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _ = model.to(device)
    for z in range(len(final_input_bioc)):
        print(f'Processing file {z+1} out of {len(final_input_bioc)}.')
        with open(final_input_bioc[z]) as f:
            d = json.load(f)
        total = 1
        for abc in range(len(d['documents'][0]['passages'])):
            paragraph_offset = d['documents'][0]['passages'][abc]['offset']
            sentence_text = [d['documents'][0]['passages'][abc]['text'].replace('\n', ' ')]

            start_meta, len_meta, trigger_meta = [], [], []

            for j, input_text in enumerate(sentence_text):
                current_offset = sum(len(s) for s in sentence_text[:j])

                encoded = tokenizer(
                    input_text,
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    return_offsets_mapping=True,
                    return_overflowing_tokens=True,
                    max_length=512,
                    stride=50
                )

                for i in range(encoded["input_ids"].size(0)):
                    inputs_for_model = {
                        "input_ids": encoded["input_ids"][i].unsqueeze(0).to(device),
                        "attention_mask": encoded["attention_mask"][i].unsqueeze(0).to(device)
                    }
                    if "token_type_ids" in encoded:
                        inputs_for_model["token_type_ids"] = encoded["token_type_ids"][i].unsqueeze(0).to(device)

                    offsets_mapping = encoded["offset_mapping"][i]

                    with torch.no_grad():
                        outputs = model(**inputs_for_model)

                    predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().tolist()
                    tokens = tokenizer.convert_ids_to_tokens(inputs_for_model["input_ids"][0].tolist())

                    to_identify = create_sublists(predictions, offsets_mapping, tokens)

                    for k in range(len(to_identify)):
                        start = int(to_identify[k][0][0])
                        end = int(to_identify[k][-1][1])
                        if start != 0:
                            start_meta.append(start)
                            len_meta.append(end - start)
                            trigger_meta.append(input_text[start:end])

            annotations = [
                {'Entity': trigger_meta[k], 'locations': {'offset': start_meta[k], 'length': len_meta[k]}}
                for k in range(len(start_meta))
            ]

            unique_annotations = []
            seen = set()

            for ann in annotations:
                key = (ann['Entity'], ann['locations']['offset'], ann['locations']['length'])
                if key not in seen:
                    seen.add(key)
                    unique_annotations.append(ann)

            annotations = unique_annotations
            annotations = adjust_boudaries(input_text, annotations)
            annotations = adjust_abbr(input_text, annotations)
            annotations = adjust_wc(input_text, annotations)
            annotations = adjust_spp(input_text, annotations)
            annotations = remove_nested_annotations(annotations)
            annotations = merge_overlapping_annotations(input_text, annotations)
            if normalisation:
                final_nen = []
                for j in range(len(annotations)):
                    original_mention = annotations[j]['Entity']
                    # preprocess mention
                    mention = TextPreprocess().run(original_mention)
                    # embed mention
                    mention_sparse_embeds = biosyn.embed_sparse(names=[mention])
                    mention_dense_embeds = biosyn.embed_dense(names=[mention])
                    output = {
                        'mention': original_mention,
                    }
                    sparse_score_matrix = biosyn.get_score_matrix(
                        query_embeds=mention_sparse_embeds,
                        dict_embeds=dict_sparse_embeds
                    )
                    dense_score_matrix = biosyn.get_score_matrix(
                        query_embeds=mention_dense_embeds,
                        dict_embeds=dict_dense_embeds
                    )
                    sparse_weight = biosyn.get_sparse_weight().item()
                    hybrid_score_matrix = sparse_weight * sparse_score_matrix + dense_score_matrix
                    hybrid_candidate_idxs = biosyn.retrieve_candidate(
                        score_matrix = hybrid_score_matrix,
                        topk = 1
                    )
                    # get predictions from dictionary
                    predictions = dictionary[hybrid_candidate_idxs].squeeze(0)
                    candidates = [{str(id_): str(mention)} for mention, id_ in predictions]
                    result = {
                        "mention": original_mention,
                        "candidates": candidates
                    }
                    final_nen.append(result)

            annotations_list = []
            current_date = datetime.now()
            formatted_date = current_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            if normalisation:
                for k in range(len(annotations)):
                    annotations_list.append({
                        'id': str(total),
                        'infons': {'type': 'microbiome',
                               'identifier': list(final_nen[k]['candidates'][0].keys())[0],
                               'annotator': 'microbELP@omicsNLP.github',
                               'updated_at': f'{formatted_date}'},
                        'text': annotations[k]['Entity'],
                        'locations': [{'offset': annotations[k]['locations']['offset'] + paragraph_offset, 'length': annotations[k]['locations']['length']}]
                    })
                    total += 1
                d['documents'][0]['passages'][abc]['annotations'] = annotations_list
            else:
                for k in range(len(annotations)):
                    annotations_list.append({
                        'id': str(total),
                        'infons': {'type': 'microbiome',
                               'identifier': '',
                               'annotator': 'microbELP@omicsNLP.github',
                               'updated_at': f'{formatted_date}'},
                        'text': annotations[k]['Entity'],
                        'locations': [{'offset': annotations[k]['locations']['offset'] + paragraph_offset, 'length': annotations[k]['locations']['length']}]
                    })
                    total += 1
                d['documents'][0]['passages'][abc]['annotations'] = annotations_list
        with open(f'{output_directory}{final_input_bioc[z].split("/")[-1]}', 'w', encoding="utf-8") as fp:
            json.dump(d, fp, indent = 2, ensure_ascii=False)
