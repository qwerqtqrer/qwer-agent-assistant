"""天气查询工具"""

import json

import requests
from langchain.tools import tool

from app.config import config


def _beautify_weather(input_data):
    """将结构化天气数据转为美观文字"""
    instruction = "任务：查询指定城市的天气情况"
    example = """
        示例：{'location': '长沙', 'date': '2026-07-14 15:01:46', 'weather': '晴', 'temperature': '37°C', 'humidity': '55%'}
        输出：
            当前城市：湖南省长沙市
            当前时间:2026-07-14 15:01:46
            当前天气：晴天
            当前温度:37°C
            湿度:55%
            出行建议：不建议出行。如必要出行，注意防晒。
        """
    output_format = """
        按下面格式进行输出：
            当前城市：
            当前时间：
            当前天气：
            当前温度：
            湿度：
            出行建议：
        """
    from zhipuai import ZhipuAI

    client = ZhipuAI()
    prompt = f"{instruction}{example}{input_data}{output_format}"
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是一个有用的AI助手。"},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


@tool
def get_weather(location: str) -> str:
    """获取指定城市的实时天气信息"""
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={config.AMAP_API_KEY}&city={location}"
    resp = requests.get(url)
    data = json.loads(resp.text)
    info = data["lives"][0]
    weather_data = {
        "location": location,
        "date": info["reporttime"],
        "weather": info["weather"],
        "temperature": f"{info['temperature']}°C",
        "humidity": f"{info['humidity']}%",
    }
    return _beautify_weather(weather_data)
