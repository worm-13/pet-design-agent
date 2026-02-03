# -*- coding: utf-8 -*-
"""
视觉中心计算工具
用于计算图像的视觉中心点，用于宠物图像的精确定位
"""
import numpy as np
from PIL import Image


def compute_visual_center(image: Image.Image) -> tuple:
    """
    计算图像的视觉中心点

    基于图像的非透明区域计算质心，作为视觉中心

    Args:
        image: PIL Image对象（应为RGBA模式）

    Returns:
        tuple: (center_x, center_y) 视觉中心坐标
    """
    # 确保是RGBA模式
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # 获取alpha通道
    alpha = np.array(image.split()[-1])  # alpha通道

    # 创建权重矩阵（alpha值作为权重）
    y_indices, x_indices = np.indices(alpha.shape)
    total_weight = np.sum(alpha)

    if total_weight == 0:
        # 如果完全透明，使用边界框中心
        return compute_visual_center_bbox(image)

    # 计算加权中心
    center_x = np.sum(x_indices * alpha) / total_weight
    center_y = np.sum(y_indices * alpha) / total_weight

    return (center_x, center_y)


def compute_visual_center_bbox(image: Image.Image) -> tuple:
    """
    基于边界框计算视觉中心（简单版本）

    Args:
        image: PIL Image对象

    Returns:
        tuple: (center_x, center_y) 边界框中心
    """
    # 获取非透明区域的边界框
    bbox = image.getbbox()
    if bbox is None:
        # 完全透明，返回图像中心
        return (image.width / 2, image.height / 2)

    left, top, right, bottom = bbox
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    return (center_x, center_y)


def compute_visual_center_advanced(image: Image.Image,
                                 method: str = "alpha_weighted") -> tuple:
    """
    高级视觉中心计算

    Args:
        image: PIL Image对象
        method: 计算方法
            - "alpha_weighted": 基于alpha通道加权（默认，推荐）
            - "bbox_center": 基于边界框中心
            - "geometric_center": 几何中心

    Returns:
        tuple: (center_x, center_y) 视觉中心坐标
    """
    if method == "alpha_weighted":
        return compute_visual_center(image)
    elif method == "bbox_center":
        return compute_visual_center_bbox(image)
    elif method == "geometric_center":
        return (image.width / 2, image.height / 2)
    else:
        raise ValueError(f"未知的计算方法: {method}")


# 为了向后兼容，提供别名
def compute_center_of_mass(image: Image.Image) -> tuple:
    """compute_visual_center的别名"""
    return compute_visual_center(image)