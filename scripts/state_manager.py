# -*- coding: utf-8 -*-
"""
状态管理器：管理多宠物项目的状态文件
支持从单宠物结构平滑迁移到多宠物结构
"""
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PetConfig:
    """单只宠物的配置"""
    id: str
    image: str
    crop_mode: str = "head"
    scale: float = 0.9
    anchor: tuple = (0.5, 0.55)  # (x, y) 相对坐标


@dataclass
class MultiPetState:
    """多宠物状态"""
    session_id: str
    pets: List[PetConfig]
    template: Optional[str] = None
    text_content: Optional[str] = None
    text_style: Optional[Dict[str, Any]] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class StateManager:
    """状态管理器"""

    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)

    def _get_state_path(self, session_id: str) -> str:
        """获取状态文件路径"""
        return os.path.join(self.sessions_dir, session_id, "state.json")

    def _ensure_session_dir(self, session_id: str):
        """确保会话目录存在"""
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)

    def load_state(self, session_id: str) -> MultiPetState:
        """加载状态，支持从旧格式迁移"""
        state_path = self._get_state_path(session_id)

        if not os.path.exists(state_path):
            # 新建状态
            return MultiPetState(session_id=session_id, pets=[])

        with open(state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否为旧的单宠物格式
        if "pet" in data and "pets" not in data:
            # 迁移到新格式
            old_pet = data["pet"]
            new_pet = PetConfig(
                id="pet_a",
                image=old_pet.get("image", ""),
                crop_mode=old_pet.get("crop_mode", "head"),
                scale=old_pet.get("scale", 0.9),
                anchor=tuple(old_pet.get("anchor", [0.5, 0.55]))
            )
            data["pets"] = [asdict(new_pet)]
            del data["pet"]

        # 转换为MultiPetState
        pets = []
        for pet_data in data.get("pets", []):
            pet = PetConfig(**pet_data)
            # 确保anchor是tuple
            if isinstance(pet.anchor, list):
                pet.anchor = tuple(pet.anchor)
            pets.append(pet)

        return MultiPetState(
            session_id=session_id,
            pets=pets,
            template=data.get("template"),
            text_content=data.get("text_content"),
            text_style=data.get("text_style"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )

    def save_state(self, state: MultiPetState):
        """保存状态"""
        self._ensure_session_dir(state.session_id)
        state_path = self._get_state_path(state.session_id)

        # 更新时间戳
        state.updated_at = datetime.now().isoformat()

        # 转换为字典（处理tuple）
        data = asdict(state)
        for pet in data["pets"]:
            if isinstance(pet["anchor"], tuple):
                pet["anchor"] = list(pet["anchor"])

        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_pet(self, session_id: str, image_path: str, crop_mode: str = "head") -> MultiPetState:
        """添加一只宠物"""
        state = self.load_state(session_id)

        # 生成新宠物ID
        existing_ids = {pet.id for pet in state.pets}
        new_id = f"pet_{chr(97 + len(state.pets))}"  # pet_a, pet_b, pet_c...

        # 默认配置
        new_pet = PetConfig(
            id=new_id,
            image=image_path,
            crop_mode=crop_mode,
            scale=0.9
        )

        state.pets.append(new_pet)
        self.save_state(state)
        return state

    def update_pet_layout(self, session_id: str, pet_id: str,
                         anchor: Optional[tuple] = None,
                         scale: Optional[float] = None) -> MultiPetState:
        """更新指定宠物的布局"""
        state = self.load_state(session_id)

        for pet in state.pets:
            if pet.id == pet_id:
                if anchor is not None:
                    pet.anchor = anchor
                if scale is not None:
                    pet.scale = scale
                break

        self.save_state(state)
        return state

    def set_template(self, session_id: str, template_path: str) -> MultiPetState:
        """设置模板"""
        state = self.load_state(session_id)
        state.template = template_path
        self.save_state(state)
        return state

    def set_text(self, session_id: str, content: str, style: Optional[Dict] = None) -> MultiPetState:
        """设置文字"""
        state = self.load_state(session_id)
        state.text_content = content
        if style:
            state.text_style = style
        self.save_state(state)
        return state

    def get_pet_count(self, session_id: str) -> int:
        """获取宠物数量"""
        state = self.load_state(session_id)
        return len(state.pets)

    def is_multi_pet(self, session_id: str) -> bool:
        """判断是否为多宠物模式"""
        return self.get_pet_count(session_id) > 1