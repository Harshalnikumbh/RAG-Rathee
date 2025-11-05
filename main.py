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

    CRITICAL: Use ONLY HTML tags in your response. NO markdown syntax at all.

    RESPONSE FORMAT:
    <strong>Video Title:</strong> [title]<br>
    <strong>Video URL:</strong> <a href="[url]" target="_blank">[url]</a>

    <p>[Brief intro paragraph explaining what the videos cover]</p>

    <strong>Main Explanation:</strong>
    <ul>
    <li><strong>[Topic 1]:</strong> Explanation here <a href="[video_url]&t=[start_time_in_seconds]s" target="_blank">[start – end min]</a></li>
    <li><strong>[Topic 2]:</strong> Explanation here <a href="[video_url]&t=[start_time_in_seconds]s" target="_blank">[start – end min]</a></li>
    <li><strong>[Topic 3]:</strong> Explanation here <a href="[video_url]&t=[start_time_in_seconds]s" target="_blank">[start – end min]</a></li>
    </ul>

    <strong>Conclusion:</strong>
    <p>[Summary sentence with final thoughts]</p>

    TIMESTAMP RULES:
    1. Timestamps should be embedded INLINE within bullet points only
    2. Each bullet point gets ONE timestamp link at the end of its explanation
    3. DO NOT list timestamps separately after the conclusion
    4. DO NOT repeat video titles and timestamps at the end
    5. Timestamps format: <a href="[video_url]&t=[start_time_in_seconds]s" target="_blank">[start – end min]</a>
    6. Convert minutes to seconds for URL (multiply by 60)

    GENERAL RULES:
    1. Use ONLY information from provided transcripts
    2. Start response with video title and clickable URL
    3. Use HTML tags: <strong>, <p>, <ul>, <li>, <a>, <br>
    4. Make ALL URLs clickable with target="_blank"
    5. If multiple videos used, list each video title/URL at the start
    6. Be detailed and specific in explanations
    7. If question can't be answered: "I can only answer based on the provided video content."
    8. Keep conclusion brief without additional timestamp references

    EXAMPLE OUTPUT:
    <strong>Video Title:</strong> How Companies Fool You<br>
    <strong>Video URL:</strong> <a href="https://www.youtube.com/watch?v=DskRAuw8vxk" target="_blank">https://www.youtube.com/watch?v=DskRAuw8vxk</a>

    <p>Companies use several deceptive pricing methods to manipulate customers into spending more money.</p>

    <strong>Main Explanation:</strong>
    <ul>
    <li><strong>Drip Pricing:</strong> Initial low prices hide additional charges that are revealed later in the checkout process <a href="https://www.youtube.com/watch?v=DskRAuw8vxk&t=1114s" target="_blank">[18.56 – 19.52 min]</a></li>
    <li><strong>Bait and Switch:</strong> Advertised deals lure customers into stores to buy different, higher-margin products instead <a href="https://www.youtube.com/watch?v=DskRAuw8vxk&t=1166s" target="_blank">[19.44 – 20.38 min]</a></li>
    <li><strong>Razor & Blade Model:</strong> Cheap primary products create dependency on expensive refills and consumables <a href="https://www.youtube.com/watch?v=DskRAuw8vxk&t=666s" target="_blank">[11.10 – 11.62 min]</a></li>
    </ul>

    <strong>Conclusion:</strong>
    <p>These deceptive tactics are used systematically across industries, making consumer awareness and vigilance essential for protecting yourself from manipulation.</p>

    WHAT NOT TO DO:
    ❌ Do not add a separate list of timestamps after conclusion
    ❌ Do not repeat video titles at the end
    ❌ Do not use markdown syntax (**, ##, etc.)
    ❌ Do not add citations outside of bullet points
    ❌ Do not end with "📹 Video Title ⏱️ timestamp" format"""
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