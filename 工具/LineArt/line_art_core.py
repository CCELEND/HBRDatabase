# -*- coding: utf-8 -*-
"""图片 / 视频转线稿的公共算法。

只依赖 numpy + opencv，不依赖 Qt。
「图片转线稿工具 2.0」和「视频转线稿」都调用 :func:`to_line_art`，
保证两个工具的线稿效果完全一致。
"""
import cv2
import numpy as np

# 清晰度增强：下拉框文字 -> 处理分支编号（顺序与界面一致）
ENHANCE_MAP = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}

# 工具支持的扩展名
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
              ".m4v", ".mpg", ".mpeg", ".ts")


def to_gray(img):
    """统一转成灰度图（兼容 BGR / BGRA / 已是灰度）。"""
    if img.ndim == 2:
        return img
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def to_line_art(img, min_radius=2, brightness_offset=50, enhance_mode=0,
                invert=False):
    """把一张图片转成线稿，返回灰度 numpy 数组（uint8）。

    :param img: 原始图片（BGR / BGRA / 灰度）
    :param min_radius: 最小值半径 1~10，越大线条越粗
    :param brightness_offset: 亮度补偿 0~100，50 为不补偿
    :param enhance_mode: 0 无 / 1 对比度拉伸 / 2 轻度锐化 / 3 强锐化+去噪
    :param invert: True 输出黑底白线
    """
    gray = to_gray(img)

    # 取「反相后的最小值滤波」再与原图相加，得到线稿效果
    inverted = 255 - gray
    kernel_size = 2 * int(min_radius) + 1
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1),
                             borderType=cv2.BORDER_REPLICATE)
    result = cv2.add(gray, inverted_min)

    # 亮度补偿
    offset = (brightness_offset - 50) * 1.0
    if offset != 0:
        result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

    # 清晰度增强
    if enhance_mode == 1:  # 对比度拉伸
        p_low, p_high = np.percentile(result, (2, 98))
        if p_high > p_low:
            result = np.clip((result - p_low) / (p_high - p_low) * 255,
                             0, 255).astype(np.uint8)
    elif enhance_mode == 2:  # 轻度锐化
        gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=1.5)
        result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)
    elif enhance_mode == 3:  # 强锐化+去噪
        kernel_open = np.ones((2, 2), np.uint8)
        result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel_open)
        gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=2.0)
        result = cv2.addWeighted(result, 2.0, gaussian, -1.0, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)

    if invert:
        result = 255 - result

    return result
