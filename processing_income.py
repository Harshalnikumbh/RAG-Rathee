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
top_results = 7
max_index = similarities.argsort()[::-1][0:top_results] 
print(max_index)
new_df = df.loc[max_index]
# print(new_df[['text','video_title','chunk_id']])

prompt = f'''User asked the following question related to content from videos including titles,urls and timestamps: {new_df[['video_title','chunk_id','start_time','end_time','text']].to_json()} 
Based on the content from the videos, provide a detailed answer to the user's question
--------------------------------
User Question: "{ask_questions}".
----------------------------------
you have to answer where and how much based on the  content Based on the following context from videos, provide a detailed answer to the user's question and also mention the video title,Video_url, start time and end time from which you got the information. and the text at that time. If user ask unrelated question , response that you can only answer question related to the video\n\n'''

with open('prompt.txt','w') as f:
    f.write(prompt)

# for index, item in new_df.iterrows():
#     print(index,item['video_title'],item['chunk_id'],item['text'],
#           item['start_time'],item['end_time'])

