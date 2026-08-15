"""天气查询工具：高德地图 API + LLM 出行建议。"""

import json

import requests
from langchain.tools import tool

from app.core.config import config
from app.core.llm import build_llm
from app.core.logging import get_logger

logger = get_logger("app.tools.weather")


def _fallback_text(weather_data: dict) -> str:
    return (
        f"当前城市：{weather_data['location']}\n"
        f"当前时间：{weather_data['date']}\n"
        f"当前天气：{weather_data['weather']}\n"
        f"当前温度：{weather_data['temperature']}\n"
        f"湿度：{weather_data['humidity']}\n"
        "出行建议：请根据实时天气合理安排出行。"
    )


def _beautify_weather(input_data):
    """将结构化天气数据转为美观文字。"""
    if not config.llm_configured:
        return _fallback_text(input_data)

    instruction = "任务：查询指定城市的天气情况"
    example = (
        "示例：{'location': '长沙', 'date': '2026-07-14 15:01:46', 'weather': '晴', "
        "'temperature': '37°C', 'humidity': '55%'}\n"
        "输出：\n当前城市：湖南省长沙市\n当前时间：2026-07-14 15:01:46\n"
        "当前天气：晴天\n当前温度：37°C\n湿度：55%\n出行建议：不建议出行。如必要出行，注意防晒。"
    )
    output_format = (
        "按下面格式进行输出：\n当前城市：\n当前时间：\n当前天气：\n当前温度：\n湿度：\n出行建议："
    )
    prompt = f"{instruction}\n{example}\n{input_data}\n{output_format}"
    resp = build_llm().invoke(
        [
            ("system", "你是一个有用的AI助手。"),
            ("user", prompt),
        ]
    )
    return str(resp.content)


@tool
def get_weather(location: str) -> str:
    """获取指定城市的实时天气信息"""
    if not config.amap_api_key:
        return f"天气服务未配置（缺少 AMAP_API_KEY），暂时无法查询「{location}」的天气。"

    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={config.amap_api_key}&city={location}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = json.loads(resp.text)
        if data.get("status") != "1" or not data.get("lives"):
            return f"天气查询失败：{data.get('info', '未知错误')}"
        info = data["lives"][0]
        weather_data = {
            "location": location,
            "date": info["reporttime"],
            "weather": info["weather"],
            "temperature": f"{info['temperature']}°C",
            "humidity": f"{info['humidity']}%",
        }
        return _beautify_weather(weather_data)
    except Exception as exc:
        logger.exception("天气查询失败")
        return f"天气查询失败：{exc}"
