# -*- coding: utf-8 -*-
"""
多宠物自动布局引擎
根据模板方向和宠物数量选择布局策略，实现防遮挡的自动排版
"""
import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class PetLayout:
    """宠物布局对象"""
    id: str
    anchor: Tuple[float, float]  # (x, y) 相对坐标 0-1
    scale: float
    rect: Tuple[float, float, float, float] = None  # (left, top, right, bottom)


class MultiPetLayoutEngine:
    """多宠物自动布局引擎"""

    def __init__(self, template_width: int, template_height: int):
        self.template_width = template_width
        self.template_height = template_height
        self.orientation = "landscape" if template_width >= template_height else "portrait"

    def select_layout_strategy(self, pet_count: int) -> str:
        """根据宠物数量选择布局策略"""
        if pet_count == 1:
            return "single"
        elif pet_count == 2:
            return "side_by_side" if self.orientation == "landscape" else "vertical_stack"
        elif pet_count == 3:
            return "triangle" if self.orientation == "landscape" else "inverted_triangle"
        elif pet_count == 4:
            return "grid_2x2"
        else:
            raise ValueError(f"不支持 {pet_count} 只宠物")

    def get_default_layouts(self, pet_count: int) -> List[PetLayout]:
        """获取默认布局配置"""
        strategy = self.select_layout_strategy(pet_count)

        if strategy == "single":
            return [PetLayout("pet_0", (0.5, 0.55), 1.0)]

        elif strategy == "side_by_side":  # 横版：左右并列
            return [
                PetLayout("pet_0", (0.35, 0.55), 0.9),
                PetLayout("pet_1", (0.65, 0.55), 0.9)
            ]

        elif strategy == "vertical_stack":  # 竖版：上下排列
            return [
                PetLayout("pet_0", (0.5, 0.40), 0.9),
                PetLayout("pet_1", (0.5, 0.68), 0.9)
            ]

        elif strategy == "triangle":  # 横版：三角构图
            return [
                PetLayout("pet_0", (0.50, 0.40), 1.0),  # 上方主视觉
                PetLayout("pet_1", (0.32, 0.62), 0.9),  # 左下
                PetLayout("pet_2", (0.68, 0.62), 0.9)   # 右下
            ]

        elif strategy == "inverted_triangle":  # 竖版：倒三角
            return [
                PetLayout("pet_0", (0.35, 0.38), 0.9),  # 左上
                PetLayout("pet_1", (0.65, 0.38), 0.9),  # 右上
                PetLayout("pet_2", (0.50, 0.68), 1.0)   # 下方主视觉
            ]

        elif strategy == "grid_2x2":  # 2x2网格
            base_y = 0.35 if self.orientation == "portrait" else 0.40
            return [
                PetLayout("pet_0", (0.35, base_y), 0.85),
                PetLayout("pet_1", (0.65, base_y), 0.85),
                PetLayout("pet_2", (0.35, base_y + 0.25), 0.85),
                PetLayout("pet_3", (0.65, base_y + 0.25), 0.85)
            ]

    def calculate_occupancy_rect(self, pet: PetLayout, pet_image_size: Tuple[int, int]) -> Tuple[float, float, float, float]:
        """
        计算宠物的占用矩形（基于缩放后的尺寸和锚点位置）
        返回：(left, top, right, bottom) 相对坐标 0-1
        """
        img_width, img_height = pet_image_size
        scaled_width = img_width * pet.scale / self.template_width
        scaled_height = img_height * pet.scale / self.template_height

        # 以锚点为中心计算矩形
        center_x, center_y = pet.anchor
        half_width = scaled_width / 2
        half_height = scaled_height / 2

        left = max(0, center_x - half_width)
        right = min(1, center_x + half_width)
        top = max(0, center_y - half_height)
        bottom = min(1, center_y + half_height)

        return (left, top, right, bottom)

    def check_overlap(self, rect1: Tuple[float, float, float, float],
                     rect2: Tuple[float, float, float, float]) -> bool:
        """检测两个矩形是否重叠"""
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2

        return not (
            right1 <= left2 or
            left1 >= right2 or
            bottom1 <= top2 or
            top1 >= bottom2
        )

    def apply_anti_overlap_corrections(self, layouts: List[PetLayout],
                                      pet_sizes: List[Tuple[int, int]]) -> List[PetLayout]:
        """
        应用防遮挡修正
        优先级：横向拉开 → 纵向错位 → 缩小兜底
        """
        # 更新所有rect
        for i, layout in enumerate(layouts):
            layout.rect = self.calculate_occupancy_rect(layout, pet_sizes[i])

        # 检测并修正重叠
        max_iterations = 3
        for iteration in range(max_iterations):
            has_overlap = False

            # 检查所有宠物对的重叠
            for i in range(len(layouts)):
                for j in range(i + 1, len(layouts)):
                    if self.check_overlap(layouts[i].rect, layouts[j].rect):
                        has_overlap = True
                        self._fix_overlap(layouts[i], layouts[j], pet_sizes[i], pet_sizes[j])
                        # 重新计算受影响的rect
                        layouts[i].rect = self.calculate_occupancy_rect(layouts[i], pet_sizes[i])
                        layouts[j].rect = self.calculate_occupancy_rect(layouts[j], pet_sizes[j])

            if not has_overlap:
                break

        return layouts

    def _fix_overlap(self, layout1: PetLayout, layout2: PetLayout,
                    size1: Tuple[int, int], size2: Tuple[int, int]):
        """修正两个宠物的重叠"""
        rect1, rect2 = layout1.rect, layout2.rect

        # 计算重叠区域
        overlap_left = max(rect1[0], rect2[0])
        overlap_right = min(rect1[2], rect2[2])
        overlap_width = max(0, overlap_right - overlap_left)

        overlap_top = max(rect1[1], rect2[1])
        overlap_bottom = min(rect1[3], rect2[3])
        overlap_height = max(0, overlap_bottom - overlap_top)

        # 优先横向拉开
        if overlap_width > overlap_height:
            # 计算需要移动的距离
            min_separation = (rect1[2] - rect1[0] + rect2[2] - rect2[0]) / 2
            move_distance = (overlap_width + min_separation) / 2

            # 向左右移动
            center_x = (layout1.anchor[0] + layout2.anchor[0]) / 2
            layout1.anchor = (max(0.2, center_x - move_distance), layout1.anchor[1])
            layout2.anchor = (min(0.8, center_x + move_distance), layout2.anchor[1])

        else:
            # 纵向错位
            center_y = (layout1.anchor[1] + layout2.anchor[1]) / 2
            move_distance = 0.05  # 固定错位距离
            layout1.anchor = (layout1.anchor[0], max(0.2, center_y - move_distance))
            layout2.anchor = (layout2.anchor[0], min(0.8, center_y + move_distance))

    def calculate_auto_scale(self, pet_size: Tuple[int, int], layout: PetLayout) -> float:
        """
        根据宠物尺寸和模板尺寸自动计算合适的缩放比例
        确保缩放后的图像能够适应模板，不会过大
        """
        pet_width, pet_height = pet_size
        
        # 计算缩放后的尺寸
        scaled_width = pet_width * layout.scale
        scaled_height = pet_height * layout.scale
        
        # 计算模板可用空间（考虑锚点位置）
        # 对于左右布局，每只宠物大约占模板宽度的40%
        # 对于上下布局，每只宠物大约占模板高度的40%
        if self.orientation == "landscape":
            # 横版：主要限制宽度
            max_width = self.template_width * 0.4  # 每只宠物最多占40%宽度
            max_height = self.template_height * 0.6  # 高度限制60%
        else:
            # 竖版：主要限制高度
            max_width = self.template_width * 0.6  # 宽度限制60%
            max_height = self.template_height * 0.4  # 每只宠物最多占40%高度
        
        # 计算需要的缩放比例
        scale_x = max_width / pet_width if pet_width > 0 else 1.0
        scale_y = max_height / pet_height if pet_height > 0 else 1.0
        
        # 取较小的缩放比例，确保两个方向都能适应
        auto_scale = min(scale_x, scale_y, layout.scale)
        
        # 限制最小和最大缩放
        auto_scale = max(0.3, min(1.0, auto_scale))
        
        return auto_scale

    def generate_layout(self, pet_count: int, pet_sizes: List[Tuple[int, int]]) -> List[PetLayout]:
        """生成完整的布局配置"""
        layouts = self.get_default_layouts(pet_count)
        
        # 根据实际图像尺寸自动调整缩放比例
        for i, (layout, pet_size) in enumerate(zip(layouts, pet_sizes)):
            auto_scale = self.calculate_auto_scale(pet_size, layout)
            layout.scale = auto_scale
        
        layouts = self.apply_anti_overlap_corrections(layouts, pet_sizes)
        return layouts


def create_multi_pet_layout(template_size: Tuple[int, int],
                          pet_count: int,
                          pet_sizes: List[Tuple[int, int]]) -> List[PetLayout]:
    """
    便捷函数：创建多宠物布局
    """
    engine = MultiPetLayoutEngine(template_size[0], template_size[1])
    return engine.generate_layout(pet_count, pet_sizes)