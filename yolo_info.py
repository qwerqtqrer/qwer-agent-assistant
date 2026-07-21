from ultralytics import YOLO
import cv2


def get_yolo_info(model, img_path):
    # 加载模型
    model = YOLO(model)

    # 对图片列表进行批量推理
    results = model([img_path])

    # 获取信息列表
    info_list = []

    # 遍历推理结果，获取图片全部信息
    for res in results:
        # 1. 获取原图数组 (numpy格式，BGR通道，可直接cv2处理)
        origin_img = res.orig_img
        # 图片宽高通道
        img_h, img_w, img_c = origin_img.shape
        print(f"图片尺寸：宽{img_w} 高{img_h} 通道数{img_c}")

        # 2. 图片原始路径
        img_path = res.path
        print(f"图片文件路径：{img_path}")

        # 3. 检测框信息：坐标、置信度、类别ID、类别名称
        boxes = res.boxes
        if boxes is not None:
            # 框坐标 xyxy [x1,y1,x2,y2]
            xyxy = boxes.xyxy.cpu().numpy()
            # 归一化坐标 xywhn
            xywhn = boxes.xywhn.cpu().numpy()
            # 置信度
            confs = boxes.conf.cpu().numpy()
            # 类别id
            cls_ids = boxes.cls.cpu().numpy().astype(int)
            # 类别名称映射
            cls_names = res.names

            print("===== 检测目标信息 =====")
            info_list.append("yolo检测目标信息")
            for i, box in enumerate(xyxy):
                x1, y1, x2, y2 = box
                conf = confs[i]
                cid = cls_ids[i]
                cname = cls_names[cid]
                print(
                    f"目标{i + 1}：类别={cname}，置信度={conf:.2f}，框坐标[x1:{x1:.0f},y1:{y1:.0f},x2:{x2:.0f},y2:{y2:.0f}]")
                info_list.append(
                    f"目标{i + 1}：类别={cname}，置信度={conf:.2f}，框坐标[x1:{x1:.0f},y1:{y1:.0f},x2:{x2:.0f},y2:{y2:.0f}]")
    return "。".join(info_list)
