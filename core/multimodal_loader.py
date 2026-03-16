# core/multimodal_loader.py - 多模态文档加载器

import os
from typing import List, Union
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
import pandas as pd
from PIL import Image
import pytesseract
from pypdf import PdfReader

class MultiModalLoader:
    """多模态文档加载器：支持txt、图片、PDF、Excel等"""
    
    def __init__(self, ocr_lang='chi_sim+eng'):
        """
        初始化
        
        参数：
            ocr_lang: OCR语言，中文用'chi_sim'，英文用'eng'
        """
        self.ocr_lang = ocr_lang
    
    def load(self, file_path: str) -> List[Document]:
        """根据文件类型自动选择加载方式"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt':
            return self._load_txt(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self._load_image(file_path)
        elif ext == '.pdf':
            return self._load_pdf(file_path)
        elif ext in ['.csv']:
            return self._load_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            return self._load_excel(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
    
    def _load_txt(self, file_path: str) -> List[Document]:
        """加载txt文件"""
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    
    def _load_image(self, file_path: str) -> List[Document]:
        """加载图片（OCR提取文字）"""
        try:
            # 打开图片
            image = Image.open(file_path)
            
            # OCR提取文字
            text = pytesseract.image_to_string(image, lang=self.ocr_lang)
            
            # 创建Document
            doc = Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "type": "image",
                    "ocr_lang": self.ocr_lang
                }
            )
            return [doc]
        except Exception as e:
            print(f"图片处理失败: {e}")
            return []
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """加载PDF"""
        documents = []
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():  # 只保留有内容的页
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "type": "pdf",
                            "page": i + 1,
                            "total_pages": len(reader.pages)
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            print(f"PDF处理失败: {e}")
        
        return documents
    
    def _load_csv(self, file_path: str) -> List[Document]:
        """加载CSV（每行一个文档）"""
        documents = []
        try:
            df = pd.read_csv(file_path)
            for idx, row in df.iterrows():
                # 把行转成文本描述
                row_text = "，".join([f"{col}:{val}" for col, val in row.items()])
                
                doc = Document(
                    page_content=row_text,
                    metadata={
                        "source": file_path,
                        "type": "csv",
                        "row": idx + 1,
                        "columns": list(df.columns)
                    }
                )
                documents.append(doc)
        except Exception as e:
            print(f"CSV处理失败: {e}")
        
        return documents
    
    def _load_excel(self, file_path: str) -> List[Document]:
        """加载Excel（每个sheet每个行一个文档）"""
        documents = []
        try:
            # 读取所有sheet
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                for idx, row in df.iterrows():
                    row_text = "，".join([f"{col}:{val}" for col, val in row.items()])
                    
                    doc = Document(
                        page_content=row_text,
                        metadata={
                            "source": file_path,
                            "type": "excel",
                            "sheet": sheet_name,
                            "row": idx + 1
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            print(f"Excel处理失败: {e}")
        
        return documents
    
    def load_folder(self, folder_path: str) -> List[Document]:
        """加载文件夹下所有支持的文件"""
        all_docs = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    docs = self.load(file_path)
                    all_docs.extend(docs)
                    print(f"✅ 已加载: {file}")
                except Exception as e:
                    print(f"❌ 加载失败 {file}: {e}")
        
        print(f"共加载 {len(all_docs)} 个文档")
        return all_docs


# 测试代码
if __name__ == "__main__":
    loader = MultiModalLoader()
    
    # 测试文件夹
    test_folder = "./test_docs"
    if os.path.exists(test_folder):
        docs = loader.load_folder(test_folder)
        for doc in docs[:5]:
            print(f"\n类型: {doc.metadata.get('type')}")
            print(f"内容预览: {doc.page_content[:100]}...")