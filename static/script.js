// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const chatHistoryContainer = document.querySelector('.chat-history');

// State
let isProcessing = false;
let chats = []; // Store all chats
let currentChatId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadChatsFromStorage();
    setupEventListeners();
    autoResizeTextarea();
    
    // Create initial chat if no chats exist
    if (chats.length === 0) {
        createNewChat();
    } else {
        // Load the most recent chat
        loadChat(chats[0].id);
    }
});

// Load chats from localStorage
function loadChatsFromStorage() {
    const stored = localStorage.getItem('ragrathee_chats');
    if (stored) {
        chats = JSON.parse(stored);
    }
}

// Save chats to localStorage
function saveChatsToStorage() {
    localStorage.setItem('ragrathee_chats', JSON.stringify(chats));
}

// Create new chat
function createNewChat() {
    const newChat = {
        id: Date.now().toString(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString()
    };
    
    chats.unshift(newChat); // Add to beginning
    currentChatId = newChat.id;
    saveChatsToStorage();
    renderChatHistory();
    clearMessages();
}

// Update chat title based on first message
function updateChatTitle(chatId, firstMessage) {
    const chat = chats.find(c => c.id === chatId);
    if (chat && chat.title === 'New Chat') {
        // Use first 30 characters of the message as title
        chat.title = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '');
        saveChatsToStorage();
        renderChatHistory();
    }
}

// Save message to current chat
function saveMessageToChat(message, role, sources = null) {
    const chat = chats.find(c => c.id === currentChatId);
    if (chat) {
        chat.messages.push({ message, role, sources, timestamp: new Date().toISOString() });
        
        // Update title if it's the first user message
        if (role === 'user' && chat.messages.filter(m => m.role === 'user').length === 1) {
            updateChatTitle(currentChatId, message);
        }
        
        saveChatsToStorage();
    }
}

// Load chat by ID
function loadChat(chatId) {
    const chat = chats.find(c => c.id === chatId);
    if (!chat) return;
    
    currentChatId = chatId;
    clearMessages();
    
    // Render all messages from this chat
    chat.messages.forEach(msg => {
        addMessage(msg.message, msg.role, msg.sources, false); // false = don't save again
    });
    
    renderChatHistory();
}

// Render chat history in sidebar
function renderChatHistory() {
    chatHistoryContainer.innerHTML = '';
    
    chats.forEach(chat => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item' + (chat.id === currentChatId ? ' active' : '');
        historyItem.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${chat.title}</span>
        `;
        
        historyItem.addEventListener('click', () => {
            loadChat(chat.id);
        });
        
        chatHistoryContainer.appendChild(historyItem);
    });
}

// Clear messages container
function clearMessages() {
    messagesContainer.innerHTML = '';
    showWelcomeScreen();
}

// Show welcome screen
function showWelcomeScreen() {
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
    attachExampleCardListeners();
}

// Attach listeners to example cards
function attachExampleCardListeners() {
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
}

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

    // New chat button
    newChatBtn.addEventListener('click', () => {
        createNewChat();
    });
    
    // Initial example cards
    attachExampleCardListeners();
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
    const welcomeElement = document.getElementById('welcomeScreen');
    if (welcomeElement) {
        welcomeElement.style.display = 'none';
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
function addMessage(text, role, sources = null, shouldSave = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    
    if (role === 'assistant') {
        messageText.innerHTML = text;  // Renders HTML for assistant
    } else {
        messageText.textContent = text;  // Plain text for user (security)
    }

    content.appendChild(messageText);

    // Add citations if available
    if (sources && sources.length > 0) {
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'citations';
        
        sources.forEach(source => {
            const citationItem = document.createElement('div');
            citationItem.className = 'citation-item';
            
            const citationTitle = document.createElement('div');
            citationTitle.className = 'citation-title';
            citationTitle.innerHTML = `📹 <a href="${source.video_url}" target="_blank" class="citation-link">${source.video_title}</a>`;
            
            const citationTime = document.createElement('div');
            citationTime.className = 'citation-time';
            const startSeconds = Math.floor(source.start_time * 60);
            const videoWithTime = `${source.video_url}${source.video_url.includes('?') ? '&' : '?'}t=${startSeconds}s`;
            citationTime.innerHTML = `⏱️ <a href="${videoWithTime}" target="_blank" class="timestamp-link">${source.start_time.toFixed(2)} - ${source.end_time.toFixed(2)} min</a>`;
            
            citationItem.appendChild(citationTitle);
            citationItem.appendChild(citationTime);
            citationsDiv.appendChild(citationItem);
        });
        
        content.appendChild(citationsDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    // Save to chat history
    if (shouldSave) {
        saveMessageToChat(text, role, sources);
    }

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