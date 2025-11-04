// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');

// State
let isProcessing = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    autoResizeTextarea();
});

// Event Listeners
function setupEventListeners() {
    // Send button click
    sendBtn.addEventListener('click', handleSendMessage);

    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', autoResizeTextarea);

    // Enable/disable send button based on input
    userInput.addEventListener('input', () => {
        sendBtn.disabled = !userInput.value.trim() || isProcessing;
    });

    // Example prompt cards
    const exampleCards = document.querySelectorAll('.example-card');
    exampleCards.forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            userInput.value = prompt;
            userInput.focus();
            sendBtn.disabled = false;
            handleSendMessage();
        });
    });

    // New chat button
    newChatBtn.addEventListener('click', handleNewChat);
}

// Auto-resize textarea
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

// Handle send message
async function handleSendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isProcessing) return;

    // Hide welcome screen
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }

    // Add user message to UI
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    isProcessing = true;

    // Show loading indicator
    const loadingId = addLoadingMessage();

    try {
        // Send to backend
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        // Add assistant response
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        console.error('Error:', error);
        removeLoadingMessage(loadingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

// Add message to UI
function addMessage(text, role, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    
    // ✅ FIXED: Proper if/else without duplicate
    if (role === 'assistant') {
        messageText.innerHTML = text;  // Renders HTML for assistant
    } else {
        messageText.textContent = text;  // Plain text for user (security)
    }

    content.appendChild(messageText);

    // // Add citations if available
    // if (sources && sources.length > 0) {
    //     const citationsDiv = document.createElement('div');
    //     citationsDiv.className = 'citations';
        
    //     sources.forEach(source => {
    //         const citationItem = document.createElement('div');
    //         citationItem.className = 'citation-item';
            
    //         // ✅ Make video title clickable
    //         const citationTitle = document.createElement('div');
    //         citationTitle.className = 'citation-title';
    //         citationTitle.innerHTML = `📹 <a href="${source.video_url}" target="_blank" class="citation-link">${source.video_title}</a>`;
            
    //         // ✅ Make timestamp clickable with URL + time
    //         const citationTime = document.createElement('div');
    //         citationTime.className = 'citation-time';
    //         const startSeconds = Math.floor(source.start_time * 60);
    //         const videoWithTime = `${source.video_url}${source.video_url.includes('?') ? '&' : '?'}t=${startSeconds}s`;
    //         citationTime.innerHTML = `⏱️ <a href="${videoWithTime}" target="_blank" class="timestamp-link">${source.start_time.toFixed(2)} - ${source.end_time.toFixed(2)} min</a>`;
            
    //         citationItem.appendChild(citationTitle);
    //         citationItem.appendChild(citationTime);
    //         citationsDiv.appendChild(citationItem);
    //     });
        
    //     content.appendChild(citationsDiv);
    // }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

// Add loading message
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loading-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.innerHTML = `
        <span>Thinking</span>
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    content.appendChild(loading);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
    return 'loading-message';
}

// Remove loading message
function removeLoadingMessage(id) {
    const loadingMsg = document.getElementById(id);
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle new chat
function handleNewChat() {
    // Clear messages
    messagesContainer.innerHTML = '';
    
    // Show welcome screen
    const welcomeHTML = `
        <div class="welcome-screen" id="welcomeScreen">
            <div class="welcome-content">
                <h2>Welcome to RAGRathee</h2>
                <p>Ask questions about Dhruv Rathee's video content</p>
                
                <div class="example-prompts">
                    <div class="example-card" data-prompt="How do companies fool customers?">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        <span>How do companies fool customers?</span>
                    </div>
                    <div class="example-card" data-prompt="Who is the oldest human?">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <span>Who is the oldest human?</span>
                    </div>
                    <div class="example-card" data-prompt="Tell me about shrinkflation">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                        </svg>
                        <span>Tell me about shrinkflation</span>
                    </div>
                    <div class="example-card" data-prompt="What is planned obsolescence?">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                            <path d="M16 3v4M8 3v4M2 11h20"></path>
                        </svg>
                        <span>What is planned obsolescence?</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.innerHTML = welcomeHTML;
    
    // Re-attach event listeners to new example cards
    const exampleCards = document.querySelectorAll('.example-card');
    exampleCards.forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            userInput.value = prompt;
            userInput.focus();
            sendBtn.disabled = false;
            handleSendMessage();
        });
    });
    
    // Clear input
    userInput.value = '';
    userInput.focus();
}