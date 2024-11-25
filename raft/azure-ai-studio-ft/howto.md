# HOWTO: Fine-tune llama-2-7b in Azure AI Studio

> ⚠️ See the **Azure RAFT Distillation Recipe repo** ([Azure-Samples/raft-distillation-recipe](https://aka.ms/raft-recipe)) for instructions, notebooks and infrastructure provisioning for Meta Llama 3.1 and 3.2 as well as GPT-4o.

## Prerequisites

[Prerequisites in MS Learn article "Fine-tune a Llama 2 model in Azure AI Studio"](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/fine-tune-model-llama#prerequisites)

## Key things to get right for everything to work

- Select the West US 3 location
- Use a Pay As You go Subscription with a credit card linked
- Make sure the subscription is registered to the `Microsoft.Network` resource provider

## Detailed step by step

This builds on the ["Fine-tune a Llama 2 model in Azure AI Studio" MS Learn tutorial](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/fine-tune-model-llama#prerequisites) and adds a few details here and there.

Open https://ai.azure.com/

Create a new AI Project
![Step 01](images/azure-ai-studio-finetuning-01.png)

Enter a name and create a new resource
![Step 02](images/azure-ai-studio-finetuning-02.png)

Enter an AI Hub resource name, select the PAYG (Pay As You Go) Subscription and West US 3 location
![Step 03](images/azure-ai-studio-finetuning-03.png)

Note: It's important to use a PAYG subscription with a credit card linked to the account. Grant based subscriptions and credits will not work.

Review that the location is correctly set to West US 3 and that the subscription is correct
![Step 04](images/azure-ai-studio-finetuning-04.png)

The resources should begin being created
![Step 05](images/azure-ai-studio-finetuning-05.png)

Wait until all resources have been created
![Step 06](images/azure-ai-studio-finetuning-06.png)

Once in the AI Studio project, open the Fine-tuning tab and click on the Fine-tune model button
![Step 07](images/azure-ai-studio-finetuning-07.png)

Select the model to fine-tune, for example Llama 2 7b
![Step 08](images/azure-ai-studio-finetuning-08.png)

Subscribe if necessary to the Meta subscription and start the fine-tuning
![Step 09](images/azure-ai-studio-finetuning-09.png)

Enter the name of the fine-tuned model
![Step 10](images/azure-ai-studio-finetuning-10.png)

Select the task type, currently, only text generation is supported
![Step 11](images/azure-ai-studio-finetuning-11.png)

Select the upload data option and upload your file, it must be in JSONL format
![Step 12](images/azure-ai-studio-finetuning-12.png)

The wizard will show you an overview of the top lines
![Step 13](images/azure-ai-studio-finetuning-13.png)

Select which columns is the prompt and which one is the completion column
![Step 14](images/azure-ai-studio-finetuning-14.png)

Select the task parameters
![Step 15](images/azure-ai-studio-finetuning-15.png)

Review the settings
![Step 16](images/azure-ai-studio-finetuning-16.png)

The job should be in running state
![Step 17](images/azure-ai-studio-finetuning-17.png)

Wait until the job is completed
![Step 18](images/azure-ai-studio-finetuning-18.png)
