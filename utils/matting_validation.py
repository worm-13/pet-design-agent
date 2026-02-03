# -*- coding: utf-8 -*-
"""
抠图结果有效性校验
用于多宠物合成前判断每只宠物的抠图是否「像一只宠物」，任一失败则中断或降级。
参考：升级方案.md 模块一、圆形双宠规范六。
"""
import numpy as np
from PIL import Image
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """单只宠物抠图校验结果"""
    valid: bool
    pet_id: str
    reason: str  # 失败时说明原因
    alpha_ratio: float
    largest_component_ratio: float
    aspect_ratio: float


# 通用阈值（升级方案 模块一）
ALPHA_RATIO_MIN = 0.05
ALPHA_RATIO_MAX = 0.6
LARGEST_COMPONENT_MIN_RATIO = 0.80
ASPECT_RATIO_MIN = 0.6
ASPECT_RATIO_MAX = 1.8

# 圆形双宠专用（更严格；头部占满方框时可达 50%–70%，上限放宽到 0.65）
CIRCLE_ALPHA_RATIO_MIN = 0.08
CIRCLE_ALPHA_RATIO_MAX = 0.70
CIRCLE_ASPECT_RATIO_MIN = 0.7
CIRCLE_ASPECT_RATIO_MAX = 1.6


