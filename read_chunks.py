import json
import os
import pandas as pd
import numpy as np
import joblib
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

def create_embeddings(text_list, model):
    """Create embeddings for a list of texts."""
    embeddings = model.encode(text_list, show_progress_bar=True)
    return embeddings

# Load model once
print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!\n")

if __name__ == "__main__":
    # Get all JSON files
    jsons = [f for f in os.listdir('transcripts_json') if f.endswith('.json')]

    chunks = []

# Process only first file (with break)
    for json_file in jsons:
        with open(f"transcripts_json/{json_file}",encoding='utf-8') as f:
            content = json.load(f)
        print("processing: ", json_file)
        
        print(f"Creating Embeddings for {json_file}")
        embeddings = create_embeddings([c['text'] for c in content['chunks']], model)
        
        for i, chunk in enumerate(content['chunks']):
            chunk['video_id'] = content['video_id']
            chunk['video_url'] = content['video_url']
            chunk['duration_minutes'] = content['duration_minutes']
            chunk['embedding'] = embeddings[i].tolist()
            chunks.append(chunk)
        
    df = pd.DataFrame.from_records(chunks)
    # save this df 
    joblib.dump(df, 'embeddings.joblib')

                                 