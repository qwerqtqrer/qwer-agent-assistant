"""YOLO 目标检测：模型缓存 + 结构化结果输出。"""

import os
from pathlib import Path

import cv2

from app.core.logging import get_logger

logger = get_logger("yolo_info")
_model_cache = {}

_YOLO_CONFIG_DIR = str(Path(__file__).resolve().parent / "data" / "ultralytics")


def _ensure_ultralytics_config_dir() -> None:
    """把 Ultralytics 配置目录固定到项目 data 目录，避免读取用户目录失败。"""
    if os.environ.get("YOLO_CONFIG_DIR"):
        return
    os.environ["YOLO_CONFIG_DIR"] = _YOLO_CONFIG_DIR
    Path(_YOLO_CONFIG_DIR).mkdir(parents=True, exist_ok=True)


def get_yolo_info(model_path, img_path):
    _ensure_ultralytics_config_dir()
    from ultralytics import YOLO

    if model_path not in _model_cache:
        _model_cache[model_path] = YOLO(model_path)
    model = _model_cache[model_path]

    results = model([img_path])
    info_list = []

    for res in results:
        origin_img = res.orig_img
        img_h, img_w, img_c = origin_img.shape
        logger.info("图片尺寸：宽%s 高%s 通道数%s", img_w, img_h, img_c)

        boxes = res.boxes
        if boxes is not None:
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy().astype(int)
            cls_names = res.names

            info_list.append("yolo检测目标信息")
            for i, box in enumerate(xyxy):
                x1, y1, x2, y2 = box
                conf = confs[i]
                cid = cls_ids[i]
                cname = cls_names[cid]
                info_list.append(
                    f"目标{i + 1}：类别={cname}，置信度={conf:.2f}，"
                    f"框坐标[x1:{x1:.0f},y1:{y1:.0f},x2:{x2:.0f},y2:{y2:.0f}]"
                )
    return "。".join(info_list)
