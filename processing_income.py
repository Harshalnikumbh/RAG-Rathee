from sklearn.metrics.pairwise import cosine_similarity
from read_chunks import model
import pandas as pd
import numpy as np
import joblib

def create_embeddings(text_list, model):
    """Create embeddings for a list of texts."""
    embeddings = model.encode(text_list, show_progress_bar=True)
    return embeddings

# Load the dataframe
df = joblib.load('embeddings.joblib')

ask_questions = input("Ask a Question: ")
question_embedding = create_embeddings([ask_questions],model)[0]
# print(question_embedding)
# print(np.vstack(df['embedding'].values))
# print(np.vstack(df['embedding']).shape)

similarities = cosine_similarity(np.vstack(df['embedding']),[question_embedding]).flatten()
# print(similarities)
top_results = 3
max_index = similarities.argsort()[::-1][0:top_results] 
print(max_index)
new_df = df.loc[max_index]
# print(new_df[['text','video_title','chunk_id']])

for index, item in new_df.iterrows():
    print(index,item['video_title'],item['chunk_id'],item['text'],
          item['start_time'],item['end_time'])

