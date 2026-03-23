const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const recentFundsList = document.getElementById('recent-funds');
const suggestionList = document.getElementById('suggestions');

const API_URL = 'http://localhost:8000/chat';
const STATUS_URL = 'http://localhost:8000/status';
const SUGGESTIONS_URL = 'http://localhost:8000/suggestions';

async function init() {
    // Fetch last updated status
    try {
        const res = await fetch(STATUS_URL);
        const data = await res.json();
        document.getElementById('last-updated').innerText = `Last Data Update: ${data.last_updated}`;
    } catch (e) {
        document.getElementById('last-updated').innerText = 'Ask me anything about MF schemes';
    }

    // Fetch and populate suggestions
    try {
        const sRes = await fetch(SUGGESTIONS_URL);
        const suggestions = await sRes.json();
        suggestionList.innerHTML = ''; // Clear existing
        suggestions.forEach(s => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `
                <div class="s-info">
                    <div class="s-info-name">${s}</div>
                </div>
                <div class="add-btn" onclick="askQuestion('${s}')">ASK</div>
            `;
            suggestionList.appendChild(item);
        });
    } catch (e) {
        console.error("Failed to load suggestions");
    }

    // Event listeners
    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
}

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message to UI
    appendMessage('user', text);
    userInput.value = '';

    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    appendMessage('bot', '...', loadingId);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Remove loading
        document.getElementById(loadingId).remove();

        if (response.ok) {
            appendMessage('bot', data.answer, null, data.sources);
            updateRecent(text, data.answer.substring(0, 30) + '...');
        } else {
            appendMessage('bot', 'Error: ' + data.detail);
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage('bot', 'Failed to connect to backend. Make sure FastAPI server is running.');
    }
}

function appendMessage(sender, text, id = null, sources = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    if (id) msgDiv.id = id;

    let sourceHtml = '';
    if (sources && sources.length > 0) {
        sourceHtml = sources.map(s => `<a href="${s}" target="_blank" class="source-tag"><i class="fas fa-link"></i> ${new URL(s).pathname.split('/').pop()}</a>`).join(' ');
    }

    msgDiv.innerHTML = `
        <div class="bubble">
            ${text}
            ${sourceHtml}
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function askQuestion(text) {
    userInput.value = text;
    handleSend();
}

function updateRecent(title, preview) {
    // Update the left sidebar with the latest query
    const html = `
        <div class="avatar"><i class="fas fa-search"></i></div>
        <div class="chat-info">
            <span class="chat-name">${title}</span>
            <span class="chat-preview">${preview}</span>
        </div>
        <span class="time">just now</span>
    `;
    const item = document.createElement('div');
    item.className = 'chat-item';
    item.innerHTML = html;
    
    // Remove active from others
    Array.from(recentFundsList.children).forEach(c => c.classList.remove('active'));
    item.classList.add('active');
    
    recentFundsList.prepend(item);
}

init();
