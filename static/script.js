// ===============================
// DOM Elements
// ===============================
const messagesContainer = document.getElementById('messagesContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const chatHistoryContainer = document.querySelector('.chat-history');

// ===============================
// State Management
// ===============================
let isProcessing = false;
let chats = [];
let currentChatId = null;

// ===============================
// Initialization
// ===============================
document.addEventListener('DOMContentLoaded', () => {
    loadChatsFromStorage();
    setupEventListeners();
    autoResizeTextarea();

    if (chats.length === 0) {
        createNewChat();
    } else {
        loadChat(chats[0].id);
    }
});

// ===============================
// Storage Functions
// ===============================
function loadChatsFromStorage() {
    const stored = localStorage.getItem('ragrathee_chats');
    if (stored) {
        chats = JSON.parse(stored);
    }
}

function saveChatsToStorage() {
    localStorage.setItem('ragrathee_chats', JSON.stringify(chats));
}

// ===============================
// Chat Management
// ===============================
function createNewChat() {
    const newChat = {
        id: Date.now().toString(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString()
    };

    chats.unshift(newChat);
    currentChatId = newChat.id;
    saveChatsToStorage();
    renderChatHistory();
    clearMessages();
}

function loadChat(chatId) {
    const chat = chats.find(c => c.id === chatId);
    if (!chat) return;

    currentChatId = chatId;
    clearMessages();

    chat.messages.forEach(msg => {
        addMessage(msg.message, msg.role, msg.sources, false);
    });

    renderChatHistory();
}

function updateChatTitle(chatId, firstMessage) {
    const chat = chats.find(c => c.id === chatId);
    if (chat && chat.title === 'New Chat') {
        chat.title = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '');
        saveChatsToStorage();
        renderChatHistory();
    }
}

function renameChat(chatId, newName) {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
        chat.title = newName;
        saveChatsToStorage();
        renderChatHistory();
    }
}

function deleteChat(chatId) {
    chats = chats.filter(c => c.id !== chatId);
    saveChatsToStorage();
    
    if (currentChatId === chatId) {
        if (chats.length > 0) {
            loadChat(chats[0].id);
        } else {
            createNewChat();
        }
    } else {
        renderChatHistory();
    }
}

function saveMessageToChat(message, role, sources = null) {
    const chat = chats.find(c => c.id === currentChatId);
    if (chat) {
        chat.messages.push({ 
            message, 
            role, 
            sources, 
            timestamp: new Date().toISOString() 
        });

        if (role === 'user' && chat.messages.filter(m => m.role === 'user').length === 1) {
            updateChatTitle(currentChatId, message);
        }

        saveChatsToStorage();
    }
}

function clearMessages() {
    messagesContainer.innerHTML = '';
    showWelcomeScreen();
}

