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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENWEATHERMAP_KEY = os.getenv("OPENWEATHERMAP_KEY")
app = FastAPI(title="AI智能助手")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 初始化核心服务
llm = DeepSeekLLM()
rag = RAGSystem()
# 高级 RAG（混合检索+重排序），失败时仅用基础 RAG
advanced_rag = None
try:
    from core.rag_advanced import AdvancedRAG
    advanced_rag = AdvancedRAG()
    print("✅ 高级RAG已加载（可切换文档模式）")
except Exception as e:
    print("⚠️ 高级RAG加载失败，仅使用基础RAG:", e)
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
        rag_mode = data.get("rag_mode", "basic")  # "basic" | "advanced"
        
        if not user_message:
            return JSONResponse({"response": "请输入消息"}, status_code=400)
        
        # 保存用户消息
        conversations.append({"role": "user", "content": user_message})
        
        # 智能路由：根据消息内容选择处理方式，文档类问题按 rag_mode 选 RAG
        response, tool_used = route_message(user_message, rag_mode=rag_mode)
        
        # 保存AI回复
        conversations.append({"role": "assistant", "content": response})
        
        return JSONResponse({
            "response": response,
            "tool_used": tool_used
        })
        
    except Exception as e:
        return JSONResponse({"response": f"服务器错误: {str(e)}"}, status_code=500)

def route_message(message, rag_mode="basic"):
    """智能路由：工具类走 Agent；选 RAG 模式时非工具问题都走 RAG，否则按关键词走 RAG 或普通聊天"""
    
    # 1. 工具关键词 → 始终走 Agent
    tool_keywords = ["时间", "几点", "计算", "等于", "天气", "气温"]
    if any(keyword in message for keyword in tool_keywords):
        result = agent.run(message)
        return result, "agent"
    
    # 2. 用户已选「高级 RAG」→ 用带改写的高级 RAG
    if rag_mode == "advanced":
        if advanced_rag is not None:
            result = advanced_rag.answer_with_rewrite(message, llm)
            return result, "rag(高级)"
        result = rag.answer(message, llm)
        return result, "rag(高级不可用，已用基础)"
    
    # 3. 用户已选「基础 RAG」→ 非工具问题一律走基础 RAG（无改写）
    if rag_mode == "basic":
        result = rag.answer(message, llm)
        return result, "rag(基础)"
    
    # 4. 兼容：未传 rag_mode 时按关键词决定是否用基础 RAG，否则普通聊天
    doc_keywords = ["文档", "资料", "政策", "介绍", "说明", "规则"]
    if any(keyword in message for keyword in doc_keywords):
        result = rag.answer(message, llm)
        return result, "rag(基础)"
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