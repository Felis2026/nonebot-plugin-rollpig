import json
import random
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

import nonebot_plugin_localstore as store
from nonebot import get_plugin_config, logger
from openai import AsyncOpenAI  # 需要 pip install openai

from .config import Config

# 获取配置
plugin_config = get_plugin_config(Config)

# 数据文件
ROAST_LIB_FILE = store.get_plugin_data_file("roast_library.json")

# ================= 默认兜底文案模板 =================
# {origin} = 原本的猪名, {food} = 变成的美食名
DEFAULT_TEMPLATES = [
    "你本是一只无忧无虑的【{origin}】，却没能逃过命运的安排，含泪变成了【{food}】。",
    "看看你现在的样子！虽然不再是【{origin}】，但作为【{food}】的你，依然散发着诱人的光泽。",
    "再见了【{origin}】，你好【{food}】。虽然换了个形态，但你依然是大家的最爱（指食欲上）。",
    "从【{origin}】到【{food}】，只需要一把孜然和一点点火候。这不仅是猪生的蜕变，更是美味的升华。",
    "很遗憾，作为【{origin}】的生涯结束了。但作为【{food}】，你的统御才刚刚开始！",
]

class RoastManager:
    def __init__(self):
        self.file = ROAST_LIB_FILE
        # 结构: { "origin_id": { "target_id": ["文案1", "文案2"] } }
        self.library: Dict[str, Dict[str, List[str]]] = self._load()
        
        # 初始化 OpenAI 客户端 (如果配置了Key)
        self.client = None
        if plugin_config.rollpig_deepseek_key:
            self.client = AsyncOpenAI(
                api_key=plugin_config.rollpig_deepseek_key,
                base_url=plugin_config.rollpig_deepseek_base,
                # 如果需要代理，可以在这里配置 http_client
            )

    def _load(self) -> dict:
        if not self.file.exists():
            return {}
        try:
            return json.loads(self.file.read_text("utf-8"))
        except Exception as e:
            logger.error(f"加载烤猪文案库失败: {e}")
            return {}

    def _save(self):
        self.file.write_text(json.dumps(self.library, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_local_text(self, origin_id: str, target_id: str) -> Optional[str]:
        """尝试获取本地缓存的文案"""
        targets = self.library.get(origin_id, {})
        texts = targets.get(target_id, [])
        if texts:
            return random.choice(texts)
        return None

    def _save_new_text(self, origin_id: str, target_id: str, text: str):
        """保存新生成的文案"""
        if origin_id not in self.library:
            self.library[origin_id] = {}
        if target_id not in self.library[origin_id]:
            self.library[origin_id][target_id] = []
        
        # 避免重复
        if text not in self.library[origin_id][target_id]:
            self.library[origin_id][target_id].append(text)
            self._save()

    def _get_default_text(self, origin_name: str, food_name: str) -> str:
        """获取默认模板文案"""
        tmpl = random.choice(DEFAULT_TEMPLATES)
        return tmpl.format(origin=origin_name, food=food_name)

    async def get_roast_text(self, origin_pig: dict, target_food: dict) -> str:
        o_id = origin_pig["id"]
        t_id = target_food["id"]
        
        # 1. 获取本地缓存列表
        local_texts = self.library.get(o_id, {}).get(t_id, [])
        
        # 🎲 概率逻辑：
        # 如果本地没有(必要生成) OR (有AI开关 AND 本地少于3条 AND 30%概率触发新增)
        should_generate_new = (not local_texts) or \
                              (plugin_config.rollpig_ai_enabled and len(local_texts) < 3 and random.random() < 0.3)

        if should_generate_new:
            try:
                # 调 AI 生成
                text = await self._call_ai(origin_pig, target_food)
                if text:
                    self._save_new_text(o_id, t_id, text)
                    return text
            except:
                # 失败了如果本地有货，就用本地的
                if local_texts: return random.choice(local_texts)

        # 2. 否则使用本地缓存
        if local_texts:
            return random.choice(local_texts)
            
        # 3. 兜底
        return self._get_default_text(origin_pig["name"], target_food["name"])

    async def _call_ai(self, origin_pig: dict, target_food: dict) -> Optional[str]:
        """调用 DeepSeek API"""
        prompt = (
            f"你是一个幽默且带点地狱笑话风格的美食解说。现在有一只【{origin_pig['name']}】"
            f"（原本的描述是：{origin_pig['analysis']}），它不幸（或幸运）地被做成了【{target_food['name']}】。"
            f"请写一段40字以内的评语，既要提到它原本的特征，又要描述它现在的美味或状态。"
            f"要求：口语化，生动有趣，不要太残忍，要好笑。"
        )

        try:
            response = await self.client.chat.completions.create(
                model=plugin_config.rollpig_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            content = response.choices[0].message.content
            # 简单的清洗，去掉可能的引号
            return content.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"DeepSeek API 请求错误: {e}")
            raise e

roast_manager = RoastManager()