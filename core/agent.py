# core/agent.py
import importlib
import os

class Agent:
    """Agent智能体系统"""
    
    def __init__(self, llm, tools_module="tools"):
        self.llm = llm
        self.tools = self._load_tools(tools_module)
        self.messages = []
    
    def _load_tools(self, module_name):
        """动态加载工具"""
        tools = []
        try:
            # 获取tools目录下所有py文件
            tools_dir = module_name.replace('.', '/')
            if not os.path.exists(tools_dir):
                return tools
            
            for file in os.listdir(tools_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    module = importlib.import_module(f"{module_name}.{file[:-3]}")
                    # 查找工具类
                    for attr in dir(module):
                        tool_class = getattr(module, attr)
                        if (hasattr(tool_class, 'name') and 
                            hasattr(tool_class, 'description') and
                            hasattr(tool_class, 'execute')):
                            tools.append({
                                "name": tool_class.name,
                                "description": tool_class.description,
                                "function": tool_class.execute
                            })
        except Exception as e:
            print(f"加载工具失败: {e}")
        
        return tools
    
    def _create_prompt(self, user_input):
        """创建ReAct提示词"""
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}" for t in self.tools
        ])
        
        return f"""你是一个能使用工具的AI助手。可用工具：

{tools_desc}

请按照以下格式：
思考：我需要用什么工具？
行动：工具名称(参数)
观察：工具返回的结果
...（可重复）
思考：我现在可以回答了
最终答案：给用户的最终回答

注意：
1. 每次只能执行一个行动
2. 没有合适的工具就直接回答

问题：{user_input}"""
    
    def _parse_action(self, response):
        """解析AI响应中的行动"""
        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith('行动：') or line.startswith('行动:'):
                action_text = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                action_text = action_text.strip()
                
                if '(' in action_text and ')' in action_text:
                    tool_name = action_text.split('(')[0].strip()
                    args_str = action_text.split('(')[1].split(')')[0].strip()
                    args = args_str if args_str else None
                    return tool_name, args
        return None, None
    
    def _execute_tool(self, tool_name, args):
        """执行工具"""
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    if args is None:
                        result = tool['function']()
                    else:
                        result = tool['function'](args)
                    return f"观察：{result}"
                except Exception as e:
                    return f"观察：工具执行失败 - {e}"
        return f"观察：未知工具 '{tool_name}'"
    
    def _extract_answer(self, response):
        """提取最终答案"""
        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith('最终答案：') or line.startswith('最终答案:'):
                return line.split('：')[-1] if '：' in line else line.split(':')[-1]
        return response
    
    def run(self, user_input, max_steps=5):
        """运行Agent"""
        print(f"\n🔧 Agent处理: {user_input}")
        
        # 初始化对话
        prompt = self._create_prompt(user_input)
        self.messages = [{"role": "user", "content": prompt}]
        
        for step in range(max_steps):
            print(f"  Step {step+1}: 调用LLM...")
            response = self.llm.chat(self.messages)
            
            # 检查是否是最终答案
            if "最终答案：" in response or "最终答案:" in response:
                answer = self._extract_answer(response)
                print(f"  ✅ Agent完成")
                return answer
            
            # 解析工具调用
            tool_name, args = self._parse_action(response)
            if tool_name:
                print(f"  🔧 调用工具: {tool_name}({args})")
                observation = self._execute_tool(tool_name, args)
                print(f"  📊 {observation}")
                
                # 把AI的思考和观察加入对话
                self.messages.append({"role": "assistant", "content": response})
                self.messages.append({"role": "user", "content": observation})
            else:
                # 没有工具调用，可能是直接回答
                return response
        
        return "⚠️ 处理超时，请重试"