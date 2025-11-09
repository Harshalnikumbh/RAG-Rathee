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
let currentUser = null;

// ===============================
// Mobile Sidebar Toggle (MOVED TO TOP)
// ===============================
function setupMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    console.log('Sidebar:', sidebar); // Debug
    console.log('Toggle:', sidebarToggle); // Debug
    console.log('Overlay:', sidebarOverlay); // Debug

    if (!sidebarToggle || !sidebarOverlay || !sidebar) {
        console.error('Sidebar elements not found!');
        return;
    }

    // Toggle sidebar
    sidebarToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Toggle clicked!'); // Debug
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
    });

    // Close sidebar when overlay is clicked
    sidebarOverlay.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Overlay clicked!'); // Debug
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
    });

    // Close sidebar when a chat is selected (mobile only)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && e.target.closest('.history-item')) {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        }
    });
}

// ===============================
// Initialization
// ===============================
document.addEventListener('DOMContentLoaded', async () => {
    console.log("DOM fully loaded and parsed"); 
    setupMobileSidebar();
    await checkAuthStatus();
    setupEventListeners();
    autoResizeTextarea();
});

// ===============================
// Authentication Functions
// ===============================
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/user');
        const user = await response.json();
        
        if (user) {
            currentUser = user;
            document.querySelector('.sidebar-footer').innerHTML = `
                <div class="user-profile">
                    <img src="${user.picture}" alt="${user.name}" class="user-avatar">
                    <div class="user-info">
                        <div class="user-name">${user.name}</div>
                        <div class="user-email">${user.email}</div>
                    </div>
                    <button class="logout-btn" onclick="logout()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16 17 21 12 16 7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                    </button>
                </div>
            `;
            
            await loadUserChats();
            
            if (chats.length === 0) {
                createNewChat();
            } else {
                loadChat(chats[0].id);
            }
        } else {
            showLoginScreen();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginScreen();
    }
}

function showLoginScreen() {
    messagesContainer.innerHTML = `
        <div class="login-screen">
            <div class="login-content">
                <div class="login-logo">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <h2>Welcome to RAGRathee</h2>
                <p>Sign in to start asking questions about Dhruv Rathee's videos</p>
                <button class="google-signin-btn" onclick="window.location.href='/login'">
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </button>
            </div>
        </div>
    `;
    
    // Disable input when not logged in
    userInput.disabled = true;
    sendBtn.disabled = true;
    newChatBtn.disabled = true;
}

async function logout() {
    try {
        await fetch('/logout');
        currentUser = null;
        chats = [];
        currentChatId = null;
        showLoginScreen();
        chatHistoryContainer.innerHTML = '';
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// ===============================
// Storage Functions (Server-side)
// ===============================
async function loadUserChats() {
    try {
        const response = await fetch('/chats');
        if (response.ok) {
            chats = await response.json();
            renderChatHistory();
        }
    } catch (error) {
        console.error('Failed to load chats:', error);
        chats = [];
    }
}

async function saveChatsToServer() {
    try {
        await fetch('/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(chats)
        });
    } catch (error) {
        console.error('Failed to save chats:', error);
    }
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
    saveChatsToServer();
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
        saveChatsToServer();
        renderChatHistory();
    }
}

function renameChat(chatId, newName) {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
        chat.title = newName;
        saveChatsToServer();
        renderChatHistory();
    }
}

function deleteChat(chatId) {
    chats = chats.filter(c => c.id !== chatId);
    saveChatsToServer();
    
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

        saveChatsToServer();
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
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllMenus();
            const popup = btn.nextElementSibling;
            popup.classList.toggle('hidden');
        });
    });

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

    document.querySelectorAll('.menu-item.delete').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chatId = item.closest('.history-item').dataset.id;
            deleteChat(chatId);
            closeAllMenus();
        });
    });

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

        if (response.status === 401) {
            const data = await response.json();
            removeLoadingMessage(loadingId);
            showToast("⚠️ Please log in to continue");
            setTimeout(() => window.location.href = '/login', 1500);
            return;
        }

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