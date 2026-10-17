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

# 「对比度拉伸」的白场档位（界面上的「去杂点」下拉框）：
# 线稿里近白像素大多是背景纹理 / JPEG 杂点。亮图的白场分位通常就是 255，直接线性
# 拉伸会把这一段的杂点放大 2~3 倍，看上去灰蒙蒙一片（常说的「噪点、螺纹花纹」）。
# 把白场上限压低能明显干净，但**压得越狠、很淡的细节线条也会越浅**，所以做成可选档位。
DENOISE_MAP = {
    "关（最保细节）": 255.0,
    "轻（推荐）": 248.0,
    "中": 243.0,
    "重（背景最干净）": 235.0,
}
DEFAULT_DENOISE = "轻（推荐）"

# 肩部宽度：白场~255 平滑压进 (255-4)~255。
# 不用硬截断 —— 硬截断会在平滑渐变背景上切出一大片死白 + 一圈可见的等高线。
CONTRAST_SHOULDER = 4.0
# 放大倍数上限（数值默认值，界面上的「放大上限」档位见 GAIN_MAX_MAP）：
# 黑场离白场太近时（画面几乎没有暗部）不再硬拉，否则会把一点点噪声放大成一片，
# 也是「满屏噪点」的元凶之一。0 表示不限制（等同旧版行为）。
CONTRAST_GAIN_MAX = 3.5

# 「放大上限」档位：界面下拉框文字 -> 倍数（0 = 不限制）
# 5 倍以下每 0.5 一档，5 倍以上每 1 一档，最大 10 倍
GAIN_MAX_MAP = {
    "不限制": 0.0,
    "2 倍": 2.0,
    "2.5 倍": 2.5,
    "3 倍": 3.0,
    "3.5 倍（推荐）": 3.5,
    "4 倍": 4.0,
    "4.5 倍": 4.5,
    "5 倍": 5.0,
    "6 倍": 6.0,
    "7 倍": 7.0,
    "8 倍": 8.0,
    "9 倍": 9.0,
    "10 倍": 10.0,
}
DEFAULT_GAIN_MAX = "3.5 倍（推荐）"

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


def denoise_knee(denoise=DEFAULT_DENOISE):
    """把「去杂点」档位换算成白场上限（支持档位文字或直接给数值）。"""
    if denoise is None:
        denoise = DEFAULT_DENOISE
    if isinstance(denoise, str):
        return float(DENOISE_MAP.get(denoise, DENOISE_MAP[DEFAULT_DENOISE]))
    return float(denoise)


def gain_max_value(gain_max=DEFAULT_GAIN_MAX):
    """把「放大上限」档位换算成倍数（支持档位文字或直接给数值；0 = 不限制）。"""
    if gain_max is None:
        gain_max = DEFAULT_GAIN_MAX
    if isinstance(gain_max, str):
        return float(GAIN_MAX_MAP.get(gain_max, GAIN_MAX_MAP[DEFAULT_GAIN_MAX]))
    return float(gain_max)


def stretch_levels(gray, lo_p=2, hi_p=98, white_knee=None,
                   shoulder=CONTRAST_SHOULDER, gain_max=CONTRAST_GAIN_MAX):
    """按分位数做「对比度拉伸」，近白部分用肩部压平。

    :param lo_p: 黑场分位（默认 2%）
    :param hi_p: 白场分位（默认 98%）
    :param white_knee: 白场上限（见 ``DENOISE_MAP``），255 = 不压、纯线性拉伸
    :param shoulder: 肩部宽度：white_knee~255 被压进 (255-shoulder)~255，
                     取 0 表示硬截断（渐变背景上会出现等高线，不建议）
    :param gain_max: 放大倍数上限（<=0 表示不限制）
    """
    if white_knee is None:
        white_knee = denoise_knee()
    lo, hi = np.percentile(gray, (lo_p, hi_p))
    hi = float(min(hi, white_knee))
    if gain_max and gain_max > 0:
        # 黑场离白场太近时把黑场降下来，限制放大倍数（保细节同时不放大噪声）
        lo = max(0.0, min(float(lo), hi - 255.0 / float(gain_max)))
    if hi <= lo + 1:
        return gray
    x = gray.astype(np.float32)
    out = (x - lo) / (hi - lo) * 255.0
    if shoulder > 0 and hi < 255:
        # 肩部：斜率远小于主段，等于把近白杂点压成几乎一样的白
        m = x > hi
        out[m] = (255.0 - shoulder) + (x[m] - hi) * (shoulder / (255.0 - hi))
    return np.clip(out, 0, 255).astype(np.uint8)


def to_line_art(img, min_radius=2, brightness_offset=50, enhance_mode=0,
                invert=False, denoise=DEFAULT_DENOISE,
                gain_max=DEFAULT_GAIN_MAX):
    """把一张图片转成线稿，返回灰度 numpy 数组（uint8）。

    :param img: 原始图片（BGR / BGRA / 灰度）
    :param min_radius: 最小值半径 1~10，越大线条越粗
    :param brightness_offset: 亮度补偿 0~100，50 为不补偿
    :param enhance_mode: 0 无 / 1 对比度拉伸 / 2 轻度锐化 / 3 强锐化+去噪
    :param invert: True 输出黑底白线
    :param denoise: 「去杂点」档位（``DENOISE_MAP`` 里的文字），只影响「对比度拉伸」
    :param gain_max: 「放大上限」档位（``GAIN_MAX_MAP`` 里的文字，0 = 不限制），
                     同样只影响「对比度拉伸」
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
        result = stretch_levels(result, white_knee=denoise_knee(denoise),
                                gain_max=gain_max_value(gain_max))
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