def _get_alpha_mask_binary(image: Image.Image, threshold: int = 20) -> np.ndarray:
    """获取二值 alpha mask（> threshold 为 1）"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    alpha = np.array(image.split()[3])
    return (alpha > threshold).astype(np.uint8)


def _largest_connected_component_ratio(alpha_binary: np.ndarray) -> float:
    """
    计算最大连通域占所有 alpha 像素的比例。
    若 < 80% 判定为抠图碎裂/失败。
    """
    from scipy import ndimage
    labeled, num_features = ndimage.label(alpha_binary)
    if num_features == 0:
        return 0.0
    total = np.sum(alpha_binary > 0)
    if total == 0:
        return 0.0
    sizes = ndimage.sum(alpha_binary, labeled, range(1, num_features + 1))
    if sizes.size == 0:
        return 0.0
    largest = float(np.max(sizes))
    return largest / total


def _largest_connected_component_ratio_cv(alpha_binary: np.ndarray) -> float:
    """最大连通域占比：优先 scipy，否则 4 邻域 BFS。"""
    try:
        from scipy import ndimage
        labeled, num_features = ndimage.label(alpha_binary)
        if num_features == 0:
            return 0.0
        total = int(np.sum(alpha_binary > 0))
        if total == 0:
            return 0.0
        sizes = ndimage.sum(alpha_binary, labeled, range(1, num_features + 1))
        if sizes.size == 0:
            return 0.0
        largest = float(np.max(sizes))
        return largest / total
    except ImportError:
        pass
    # 无 scipy：4 邻域 BFS，只向 alpha 邻居扩展
    h, w = alpha_binary.shape
    visited = np.zeros_like(alpha_binary, dtype=bool)
    total = 0
    largest = 0
    for y in range(h):
        for x in range(w):
            if alpha_binary[y, x] == 0 or visited[y, x]:
                continue
            stack = [(y, x)]
            count = 0
            while stack:
                cy, cx = stack.pop()
                if cy < 0 or cy >= h or cx < 0 or cx >= w or alpha_binary[cy, cx] == 0 or visited[cy, cx]:
                    continue
                visited[cy, cx] = True
                count += 1
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and alpha_binary[ny, nx] and not visited[ny, nx]:
                        stack.append((ny, nx))
            total += count
            if count > largest:
                largest = count
    return largest / total if total > 0 else 0.0


def validate_pet_matting(
    image: Image.Image,
    pet_id: str = "unknown",
    for_circular_template: bool = False
) -> ValidationResult:
    """
    单只宠物抠图结果有效性校验。
    
    规则：
    1. alpha 覆盖率在合理范围内（过小=没抠到，过大=整张图）
    2. 最大连通域占比 >= 80%（否则判定抠图碎裂/失败）
    3. 长宽比 sanity（过滤规则方块、拉伸残影）
    
    Args:
        image: RGBA 抠图结果
        pet_id: 宠物 ID，用于返回信息
        for_circular_template: 是否圆形双宠模板（使用更严阈值）
    
    Returns:
        ValidationResult(valid, pet_id, reason, alpha_ratio, largest_ratio, aspect_ratio)
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    w, h = image.size
    total_pixels = w * h
    
    alpha_min = CIRCLE_ALPHA_RATIO_MIN if for_circular_template else ALPHA_RATIO_MIN
    alpha_max = CIRCLE_ALPHA_RATIO_MAX if for_circular_template else ALPHA_RATIO_MAX
    aspect_min = CIRCLE_ASPECT_RATIO_MIN if for_circular_template else ASPECT_RATIO_MIN
    aspect_max = CIRCLE_ASPECT_RATIO_MAX if for_circular_template else ASPECT_RATIO_MAX
    
    alpha_bin = _get_alpha_mask_binary(image, threshold=20)
    non_zero = np.sum(alpha_bin > 0)
    alpha_ratio = non_zero / total_pixels if total_pixels > 0 else 0.0
    
    # 规则 1：alpha 覆盖率
    if alpha_ratio < alpha_min:
        return ValidationResult(
            valid=False, pet_id=pet_id,
            reason=f"alpha 覆盖率过低 ({alpha_ratio:.2%})，可能未抠到主体（要求 {alpha_min:.0%}~{alpha_max:.0%}）",
            alpha_ratio=alpha_ratio, largest_component_ratio=0.0, aspect_ratio=w/h if h else 0
        )
    if alpha_ratio > alpha_max:
        return ValidationResult(
            valid=False, pet_id=pet_id,
            reason=f"alpha 覆盖率过高 ({alpha_ratio:.2%})，可能整张图被保留（要求 {alpha_min:.0%}~{alpha_max:.0%}）",
            alpha_ratio=alpha_ratio, largest_component_ratio=0.0, aspect_ratio=w/h if h else 0
        )
    
    # 规则 2：最大连通域占比
    largest_ratio = _largest_connected_component_ratio_cv(alpha_bin)
    if largest_ratio < LARGEST_COMPONENT_MIN_RATIO:
        return ValidationResult(
            valid=False, pet_id=pet_id,
            reason=f"最大连通域占比过低 ({largest_ratio:.1%})，抠图可能碎裂/失败（要求 >= {LARGEST_COMPONENT_MIN_RATIO:.0%}）",
            alpha_ratio=alpha_ratio, largest_component_ratio=largest_ratio, aspect_ratio=w/h if h else 0
        )
    
    # 规则 3：长宽比
    aspect_ratio = w / h if h else 0
    if aspect_ratio < aspect_min or aspect_ratio > aspect_max:
        return ValidationResult(
            valid=False, pet_id=pet_id,
            reason=f"长宽比异常 ({aspect_ratio:.2f})，可能为规则方块或拉伸残影（要求 {aspect_min}~{aspect_max}）",
            alpha_ratio=alpha_ratio, largest_component_ratio=largest_ratio, aspect_ratio=aspect_ratio
        )
    
    return ValidationResult(
        valid=True, pet_id=pet_id, reason="",
        alpha_ratio=alpha_ratio, largest_component_ratio=largest_ratio, aspect_ratio=aspect_ratio
    )


def validate_all_pet_mattings(
    pet_images: List[Image.Image],
    pet_ids: List[str],
    for_circular_template: bool = False
) -> Tuple[bool, List[ValidationResult]]:
    """
    校验多只宠物抠图结果。任一失败则整体不通过。
    
    Returns:
        (all_valid, list of ValidationResult)
    """
    results = []
    for img, pid in zip(pet_images, pet_ids):
        r = validate_pet_matting(img, pet_id=pid, for_circular_template=for_circular_template)
        results.append(r)
        if not r.valid:
            return False, results
    return True, results
