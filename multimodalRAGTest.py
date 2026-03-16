from PIL import Image
import pytesseract
import os
from pypdf import PdfReader
import pandas as pd
from langchain.schema import Document
pytesseract.pytesseract.tesseract_cmd = r"D:\tesseract\tesseract.exe"
def extract_text_from_image(image_path):
    """
    从图片中提取文字
    
    参数：
        image_path: 图片路径
        
    返回：
        提取出的文字
    """
    # 你的代码写在这里
    # 提示：
    # 1. 用 Image.open() 打开图片
    # 2. 用 pytesseract.image_to_string() 提取文字
    # 3. 返回提取的文字
    image= Image.open(image_path)
    text=pytesseract.image_to_string(image,lang="chi_sim+eng",config="--oem 3 --psm 6")
    return text

# 测试
if __name__ == "__main__":
    text = extract_text_from_image("docs/screenshot.png")
    print(f"提取的文字：{text}")
    


def extract_text_from_pdf(pdf_path):
    """
    从PDF文件中提取文字
    
    参数：
        pdf_path: PDF文件路径
        
    返回：
        所有页的文字内容
    """
    # 你的代码写在这里
    # 提示：
    # 1. 用 PdfReader() 打开PDF
    # 2. 遍历每一页
    # 3. 用 page.extract_text() 提取文字
    # 4. 拼接所有页的内容
    try:
        if not os.path.exists(pdf_path):
            return "PDF文件不存在"
        reader=PdfReader(pdf_path)
        text=""
        for page in reader.pages:
          text+=page.extract_text()
        return text
    except Exception as e:
        print(f"提取PDF内容失败: {e}")

# 测试
if __name__ == "__main__":
    text = extract_text_from_pdf("docs/testpdf.pdf")
    print(f"PDF内容：{text[:500]}...")

def csv_to_documents(csv_path):
    """
    把CSV文件的每一行转成Document对象
    
    参数：
        csv_path: CSV文件路径
        
    返回：
        Document对象列表
    """
    # 你的代码写在这里
    # 提示：
    # 1. 用 pd.read_csv() 读取CSV
    # 2. 遍历每一行
    # 3. 把行数据转成字符串（如："姓名：张三，年龄：25"）
    # 4. 创建 Document 对象，page_content=行文本，metadata={"source": csv_path, "row": i}
    # 5. 添加到列表
    try:
        if not os.path.exists(csv_path):
            return "CSV文件不存在"
        df=pd.read_csv(csv_path)
        documents=[]
        for index,row in df.iterrows():
            parts = [f"{col}：{row[col]}" for col in df.columns]  # 或者只挑你关心的列
            line="，".join(parts)
            documents.append(Document(page_content=line,metadata={"source": csv_path, "row": index}))
            print(f"index:{index} row:{row},line:{line}")
        return documents    
    except Exception as e:
        print(f"转换CSV为Document对象失败: {e}")

# 测试
if __name__ == "__main__":
    docs = csv_to_documents("docs/testcsv.csv")
    for doc in docs[:3]:
        print(f"文档：{doc.page_content}")