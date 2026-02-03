# -*- coding: utf-8 -*-
"""
多宠物编排器：识别多宠物意图并协调完整工作流
支持从单宠物平滑过渡到多宠物模式
用法: python run_multi_pet_orchestrator.py <session_id> <image1> [image2] [--instruction "指令"]
"""
import argparse
import os
import sys
import re
from typing import List, Dict, Any, Optional

# 确保脚本目录和项目根目录在 path 中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from run_multi_pet_matting import run_multi_pet_matting
from run_multi_pet_composition import run_multi_pet_composition
from run_text_style_adjustment import run_text_adjustment


class MultiPetIntentDetector:
    """多宠物意图识别器"""

    MULTI_PET_KEYWORDS = [
        "两只宠物", "两个宠物", "两张照片", "两个图片",
        "合照", "一起", "一左一右", "并排",
        "多只", "多张", "多个", "宠物们",
        "第一只", "第二只", "左边", "右边",
        "上面", "下面", "中间"
    ]

    ADJUSTMENT_PATTERNS = [
        # 位置调整
        r"(左边|右边|上面|下面|中间)(?:那只|的)?(?:宠物)?(?:往|移到|移至|移动到)(.+)",
        r"(?:把)?(.+?)(?:宠物)?(?:往|移到|移至|移动到)(.+)",
        # 大小调整
        r"(左边|右边|上面|下面|中间)(?:那只|的)?(?:宠物)?(?:大|小)(?:一点)?",
        r"(?:让)?(.+?)(?:宠物)?(?:大|小)(?:一点)?",
        # 具体位置
        r"(?:把)?(.+?)(?:宠物)?放在(.+)",
    ]

    def detect_multi_pet_intent(self, instruction: str, current_pet_count: int) -> Dict[str, Any]:
        """
        检测多宠物相关意图
        返回意图分析结果
        """
        result = {
            "intent": "single_pet",  # 默认单宠物
            "pet_count": current_pet_count,
            "target_pet": None,
            "action": None,
            "parameters": {}
        }

        # 检查是否包含多宠物关键词
        has_multi_keywords = any(keyword in instruction for keyword in self.MULTI_PET_KEYWORDS)

        # 检查是否提到第二张图片
        mentions_second_image = "第二" in instruction or "另一" in instruction

        # 检查位置关系词
        position_words = ["左边", "右边", "上面", "下面", "中间", "旁边"]
        has_position_relation = any(word in instruction for word in position_words)

        # 判断是否为多宠物意图
        if has_multi_keywords or mentions_second_image or has_position_relation:
            result["intent"] = "multi_pet_layout"
            result["pet_count"] = max(current_pet_count, 2)  # 至少2只

        # 检查是否为单独调整意图
        for pattern in self.ADJUSTMENT_PATTERNS:
            match = re.search(pattern, instruction)
            if match:
                result["intent"] = "update_pet_layout"
                # 解析目标宠物
                target_desc = match.group(1)
                if "左" in target_desc:
                    result["target_pet"] = "pet_a"  # 假设pet_a是左边的
                elif "右" in target_desc:
                    result["target_pet"] = "pet_b"  # 假设pet_b是右边的
                elif "上" in target_desc:
                    result["target_pet"] = "pet_a"  # 假设pet_a是上边的
                elif "下" in target_desc:
                    result["target_pet"] = "pet_b"  # 假设pet_b是下边的

                # 解析动作
                if "大" in instruction:
                    result["action"] = "scale_up"
                    result["parameters"]["scale"] = 1.1
                elif "小" in instruction:
                    result["action"] = "scale_down"
                    result["parameters"]["scale"] = 0.9
                elif "移" in instruction or "放" in instruction:
                    result["action"] = "move"
                    # 这里可以进一步解析具体位置

                break

        return result


