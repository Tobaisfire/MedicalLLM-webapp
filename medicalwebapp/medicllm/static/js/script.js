const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const chatHistory = document.getElementById('chat-history');
const newChatBtn = document.getElementById('new-chat-btn');
const userInfoForm = document.getElementById('user-info-form');
const userNameInput = document.getElementById('user-name');
const userAgeInput = document.getElementById('user-age');
const userGenderInput = document.getElementById('user-gender');
const userAboutInput = document.getElementById('user-about');

// Add marked.js for markdown rendering if not already present
if (typeof marked === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(script);
}

// Fetch all chats and messages from backend
async function fetchChats() {
    const res = await fetch('/api/chats');
    const data = await res.json();
    return data.chats;
}

// Save a new chat session to backend
async function saveChat(chat) {
    await fetch('/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chat)
    });
}

// Save a new message to backend
async function saveMessage(message) {
    await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message)
    });
}

let chats = [];
let activeChatId = null;

async function initializeChats() {
    chats = await fetchChats();
    if (chats.length) {
        activeChatId = chats[0].id;
    }
    renderChatList();
    renderMessages();
    showUserInfoFormIfNeeded();
}

function renderChatList() {
    chatHistory.innerHTML = '';
    chats.forEach(chat => {
        const li = document.createElement('li');
        li.textContent = chat.title || 'Untitled Chat';
        li.className = chat.id === activeChatId ? 'active' : '';
        li.onclick = () => {
            activeChatId = chat.id;
            onChatSwitch();
        };
        chatHistory.appendChild(li);
    });
    // Add report buttons below chat list if a chat is selected
    const reportBtns = document.getElementById('report-btns');
    if (reportBtns) reportBtns.remove();
    if (activeChatId) {
        const btnDiv = document.createElement('div');
        btnDiv.id = 'report-btns';
        btnDiv.style.display = 'flex';
        btnDiv.style.gap = '12px';
        btnDiv.style.margin = '18px 32px 0 32px';
        btnDiv.innerHTML = `
            <button class="send-btn" onclick="window.open('/api/report/${activeChatId}/view', '_blank')">View Report</button>
            <button class="send-btn" onclick="window.open('/api/report/${activeChatId}/download', '_blank')">Download PDF</button>
            <button class="send-btn" onclick="window.open('/api/report/${activeChatId}/figure', '_blank')">View XAI</button>
        `;
        document.querySelector('.chat-section').prepend(btnDiv);
    }
}

