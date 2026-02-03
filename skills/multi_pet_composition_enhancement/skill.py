# -*- coding: utf-8 -*-
"""
多宠物合成增强技能
实现展示级边缘处理、视觉面积归一化、组合视觉中心对齐等功能
"""
import os
import sys
from typing import List, Optional, Dict, Any
from PIL import Image

# 确保可以导入项目模块
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

for path in [_PROJECT_ROOT, _SCRIPT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from utils.multi_pet_enhancement import (
    process_pet_image_for_display,
    normalize_visual_areas,
    align_group_to_template_center,
    clamp_layout_anchors,
    is_circular_template,
    apply_circular_template_scaling,
    CIRCLE_FACTOR_CLAMP_MIN,
    CIRCLE_FACTOR_CLAMP_MAX,
    SCALE_CLAMP_MIN,
    SCALE_CLAMP_MAX,
    ANCHOR_X_LIMITS,
    ANCHOR_Y_LIMITS,
    CIRCLE_ANCHOR_X_LIMITS,
    CIRCLE_ANCHOR_Y_LIMITS,
    CIRCLE_VISUAL_CENTER,
)
from utils.multi_pet_layout import PetLayout
from utils.visual_center import compute_visual_center


class MultiPetCompositionEnhancementSkill:
    """
    多宠物合成增强技能
    
    将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"
    """
    
    def enhance_composition(
        self,
        pet_images: List[Image.Image],
        template_path: str,
        layouts: List[PetLayout],
        enable_edge_cleaning: bool = True,
        enable_feather: bool = True,
        enable_stroke: bool = False,
        enable_visual_normalization: bool = True,
        enable_group_alignment: bool = True,
        use_state_layout: bool = False
    ) -> Image.Image:
        """
        增强多宠物合成

        Args:
            pet_images: 宠物抠图结果列表（RGBA）
            template_path: 模板路径
            layouts: 布局配置列表
            enable_edge_cleaning: 是否启用边缘净化
            enable_feather: 是否启用轻度羽化
            enable_stroke: 是否启用内描边
            enable_visual_normalization: 是否启用视觉面积归一化
            enable_group_alignment: 是否启用组合中心对齐
            use_state_layout: 为 True 时使用 state 自定义布局，跳过归一化与组合对齐，仅做边缘处理、anchor 硬约束与圆形缩放

        Returns:
            增强后的合成图像
        """
        # 圆形双宠专用：内描边默认开启（升级方案 规范七）
        is_circle = is_circular_template(template_path)
        use_stroke = enable_stroke or is_circle

        # 1. 抠图后边缘展示级处理
        processed_images = []
        for pet_image in pet_images:
            processed = process_pet_image_for_display(
                pet_image,
                enable_edge_cleaning=enable_edge_cleaning,
                enable_feather=enable_feather,
                enable_stroke=use_stroke
            )
            processed_images.append(processed)

        # 使用 state 自定义布局时：不归一化、不对齐，只做 anchor 硬约束与圆形缩放
        if use_state_layout:
            if is_circle:
                layouts = clamp_layout_anchors(
                    layouts,
                    anchor_x_limits=CIRCLE_ANCHOR_X_LIMITS,
                    anchor_y_limits=CIRCLE_ANCHOR_Y_LIMITS
                )
            else:
                layouts = clamp_layout_anchors(
                    layouts,
                    anchor_x_limits=ANCHOR_X_LIMITS,
                    anchor_y_limits=ANCHOR_Y_LIMITS
                )
            if is_circle:
                layouts = apply_circular_template_scaling(layouts, scale_reduction=0.15)
        else:
            # 2–4. 视觉面积归一化 + clamp（圆形用更严 factor 与 scale 上限 1.0）
            if enable_visual_normalization:
                base_scales = [layout.scale for layout in layouts]
                if is_circle:
                    normalized_scales = normalize_visual_areas(
                        processed_images, base_scales,
                        factor_clamp=(CIRCLE_FACTOR_CLAMP_MIN, CIRCLE_FACTOR_CLAMP_MAX),
                        scale_clamp=(SCALE_CLAMP_MIN, SCALE_CLAMP_MAX)
                    )
                else:
                    normalized_scales = normalize_visual_areas(processed_images, base_scales)
                for layout, new_scale in zip(layouts, normalized_scales):
                    layout.scale = new_scale

            # 8. 组合视觉中心对齐 + anchor 硬约束（圆形用 circle_visual_center 与专用 anchor 范围）
            if enable_group_alignment:
                template = Image.open(template_path)
                template_size = template.size
                template.close()
                if is_circle:
                    layouts = align_group_to_template_center(
                        processed_images, layouts, template_size,
                        target_center=CIRCLE_VISUAL_CENTER,
                        anchor_x_limits=CIRCLE_ANCHOR_X_LIMITS,
                        anchor_y_limits=CIRCLE_ANCHOR_Y_LIMITS
                    )
                else:
                    layouts = align_group_to_template_center(
                        processed_images, layouts, template_size
                    )

            # 9. 圆形模板整体缩放兜底（global_scale_multiplier = 0.85）
            if is_circle:
                layouts = apply_circular_template_scaling(layouts, scale_reduction=0.15)
        
        # 10. 合成输出
        result = self._composite_pets(
            template_path,
            processed_images,
            layouts
        )
        
        return result
    
    def _composite_pets(
        self,
        template_path: str,
        pet_images: List[Image.Image],
        layouts: List[PetLayout]
    ) -> Image.Image:
        """
        执行最终的合成操作
        """
        template = Image.open(template_path).convert("RGBA")
        template_width, template_height = template.size
        
        result = Image.new("RGBA", (template_width, template_height), (0, 0, 0, 0))
        result.paste(template, (0, 0))
        
        for pet_image, layout in zip(pet_images, layouts):
            if pet_image.mode != 'RGBA':
                pet_image = pet_image.convert('RGBA')
            
            # 缩放宠物图像
            scaled_width = int(pet_image.width * layout.scale)
            scaled_height = int(pet_image.height * layout.scale)
            
            if scaled_width > 0 and scaled_height > 0:
                scaled_pet = pet_image.resize(
                    (scaled_width, scaled_height),
                    Image.Resampling.LANCZOS
                )
                
                # 计算缩放后的视觉中心
                cx_scaled, cy_scaled = compute_visual_center(scaled_pet)
                
                # 计算粘贴位置
                anchor_x_px = layout.anchor[0] * template_width
                anchor_y_px = layout.anchor[1] * template_height
                
                paste_x = int(anchor_x_px - cx_scaled)
                paste_y = int(anchor_y_px - cy_scaled)
                
                # 边界检查
                if paste_x + scaled_width < 0:
                    paste_x = -scaled_width + 10
                if paste_x > template_width:
                    paste_x = template_width - 10
                if paste_y + scaled_height < 0:
                    paste_y = -scaled_height + 10
                if paste_y > template_height:
                    paste_y = template_height - 10
                
                # 粘贴到结果图
                result.paste(scaled_pet, (paste_x, paste_y), scaled_pet)
        
        return result
