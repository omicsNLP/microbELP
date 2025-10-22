import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

def create_sublists(lst, lst2, tokens):
    sublists = []
    start_idx = None
    for i, value in enumerate(lst):
        if value == 1:
            start_idx = i
        elif value == 0 and start_idx is not None:
            end_idx = i
            while start_idx > 0 and tokens[start_idx][:2] == '##':
                start_idx -= 1
            if tokens[end_idx][:2] == '##':
                end_idx += 1
                while end_idx < len(tokens) - 1 and tokens[end_idx + 1][:2] == '##':
                    end_idx += 1
                sublists.append(lst2[start_idx:end_idx])
            else:
                sublists.append(lst2[start_idx:end_idx])
            start_idx = None
    return sublists

def is_space(char):
    return char.isspace()

def adjust_spaces_on_right(text, start_offset):
    while start_offset < len(text) and is_space(text[start_offset]):
        start_offset += 1    
    return start_offset

def adjust_spaces_on_left(text, end_offset):
    while end_offset > 0 and is_space(text[end_offset - 1]):
        end_offset -= 1    
    return end_offset

def adjust_offsets(text, start_offset, end_offset):
    if start_offset < 0 or end_offset >= len(text) or start_offset > end_offset:
        return start_offset, end_offset    
    original_start = start_offset
    original_end = end_offset    
    while start_offset > 0 and text[start_offset - 1].isalpha():
        start_offset -= 1   
    while end_offset < len(text) and text[end_offset].isalpha():
        end_offset += 1
    return start_offset, end_offset

def adjust_boudaries(input_text, annotations):
    for i in range(len(annotations)):
        start_index = annotations[i]['locations']['offset']
        end_index = annotations[i]['locations']['offset'] + annotations[i]['locations']['length']
        start_index2 = adjust_spaces_on_right(input_text, start_index)
        end_index2 = adjust_spaces_on_left(input_text, end_index)
        adjusted_start, adjusted_end = adjust_offsets(input_text, start_index2, end_index2)
        if adjusted_start != start_index or end_index != adjusted_end:
            annotations[i]['Entity'] = input_text[adjusted_start:adjusted_end]
            annotations[i]['locations']['offset'] = adjusted_start
            annotations[i]['locations']['length'] = adjusted_end - adjusted_start
    return annotations

def adjust_abbr(input_text, annotations):
    for j in range(len(annotations)):
        current_text = input_text[annotations[j]['locations']['offset']:]
        current_text = current_text.split()
        
        if len(annotations[j]['Entity']) == 2:
            if len(current_text[0]) != 2:
                annotations[j] = {}
            else:
                if current_text[0][0].isalpha() and current_text[0][1] == '.':
                    counter = 0
                    for z in range(len(current_text[1])):
                        if current_text[1][z].isalpha():
                            counter += 1
                    candidate = current_text[:len(annotations[j]['Entity'].split())+1]
                    candidate[1] = candidate[1][:counter]
                    annotations[j]['Entity'] = ' '.join(candidate)
                    annotations[j]['locations']['length'] = len(' '.join(candidate))
        
        if len(annotations[j]['Entity']) == 1:
            if len(current_text[0]) != 2:
                annotations[j] = {}
            else:
                if current_text[0][0].isalpha() and current_text[0][1] == '.':
                    counter = 0
                    for z in range(len(current_text[1])):
                        if current_text[1][z].isalpha():
                            counter += 1
                    candidate = current_text[:len(annotations[j]['Entity'].split())+1]
                    candidate[1] = candidate[1][:counter]
                    annotations[j]['Entity'] = ' '.join(candidate)
                    annotations[j]['locations']['length'] = len(' '.join(candidate))
    
    final_list = []
    for j in range(len(annotations)):
        if annotations[j] != {}:
            final_list.append(annotations[j])
    return final_list

