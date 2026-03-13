# tools/calculator.py
import numexpr as ne

class CalculatorTool:
    name = "calculate"
    description = "数学计算，参数是表达式，例如 '2+3*4'"
    
    @staticmethod
    def execute(expression):
        try:
            result = ne.evaluate(expression).item()
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算失败: {e}"