// ===============================
// Chat History Rendering
// ===============================
function renderChatHistory() {
    chatHistoryContainer.innerHTML = '';

    chats.forEach(chat => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item' + (chat.id === currentChatId ? ' active' : '');
        historyItem.dataset.id = chat.id;

        historyItem.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="chat-title">${chat.title}</span>
            
            <div class="menu-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="5" r="1.5"></circle>
                    <circle cx="12" cy="12" r="1.5"></circle>
                    <circle cx="12" cy="19" r="1.5"></circle>
                </svg>
            </div>
            <div class="menu-popup hidden">
                <div class="menu-item rename">✏️ Rename</div>
                <div class="menu-item share">🔗 Share</div>
                <div class="menu-item delete">🗑️ Delete</div>
            </div>
        `;

        historyItem.addEventListener('click', (e) => {
            if (!e.target.closest('.menu-btn') && !e.target.closest('.menu-popup')) {
                loadChat(chat.id);
            }
        });

        chatHistoryContainer.appendChild(historyItem);
    });

    setupMenuListeners();
}

// ===============================
// Menu System
// ===============================
function setupMenuListeners() {
    // Toggle menu
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllMenus();
            const popup = btn.nextElementSibling;
            popup.classList.toggle('hidden');
        });
    });

    // Rename functionality
    document.querySelectorAll('.menu-item.rename').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chatEl = item.closest('.history-item');
            const chatId = chatEl.dataset.id;
            const titleEl = chatEl.querySelector('.chat-title');
            
            const input = document.createElement('input');
            input.type = 'text';
            input.value = titleEl.textContent;
            input.className = 'rename-input';
            titleEl.replaceWith(input);
            input.focus();
            input.select();

            const saveName = () => {
                const newName = input.value.trim() || 'Untitled Chat';
                renameChat(chatId, newName);
            };

            input.addEventListener('keydown', e => {
                if (e.key === 'Enter') saveName();
                if (e.key === 'Escape') renderChatHistory();
            });
            input.addEventListener('blur', saveName);
            
            closeAllMenus();
        });
    });

    // Delete functionality (no confirmation)
    document.querySelectorAll('.menu-item.delete').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chatId = item.closest('.history-item').dataset.id;
            deleteChat(chatId);
            closeAllMenus();
        });
    });

    // Share functionality
    document.querySelectorAll('.menu-item.share').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chatId = item.closest('.history-item').dataset.id;
            const shareUrl = `${window.location.origin}/chat?id=${chatId}`;
            
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast("🔗 Link copied!");
            }).catch(() => {
                showToast("❌ Failed to copy link");
            });
            
            closeAllMenus();
        });
    });

    document.addEventListener('click', closeAllMenus);
}

function closeAllMenus() {
    document.querySelectorAll('.menu-popup').forEach(popup => {
        popup.classList.add('hidden');
    });
}

// ===============================
// Welcome Screen
// ===============================
function showWelcomeScreen() {
    const welcomeHTML = `
        <div class="welcome-screen" id="welcomeScreen">
            <div class="welcome-content">
                <h2>Welcome to RAGRathee</h2>
                <p>Ask questions about Dhruv Rathee's video content</p>

                <div class="example-prompts">
                    <div class="example-card" data-prompt="How do companies fool customers?">
                        How do companies fool customers?
                    </div>
                    <div class="example-card" data-prompt="Who is the oldest human?">
                        Who is the oldest human?
                    </div>
                    <div class="example-card" data-prompt="Tell me about shrinkflation">
                        Tell me about shrinkflation
                    </div>
                    <div class="example-card" data-prompt="What is planned obsolescence?">
                        What is planned obsolescence?
                    </div>
                </div>
            </div>
        </div>
    `;
    messagesContainer.innerHTML = welcomeHTML;
    attachExampleCardListeners();
}

// ===============================
// Event Listeners
// ===============================
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    userInput.addEventListener('input', () => {
        sendBtn.disabled = !userInput.value.trim() || isProcessing;
        autoResizeTextarea();
    });

    newChatBtn.addEventListener('click', createNewChat);
    attachExampleCardListeners();
}

function attachExampleCardListeners() {
    document.querySelectorAll('.example-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            userInput.value = prompt;
            sendBtn.disabled = false;
            handleSendMessage();
        });
    });
}

// ===============================
// Message Handling
// ===============================
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message || isProcessing) return;

    const welcomeElement = document.getElementById('welcomeScreen');
    if (welcomeElement) {
        welcomeElement.style.display = 'none';
    }

    addMessage(message, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    isProcessing = true;

    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: message })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();
        removeLoadingMessage(loadingId);
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

// ===============================
// Message Display
// ===============================
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
    messageText.innerHTML = role === 'assistant' ? text : text.replace(/</g, '&lt;');

    content.appendChild(messageText);

    // Sources are already embedded in the message text as clickable links
    // No need to display them separately

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    if (shouldSave) {
        saveMessageToChat(text, role, sources);
    }
    
    scrollToBottom();
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loading-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="loading">
                <span>Thinking</span>
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return 'loading-message';
}

function removeLoadingMessage(id) {
    const msg = document.getElementById(id);
    if (msg) {
        msg.remove();
    }
}

// ===============================
// UI Utilities
// ===============================
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => toast.classList.remove('show'), 2500);
    setTimeout(() => toast.remove(), 3000);
}