# tools/weather.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WeatherTool:
    name = "weather"
    description = "查询天气，参数是城市名，例如 'Beijing' 或 'Shanghai'"

    @staticmethod
    def execute(city: str) -> str:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return "❌ 请先在 .env 中配置 WEATHER_API_KEY"

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",      # 摄氏度
            "lang": "zh_cn",        # 中文返回
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return f"❌ 天气接口错误: {resp.status_code}, {resp.text}"

            data = resp.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            name = data["name"]

            return f"{name}当前天气：{desc}，{temp}℃"
        except Exception as e:
            return f"❌ 请求天气失败: {e}"