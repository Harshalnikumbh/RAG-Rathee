from sklearn.metrics.pairwise import cosine_similarity
from read_chunks import model 
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import os
import json
import joblib
import groq
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please create a .env file.")
client = groq.Groq(api_key=api_key)

def create_embeddings(text_list, model):
    """Create embeddings for a list of texts."""
    embeddings = model.encode(text_list, show_progress_bar=True)
    return embeddings

def format_context(df):
    """Format the retrieved chunks into a clean context string."""
    context_parts = []
    for idx, row in df.iterrows():
        context_parts.append(
            f"Video: {row['video_title']}\n"
            f"Timestamp: [{row['start_time']:.2f} - {row['end_time']:.2f} minutes]\n"
            f"Content: {row['text']}\n"
        )
    return "\n---\n".join(context_parts)

def query_groq(question, context):
    """Query Groq API with the question and context."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that answers questions based on video transcripts. 
                    
                    Rules:
                    1. Answer ONLY based on the provided context
                    2. Always cite the video title and timestamp when providing information
                    3. If the question is unrelated to the videos, politely say you can only answer questions about the provided video content
                    4. Be specific and detailed in your answers
                    5. If multiple videos discuss the topic, mention all relevant sources"""
                                    },
                {
                    "role": "user",
                    "content": f"""Context from videos:
{context}

Question: {question}

Provide a detailed answer with citations (video title and timestamps)."""
                }
            ],
            temperature=0.3,  
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error querying Groq API: {str(e)}"

def main():
    df = joblib.load('embeddings.joblib')

    ask_question = input("Ask a Question: ")
    
    if not ask_question.strip():
        print("Please enter a valid question!")
        return
    
    # Create embedding for the question
    question_embedding = create_embeddings([ask_question], model)[0]
    # Compute cosine similarities
    similarities = cosine_similarity(
        np.vstack(df['embedding'].values), 
        [question_embedding]
    ).flatten()
    
    # Get top results
    top_results = 7
    top_indices = similarities.argsort()[::-1][:top_results]
    
    print(f" Found top {top_results} relevant chunks:")
    print(f"   Indices: {top_indices}")
    print(f"   Similarity scores: {similarities[top_indices]}\n")
    
    # Get relevant chunks
    relevant_df = df.iloc[top_indices].copy()
    
    # Display retrieved chunks
    print("📋 Retrieved Chunks:")
    print("=" * 80)
    for idx, row in relevant_df.iterrows():
        print(f"Video: {row['video_title']}")
        print(f"Video URL: {row['video_url']}")
        print(f"Chunk #{row['chunk_id']} | Time: {row['start_time']:.2f}-{row['end_time']:.2f} min")
        print(f"Text: {row['text'][:150]}...")
        print("-" * 80)
    
    # Format context
    context = format_context(relevant_df)
    
    # Save prompt for debugging (optional)
    debug_prompt = f"""Question: {ask_question}

Context:
{context}
"""
    with open('prompt.txt', 'w', encoding='utf-8') as f:
        f.write(debug_prompt)
    print("\n Debug prompt saved to 'prompt.txt'")
    
    # Query Groq API
    print("\n Querying Groq API...\n")
    answer = query_groq(ask_question, context)
    
    # Display answer
    print("=" * 80)
    print(" ANSWER:")
    print("=" * 80)
    print(answer)
    print("=" * 80)
    
    # Save results
    results = {
        "question": ask_question,
        "answer": answer,
        "sources": relevant_df[['video_title', 'chunk_id', 'start_time', 'end_time', 'text']].to_dict('records')
    }
    
    with open('last_query_result.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n💾 Results saved to 'last_query_result.json'")

if __name__ == "__main__":
    main()