def adjust_wc(input_text, annotations):
    for j in range(len(annotations)):
        current_text = input_text[annotations[j]['locations']['offset']:]
        current_text = current_text.split()
        if len(annotations[j]['Entity'].split()) > 2:
            current_check = annotations[j]['Entity'].split()
            if current_check[2] != 'sp' and current_check[2] != 'sp.' and current_check[2] != 'spp' and current_check[2] != 'spp.':
                if len(current_check[0]) < 2:
                    pass
                else:
                    if current_check[0][0].isalpha() and current_check[0][1] == '.':
                        candidate = current_check[:2]
                        annotations[j]['Entity'] = ' '.join(candidate)
                        annotations[j]['locations']['offset'] = len(' '.join(candidate))
                if len(current_check[1]) < 2:
                    pass
                else:
                    if current_check[1][0].isalpha() and current_check[1][1] == '.':
                        candidate = current_check[1:]
                        annotations[j]['Entity'] = ' '.join(candidate)
                        annotations[j]['locations']['length'] = len(' '.join(candidate))
                        annotations[j]['locations']['offset'] = annotations[j]['locations']['offset'] + len(current_check[0]) + 1
                if len(current_check[0]) < 2:
                    pass
                else:
                    if current_check[0][0].isalpha() and current_check[0][-1] == '.':
                        candidate = current_check[:2]
                        annotations[j]['Entity'] = ' '.join(candidate)
                        annotations[j]['locations']['length'] = len(' '.join(candidate))
                if len(current_check[1]) < 2:
                    pass
                else:
                    if current_check[1][0].isalpha() and current_check[1][-1] == '.':
                        candidate = current_check[1:]
                        annotations[j]['Entity'] = ' '.join(candidate)
                        annotations[j]['locations']['length'] = len(' '.join(candidate))
                        annotations[j]['locations']['offset'] = annotations[j]['locations']['offset'] + len(current_check[0]) + 1
                if current_check[1] == 'sp' or current_check[1] == 'spp' or current_check[1] == 'sp.' or current_check[1] == 'spp.':
                    candidate = current_check[:2]
                    annotations[j]['Entity'] = ' '.join(candidate)
                    annotations[j]['locations']['length'] = len(' '.join(candidate))
                if current_check[0][0].isupper() and current_check[1][0].islower():
                    candidate = current_check[:2]
                    annotations[j]['Entity'] = ' '.join(candidate)
                    annotations[j]['locations']['length'] = len(' '.join(candidate))
                if current_check[0][0].islower() and current_check[1][0].isupper():
                    candidate = current_check[1:]
                    annotations[j]['Entity'] = ' '.join(candidate)
                    annotations[j]['locations']['length'] = len(' '.join(candidate))
                    annotations[j]['locations']['offset'] = annotations[j]['locations']['offset'] + len(current_check[0]) + 1
    return annotations

def adjust_spp(input_text, annotations):
    for j in range(len(annotations)):
        current_text = input_text[annotations[j]['locations']['offset']:]
        current_text = current_text.split()
        if len(annotations[j]['Entity'].split()) < len(current_text):
            if 'sp' == current_text[len(annotations[j]['Entity'].split())]:
                if len(annotations[j]['Entity'].split()) == 1:                
                    annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                    annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                else:
                    if current_text[:len(annotations[j]['Entity'].split())+1][-2] == annotations[j]['Entity'].split()[-1]:                    
                        annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                        annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                    else:
                        pass
            elif 'sp.' == current_text[len(annotations[j]['Entity'].split())]:
                if len(annotations[j]['Entity'].split()) == 1:
                    annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                    annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                else:
                    if current_text[:len(annotations[j]['Entity'].split())+1][-2] == annotations[j]['Entity'].split()[-1]:
                        annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                        annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                    else:
                        pass
            elif 'spp' == current_text[len(annotations[j]['Entity'].split())]:
                if len(annotations[j]['Entity'].split()) == 1:
                    annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                    annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                else:
                    if current_text[:len(annotations[j]['Entity'].split())+1][-2] == annotations[j]['Entity'].split()[-1]:
                        annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                        annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                    else:
                        pass
            elif 'spp.' == current_text[len(annotations[j]['Entity'].split())]:
                if len(annotations[j]['Entity'].split()) == 1:
                    annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                    annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                else:
                    if current_text[:len(annotations[j]['Entity'].split())+1][-2] == annotations[j]['Entity'].split()[-1]:
                        annotations[j]['Entity'] = ' '.join(current_text[:len(annotations[j]['Entity'].split())+1])
                        annotations[j]['locations']['length'] = len(annotations[j]['Entity'])
                    else:
                        pass
    return annotations

