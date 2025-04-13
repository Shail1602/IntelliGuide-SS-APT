from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "microsoft/phi-1_5"  # Or replace with your preferred model

tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir="local_models/phi")
model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir="local_models/phi")

print("✅ Model and tokenizer downloaded and saved to local_models/phi")
