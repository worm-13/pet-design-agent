# -*- coding: utf-8 -*-
"""
多宠物合成增强工具
实现文档中提到的所有增强功能：
1. Alpha边缘净化
2. 极轻度羽化
3. 可选内描边
4. 视觉面积归一化
5. 组合视觉中心对齐
6. 圆形模板整体缩放
"""
import numpy as np
from PIL import Image, ImageFilter
from typing import List, Tuple, Optional
import math


def clean_alpha_edge(image: Image.Image, threshold: int = 10) -> Image.Image:
    """
    Alpha边缘净化：去除低于阈值的噪点
    
    Args:
        image: RGBA图像
        threshold: Alpha阈值，低于此值的像素设为完全透明
    
    Returns:
        处理后的图像
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    data = np.array(image)
    alpha = data[:, :, 3]
    
    # 将低于阈值的alpha设为0
    mask = alpha < threshold
    data[mask, 3] = 0
    
    return Image.fromarray(data, 'RGBA')


def apply_light_feather(image: Image.Image, radius: float = 1.5) -> Image.Image:
    """
    极轻度羽化：只作用于alpha边缘，不模糊主体
    
    Args:
        image: RGBA图像
        radius: 羽化半径（1-2px）
    
    Returns:
        处理后的图像
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # 分离alpha通道
    alpha = image.split()[3]
    
    # 对alpha通道应用轻微的高斯模糊
    alpha_feathered = alpha.filter(ImageFilter.GaussianBlur(radius=radius))
    
    # 重新组合图像
    r, g, b, _ = image.split()
    result = Image.merge('RGBA', (r, g, b, alpha_feathered))
    
    return result


