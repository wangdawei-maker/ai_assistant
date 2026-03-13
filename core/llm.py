# core/llm.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DeepSeekLLM:
    """DeepSeek API封装"""
    
    def __init__(self, api_key=None, temperature=0.7):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        self.url = "https://api.deepseek.com/v1/chat/completions"
        self.temperature = temperature
    
    def chat(self, messages):
        """基础聊天方法"""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"❌ API错误: {response.status_code}"
        except Exception as e:
            return f"❌ 请求失败: {e}"
    
    def chat_with_prompt(self, prompt):
        """简化版：直接传字符串"""
        return self.chat([{"role": "user", "content": prompt}])