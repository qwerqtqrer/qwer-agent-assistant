"""翻译工具"""

from langchain.tools import tool


@tool
def translate_text(text: str, target_lang: str = "中文") -> str:
    """
    翻译文本到目标语言
    :param text: 待翻译的文本
    :param target_lang: 目标语言（如 中文、English、日本語 等）
    """
    from zhipuai import ZhipuAI

    client = ZhipuAI()
    prompt = f"请将以下文本翻译为{target_lang}，只返回翻译结果：\n\n{text}"
    resp = client.chat.completions.create(
        model="glm-5.2",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
