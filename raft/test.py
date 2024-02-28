from datasets import Dataset, load_dataset

ds2 = Dataset.load_from_disk("sample_ds4")

print(ds2[0])