class MultiPetOrchestrator:
    """多宠物编排器"""

    def __init__(self):
        self.state_manager = StateManager()
        self.intent_detector = MultiPetIntentDetector()

    def orchestrate(self, session_id: str, image_paths: List[str],
                   instruction: Optional[str] = None,
                   template_path: Optional[str] = None) -> str:
        """
        多宠物编排主流程
        """
        print(f"开始多宠物编排: session={session_id}, images={len(image_paths)}")

        # 1. 初始化或加载状态
        state = self.state_manager.load_state(session_id)

        # 2. 添加宠物到状态
        for image_path in image_paths:
            if not any(pet.image == image_path for pet in state.pets):
                state = self.state_manager.add_pet(session_id, image_path)

        # 3. 分析指令意图
        intent_analysis = self.intent_detector.detect_multi_pet_intent(
            instruction or "", len(state.pets)
        )

        print(f"意图分析: {intent_analysis}")

        # 4. 根据意图执行相应操作
        if intent_analysis["intent"] == "multi_pet_layout":
            return self._handle_multi_pet_layout(session_id, template_path)

        elif intent_analysis["intent"] == "update_pet_layout":
            return self._handle_pet_adjustment(session_id, intent_analysis)

        else:
            # 单宠物流程
            return self._handle_single_pet_flow(session_id, template_path)

    def _handle_multi_pet_layout(self, session_id: str, template_path: Optional[str]) -> str:
        """处理多宠物布局"""
        print("执行多宠物布局流程")

        # 设置模板（如果提供）
        if template_path:
            self.state_manager.set_template(session_id, template_path)

        # 执行抠图
        extracted_paths = run_multi_pet_matting(session_id)

        # 执行合成
        design_path = run_multi_pet_composition(session_id)

        return design_path

    def _handle_pet_adjustment(self, session_id: str, intent_analysis: Dict[str, Any]) -> str:
        """处理宠物调整"""
        print(f"执行宠物调整: {intent_analysis}")

        target_pet = intent_analysis.get("target_pet")
        action = intent_analysis.get("action")
        params = intent_analysis.get("parameters", {})

        if target_pet and action:
            if action == "scale_up" and "scale" in params:
                # 获取当前scale并放大
                state = self.state_manager.load_state(session_id)
                current_scale = next((pet.scale for pet in state.pets if pet.id == target_pet), 0.9)
                new_scale = min(current_scale * params["scale"], 1.5)  # 最大1.5倍
                self.state_manager.update_pet_layout(session_id, target_pet, scale=new_scale)

            elif action == "scale_down" and "scale" in params:
                # 获取当前scale并缩小
                state = self.state_manager.load_state(session_id)
                current_scale = next((pet.scale for pet in state.pets if pet.id == target_pet), 0.9)
                new_scale = max(current_scale * params["scale"], 0.5)  # 最小0.5倍
                self.state_manager.update_pet_layout(session_id, target_pet, scale=new_scale)

        # 重新合成
        return run_multi_pet_composition(session_id)

    def _handle_single_pet_flow(self, session_id: str, template_path: Optional[str]) -> str:
        """处理单宠物流程（向后兼容）"""
        print("执行单宠物流程")

        state = self.state_manager.load_state(session_id)

        if len(state.pets) == 1:
            # 单宠物：使用原有流程
            from run_pet_image_matting import run_matting
            from run_multi_pet_matting import make_square_1to1

            pet = state.pets[0]
            session_dir = os.path.join("sessions", session_id)
            extracted_path = os.path.join(session_dir, "extracted.png")

            # 抠图
            run_matting(pet.image, pet.crop_mode, extracted_path)
            
            # 调整为1:1比例（正方形）
            print("  调整为1:1比例...")
            try:
                extracted_path = make_square_1to1(extracted_path, extracted_path)
                print("  已调整为1:1比例")
            except Exception as e:
                print(f"  1:1调整失败: {e}，使用原图")

            # 合成（简化版）
            if template_path:
                from PIL import Image
                template = Image.open(template_path).convert("RGBA")
                extracted = Image.open(extracted_path).convert("RGBA")

                # 简单居中合成
                result = Image.new("RGBA", template.size, (0, 0, 0, 0))
                result.paste(template, (0, 0))

                # 计算居中位置
                x = (template.width - extracted.width) // 2
                y = (template.height - extracted.height) // 2
                result.paste(extracted, (x, y), extracted)

                design_path = os.path.join(session_dir, "design.png")
                result.save(design_path)
                return design_path

        return ""


def main():
    parser = argparse.ArgumentParser(description="多宠物编排器")
    parser.add_argument("session_id", help="会话ID")
    parser.add_argument("images", nargs="+", help="宠物图片路径")
    parser.add_argument("--instruction", "-i", default="", help="用户指令")
    parser.add_argument("--template", "-t", help="模板路径")

    args = parser.parse_args()

    try:
        orchestrator = MultiPetOrchestrator()
        result_path = orchestrator.orchestrate(
            session_id=args.session_id,
            image_paths=args.images,
            instruction=args.instruction,
            template_path=args.template
        )

        if result_path:
            print(f"编排完成，结果: {result_path}")
        else:
            print("编排完成，无输出")

    except Exception as e:
        print(f"编排失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()