# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv

# 导入核心模块
from core.llm import DeepSeekLLM
from core.rag import RAGSystem
from core.agent import Agent

load_dotenv()

app = FastAPI(title="AI智能助手")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 初始化核心服务
llm = DeepSeekLLM()
rag = RAGSystem()
agent = Agent(llm=llm)

# 对话历史
conversations = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return JSONResponse({"response": "请输入消息"}, status_code=400)
        
        # 保存用户消息
        conversations.append({"role": "user", "content": user_message})
        
        # 智能路由：根据消息内容选择处理方式
        response, tool_used = route_message(user_message)
        
        # 保存AI回复
        conversations.append({"role": "assistant", "content": response})
        
        return JSONResponse({
            "response": response,
            "tool_used": tool_used
        })
        
    except Exception as e:
        return JSONResponse({"response": f"服务器错误: {str(e)}"}, status_code=500)

def route_message(message):
    """智能路由：根据消息内容选择处理方式"""
    
    # 1. 工具关键词
    tool_keywords = ["时间", "几点", "计算", "等于", "天气", "气温"]
    if any(keyword in message for keyword in tool_keywords):
        result = agent.run(message)
        return result, "agent"
    
    # 2. 文档关键词
    doc_keywords = ["文档", "资料", "政策", "介绍", "说明", "规则"]
    if any(keyword in message for keyword in doc_keywords):
        result = rag.answer(message, llm)
        return result, "rag"
    
    # 3. 默认：普通聊天
    result = llm.chat_with_prompt(message)
    return result, None

@app.get("/api/history")
async def get_history():
    """获取对话历史"""
    return JSONResponse(conversations[-20:])  # 返回最近20条

@app.post("/api/reset")
async def reset_conversation():
    """重置对话"""
    global conversations
    conversations = []
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    print("🚀 启动AI智能助手...")
    print("🌐 访问地址: http://localhost:8000")
    print("📚 文档目录: ./docs")
    print("🔧 可用工具: 时间、计算、天气")
    uvicorn.run(app, host="0.0.0.0", port=8000)