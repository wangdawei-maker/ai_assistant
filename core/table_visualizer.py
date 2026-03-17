# core/table_visualizer.py - 表格可视化模块

import pandas as pd
import os
from datetime import datetime
import re


class TableVisualizer:
    """表格数据可视化器（返回前端可直接渲染的 ECharts 配置）"""
    
    def __init__(self, output_dir: str = "./static/charts"):
        # 目前不再生成图片文件，保留参数以兼容旧代码
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self, file_path):
        """加载数据文件（支持csv/excel）"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
    
    def detect_intent(self, query):
        """检测用户意图"""
        query = query.lower()
        
        if any(word in query for word in ['趋势', '变化', '走势', '增长', '下降']):
            return 'trend'
        elif any(word in query for word in ['比较', '对比', '哪个最高', '哪个最大', '排名']):
            return 'compare'
        elif any(word in query for word in ['占比', '比例', '份额', '分布']):
            return 'pie'
        elif any(word in query for word in ['统计', '汇总', '总共', '平均']):
            return 'stats'
        else:
            return 'unknown'
    
    def generate_chart(self, df, intent, query):
        """
        根据意图生成图表对应的 ECharts 配置。
        
        返回:
            (echarts_option: dict | None, description: str)
        """

        # 获取数值列和类别列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if not numeric_cols:
            return None, "没有找到数值列，无法生成图表"
        
        # 默认使用第一列作为x轴，第一列数值作为y轴
        x_col = categorical_cols[0] if categorical_cols else 'index'
        y_col = numeric_cols[0]

        # 通用的深色主题配置片段
        def base_cartesian(title_text: str):
            return {
                "backgroundColor": "transparent",
                "textStyle": {"color": "#e5e7eb"},
                "title": {
                    "text": title_text,
                    "left": "center",
                    "textStyle": {"color": "#e5e7eb", "fontSize": 14},
                },
                "grid": {"left": "10%", "right": "6%", "bottom": "16%", "top": "18%"},
                "tooltip": {
                    "trigger": "axis",
                    "backgroundColor": "rgba(15,23,42,0.9)",
                    "borderColor": "rgba(148,163,184,0.6)",
                    "textStyle": {"color": "#e5e7eb"},
                },
                "xAxis": {
                    "type": "category",
                    "data": df[x_col].tolist(),
                    "axisLine": {"lineStyle": {"color": "#64748b"}},
                    "axisLabel": {"color": "#cbd5f5",},
                },
                "yAxis": {
                    "type": "value",
                    "axisLine": {"lineStyle": {"color": "#64748b"}},
                    "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.25)"}},
                    "axisLabel": {"color": "#cbd5f5","formatter": "{value}"},
                },
            }

        if intent == 'trend':
            # 折线图 ECharts 配置（深色主题）
            option = base_cartesian(f"{y_col}趋势图")
            option["series"] = [
                {
                    "name": y_col,
                    "type": "line",
                    "smooth": True,
                    "symbol": "circle",
                    "symbolSize": 6,
                    "lineStyle": {"width": 3, "color": "#38bdf8"},
                    "areaStyle": {"color": "rgba(56,189,248,0.18)"},
                    "data": df[y_col].tolist(),
                }
            ]
            desc = f"展示了 {y_col} 随 {x_col} 的变化趋势"
            return option, desc
            
        elif intent == 'compare':
            # 柱状图 ECharts 配置（深色主题）
            option = base_cartesian(f"{y_col}对比图")
            option["series"] = [
                {
                    "name": y_col,
                    "type": "bar",
                    "data": df[y_col].tolist(),
                    "itemStyle": {
                        "color": "#4ade80",
                        "borderRadius": [4, 4, 0, 0],
                    },
                }
            ]
            max_val_cat = df.loc[df[y_col].idxmax(), x_col]
            desc = f"各 {x_col} 的 {y_col} 对比，其中 {max_val_cat} 最高"
            return option, desc
            
        elif intent == 'pie':
            # 饼图 ECharts 配置（深色主题）
            data = [
                {"name": cat, "value": float(val)}
                for cat, val in zip(df[x_col], df[y_col])
            ]
            option = {
                "backgroundColor": "transparent",
                "textStyle": {"color": "#e5e7eb"},
                "title": {
                    "text": f"{y_col}占比分布",
                    "left": "center",
                    "textStyle": {"color": "#e5e7eb", "fontSize": 14},
                },
                "tooltip": {
                    "trigger": "item",
                    "backgroundColor": "rgba(15,23,42,0.9)",
                    "borderColor": "rgba(148,163,184,0.6)",
                    "textStyle": {"color": "#e5e7eb"},
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left",
                    "textStyle": {"color": "#e5e7eb"},
                },
                "series": [
                    {
                        "name": y_col,
                        "type": "pie",
                        "radius": "55%",
                        "center": ["60%", "55%"],
                        "avoidLabelOverlap": True,
                        "label": {
                         "color": "#e5e7eb",
                          "formatter": "{b}: {d}%",      # 显示 名称: 百分比
                        },
                        "labelLine": {
                          "length": 10,
                          "length2": 8,
                          "smooth": True,
                        },
                        "data": data,
                    }
                ],
            }
            desc = f"展示了各 {x_col} 的 {y_col} 占比"
            return option, desc
            
        elif intent == 'stats':
            # 统计信息（不生成图表，仅返回文字）
            stats = {
                '总数': df[y_col].sum(),
                '平均': df[y_col].mean(),
                '最高': df[y_col].max(),
                '最低': df[y_col].min(),
                '中位数': df[y_col].median()
            }
            
            desc = f"{y_col}统计："
            for k, v in stats.items():
                desc += f"\n  {k}: {v:.2f}"
            return None, desc
        
        else:
            return None, "无法识别您的意图，请尝试使用'趋势'、'比较'、'占比'等关键词"
    
    def answer_with_chart(self, file_path, query):
        """主入口：根据问题返回图表或统计"""
        try:
            # 1. 加载数据
            df = self.load_data(file_path)
            
            # 2. 检测意图
            intent = self.detect_intent(query)
            
            # 3. 生成图表（ECharts 配置或纯文字）
            echarts_option, description = self.generate_chart(df, intent, query)
            
            return {
                'success': True,
                'intent': intent,
                'description': description,
            'chart_path': None,  # 为兼容保留字段，但不再生成图片
            'echarts_option': echarts_option,
            'data_shape': df.shape
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 测试代码
if __name__ == "__main__":
    visualizer = TableVisualizer()
    
    # 创建测试数据
    test_file = "test_sales.csv"
    if not os.path.exists(test_file):
        data = {
            '月份': ['1月', '2月', '3月', '4月', '5月', '6月'],
            '销售额': [12000, 15000, 18000, 16000, 21000, 19000],
            '利润': [3000, 4000, 5000, 4500, 6000, 5500]
        }
        pd.DataFrame(data).to_csv(test_file, index=False)
    
    # 测试不同查询
    test_queries = [
        "画一下销售额趋势",
        "比较每个月的销售额",
        "销售额占比",
        "统计销售额数据"
    ]
    
    for q in test_queries:
        print(f"\n📝 查询: {q}")
        result = visualizer.answer_with_chart(test_file, q)
        
        if result['success']:
            print(f"意图: {result['intent']}")
            print(f"说明: {result['description']}")
            if result['chart_path']:
                print(f"图表: {result['chart_path']}")
        else:
            print(f"❌ 错误: {result['error']}")