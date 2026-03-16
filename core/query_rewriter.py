# core/query_rewriter.py - 查询改写模块

class QueryRewriter:
    """查询改写：把口语问题转成适合检索的关键词"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def rewrite(self, query: str, style="concise") -> str:
        """
        改写查询
        
        style:
            - concise: 简洁关键词（默认，适合检索）
            - detailed: 详细描述（适合复杂查询）
            - expand: 扩展同义词
        """
        prompts = {
            "concise": f"""你是一个查询改写专家。请将用户的自然语言问题，改写成适合搜索引擎检索的关键词组合。

要求：
1. 提取核心关键词
2. 去除语气词和冗余
3. 用空格分隔关键词
4. 保持原意
5. 只返回改写后的内容，不要解释

用户问题：{query}
改写后：""",

            "detailed": f"""请将用户问题改写成更详细的检索查询，保留所有关键信息。

用户问题：{query}
改写后：""",

            "expand": f"""请将用户问题改写成包含同义词的检索查询，用空格分隔。

例如：
问题：年假几天
改写：年假 带薪年假 休假天数 假期

用户问题：{query}
改写："""
        }
        
        prompt = prompts.get(style, prompts["concise"])
        rewritten = self.llm.chat_with_prompt(prompt)
        
        # 清理结果（去除可能的引号、换行等）
        rewritten = rewritten.strip().strip('"').strip("'")
        
        return rewritten
    
    def multi_rewrite(self, query: str, n: int = 3) -> list:
        """生成多个改写版本，用于多路检索"""
        prompt = f"""请为用户问题生成{n}个不同的检索查询版本。

要求：
1. 版本1：提取核心关键词
2. 版本2：扩展同义词
3. 版本3：保持原意但更正式
4. 每个版本一行，不要编号

用户问题：{query}
改写版本："""
        
        response = self.llm.chat_with_prompt(prompt)
        versions = [v.strip() for v in response.split('\n') if v.strip()]
        
        # 确保返回n个版本，不够的用原问题补
        while len(versions) < n:
            versions.append(query)
        
        return versions[:n]


# 测试代码
if __name__ == "__main__":
    # 这里需要你的llm，先简单测试
    from core.llm import DeepSeekLLM
    llm = DeepSeekLLM()
    rewriter = QueryRewriter(llm)
    
    test_queries = [
        "去年的营收是多少？",
        "你们有什么套餐？",
        "怎么请假？",
        "工资什么时候发？"
    ]
    
    for q in test_queries:
        print(f"\n原始问题: {q}")
        rewritten = rewriter.rewrite(q)
        print(f"改写后: {rewritten}")
        
        # 测试多版本
        versions = rewriter.multi_rewrite(q, n=3)
        print(f"多版本: {versions}")