import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_sales_data(csv_path, month_col="月份", sales_col="销售额"):
    """
    读取销售数据CSV，返回统计信息。

    参数：
        csv_path: CSV 文件路径
        month_col: 月份列名，默认 "月份"（传入不同列名可适配不同 CSV）
        sales_col: 销售额列名，默认 "销售额"

    返回：
        统计字典：总销售额、平均销售额、最高销售额月份
    """
    ## 先读取 CSV，再设置索引（顺序不能反）
    df = pd.read_csv(csv_path)
    df = df.set_index(month_col)
    ## 计算总销售额、平均、最高销售额所在月份（用参数列名，不写死）
    total_sales = df[sales_col].sum()
    average_sales = df[sales_col].mean()
    highest_sales_month = df[sales_col].idxmax()

    return {
        "总销售额": total_sales,
        "平均销售额": average_sales,
        "最高销售额月份": highest_sales_month,
    }

# 测试数据
def create_test_sales_data():
    """创建测试销售数据"""
    data = {
        '月份': ['1月', '2月', '3月', '4月', '5月', '6月'],
        '销售额': [12000, 15000, 18000, 16000, 21000, 19000]
    }
    df = pd.DataFrame(data)
    df.to_csv('test_sales.csv', index=False)
    print("✅ 测试数据已创建: test_sales.csv")
    return df

if __name__ == "__main__":
    create_test_sales_data()
    result = analyze_sales_data('test_sales.csv')
    print(f"统计结果: {result}")


def plot_sales_trend(csv_path, output_image='sales_trend.png', month_col="月份", sales_col="销售额"):
    """
    根据销售数据生成趋势图。

    参数：
        csv_path: CSV 文件路径
        output_image: 输出图片文件名
        month_col: 月份列名，默认 "月份"
        sales_col: 销售额列名，默认 "销售额"

    返回：
        图片路径
    """
    # 读取 CSV
    df = pd.read_csv(csv_path)
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    # 创建画布和坐标轴
    fig, ax = plt.subplots(figsize=(10, 6))
    # 画折线图（用参数列名，不写死）
    ax.plot(df[month_col], df[sales_col], color='blue', marker='o')
    ax.set_title(f'{sales_col}趋势图') #设置标题
    ax.set_xlabel(month_col) #设置x轴标签
    ax.set_ylabel(sales_col) #设置y轴标签
    #保存图片
    fig.savefig(output_image)
    #关闭画布   
    plt.close(fig)
    return output_image

if __name__ == "__main__":
    # 先确保有测试数据
    image_path = plot_sales_trend('test_sales.csv')
    print(f"✅ 图表已生成: {image_path}")

def query_to_chart(csv_path, user_query):
    """
    根据用户问题决定画什么图
    
    参数：
        csv_path: CSV文件路径
        user_query: 用户问题，如"画一下销售额趋势"、"哪个月份最高"
        
    返回：
        图表路径和文字说明
    """
    # 你的代码写在这里
    # 提示：
    # 1. 读取数据
    # 2. 分析用户问题中的关键词
    #    - "趋势"、"变化" → 折线图
    #    - "比较"、"哪个最高" → 柱状图
    #    - "占比" → 饼图
    # 3. 根据意图调用对应的画图函数
    # 4. 返回 (图片路径, 说明文字)
    
    #读取csv文件
    df = pd.read_csv(csv_path)
    # 分析用户问题中的关键词（每个词都要写 "xxx in user_query"）
    if '趋势' in user_query or '变化' in user_query:
        img_path = plot_line(df, '月份', '销售额', '销售额趋势图')
        return img_path, '销售额趋势图'
    elif '比较' in user_query or '哪个' in user_query or '最高' in user_query:
        img_path = plot_bar(df, '月份', '销售额', '销售额比较图')
        return img_path, '销售额比较图'
    elif '占比' in user_query:
        img_path = plot_pie(df, '月份', '销售额', '销售额占比图')
        return img_path, '销售额占比图'
    else:
        return None, '无法理解用户问题'

def plot_bar(data, x_col, y_col, title):
    """画柱状图"""
    plt.figure(figsize=(10, 6))
    sns.barplot(x=data[x_col], y=data[y_col])
    plt.title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    img_path = f'bar_chart_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(img_path)
    plt.close()
    return img_path

def plot_line(data, x_col, y_col, title):
    """画折线图"""
    plt.figure(figsize=(10, 6))
    plt.plot(data[x_col], data[y_col], marker='o')
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    img_path = f'line_chart_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(img_path)
    plt.close()
    return img_path

def plot_pie(data, x_col, y_col, title):
    """画饼图"""
    plt.figure(figsize=(10, 6))
    plt.pie(data[y_col], labels=data[x_col], autopct='%1.1f%%')
    plt.title(title)
    plt.tight_layout()
    img_path = f'pie_chart_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(img_path)
    plt.close()
    return img_path
if __name__ == "__main__":
    # 测试不同查询
    queries = [
        "画一下销售额趋势",
        "比较每个月的销售额",
        "哪个月销售额最高",
        "销售额占比",
    ]
    
    for q in queries:
        img, desc = query_to_chart('test_sales.csv', q)
        print(f"查询: {q}")
        print(f"说明: {desc}")
        print(f"图片: {img}")
        print("-" * 40)