def remove_nested_annotations(annotations):
    # Sort by start offset first, then by decreasing length
    annotations = sorted(annotations, key=lambda x: (x['locations']['offset'], -x['locations']['length']))

    filtered = []
    for i, ann in enumerate(annotations):
        start_i = ann['locations']['offset']
        end_i = start_i + ann['locations']['length']
        keep = True

        # Check if this annotation is fully contained in a longer one already kept
        for kept in filtered:
            start_k = kept['locations']['offset']
            end_k = start_k + kept['locations']['length']
            if start_i >= start_k and end_i <= end_k:
                keep = False
                break

        if keep:
            filtered.append(ann)

    return filtered

def merge_overlapping_annotations(text, annotations):
    annotations = sorted(annotations, key=lambda x: x['locations']['offset'])
    merged = []
    for ann in annotations:
        start = ann['locations']['offset']
        end = start + ann['locations']['length']

        if not merged:
            merged.append(ann)
            continue
        last = merged[-1]
        last_start = last['locations']['offset']
        last_end = last_start + last['locations']['length']
        if start >= last_start and end <= last_end:
            continue
        elif start <= last_end:
            new_start = min(start, last_start)
            new_end = max(end, last_end)
            new_text = text[new_start:new_end]

            merged[-1] = {
                'Entity': new_text.strip(),
                'locations': {'offset': new_start, 'length': new_end - new_start}
            }
        else:
            merged.append(ann)
    return merged

def microbiome_DL_ner(input_text, cpu = False):
    if type(input_text) == str:
        model_name = 'omicsNLP/microbELP_NER'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        if not isinstance(cpu, bool):
            print('Parameter "cpu": Input error, this parameter only accepts a boolean as value. If "True" the code runs using the CPU otherwise, it will try to indentify if a GPU is available and will run on CPU if not.')
            return None
        else:
            if cpu == True:
                device = torch.device("cpu")
                print('Running the code using the CPU.')
            else:
                triggered_gpu = torch.cuda.is_available()
                if triggered_gpu:
                    device = torch.device("cuda")
                    print('GPU detected, running the code using the GPU.')
                else:
                    device = torch.device("cpu")
                    print('GPU not detected, running the code using the CPU.')
        _ = model.to(device)
        sentence_text = [input_text.replace('\n', ' ')]
        
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
        
        return annotations
        
    elif type(input_text) == list:
        model_name = 'omicsNLP/microbELP_NER'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        if not isinstance(cpu, bool):
            print('Parameter "cpu": Input error, this parameter only accepts a boolean as value. If "True" the code runs using the CPU otherwise, it will try to indentify if a GPU is available and will run on CPU if not.')
            return None
        else:
            if cpu == True:
                device = torch.device("cpu")
                print('Running the code using the CPU.')
            else:
                triggered_gpu = torch.cuda.is_available()
                if triggered_gpu:
                    device = torch.device("cuda")
                    print('GPU detected, running the code using the GPU.')
                else:
                    device = torch.device("cpu")
                    print('GPU not detected, running the code using the CPU.')
        _ = model.to(device)
        final_annotation_list = []
        for kui in range(len(input_text)):
            sentence_text = [input_text[kui].replace('\n', ' ')]
            
            start_meta, len_meta, trigger_meta = [], [], []
            
            for j, input_text[kui] in enumerate(sentence_text):
                current_offset = sum(len(s) for s in sentence_text[:j])
            
                encoded = tokenizer(
                    input_text[kui],
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
                            trigger_meta.append(input_text[kui][start:end])
            
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
            annotations = adjust_boudaries(input_text[kui], annotations)
            annotations = adjust_abbr(input_text[kui], annotations)
            annotations = adjust_wc(input_text[kui], annotations)
            annotations = adjust_spp(input_text[kui], annotations)
            annotations = remove_nested_annotations(annotations)
            annotations = merge_overlapping_annotations(input_text[kui], annotations)
            final_annotation_list.append(annotations)
        
        return final_annotation_list
    
    else:
        print('Input error, this function only accepts one "str" text to annotate, or a list of "str" texts to annotate as input.')
        return None
