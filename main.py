from flask import Flask, render_template, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from read_chunks import model  
import pandas as pd
import numpy as np
import joblib
import groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")
client = groq.Groq(api_key=api_key)

# Load embeddings once at startup
# print("Loading embeddings...")
df = joblib.load('embeddings.joblib')
# print(f" Loaded {len(df)} chunks from {df['video_title'].nunique()} videos\n")

# CORE FUNCTIONS

def create_embeddings(text_list, model):
    """Create embeddings for a list of texts."""
    embeddings = model.encode(text_list, show_progress_bar=False)
    return embeddings

def format_context(relevant_df):
    """Format the retrieved chunks into a clean context string."""
    context_parts = []
    for idx, row in relevant_df.iterrows():
        context_parts.append(
            f"Video: {row['video_title']}\n"
            f"Video URL: {row['video_url']}\n"
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

                    Goals:
                        - Provide a clear, accurate, and source-backed answer.
                        - Each answer must begin with the video details (title and URL).
                        - Cite timestamps precisely within the explanation.

                    CRITICAL FORMATTING RULES:
                        - Use HTML formatting ONLY: <strong>, <p>, <ul>, <li>, <a>
                        - NO markdown asterisks (*) or underscores (_)
                        - Make ALL URLs clickable with: <a href="URL" target="_blank">URL</a>
                    
                    Response Structure:
                    1. Start with video info:
                       <strong>Video Title:</strong> <title>
                       <strong>Video URL:</strong> <a href="url" target="_blank">url</a>
                    
                    2. Add intro paragraph:
                       <p>Brief summary of what the video explains...</p>
                    
                    3. Main explanation with bullet points:
                       <strong>Main Explanation:</strong>
                       <ul>
                       <li>Point 1 with details [start – end min]</li>
                       <li>Point 2 with details [start – end min]</li>
                       </ul>
                    
                    4. Conclusion:
                       <strong>Conclusion:</strong>
                       <p>Summary takeaway [start – end min]</p>
                    
                    Rules:
                    - Use ONLY provided video transcripts
                    - Cite timestamps as [start – end min] WITHOUT repeating video title/URL
                    - If question can't be answered: "I can only answer questions based on the provided video content."
                    - Be specific and detailed
                    
                    Example format:
                    **Video Title:** How Companies Fool You! | Jaago Grahak Jaago  
                    **Video URL:** https://www.youtube.com/watch?v=DskRAuw8vxk  

                    **Answer:**  
                    Companies use several deceptive pricing methods to fool customers.  
                    - **Drip Pricing:** Customers see a low price initially, but hidden charges are added later *(How Companies Fool You!, [18.56 – 19.52 min])*.  
                    - **Bait and Switch:** Attractive deals lure customers, then they're offered higher-margin alternatives *(How Companies Fool You!, [19.44 – 20.38 min])*.  
                    - **Razor & Blade Model:** The main product is cheap, but refills or parts are expensive *(How Companies Fool You!, [11.10 – 11.62 min])*.  

                    **Conclusion:**  
                    The video highlights that these tactics are used systematically, and consumers must stay alert *(How Companies Fool You!, [21.21 – 21.74 min])*.
                        
                    Rules:
                    1. Use only information from the provided video transcripts. Do NOT add outside knowledge.
                    2. Always start your answer with:
                    **Video Title:** <title>  
                    **Video URL:** <url>  
                    (If multiple videos are used, list each one on a new line.)
                    3. When mentioning facts or examples, always include the timestamp like this:
                    *(Video Title, [start_time – end_time min])*
                    4. If the question cannot be answered from the given videos, reply exactly:
                    "I'm sorry, I can only answer questions based on the provided video content."
                    5. Be specific, detailed, and explain concepts in your own words (no verbatim transcript copying).
                    6. If multiple videos cover the topic, synthesize insights from all and clearly mention which video supports which part.
                    7. Structure your answer as follows:
                    - **Intro:** Short summary of what the video(s) explain about the topic.
                    - **Main Explanation:** Bullet points or short paragraphs with timestamps and examples.
                    - **Conclusion:** One or two lines summarizing the takeaway.
                    
                    Example format:
                    **Video Title:** How Companies Fool You! | Jaago Grahak Jaago  
                    **Video URL:** https://www.youtube.com/watch?v=DskRAuw8vxk  

                    **Answer:**  
                    Companies use several deceptive pricing methods to fool customers.  
                    - **Drip Pricing:** Customers see a low price initially, but hidden charges are added later *(How Companies Fool You!, [18.56 – 19.52 min])*.  
                    - **Bait and Switch:** Attractive deals lure customers, then they're offered higher-margin alternatives *(How Companies Fool You!, [19.44 – 20.38 min])*.  
                    - **Razor & Blade Model:** The main product is cheap, but refills or parts are expensive *(How Companies Fool You!, [11.10 – 11.62 min])*.  

                    **Conclusion:**  
                    The video highlights that these tactics are used systematically, and consumers must stay alert *(How Companies Fool You!, [21.21 – 21.74 min])*.                                                    
                                                                                """
                },
                {
                    "role": "user",
                    "content": f"""Context from videos:
{context}

Question: {question}

Provide a detailed answer with citations (Video title, Video URL and timestamps)."""
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error querying Groq API: {str(e)}"
        print(error_msg)
        return error_msg

def process_question(question, top_results=7, verbose=False):
    """
    Process a question and return answer with sources.
    This function can be used by both CLI and API endpoints.
    """
    if not question.strip():
        return None, "Please enter a valid question!"
    
    # Create embedding for the question
    question_embedding = create_embeddings([question], model)[0]
    
    # Calculate similarities
    similarities = cosine_similarity(
        np.vstack(df['embedding'].values),
        [question_embedding]
    ).flatten()
    
    # Get top results
    top_indices = similarities.argsort()[::-1][:top_results]
    
    if verbose:
        print(f"\n🔍 Found top {top_results} relevant chunks")
        print(f"   Similarity scores: {similarities[top_indices]}\n")
    
    # Get relevant chunks
    relevant_df = df.iloc[top_indices].copy()
    
    # Display retrieved chunks if verbose
    if verbose:
        print("Retrieved Chunks:")
        print("=" * 80)
        for idx, row in relevant_df.iterrows():
            print(f"Video: {row['video_title']}")
            print(f"Video URL: {row['video_url']}")
            print(f"Chunk #{row['chunk_id']} | Time: {row['start_time']:.2f}-{row['end_time']:.2f} min")
            print(f"Text: {row['text'][:150]}...")
            print("-" * 80)
    
    # Format context
    context = format_context(relevant_df)
    
    # Query Groq API
    if verbose:
        print("\n Thinking....\n")
    
    answer = query_groq(question, context)
    
    # Prepare sources
    sources = []
    for idx, row in relevant_df.iterrows():
        sources.append({
            'video_title': row['video_title'],
            'video_url': row['video_url'],
            'chunk_id': int(row['chunk_id']),
            'start_time': float(row['start_time']),
            'end_time': float(row['end_time']),
            'text': row['text']
        })
    
    return answer, sources

# FLASK ROUTES
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query_endpoint():
    """Handle user queries via API."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Process the question
        answer, sources = process_question(question, verbose=False)
        
        if answer is None:
            return jsonify({'error': sources}), 400
        
        # Truncate source text for API response
        api_sources = []
        for src in sources:
            api_sources.append({
                **src,
                'text': src['text'][:200] + '...' if len(src['text']) > 200 else src['text']
            })
        
        return jsonify({
            'answer': answer,
            'sources': api_sources,
            'question': question
        })
        
    except Exception as e:
        print(f"Error in /query: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get statistics about the database."""
    try:
        unique_videos = df['video_title'].nunique()
        total_chunks = len(df)
        
        return jsonify({
            'total_videos': unique_videos,
            'total_chunks': total_chunks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CLI MODE

def run_cli():
    """Run in command-line interface mode."""
    print("\n" + "="*80)
    print("📺 RAG Video Q&A System - CLI Mode")
    print("="*80)
    print(f"📊 Loaded {len(df)} chunks from {df['video_title'].nunique()} videos")
    print("Type 'exit' or 'quit' to stop\n")
    
    while True:
        try:
            question = input("\n❓ Ask a question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not question:
                print(" Please enter a valid question!")
                continue
            
            # Process the question
            answer, sources = process_question(question, verbose=True)
            
            if answer is None:
                print(f"{sources}")
                continue
            
            # Display answer
            # print("\n" + "="*80)
            # print("💡 ANSWER:")
            # print("="*80)
            # print(answer)
            # print("="*80)
            
            # Optionally save debug info
            save = input("\n💾 Save prompt to file? (y/n): ").strip().lower()
            if save == 'y':
                context = format_context(df.iloc[[s['chunk_id'] for s in sources]])
                debug_prompt = f"""Question: {question}

Context:
{context}

Answer:
{answer}
"""
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

# MAIN ENTRY POINT

if __name__ == '__main__':
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--cli':
            # Run in CLI mode
            run_cli()
        elif sys.argv[1] == '--help':
            print("Usage: python main.py [--cli | --help]")
            print("  --cli    Run in command-line interface mode")
            print("  --help   Show this help message")

        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Default: Run Flask server
        app.run(debug=True, host='0.0.0.0', port=5000)