// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const messagesDiv = document.getElementById('messages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const toolStatus = document.getElementById('toolStatus');
    
    // 自动调整文本框高度
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // 发送消息
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // 添加用户消息
        addMessage(message, 'user');
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // 显示加载状态
        const loadingId = addLoadingMessage();
        
        try {
            // 调用后端API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            });
            
            const data = await response.json();
            
            // 移除加载消息
            removeLoadingMessage(loadingId);
            
            // 添加AI回复
            addMessage(data.response, 'assistant');
            
            // 如果有工具调用信息，显示
            if (data.tool_used) {
                toolStatus.textContent = `🔧 使用工具: ${data.tool_used}`;
            } else {
                toolStatus.textContent = '';
            }
            
        } catch (error) {
            removeLoadingMessage(loadingId);
            addMessage('出错了，请重试', 'assistant');
            console.error(error);
        }
    }
    
    // 添加消息
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <div class="content">${content}</div>
        `;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    // 添加加载消息
    function addLoadingMessage() {
        const id = 'loading-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.id = id;
        messageDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="content">思考中<span class="dots">...</span></div>
        `;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return id;
    }
    
    // 移除加载消息
    function removeLoadingMessage(id) {
        const loadingMsg = document.getElementById(id);
        if (loadingMsg) loadingMsg.remove();
    }
    
    // 回车发送
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    sendBtn.addEventListener('click', sendMessage);
});