# -*- coding: utf-8 -*-
"""
几何计算模块 - 角度/弧长/分布计算
"""
import math
from typing import List, Tuple


def compute_phrase_anchor_angles(
    phrase_count: int,
    start_angle_deg: float,
    clockwise: bool
) -> List[float]:
    """
    返回每个短语的锚点角（弧度）
    等角度分布

    Args:
        phrase_count: 短语数量
        start_angle_deg: 起始角度（度）
        clockwise: 是否顺时针

    Returns:
        每个短语锚点角的弧度列表
    """
    if phrase_count <= 0:
        return []

    start_angle_rad = math.radians(start_angle_deg)
    step = 2 * math.pi / phrase_count

    if not clockwise:
        step = -step

    anchor_angles = []
    for i in range(phrase_count):
        angle = start_angle_rad + i * step
        # 标准化到 [0, 2π) 范围
        angle = angle % (2 * math.pi)
        anchor_angles.append(angle)

    return anchor_angles


def angle_to_position(
    center: Tuple[int, int],
    radius: float,
    angle_rad: float
) -> Tuple[float, float]:
    """
    将极坐标转换为笛卡尔坐标

    Args:
        center: 圆心坐标 (x, y)
        radius: 半径
        angle_rad: 角度（弧度）

    Returns:
        位置坐标 (x, y)
    """
    cx, cy = center
    x = cx + radius * math.cos(angle_rad)
    y = cy + radius * math.sin(angle_rad)
    return x, y


def compute_rotation_angle(angle_rad: float, clockwise: bool) -> float:
    """
    计算字符的旋转角度（沿圆切线方向）

    Args:
        angle_rad: 字符位置角度（弧度）
        clockwise: 是否顺时针

    Returns:
        旋转角度（度）
    """
    if clockwise:
        rotation_deg = math.degrees(angle_rad) + 90
    else:
        rotation_deg = math.degrees(angle_rad) - 90

    return rotation_deg


def normalize_angle(angle_rad: float) -> float:
    """
    将角度标准化到 [0, 2π) 范围

    Args:
        angle_rad: 输入角度（弧度）

    Returns:
        标准化后的角度（弧度）
    """
    return angle_rad % (2 * math.pi)