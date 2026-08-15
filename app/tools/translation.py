"""翻译工具。"""

from langchain.tools import tool

from app.core.config import config
from app.core.llm import build_llm


@tool
def translate_text(text: str, target_lang: str = "中文") -> str:
    """
    翻译文本到目标语言
    :param text: 待翻译的文本
    :param target_lang: 目标语言（如 中文、English、日本語 等）
    """
    if not text or not text.strip():
        return "错误：待翻译文本不能为空。"
    if not config.llm_configured:
        return f"演示模式未配置大模型，无法翻译。目标语言：{target_lang}。"

    prompt = f"请将以下文本翻译为{target_lang}，只返回翻译结果：\n\n{text}"
    resp = build_llm().invoke([("user", prompt)])
    return str(resp.content)