function renderMessages() {
    chatMessages.innerHTML = '';
    const chat = chats.find(c => c.id === activeChatId);
    if (!chat) return;
    chat.messages.forEach(msg => {
        let div = document.createElement('div');
        let label = document.createElement('span');
        let avatar = document.createElement('span');
        if (msg.role === 'user-info') {
            div.className = 'user-info-bubble';
            label.className = 'sender-label';
            label.textContent = 'You';
            avatar.className = 'bubble-avatar';
            avatar.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="User" style="width:28px;">';
            div.appendChild(avatar);
            div.appendChild(label);
            div.appendChild(document.createTextNode(msg.content));
        } else if (msg.role === 'bot') {
            div.className = 'message bot';
            label.className = 'sender-label assistant';
            label.textContent = 'Medic Assistant';
            avatar.className = 'bubble-avatar assistant';
            avatar.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="Medic Assistant" style="width:28px;">';
            div.appendChild(avatar);
            div.appendChild(label);
            if (typeof marked !== 'undefined') {
                const contentDiv = document.createElement('div');
                contentDiv.innerHTML = marked.parse(msg.content);
                div.appendChild(contentDiv);
            } else {
                div.appendChild(document.createTextNode(msg.content));
            }
        } else if (msg.role === 'user') {
            div.className = 'message user';
            label.className = 'sender-label';
            label.textContent = 'You';
            avatar.className = 'bubble-avatar';
            avatar.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="User" style="width:28px;">';
            div.appendChild(avatar);
            div.appendChild(label);
            div.appendChild(document.createTextNode(msg.content));
        } else {
            div.className = 'message ' + msg.role;
            div.appendChild(document.createTextNode(msg.content));
        }
        chatMessages.appendChild(div);
    });
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateSixDigitAlphanumeric() {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

function showUserInfoFormIfNeeded() {
    const chat = chats.find(c => c.id === activeChatId);
    if (chat && chat.messages.length === 0) {
        userInfoForm.style.display = '';
        chatForm.style.display = 'none';
    } else {
        userInfoForm.style.display = 'none';
        chatForm.style.display = '';
    }
}

function startNewChat() {
    // Get patient ID if available (for new chat, will be set after form submission)
    const newId = generateSixDigitAlphanumeric().toString();
    const newChat = { id: newId, title: '', messages: [] };
    chats.unshift(newChat);
    activeChatId = newId;
    renderChatList();
    renderMessages();
    saveChat(newChat);
    showUserInfoFormIfNeeded();
}

userInfoForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Gather form data
    const patientId = document.getElementById('patient-id').value;
    const patientInfo = `\n  Patient_ID: ${patientId}\n\n  Age: ${document.getElementById('user-age').value}\n  Gender: ${document.getElementById('user-gender').value}\n\n  Mental Status Examination :\n    ${document.getElementById('mental-status').value}\n\n  Presenting Complaints (as described by the patient):\n    ${document.getElementById('presenting-complaints').value}\n\n  History: ${document.getElementById('history').value}\n\n  Known psychiatric diagnoses: ${document.getElementById('diagnoses').value}\n\n  Family History: ${document.getElementById('family-history').value}\n\n  Allergies: ${document.getElementById('allergies').value}\n\n  Current medications: ${document.getElementById('medications').value}\n\n  Key Observations during Consultation:\n    ${document.getElementById('observations').value}\n    `;

    // Set chat title to patient ID
    const chat = chats.find(c => c.id === activeChatId);
    if (chat) {
        chat.title = patientId || chat.id;
        chat.messages.push({ role: 'user-info', content: patientInfo });
        saveChat(chat);
        saveMessage({ chat_id: chat.id, role: 'user-info', content: patientInfo });
    }

    // Hide the form and show chat input area immediately
    userInfoForm.reset();
    userInfoForm.style.display = 'none';
    chatForm.style.display = '';

    // Show the submitted info as a user bubble
    chatMessages.innerHTML = '';
    const userBubble = document.createElement('div');
    userBubble.className = 'user-info-bubble';
    userBubble.textContent = patientInfo;
    chatMessages.appendChild(userBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Animation steps to cycle through
    const steps = [
        'Analyzing patient info',
        'Doing diagnosis',
        'Doing treatment analysis',
        'Doing medicine analysis',
        'Generating final report'
    ];
    let currentStep = 0;
    let stepDiv = null;
    let typingDiv = null;
    let dots = 0;
    let animationActive = true;

    function showNextStep() {
        if (stepDiv) stepDiv.remove();
        if (typingDiv) typingDiv.remove();
        stepDiv = document.createElement('div');
        stepDiv.className = 'message bot';
        stepDiv.textContent = steps[currentStep];
        chatMessages.appendChild(stepDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        typingDiv = createTypingAnimation();
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showNextStep();
    const stepInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        if (typingDiv) typingDiv.textContent = ' '.repeat(2) + '.'.repeat(dots);
    }, 400);
    const cycleInterval = setInterval(() => {
        currentStep = (currentStep + 1) % steps.length;
        showNextStep();
    }, 3500);

    // Find the current chat_id
    const chat_id = chat ? chat.id : null;

    // Call backend API in parallel
    let finalRecommendation = 'Sorry, something went wrong.';
    try {
        const response = await fetch('/api/process_patient', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_info: patientInfo, chat_id: chat_id })
        });
        const data = await response.json();
        finalRecommendation = data.final_recommendation;
    } catch (err) {
        finalRecommendation = 'Error: Could not get recommendation.';
    }
    // When backend responds, stop animation and show result
    animationActive = false;
    clearInterval(stepInterval);
    clearInterval(cycleInterval);
    if (stepDiv) stepDiv.remove();
    if (typingDiv) typingDiv.remove();

    // Show the final recommendation in chat (with markdown)
    const resultDiv = document.createElement('div');
    resultDiv.className = 'message bot';
    if (typeof marked !== 'undefined') {
        resultDiv.innerHTML = marked.parse(finalRecommendation);
    } else {
        resultDiv.textContent = finalRecommendation;
    }
    chatMessages.appendChild(resultDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Save the final recommendation in chat history
    if (chat) {
        chat.messages.push({ role: 'bot', content: finalRecommendation });
        saveMessage({ chat_id: chat.id, role: 'bot', content: finalRecommendation });
    }
});

chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;
    const chat = chats.find(c => c.id === activeChatId);
    if (!chat) return;
    chat.messages.push({ role: 'user', content: userMsg });
    saveMessage({ chat_id: chat.id, role: 'user', content: userMsg });
    renderMessages();
    chatInput.value = '';
    // Placeholder bot response
    setTimeout(() => {
        chat.messages.push({ role: 'bot', content: 'This is a placeholder response.' });
        saveMessage({ chat_id: chat.id, role: 'bot', content: 'This is a placeholder response.' });
        renderMessages();
    }, 600);
});

newChatBtn.addEventListener('click', startNewChat);

// Initial render: always load from backend
initializeChats();

// When switching chats, show/hide user info form as needed
function onChatSwitch() {
    renderChatList();
    renderMessages();
    showUserInfoFormIfNeeded();
}

// Update typing animation to show animated dots
function createTypingAnimation() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-animation';
    typingDiv.innerHTML = '<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
    return typingDiv;
}

// Theme toggle logic
const themeToggleBtn = document.getElementById('theme-toggle-btn');
function setTheme(dark) {
    if (dark) {
        document.body.classList.add('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '☀️ Light Mode';
    } else {
        document.body.classList.remove('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '🌙 Dark Mode';
    }
    localStorage.setItem('medicllm_theme', dark ? 'dark' : 'light');
}
if (themeToggleBtn) {
    themeToggleBtn.onclick = () => {
        setTheme(!document.body.classList.contains('dark-mode'));
    };
}
// On load, set theme from localStorage
setTheme(localStorage.getItem('medicllm_theme') === 'dark');
