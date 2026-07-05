document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const imageUrlInput = document.getElementById('image-url-input');
    const sendBtn = document.getElementById('send-btn');

    // Create a unique user ID for this session or load existing
    let userId = sessionStorage.getItem('greenbin_userId');
    if (!userId) {
        userId = "user_" + Math.random().toString(36).substring(7);
        sessionStorage.setItem('greenbin_userId', userId);
    }

    // Restore chat history if it exists
    const savedChat = sessionStorage.getItem('greenbin_chat');
    if (savedChat) {
        chatBox.innerHTML = savedChat;
        if (typeof feather !== 'undefined') feather.replace();
        setTimeout(scrollToBottom, 100);
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addMessage(text, isUser = false, imageUrl = null, isFlagged = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'user-message' : 'ai-message'} ${isFlagged ? 'flagged' : ''}`;
        
        let contentHtml = '';
        if (imageUrl) {
            contentHtml += `<img src="${imageUrl}" class="msg-image" alt="Uploaded waste" onerror="this.style.display='none'"/>`;
        }
        
        // Escape HTML to prevent XSS
        const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
        contentHtml += `<p>${escapedText}</p>`;

        const avatarIcon = isUser ? 'user' : 'cpu';
        const avatarClass = isUser ? 'user-avatar' : 'ai-avatar';

        msgDiv.innerHTML = `
            <div class="avatar ${avatarClass}"><i data-feather="${avatarIcon}"></i></div>
            <div class="message-content">${contentHtml}</div>
        `;
        
        chatBox.appendChild(msgDiv);
        if (typeof feather !== 'undefined') feather.replace(); // Re-render feather icons
        scrollToBottom();
        
        // Save to session storage
        sessionStorage.setItem('greenbin_chat', chatBox.innerHTML);
    }

    function showTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ai-message typing-msg`;
        msgDiv.innerHTML = `
            <div class="avatar ai-avatar"><i data-feather="cpu"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatBox.appendChild(msgDiv);
        if (typeof feather !== 'undefined') feather.replace();
        scrollToBottom();
        return msgDiv;
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        const imageUrl = imageUrlInput.value.trim();
        
        if (!message && !imageUrl) return;

        // UI Updates
        addMessage(message || "Analyzing image...", true, imageUrl);
        chatInput.value = '';
        imageUrlInput.value = '';
        const typingIndicator = showTypingIndicator();

        try {
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    message: message || "describe",
                    image_url: imageUrl
                })
            });

            const data = await response.json();
            
            // Remove typing indicator
            typingIndicator.remove();

            if (response.ok) {
                const isFlagged = data.status === "flagged";
                addMessage(data.response, false, null, isFlagged);
            } else {
                addMessage("Oops! Something went wrong communicating with the server.", false, null, true);
            }
            
            // Re-save without typing indicator
            sessionStorage.setItem('greenbin_chat', chatBox.innerHTML);
        } catch (error) {
            console.error("Chat Error:", error);
            typingIndicator.remove();
            addMessage("Network error. Please try again later.", false, null, true);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
