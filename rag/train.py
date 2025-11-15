from datasets import load_dataset
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

### Train the retriever's embedder on the squad dataset

squad_dataset = load_dataset("squad")

train_dataset = squad_dataset["train"]

train_data = [InputExample(texts=['Query: ' + x['question'], 'Context: ' + x['context']], label=1) for x in train_dataset]

model = SentenceTransformer('all-MiniLM-L6-v2', device="cuda")

train_dataloader = DataLoader(train_data, shuffle=True, batch_size=16)
train_loss = losses.ContrastiveLoss(model)

model.fit(train_objectives=[(train_dataloader, train_loss)], epochs=1, warmup_steps=100)

model.save('rag-embed-model')