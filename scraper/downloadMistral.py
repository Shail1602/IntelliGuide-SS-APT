from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "microsoft/phi-2"
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)

model.save_pretrained("local_models/mistral7b")
tokenizer.save_pretrained("local_models/mistral7b")
