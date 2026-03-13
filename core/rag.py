# core/rag.py
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

class RAGSystem:
    """RAG知识库系统"""
    
    def __init__(self, docs_path="./docs", db_path="./data/vector_db"):
        self.docs_path = docs_path
        self.db_path = db_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """初始化向量数据库"""
        if os.path.exists(self.db_path):
            # 加载已有数据库
            self.vectorstore = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )
            print(f"✅ 加载已有向量数据库: {self.db_path}")
        else:
            # 创建新数据库
            self._build_vectorstore()
    
    def _build_vectorstore(self):
        """从文档构建向量数据库"""
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            print(f"📁 创建文档目录: {self.docs_path}")
            return
        
        documents = []
        for file in os.listdir(self.docs_path):
            if file.endswith('.txt'):
                loader = TextLoader(f"{self.docs_path}/{file}", encoding='utf-8')
                documents.extend(loader.load())
                print(f"📄 加载文档: {file}")
        
        if not documents:
            print("⚠️ 没有找到文档")
            return
        
        # 文档切分
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=50
        )
        chunks = splitter.split_documents(documents)
        
        # 创建向量数据库
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print(f"✅ 创建向量数据库，共 {len(chunks)} 个块")
    
    def search(self, query, k=3):
        """检索相关文档"""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def answer(self, question, llm):
        """RAG问答"""
        docs = self.search(question)
        if not docs:
            return "📚 知识库中没有相关文档"
        
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"""请基于以下资料回答问题：

资料：
{context}

问题：{question}

回答："""
        
        return llm.chat_with_prompt(prompt)