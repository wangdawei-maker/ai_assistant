// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const messagesDiv = document.getElementById('messages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const toolStatus = document.getElementById('toolStatus');
    const tableFileInput = document.getElementById('tableFile');
    const uploadStatus = document.getElementById('uploadStatus');
    let currentTableFilePath = null;
    
    // 自动调整文本框高度
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // 上传表格文件
    tableFileInput.addEventListener('change', async function() {
        const file = this.files[0];
        if (!file) return;

        uploadStatus.textContent = '上传中...';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const resp = await fetch('/api/upload_table', {
                method: 'POST',
                body: formData
            });

            const data = await resp.json();
            if (data.file_path) {
                currentTableFilePath = data.file_path;
                uploadStatus.textContent = `已上传：${file.name}`;
            } else {
                uploadStatus.textContent = '上传失败';
            }
        } catch (e) {
            console.error(e);
            uploadStatus.textContent = '上传失败';
        }
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
            // 如果用户以 "表格:" 或 "表格：" 开头，走表格可视化接口
            const isTableQuery = message.startsWith('表格:') || message.startsWith('表格：');
            if (isTableQuery) {
                const queryText = message.replace(/^表格[:：]/, '').trim();
                const query = queryText || '画一下数据趋势';

                if (!currentTableFilePath) {
                    removeLoadingMessage(loadingId);
                    addMessage('请先在上方上传一个表格文件，再使用表格分析功能。', 'assistant');
                    toolStatus.textContent = '📊 尚未上传表格文件';
                    return;
                }

                const vizResp = await fetch('/api/table_viz', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_path: currentTableFilePath,
                        query
                    })
                });
                const vizData = await vizResp.json();

                removeLoadingMessage(loadingId);

                if (!vizData.success) {
                    addMessage(`表格分析失败：${vizData.error || '未知错误'}`, 'assistant');
                    toolStatus.textContent = '📊 表格可视化失败';
                    return;
                }

                // 构造包含 ECharts 容器的消息 HTML
                const chartId = `chart-${Date.now()}`;
                let html = vizData.description || '已完成表格分析。';
                if (vizData.echarts_option) {
                    html += `
                        <div class="chart-wrapper">
                            <div id="${chartId}" class="chart-echarts"></div>
                        </div>
                    `;
                }
                const msgEl = addMessage(html, 'assistant');

                // 使用 ECharts 在前端渲染图表
                if (vizData.echarts_option && window.echarts) {
                    const chartDom = msgEl.querySelector(`#${chartId}`);
                    if (chartDom) {
                        // 让包含图表的气泡更宽一点
                        const contentEl = msgEl.querySelector('.content');
                        if (contentEl) {
                            contentEl.classList.add('chart-content');
                        }

                        const chart = echarts.init(chartDom);
                        chart.setOption(vizData.echarts_option);
                    }
                }

                toolStatus.textContent = `📊 使用工具: table_viz (${vizData.intent || 'unknown'})`;
            } else {
                // 否则走原来的聊天/RAG 接口
                const ragMode = document.getElementById('ragMode').value; // "basic" | "advanced"
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: message, rag_mode: ragMode })
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
            }
            
        } catch (error) {
            removeLoadingMessage(loadingId);
            addMessage('出错了，请重试', 'assistant');
            console.error(error);
        }
    }
    
    // 添加消息（返回创建的消息 DOM，便于后续挂载图表等）
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <div class="content">${content}</div>
        `;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return messageDiv;
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