def compute_average_color(image: Image.Image) -> Tuple[int, int, int]:
    """
    计算图像的平均颜色（用于内描边）
    只考虑非透明像素
    
    Args:
        image: RGBA图像
    
    Returns:
        (r, g, b) 平均颜色
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    data = np.array(image)
    alpha = data[:, :, 3]
    
    # 只考虑非透明像素
    mask = alpha > 128
    if not np.any(mask):
        return (128, 128, 128)  # 默认灰色
    
    rgb = data[:, :, :3]
    masked_rgb = rgb[mask]
    
    avg_r = int(np.mean(masked_rgb[:, 0]))
    avg_g = int(np.mean(masked_rgb[:, 1]))
    avg_b = int(np.mean(masked_rgb[:, 2]))
    
    return (avg_r, avg_g, avg_b)


def apply_inner_stroke(image: Image.Image, 
                       stroke_width: int = 1,
                       stroke_color: Optional[Tuple[int, int, int]] = None,
                       opacity: int = 180) -> Image.Image:
    """
    应用轻微内描边
    
    Args:
        image: RGBA图像
        stroke_width: 描边宽度（1px）
        stroke_color: 描边颜色，如果为None则使用图像平均色
        opacity: 描边透明度（0-255）
    
    Returns:
        处理后的图像
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    if stroke_color is None:
        stroke_color = compute_average_color(image)
    
    # 获取alpha通道
    alpha = np.array(image.split()[3])
    
    # 找到边缘（alpha > 0 且周围有alpha=0的像素）
    edge_mask = np.zeros_like(alpha, dtype=bool)
    
    # 检查周围像素
    h, w = alpha.shape
    for y in range(h):
        for x in range(w):
            if alpha[y, x] > 0:  # 当前像素不透明
                # 检查周围是否有透明像素
                is_edge = False
                for dy in range(-stroke_width, stroke_width + 1):
                    for dx in range(-stroke_width, stroke_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            if alpha[ny, nx] == 0:
                                is_edge = True
                                break
                        else:
                            # 边界外视为透明
                            is_edge = True
                            break
                    if is_edge:
                        break
                edge_mask[y, x] = is_edge
    
    # 创建描边图层
    stroke_data = np.array(image.copy())
    
    # 在边缘位置绘制描边（只修改边缘像素的颜色和透明度）
    stroke_data[edge_mask, 0] = stroke_color[0]
    stroke_data[edge_mask, 1] = stroke_color[1]
    stroke_data[edge_mask, 2] = stroke_color[2]
    # 保持原有alpha，但可以稍微降低以产生内描边效果
    stroke_data[edge_mask, 3] = np.minimum(alpha[edge_mask], opacity)
    
    result = Image.fromarray(stroke_data, 'RGBA')
    
    return result


def process_pet_image_for_display(image: Image.Image,
                                 enable_edge_cleaning: bool = True,
                                 enable_feather: bool = True,
                                 enable_stroke: bool = False) -> Image.Image:
    """
    对单只宠物图像进行展示级边缘处理
    
    Args:
        image: 宠物抠图结果（RGBA）
        enable_edge_cleaning: 是否启用边缘净化
        enable_feather: 是否启用轻度羽化
        enable_stroke: 是否启用内描边
    
    Returns:
        处理后的图像
    """
    result = image.copy()
    
    if enable_edge_cleaning:
        result = clean_alpha_edge(result, threshold=10)
    
    if enable_feather:
        result = apply_light_feather(result, radius=1.5)
    
    if enable_stroke:
        result = apply_inner_stroke(result, stroke_width=1, opacity=180)
    
    return result


def compute_visual_area(image: Image.Image, alpha_threshold: int = 20) -> float:
    """
    计算宠物主体的视觉面积（基于 alpha mask）
    
    核心思想：使用 alpha mask 计算主体真实占用面积，只统计 alpha 高于阈值的像素，
    去除毛边噪声，得到"人眼感知面积"的近似值。
    
    Args:
        image: RGBA图像（宠物抠图结果）
        alpha_threshold: Alpha阈值，低于此值的像素视为透明（默认20，用于忽略半透明毛边）
    
    Returns:
        视觉面积（像素数量，int）
    
    说明：
        - alpha_threshold=20 用于忽略半透明毛边，只统计主体真实占用
        - 得到的是"人眼感知面积"的近似值
        - 几何尺寸 ≠ 视觉尺寸（毛多的狗头视觉面积更大，轮廓紧凑的猫头视觉面积更小）
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    alpha = np.array(image.split()[3])
    # 只统计 alpha 高于阈值的像素，去除毛边噪声
    visual_pixels = np.sum(alpha > alpha_threshold)
    
    return float(visual_pixels)


# 视觉面积归一化安全兜底（升级方案 模块二、圆形双宠规范四）
FACTOR_CLAMP_MIN = 0.75
FACTOR_CLAMP_MAX = 1.25
SCALE_CLAMP_MIN = 0.65
SCALE_CLAMP_MAX = 1.0  # 禁止单宠放大超过原始尺寸
CIRCLE_FACTOR_CLAMP_MIN = 0.80
CIRCLE_FACTOR_CLAMP_MAX = 1.20


def normalize_visual_areas(pet_images: List[Image.Image],
                          base_scales: List[float],
                          reference_index: int = 0,
                          factor_clamp: Tuple[float, float] = (FACTOR_CLAMP_MIN, FACTOR_CLAMP_MAX),
                          scale_clamp: Tuple[float, float] = (SCALE_CLAMP_MIN, SCALE_CLAMP_MAX)) -> List[float]:
    """
    视觉面积归一化函数（核心算法）+ 安全兜底
    
    根据视觉面积归一化 scale，使多只宠物视觉大小接近。
    factor 与 scale 均做 clamp，防止异常 area 导致 scale 爆炸（升级方案 模块二）。
    
    Args:
        pet_images: RGBA 抠图结果
        base_scales: 当前每只宠物的 scale
        reference_index: 参考宠物索引
        factor_clamp: factor 限制 (min, max)，圆形模板建议 (0.80, 1.20)
        scale_clamp: 最终 scale 限制 (min, max)，圆形禁止 > 1.0
    
    Returns:
        归一化后的 scale 列表
    """
    if len(pet_images) < 2:
        return base_scales
    
    areas = [compute_visual_area(img) for img in pet_images]
    reference_area = areas[reference_index]
    if reference_area == 0:
        reference_area = max(areas) if max(areas) > 0 else 1.0
    
    f_min, f_max = factor_clamp
    s_min, s_max = scale_clamp
    normalized_scales = []
    for area, scale in zip(areas, base_scales):
        if area == 0:
            normalized_scales.append(max(s_min, min(s_max, scale)))
            continue
        factor = math.sqrt(reference_area / area)
        factor = max(f_min, min(f_max, factor))
        normalized_scale = scale * factor
        normalized_scale = max(s_min, min(s_max, normalized_scale))
        normalized_scales.append(normalized_scale)
    
    return normalized_scales


def compute_group_visual_center(pet_images: List[Image.Image],
                               layouts: List,
                               template_size: Tuple[int, int]) -> Tuple[float, float]:
    """
    双宠物组合视觉中心算法（核心算法）
    
    计算组合视觉中心，让两只宠物作为一个"组合对象"整体对齐模板中心。
    即：组合有自己的视觉中心，宠物只是组合内部的成员。
    
    核心思想：
        - 从"两个物体分别对齐模板"升级为"一个组合对象整体对齐模板"
        - 这是设计师在排多主体时的真实思路
    
    工程约束：
        - 组合视觉中心对齐必须在最终 anchor 确定之前完成
        - 只影响 anchor，不修改图像内容
    
    Args:
        pet_images: 宠物图像列表
        layouts: 布局列表（包含anchor和scale）
        template_size: 模板尺寸 (width, height)
    
    Returns:
        组合视觉中心坐标 (x, y) 像素坐标
    
    算法步骤（2只宠物）：
        1. 计算每只宠物在模板坐标系中的视觉中心
        2. 计算组合中心 = (center_a + center_b) / 2
        3. 注意：这里的 centers 是视觉中心，不是图像几何中心
    """
    # 延迟导入避免循环依赖
    import sys
    import os
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)
    from utils.visual_center import compute_visual_center
    
    if len(pet_images) == 0:
        return (template_size[0] / 2, template_size[1] / 2)
    
    # 步骤1：计算每只宠物在模板坐标系中的视觉中心
    visual_centers = []
    
    for pet_image, layout in zip(pet_images, layouts):
        # 缩放图像
        scaled_width = int(pet_image.width * layout.scale)
        scaled_height = int(pet_image.height * layout.scale)
        scaled_pet = pet_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # 计算缩放后的视觉中心（相对于缩放后图像的坐标）
        cx_local, cy_local = compute_visual_center(scaled_pet)
        
        # 转换为模板坐标系
        anchor_x_px = layout.anchor[0] * template_size[0]
        anchor_y_px = layout.anchor[1] * template_size[1]
        
        # 视觉中心在模板中的位置 = 锚点位置 - (视觉中心相对于图像中心的偏移)
        pet_center_x = anchor_x_px - (scaled_width / 2 - cx_local)
        pet_center_y = anchor_y_px - (scaled_height / 2 - cy_local)
        
        visual_centers.append((pet_center_x, pet_center_y))
    
    # 步骤2：计算组合中心
    if len(visual_centers) == 1:
        return visual_centers[0]
    
    # 基础算法（2只宠物）：组合中心 = (center_a + center_b) / 2
    # 对于多只宠物：组合中心 = 所有视觉中心的平均值
    if len(visual_centers) == 2:
        # 双宠物组合视觉中心计算
        cx = (visual_centers[0][0] + visual_centers[1][0]) / 2
        cy = (visual_centers[0][1] + visual_centers[1][1]) / 2
        return (cx, cy)
    else:
        # 多宠物：所有视觉中心的平均值
        group_center_x = sum(cx for cx, cy in visual_centers) / len(visual_centers)
        group_center_y = sum(cy for cx, cy in visual_centers) / len(visual_centers)
        return (group_center_x, group_center_y)


# 圆形双宠 anchor 硬约束（升级方案 模块三、圆形双宠规范三/五）
ANCHOR_X_LIMITS = (0.2, 0.8)
ANCHOR_Y_LIMITS = (0.25, 0.75)
CIRCLE_ANCHOR_X_LIMITS = (0.30, 0.70)
CIRCLE_ANCHOR_Y_LIMITS = (0.42, 0.62)
CIRCLE_VISUAL_CENTER = (0.5, 0.53)  # 圆形模板视觉重心略低于正中心


def align_group_to_template_center(pet_images: List[Image.Image],
                                  layouts: List,
                                  template_size: Tuple[int, int],
                                  target_center: Tuple[float, float] = (0.5, 0.5),
                                  anchor_x_limits: Tuple[float, float] = ANCHOR_X_LIMITS,
                                  anchor_y_limits: Tuple[float, float] = ANCHOR_Y_LIMITS) -> List:
    """
    组合中心对齐模板中心（关键步骤）+ anchor 硬约束
    
    将组合视觉中心整体平移到目标中心；对齐后 anchor 必须 clamp 到指定范围
    （升级方案 模块三、圆形双宠规范五）。
    """
    group_center = compute_group_visual_center(pet_images, layouts, template_size)
    
    target_x = target_center[0] * template_size[0]
    target_y = target_center[1] * template_size[1]
    dx = target_x - group_center[0]
    dy = target_y - group_center[1]
    
    ax_min, ax_max = anchor_x_limits
    ay_min, ay_max = anchor_y_limits
    for layout in layouts:
        anchor_x_px = layout.anchor[0] * template_size[0]
        anchor_y_px = layout.anchor[1] * template_size[1]
        new_anchor_x_px = anchor_x_px + dx
        new_anchor_y_px = anchor_y_px + dy
        new_anchor_x = new_anchor_x_px / template_size[0]
        new_anchor_y = new_anchor_y_px / template_size[1]
        new_anchor_x = max(ax_min, min(ax_max, new_anchor_x))
        new_anchor_y = max(ay_min, min(ay_max, new_anchor_y))
        layout.anchor = (new_anchor_x, new_anchor_y)
    
    return layouts


def clamp_layout_anchors(layouts: List,
                         anchor_x_limits: Tuple[float, float] = ANCHOR_X_LIMITS,
                         anchor_y_limits: Tuple[float, float] = ANCHOR_Y_LIMITS) -> List:
    """
    仅对布局中的 anchor 做硬约束（不移动组合中心）。
    用于「使用 state 自定义布局」时保留用户位置/比例，只限制在安全范围内。
    """
    ax_min, ax_max = anchor_x_limits
    ay_min, ay_max = anchor_y_limits
    for layout in layouts:
        x, y = layout.anchor[0], layout.anchor[1]
        layout.anchor = (max(ax_min, min(ax_max, x)), max(ay_min, min(ay_max, y)))
    return layouts


def is_circular_template(template_path: str) -> bool:
    """
    检测模板是否为圆形或强裁切形状
    
    Args:
        template_path: 模板路径
    
    Returns:
        是否为圆形模板
    """
    try:
        template = Image.open(template_path).convert('RGBA')
        
        # 检查alpha通道：如果是圆形模板，边缘会有大量透明区域
        alpha = np.array(template.split()[3])
        
        # 计算中心区域的非透明像素比例
        h, w = alpha.shape
        center_h, center_w = h // 2, w // 2
        center_region = alpha[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4]
        center_opacity = np.sum(center_region > 128) / center_region.size
        
        # 计算边缘区域的非透明像素比例
        edge_mask = np.zeros_like(alpha, dtype=bool)
        edge_mask[:h//8, :] = True  # 上边缘
        edge_mask[-h//8:, :] = True  # 下边缘
        edge_mask[:, :w//8] = True  # 左边缘
        edge_mask[:, -w//8:] = True  # 右边缘
        
        edge_opacity = np.sum(alpha[edge_mask] > 128) / np.sum(edge_mask)
        
        # 如果中心区域不透明但边缘区域透明，可能是圆形模板
        is_circular = center_opacity > 0.7 and edge_opacity < 0.3
        
        # 或者检查文件名（含中文模板名）
        import os
        filename = os.path.basename(template_path).lower()
        if 'circle' in filename or 'circular' in filename or 'round' in filename:
            is_circular = True
        # 清新粉蓝等圆形背景模板
        if '清新粉蓝' in template_path or 'qingxin' in template_path or 'fenlan' in template_path:
            is_circular = True
        
        return is_circular
    except:
        return False


def apply_circular_template_scaling(layouts: List, scale_reduction: float = 0.15) -> List:
    """
    对圆形模板应用整体缩放（升级方案：global_scale_multiplier = 0.85，即 1-0.15）
    并禁止任何 pet scale > 1.0。
    
    Args:
        layouts: 布局列表（会被修改）
        scale_reduction: 缩放减少比例（0.15 = 15%，即乘 0.85）
    
    Returns:
        修改后的布局列表
    """
    for layout in layouts:
        layout.scale = layout.scale * (1.0 - scale_reduction)
        layout.scale = min(1.0, layout.scale)  # 禁止单宠放大超过原始尺寸
    return layouts
