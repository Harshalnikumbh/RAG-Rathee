from flask import Flask, render_template, request, jsonify , session, redirect, url_for
from sklearn.metrics.pairwise import cosine_similarity
from transcripts_json_YT_Transcript.read_chunks import model  
from authlib.integrations.flask_client import OAuth 
from dotenv import load_dotenv
from functools import wraps
import pandas as pd
import numpy as np
import joblib
import groq
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

#intialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

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
user_chats = {}  # In-memory storage for user chats

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

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
     Do not add a separate list of timestamps after conclusion
     Do not repeat video titles at the end
     Do not use markdown syntax (**, ##, etc.)
     Do not add citations outside of bullet points
     Do not end with "📹 Video Title ⏱️ timestamp" format
     If user reply "thankyou" , don't provide any URL , Title , Main Explaination or Conclusion , just reply "You're welcome! If you have any more questions, feel free to ask".
     if user say Who are you, respond with "I am an AI assistant designed to help answer questions based on video transcripts.
     if user say What can you do, respond with "I can help answer questions using information about dhruv rathee video.
     note: always follow the RESPONSE FORMAT strictly
     if user say anything unrelated to the video content, respond with "I can only answer based on the provided video content and also then dont provide any video related answer.
     if user ask for list, respond with "I can only answer based on the provided video content and also then dont provide any video related answer.
     if user say anything offensive, respond with "I am here to provide helpful and respectful information. Let's keep our conversation positive and focused on the video content.
     if user say anything political, respond with "I can only answer based on the provided video content and also then dont provide any video related answer.
     if user say anything religious, respond with "I can only answer based on the provided video content and also then dont provide any video related answer.
     if user say anything sexual, respond with "I am here to provide helpful and respectful information. Let's keep our conversation positive and focused on the video content.
     if user say anything hateful, respond with "I am here to provide helpful and respectful information. Let's keep our conversation positive and focused on the video content
     If user reply "How are you? reply -> I am an AI assistant, and I don't have personal feelings or emotions, but I can provide information on how to maintain good health and well-being related to the Dhruv Rathe video.
    and also in answer don't provide any video related answer don't provide any URL , Title , Main Explaination or Conclusion. """
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

# Helper functions for user chat management
def get_user_chats(user_email):
    """Get chats for a specific user."""
    if user_email not in user_chats:
        user_chats[user_email] = []
    return user_chats[user_email]

def save_user_chats(user_email, chats):
    """Save chats for a specific user."""
    user_chats[user_email] = chats

#Authetication Route
@app.route('/login')
def login():
    """Redirect to Google OAuth login."""
    redirect_uri = url_for('authorize', _external=True)
    print(f"Redirect URL: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    """Handle OAuth callback."""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            session['user'] = {
                'email': user_info['email'],
                'name': user_info.get('name', 'User'),
                'picture': user_info.get('picture', '')
            }
            return redirect('/')
        else:
            return redirect('/login')
    except Exception as e:
        print(f"OAuth error: {str(e)}")
        return redirect('/login')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    return redirect('/')

@app.route('/api/user')
def get_user():
    """Get current user info."""
    if 'user' in session:
        return jsonify(session['user'])
    return jsonify(None)

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

@app.route('/chats', methods=['POST'])
@login_required
def save_chats():
    """Save chats for the current user."""
    try:
        user_email = session['user']['email']
        chats = request.get_json()
        save_user_chats(user_email, chats)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chats', methods=['GET'])
@login_required
def get_chats():
    """Get chats for the current user."""
    try:
        user_email = session['user']['email']
        chats = get_user_chats(user_email)
        return jsonify(chats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get statistics about the database."""
    try:
        unique_videos = df['video_  title'].nunique()
        total_chunks = len(df)
        
        return jsonify({
            'total_videos': unique_videos,
            'total_chunks': total_chunks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# MAIN ENTRY POINT
if __name__ == '__main__':
        # Run the Flask app
        # app.run(debug=True, host='0.0.0.0', port=5000)
        import os 
        port = int(os.environ.get("PORT", 7860))
        app.run(host='0.0.0.0', port=port, debug=False)
