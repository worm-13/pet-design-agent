# -*- coding: utf-8 -*-
"""
视觉中心计算：基于 alpha 通道的加权重心，近似人眼关注点（头部权重更高）。
用于合成时对齐宠物视觉中心到模板锚点。
"""
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def compute_visual_center_from_alpha(
    pet_rgba: Image.Image,
    alpha_threshold: int = 20,
    top_weight: float = 1.5,
    bottom_weight: float = 0.8,
) -> tuple[float, float]:
    """
    从宠物 RGBA 图的 alpha 通道计算视觉中心（加权重心）。

    算法：alpha 作为权重基础，引入纵向权重（头部更重要），
    计算加权重心作为视觉中心。

    Args:
        pet_rgba: 抠图后的宠物 RGBA 图（必须含 alpha）
        alpha_threshold: 低 alpha 噪声阈值，低于此值视为透明
        top_weight: 顶部（头部）权重，越大头部越重要
        bottom_weight: 底部权重

    Returns:
        (cx, cy): 视觉中心坐标，以 pet 图像坐标系，浮点
    """
    arr = np.array(pet_rgba)
    if arr.ndim != 3 or arr.shape[2] < 4:
        logger.warning("pet_rgba 无 alpha 通道，回退到几何中心")
        h, w = arr.shape[:2]
        return float(w) / 2, float(h) / 2

    alpha = arr[:, :, 3].astype(np.float64)  # 0-255

    # 去掉低透明度噪声
    alpha = np.where(alpha < alpha_threshold, 0, alpha)

    # 使用 alpha 作为权重基础
    weights = alpha.copy()

    h, w = alpha.shape

    # 纵向视觉权重：头部(顶部)更重要
    # linspace: 第0行(top) -> top_weight, 第h-1行(bottom) -> bottom_weight
    vertical_weight = np.linspace(top_weight, bottom_weight, h)
    weights = weights * vertical_weight[:, np.newaxis]

    total = np.sum(weights)
    if total <= 0:
        logger.warning("alpha mask 全空或异常，回退到几何中心 (W/2, H/2)")
        return float(w) / 2, float(h) / 2

    # 加权重心
    # x 坐标: 列索引加权平均，weights[y,x] * x
    xx = np.arange(w, dtype=np.float64)
    cx = np.sum(weights * xx) / total
    # y 坐标: 行索引加权平均，weights[y,x] * y
    yy = np.arange(h, dtype=np.float64)[:, np.newaxis]
    cy = np.sum(weights * yy) / total

    return float(cx), float(cy)
