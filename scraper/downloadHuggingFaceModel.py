from transformers import AutoModel, AutoTokenizer
import shutil
from sentence_transformers import SentenceTransformer

model_name = "sentence-transformers/all-MiniLM-L6-v2"
target_dir = "local_model"

# Download and save model in bin format
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

model.save_pretrained(target_dir, safe_serialization=False)
tokenizer.save_pretrained(target_dir)

# Zip the folder
#shutil.make_archive(target_dir, 'zip', target_dir)
print("✅ Model downloaded and zipped successfully.")
