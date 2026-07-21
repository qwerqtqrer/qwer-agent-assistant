"""图片处理工具：base64 编码、拍照、保存、识别"""

import base64
import os
import tempfile
import uuid
from io import BytesIO

import cv2
import gradio as gr
from PIL import Image

from app.config import config


def image_to_base64(image: Image.Image):
    buffer = BytesIO()
    image.save(buffer, format="png")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pre_recognize_image(image, prompt="详细描述图片中的所有信息"):
    """调用 GLM-4V 识别图片内容"""
    from zhipuai import ZhipuAI

    if image is None:
        return ""
    client = ZhipuAI()
    img_64 = image_to_base64(image)
    resp = client.chat.completions.create(
        model="glm-4v",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_64}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content


def save_pil_image(pil_img: Image.Image):
    """将 PIL 图片保存到缓存目录，返回路径信息"""
    unique_name = f"{uuid.uuid4()}.png"
    save_dir = config.UPLOAD_CACHE_DIR
    os.makedirs(save_dir, exist_ok=True)
    full_save_path = os.path.join(save_dir, unique_name)
    pil_img.save(full_save_path)
    file_name = os.path.basename(full_save_path)
    name_no_ext, ext = os.path.splitext(file_name)
    return {
        "full_path": full_save_path,
        "file_name": file_name,
        "name_without_ext": name_no_ext,
        "suffix": ext,
    }


def take_photo():
    """调用摄像头拍照，返回 PIL Image"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise gr.Error("无法正常打开摄像头！")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise gr.Error("拍照失败，未能获取到摄像头画面！")
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def build_chat_image_content(image: Image.Image):
    """将 PIL 图片保存为临时文件，返回 Gradio 聊天组件所需的 content_list 片段"""
    if image is None:
        return []
    tmp = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
    image.save(tmp, format="PNG")
    path = tmp.name
    tmp.close()
    return [{"type": "image", "path": path}]
