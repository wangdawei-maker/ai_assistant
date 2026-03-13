# tools/time_tool.py
from datetime import datetime

class TimeTool:
    name = "get_time"
    description = "获取当前时间，不需要参数"
    
    @staticmethod
    def execute(args=None):
        now = datetime.now()
        return now.strftime("%Y年%m月%d日 %H:%M:%S")