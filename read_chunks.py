from sentence_transformers import SentenceTransformer
import time
import os
import time
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # hide TensorFlow logs
print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!\n")

print("Testing single embedding...")
start = time.time()
embedding = model.encode("Hello, world!")
elapsed = time.time() - start

print(f" Time: {elapsed:.3f}s")
print(f" Dimensions: {len(embedding)}")
print(f" values: {embedding}")
