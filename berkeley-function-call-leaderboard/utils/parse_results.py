import pandas as pd
import json
import os

# this is really hacky code. But it should do for now.
# TODO: clean this up

# returns datafame with accuracy info for a given model
def get_acc_df(models=['databricks-dbrx-instruct-old-run'], scores_path='score'):
    acc_df_list = []
    for model in models:
        # get all json files in score/ directory
        results_dir = f'{scores_path}/{model}'
        json_files = [f'{results_dir}/{f}' for f in os.listdir(results_dir) if f.endswith('.json')]

        results_dict = {'filename': [], 'accuracy': [], 'correct_count': [], 'total_count': []}
        for filename in json_files:
            with open(filename, 'r') as f:
                data = [json.loads(line) for line in f.readlines()]
                accuracy_info = data[0]
                results_dict['filename'].append(filename)
                for key in accuracy_info.keys():
                    results_dict[key].append(accuracy_info[key])

        acc_df = pd.DataFrame(results_dict)
        acc_df['metric'] = acc_df['filename'].apply(lambda x: x.split('/')[-1].split('.')[0])

        overall_acc = acc_df.correct_count.sum() / acc_df.total_count.sum()
        if model == "generic-vllm-model":
            model_name = os.environ.get("VLLM_MODEL_NAME", model)
        else:
            model_name = model

        print(f'\n\nModel: {model_name} | Overall accuracy: {overall_acc}\n\n')
        acc_df_list.append(acc_df)

    return pd.concat(acc_df_list)


# returns acc_df, error_result_df, full_result_df for a given list of models
def get_results_df(models=['databricks-dbrx-instruct-old-run'], scores_path='score', results_path='result'):
    error_results_df_list = []
    full_results_df_list = []
    acc_dict = {'model': [], 'filename': [], 'accuracy': [], 'correct_count': [], 'total_count': []}
    for model in models:
        # model = 'gpt-3.5-turbo-0125'
        results_dir = f'{scores_path}/{model}'
        json_files = [f'{results_dir}/{f}' for f in os.listdir(results_dir) if f.endswith('.json')]
        for filename in json_files:
            with open(filename, 'r') as f:
                try:
                    data = [json.loads(line) for line in f.readlines()]
                    # skip the accuracy line
                    df = pd.DataFrame(data[1:])
                    df['filename'] = filename.split('/')[-1]
                    error_results_df_list.append(df)
                    # parse out accuracy_info
                    acc_info = data[0]
                    acc_dict['filename'].append(filename.split('/')[-1])
                    acc_info['model'] = model
                    for key in acc_info.keys():
                        acc_dict[key].append(acc_info[key])
                except Exception as e:
                    print(f'Error reading {filename}: {e}')
                    
    # now read full results
    for model in models:
        results_dir = f'{results_path}/{model}'
        json_files = [f'{results_dir}/{f}' for f in os.listdir(results_dir) if f.endswith('.json')]
        for filename in json_files:
            with open(filename, 'r') as f:
                try:
                    data = [json.loads(line) for line in f.readlines()]
                    df = pd.DataFrame(data)
                    df['filename'] = filename.split('/')[-1]
                    df['model_name'] = model
                    full_results_df_list.append(df)
                except Exception as e:
                    print(f'Error reading {filename}: {e}')

    acc_df = pd.DataFrame(acc_dict)
    acc_df['metric'] = acc_df['filename'].apply(lambda x: x.split('/')[-1].split('.')[0])
    error_result_df = pd.concat(error_results_df_list)
    full_result_df = pd.concat(full_results_df_list)

    for model in acc_df['model'].unique():
        acc = acc_df[acc_df['model'] == model].correct_count.sum() / acc_df[acc_df['model'] == model].total_count.sum()
        print(f'Model: {model} : Acc = {100.0*acc}%')

    return acc_df, error_result_df, full_result_df
