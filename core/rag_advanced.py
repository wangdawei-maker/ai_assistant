import os
import jieba
from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import CrossEncoder
import re
# 在 AdvancedRAG 类里添加改写功能

from core.query_rewriter import QueryRewriter
from core.multimodal_loader import MultiModalLoader
class AdvancedRAG:
    """高级RAG系统:混合检索+重排序"""
    
    def __init__(self, docs_path="./docs", db_path="./data/faiss_index"):
        self.docs_path = docs_path
        self.db_path = db_path
        self.chunks=[] #保存所有文本块
        self.bm25=None #BM25检索器
        self.vectorstore=None #向量检索器
        # 初始化查询改写器（需要传入llm）
        self.rewriter = None  # 外部设置
        #初始化embedding模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        #初始化重排序模型(cross-encoder)
        print("加载重排序模型...")
        self.rerank_model=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2',max_length=512)
        
        self._init_chunks()
        self._init_vectorstore()
        self._init_bm25()
        
    def _init_chunks(self):
        """加载并切分文档（支持多模态）"""
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            print(f"📁 创建文档目录: {self.docs_path}")
            return
        
        # 使用多模态加载器，支持 txt / 图片 / PDF / CSV / Excel 等
        loader = MultiModalLoader()
        documents = loader.load_folder(self.docs_path)

        if not documents:
            print("没有找到可用文档")
            return
        
        #文档切分
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=150,
            chunk_overlap=30,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        self.chunks = splitter.split_documents(documents)
        self.chunk_texts = [doc.page_content for doc in self.chunks]
        print(f"✅ 切分文档，共 {len(self.chunks)} 个块")
        
    def _init_vectorstore(self):
        """初始化向量数据库"""
        if not self.chunks:
            return
        
        if os.path.exists(f"{self.db_path}.faiss"):
            #加载已有索引
            self.vectorstore = FAISS.load_local(self.db_path,self.embeddings,allow_dangerous_deserialization=True)
            print(f"✅ 加载已有向量索引: {self.db_path}")
        else:
            #创建新索引
            self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)
            self.vectorstore.save_local(self.db_path)
            print(f"创建向量索引，共 {len(self.chunks)} 个块")
            
    def _init_bm25(self):
        """初始化BM25检索器"""
        if not self.chunks:
            return
        
        #中文分词
        tokenized_chunks=[]
        for chunk in self.chunk_texts:
            #用jieba分词
            tokens = list(jieba.cut_for_search(chunk))
            tokenized_chunks.append(tokens)
        
        self.bm25=BM25Okapi(tokenized_chunks)
        print("✅ 初始化BM25检索器")
        
    def vector_search(self,query:str,k:int=10)->List[Dict]:
        """向量检索"""
        if not self.vectorstore:
            return []
        
        #向量检索返回更多结果，留给重排序筛选
        docs=self.vectorstore.similarity_search_with_score(query,k=k)
        
        results=[]
        for doc,score in docs:
            results.append({
                'text':doc.page_content,
                'score':score,
                'method':'vector'
            })
        return results
    
    def bm25_search(self,query:str,k:int=10)->List[Dict]:
        """BM25检索"""
        if not self.bm25:
            return []
        
        # 对查询也做分词
        tokenized_query=list(jieba.cut_for_search(query))
        scores=self.bm25.get_scores(tokenized_query)
        
        #获取top-k
        top_indices=np.argsort(scores)[-k:][::-1]
        
        results=[]
        for idx in top_indices:
            if scores[idx]>0: #只保留相关性高的结果
                results.append({
                    'text':self.chunk_texts[idx],
                    'socre':float(scores[idx]),
                    'method':'bm25'
                })
        return results
    
    def hybrid_search(self,query:str,vector_k:int=10,bm25_k:int=10)->List[Dict]:
        """混合检索:向量+BM25"""
        print(f"混合检索: {query}")
        
        #并行执行两种检索
        vector_results=self.vector_search(query,k=vector_k)
        bm25_results=self.bm25_search(query,k=bm25_k)
        
        print(f"向量检索结果: {len(vector_results)}")
        print(f"BM25检索结果: {len(bm25_results)}")
        
        #RRF融合
        all_results={}
        
        #处理向量检索结果
        for i,r in enumerate(vector_results):
            text=r['text']
            # RRF分数=1/(rank+60)
            score=1.0/(i+60)
            if text in all_results:
                all_results[text]['score']+=score
                all_results[text]['methods'].append('vector')
            else:
                all_results[text]={
                    'text':text,
                    'score':score,
                    'methods':['vector']
                }
        
        #处理BM25检索结果
        for i,r in enumerate(bm25_results):
            text=r['text']
            score=1.0/(i+60)
            if text in all_results:
                all_results[text]['score']+=score
                all_results[text]['methods'].append('bm25')
            else:
                all_results[text]={
                    'text':text,
                    'score':score,
                    'methods':['bm25']
                }
        
        #按融合分数排序
        hybrid_results=list(all_results.values())
        hybrid_results.sort(key=lambda x:x['score'],reverse=True)
        
        return hybrid_results[:10] #返回top10给重排序
    
    def rerank(self,query:str,results:List[Dict],top_k:int=3)->List[Dict]:
        """用cross-encoder重排序"""
        if not results:
            return []
        print(f"重排序:处理{len(results)}个结果")
        
        #准备输入对
        pairs=[[query,r['text']] for r in results]
        
        #计算相关性分数
        scores = self.rerank_model.predict(pairs)
        
        #合并分数
        for i,r in enumerate(results):
            r['rerank_score']=float(scores[i])
        
        #按重排分数重新排序
        reranked = sorted(results,key=lambda x:x['rerank_score'],reverse=True)
        
        return reranked[:top_k] #返回top-k结果
    
    def search(self,query:str,top_k:int=10)->List[Dict]:
        """高级检索:混合检索+重排序"""
        # 1.混合检索获取候选集
        hybrid_results=self.hybrid_search(query)
        if not hybrid_results:
            return []
        
        # 2.重排序
        final_results=self.rerank(query,hybrid_results,top_k=top_k)
        
        return final_results
    
    def answer(self,query:str,llm)->str:
        """RAG问答"""
        #1.检索相关文档
        results= self.search(query)
        if not results:
            return "没有找到相关文档"
        
        #2.构建上下文
        context="\n\n".join([f"[相关度:{r['rerank_score']:.2f}]{r['text']}" for r in results])
        
        #3.构建提示词
        prompt = f"""请基于以下资料回答问题。

资料（按相关度排序）：
{context}

问题：{query}

要求：
1. 如果资料中有相关信息，请基于资料回答
2. 如果资料中没有，请说"资料中未提及"
3. 回答要简洁准确

回答："""
        #4.调用LLM回答
        
        response = llm.chat_with_prompt(prompt)
        
        #5.附上来源信息
        sources=[f"来源{i+1}" for i in range(len(results))]
        return f"{response}\n\n参考：{', '.join(sources)}"

    def debug_search(self,query:str):
        """调试检索过程"""
        print("\n" + "="*60)
        print(f"🔍 查询: '{query}'")
        print("="*60)
        
        #1.混合检索
        hybrid_results=self.hybrid_search(query)
        print(f"混合检索结果: (前5条):")
        for i,r in enumerate(hybrid_results[:5]):
            methods="/".join(r['methods'])
            print(f"\n  [{i+1}] 融合分:{r['score']:.2f} [{methods}]")
            print(f"      内容: {r['text'][:100]}...")
        # 2. 重排序
        final_results = self.rerank(query, hybrid_results, top_k=3)
        print(f"\n🎯 重排序最终结果:")
        for i, r in enumerate(final_results):
            print(f"\n  [{i+1}] 重排序分:{r['rerank_score']:.2f}")
            print(f"      内容: {r['text']}")
        
        return final_results
    def set_llm(self, llm):
        """设置LLM实例（用于查询改写）"""
        from core.query_rewriter import QueryRewriter
        self.rewriter = QueryRewriter(llm)
    
    def search_with_rewrite(self, query: str, top_k: int = 3, use_rewrite: bool = True) -> List[Dict]:
        """带查询改写的检索"""
        
        if not use_rewrite or not self.rewriter:
            # 不改写，直接用原问题
            return self.search(query, top_k)
        
        # 1. 改写查询
        rewritten = self.rewriter.rewrite(query)
        print(f"原始问题: {query}")
        print(f"改写后: {rewritten}")
        
        # 2. 用改写后的查询检索
        results = self.search(rewritten, top_k=top_k)
        
        return results
    
    def multi_query_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """多版本查询检索（每个版本检索，然后融合结果）"""
        if not self.rewriter:
            return self.search(query, top_k)
        
        # 1. 生成多个查询版本
        versions = self.rewriter.multi_rewrite(query, n=3)
        print(f"查询版本: {versions}")
        
        # 2. 每个版本分别检索
        all_results = []
        for v in versions:
            results = self.hybrid_search(v)
            all_results.extend(results)
        
        # 3. 去重（按文本内容）
        unique_results = {}
        for r in all_results:
            text = r['text']
            if text not in unique_results:
                unique_results[text] = r
        
        # 4. 重排序
        final_results = self.rerank(query, list(unique_results.values()), top_k=top_k)
        
        return final_results
    
    def answer_with_rewrite(self, query: str, llm) -> str:
        """带查询改写的RAG问答"""
        # 1. 检索（使用改写）
        results = self.multi_query_search(query)
        
        if not results:
            return "知识库中没有找到相关信息。"
        
        # 2. 构建上下文
        context = "\n\n".join([r['text'] for r in results])
        
        # 3. 构建提示词
        prompt = f"""请基于以下资料回答问题。

资料：
{context}

问题：{query}

要求：
1. 如果资料中有相关信息，请基于资料回答
2. 如果资料中没有，请说"资料中未提及"
3. 回答要简洁准确

回答："""
        
        # 4. 调用LLM
        response = llm.chat_with_prompt(prompt)
        
        # 5. 附上引用来源
        sources = [f"来源{i+1}" for i in range(len(results))]
        
        return f"{response}\n\n📚 参考: {', '.join(sources)}"
#测试代码    
if __name__ == "__main__":
    print("测试高级RAG系统...")
    
    # 初始化
    rag = AdvancedRAG()
    
    # 测试查询
    test_queries = [
        "员工有什么福利？",
        "远程办公怎么申请？",
        "晋升需要什么条件？",
        "产品多少钱？",
        "春节发什么？"
    ]
    
    for q in test_queries:
        rag.debug_search(q)
        print("\n" + "-"*60)
        input("按回车继续...")