from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import TrainingArguments, Trainer
import os
import torch

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2", torch_dtype="auto", trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")

# kinda scuffed
tokenizer.pad_token = tokenizer.eos_token

def tokenize_instruction(examples):
    return tokenizer(examples["instruction"], padding="max_length", truncation=True)

def tokenize_api(examples):
    return tokenizer(examples["api"], padding="max_length", truncation=True)

tokenized_datasets = ds.map(tokenize_instruction, batched=True)
#tokenized_datasets = tokenized_datasets.map(tokenize_api, batched=True)

training_args = TrainingArguments(output_dir="test_trainer", label_names=["api"], use_cpu=True)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
)

if torch.cuda.is_available():
    torch.cuda.empty_cache()
    #torch.cuda.set_device(1)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

trainer.train()
trainer.save_model("model_finetuned")