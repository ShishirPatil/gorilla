
# Gorilla Fine-tuning

<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

## Get Started
For training, we are using the FastChat script from lm-sys. FastChat is an open platform specifically designed for training, serving, and evaluating large language model-based chatbots.

### Install Dependencies

You should install dependencies using the following command: 

```bash
conda create -n gorilla python=3.10
conda activate gorilla
git clone https://github.com/lm-sys/FastChat.git  
cd FastChat  
pip3 install -e .
pip install transformers[deepspeed]
```
### Data Preparation
you need to format the data according to the example provided in the fastchat, as shown in the code below. It is essential to ensure that the information in the dataset you select as a response is accurate and executable by the machine. 
```json
[
	{
		"id": "identity_0",
		"conversations": [
			{
				"from": "human",
				"value": "Instruction: Design a feature for a social media website to recommend articles to users based on how similar the articles are to their previously liked articles."
			},
			{
				"from": "gpt",
				"value": "<<<domain>>>: Natural Language Processing Sentence Similarity\n<<<api_call>>>: AutoModel.from_pretrained('princeton-nlp/unsup-simcse-roberta-base')\n<<<api_provider>>>: Hugging Face Transformers\n<<<explanation>>>:1. We first import the necessary classes and modules from the transformers package. This includes AutoTokenizer and AutoModel for loading the pre-trained models from Hugging Face.\n2. We use the AutoModel.from_pretrained() method to load the 'princeton-nlp/unsup-simcse-roberta-base' model, which is specially designed for calculating sentence similarity.\n3. To build the recommendation feature, we process the text of previously liked articles and compute sentence embeddings. For each new article, we compute its sentence embedding and compare it to the embeddings of previously liked articles.\n4. If the similarity between the new article's embedding and any previous liked articles' embeddings is above a certain threshold, the new article is recommended to the user.\n<<<code>>>: from transformers import AutoTokenizer, AutoModel\ntokenizer = AutoTokenizer.from_pretrained('princeton-nlp/unsup-simcse-roberta-base')\nmodel = AutoModel.from_pretrained('princeton-nlp/unsup-simcse-roberta-base')\n"
			}
		]
	}
]
```
Above data represents a conversation between a human and a language model (GPT). Here's an explanation of the structure:

1. The conversation is represented as an array, with each element containing an "id" and a "conversations" field.
2. "id" is a unique identifier for the conversation. In this case, the identifier is "identity_0".
3. "conversations" is an array containing the messages exchanged between the human and the language model.
4. Each message is represented as an object with two fields: "from" and "value".
    -   "from" indicates whether the message is from the "human" or the "gpt" (language model) participant.
    -   "value" contains the content of the message.
5. The first message is from the human participant and contains an instruction, The second message is from the language model participant and provides a response. You can see [this link](https://github.com/ShishirPatil/gorilla/blob/main/data/apibench/huggingface_eval.json) to see example format for gorilla dataset.

### Deepspeed Config
Deepspeed can be use to speed up fine tuning, you need to navigate to the FastChat script directory and create a DeepSpeed configuration. Below is an example configuration for 2 nodes with 2 P40 GPU (120 GB RAM ) each node for CPU offloading :
```json
{  
	"train_micro_batch_size_per_gpu":  "auto",  
	"gradient_accumulation_steps":  "auto",    
	"optimizer":  {  
		"type":  "Adam",  
		"params":  {  
			"lr":  "auto",  
			"betas":  "auto",  
			"eps":  "auto",  
			"weight_decay":  "auto"  
		}  
	},  
	"fp16":  {  
		"enabled":  true,  
		"loss_scale":  0,  
		"loss_scale_window":  1000,  
		"hysteresis":  2,  
		"min_loss_scale":  1  
	},
	  "scheduler": {
	    "type": "WarmupLR",
	    "params": {
	      "warmup_min_lr": 0,
	      "warmup_max_lr": "auto",
	      "warmup_num_steps": "auto"
	    }
	  },
	"zero_optimization":  {  
		"stage":  2,  
		"offload_optimizer":  {  
			"device":  "cpu"  
		},  
		"contiguous_gradients":  true,  
		"overlap_comm":  true  
	},  
	"zero_allow_untested_optimizer":  true,  
	"activation_checkpointing":  {  
		"partition_activations":  true,  
		"contiguous_memory_optimization":  true  
	},  
	"wall_clock_breakdown":  false  
}
```
### Multi Node 
To perform training using multi-nodes, you need a hostfile with the following format:
```bash
machine1 slots=2 
machine2 slots=2
```
After that, you need to include the `--hostfile` argument in the deepspeed script that will be used.

### Fastchat Training
You need to modify the `test_train.sh` script to make it compatible with DeepSpeed. Here is an example of the modified script:
```bash
deepspeed \  
	--hostfile /path/to/hostfile
	--master_port=20001 ../fastchat/train/train.py \  
	--save_total_limit 2 \  
	--model_name_or_path /path/to/model/llama-7b \  
	--data_path /path/to/data.json \  
	--fp16 True \  
	--output_dir gorilla-model/ \  
	--num_train_epochs 5 \  
	--per_device_train_batch_size 2 \  
	--per_device_eval_batch_size 2 \  
	--gradient_accumulation_steps 1 \  
	--evaluation_strategy "steps" \  
	--eval_steps 6 \  
	--save_strategy "steps" \  
	--save_steps 6 \  
	--logging_steps 6 \  
	--learning_rate 1e-5 \  
	--weight_decay 0. \  
	--warmup_ratio 0.03 \  
	--lr_scheduler_type "cosine" \  
	--tf32 False \  
	--model_max_length 2048 \  
	--gradient_checkpointing True \  
	--lazy_preprocess True \  
	--report_to "none" \  
	--deepspeed ds_config.json \
```
To execute the script and start the fine-tuning process, run the command `bash test_train.sh`. Once the fine-tuning process is completed, you can serve the model using our inference [script](https://github.com/ShishirPatil/gorilla/blob/main/inference/README.md).