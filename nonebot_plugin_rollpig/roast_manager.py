import json
import random
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

import nonebot_plugin_localstore as store
from nonebot import get_plugin_config, logger
from openai import AsyncOpenAI

from .config import Config

# 获取配置
plugin_config = get_plugin_config(Config)

# 数据文件
ROAST_LIB_FILE = store.get_plugin_data_file("roast_library.json")

# ================= 默认兜底文案模板 =================
# {origin}: 原猪种, {food}: 目标美食
# {k}: 烤猪人(Killer), {v}: 被烤猪(Victim) 
DEFAULT_TEMPLATES = [
    "你本是一只无忧无虑的【{origin}】，却没能逃过命运的安排，含泪变成了【{food}】。",
    "看看你现在的样子！虽然不再是【{origin}】，但作为【{food}】的你，依然散发着诱人的光泽。",
]

BURNT_TEMPLATES = [
    "住手！它已经是一块【{origin}】了！在你无情的二次烧烤下，它彻底变成了黑漆漆的焦炭。",
    "你还不满足吗？这块可怜的【{origin}】已经被你烤得面目全非，化作了尘埃。",
]

# PvP 兜底模板 (带占位符)
PVP_TEMPLATES = [
    "【{k}】手法娴熟，手起刀落，将【{v}】（{origin}）做成了美味的【{food}】！",
    "【{v}】还没反应过来，就被【{k}】扔上了烤架。再见了，{origin}；你好，{food}。",
]

class RoastManager:
    def __init__(self):
        self.file = ROAST_LIB_FILE
        # 结构: { "origin_id": { "target_id": ["文案1", "文案2"] } }
        self.library: Dict[str, Dict[str, List[str]]] = self._load()
        
        self.client = None
        if plugin_config.rollpig_deepseek_key:
            self.client = AsyncOpenAI(
                api_key=plugin_config.rollpig_deepseek_key,
                base_url=plugin_config.rollpig_deepseek_base,
            )

    def _load(self) -> dict:
        if not self.file.exists(): return {}
        try: return json.loads(self.file.read_text("utf-8"))
        except Exception: return {}

    def _save(self):
        self.file.write_text(json.dumps(self.library, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_new_text(self, origin_id: str, target_id: str, text: str):
        if origin_id not in self.library: self.library[origin_id] = {}
        if target_id not in self.library[origin_id]: self.library[origin_id][target_id] = []
        if text not in self.library[origin_id][target_id]:
            self.library[origin_id][target_id].append(text)
            self._save()

    def _format_text(self, text: str, origin: str, food: str, killer: str = None, victim: str = None) -> str:
        """统一处理占位符替换"""
        # 基础替换
        res = text.replace("{origin}", origin).replace("{food}", food)
        # PvP 替换 (如果模板里有 {k}/{v} 但没传名字，用默认称呼兜底)
        k_name = killer if killer else "神秘人"
        v_name = victim if victim else "倒霉蛋"
        res = res.replace("{k}", k_name).replace("{v}", v_name)
        return res

    async def get_roast_text(self, origin_pig: dict, target_food: dict, 
                             operator_name: str = None, target_name: str = None) -> str:
        """
        获取烤猪文案
        :param operator_name: 凶手名字 (PvP模式必填)
        :param target_name: 受害者名字 (PvP模式必填)
        """
        o_id = origin_pig["id"]
        t_id = target_food["id"]
        o_name = origin_pig["name"]
        t_name = target_food["name"]

        # --- 场景 1: 焦炭 ---
        if t_id == "burnt":
            if plugin_config.rollpig_ai_enabled and self.client:
                try:
                    text = await self._call_ai(origin_pig, target_food, is_burnt=True)
                    return self._format_text(text, o_name, t_name)
                except: pass
            return random.choice(BURNT_TEMPLATES).format(origin=o_name)
        
        # --- 场景 2 & 3: PvP 和 PvE 通用缓存逻辑 ---
        # 区别在于：PvP 时，我们在库里查找/存储的是带 {k}{v} 占位符的模板
        
        # 为了区分“普通烤猪文案”和“烤群友文案”，我们在 target_id 后加个后缀区分
        # 例如: "bacon" (普通) vs "bacon_pvp" (烤群友)
        lookup_t_id = t_id + ("_pvp" if operator_name else "")
        
        # 1. 查缓存
        local_texts = self.library.get(o_id, {}).get(lookup_t_id, [])
        
        should_generate = (not local_texts) or \
                          (plugin_config.rollpig_ai_enabled and len(local_texts) < 3 and random.random() < 0.4)

        template_text = None
        
        if should_generate:
            try:
                # 调 AI 生成模板
                template_text = await self._call_ai(origin_pig, target_food, is_pvp=bool(operator_name))
                if template_text:
                    self._save_new_text(o_id, lookup_t_id, template_text)
            except Exception as e:
                logger.error(f"AI 生成失败: {e}")

        # 如果 AI 失败或没触发，用缓存
        if not template_text and local_texts:
            template_text = random.choice(local_texts)
            
        # 还是没有？用兜底
        if not template_text:
            if operator_name:
                template_text = random.choice(PVP_TEMPLATES)
            else:
                template_text = random.choice(DEFAULT_TEMPLATES)

        # 2. 渲染模板 (填入名字)
        return self._format_text(template_text, o_name, t_name, operator_name, target_name)

    async def _call_ai(self, origin_pig: dict, target_food: dict, is_pvp: bool = False, is_burnt: bool = False) -> str:
        
        # 1. 提取更适合吐槽的短特征
        origin_feature = origin_pig.get('description', origin_pig['analysis'][:20])
        
        # 基础约束
        base_req = "40字以内。直接输出内容，不要包含引号。"

        # === 场景 A: 焦炭 (Prompt 独立) ===
        if is_burnt:
            prompt = (
                f"有一块已经是美食的【{origin_pig['name']}】，被贪婪的人类再次烧烤成了【焦炭/致癌物】。"
                f"请写一段毒舌吐槽，嘲讽这种浪费食物的行为。{base_req} 风格：地狱笑话。"
            )

        # === 场景 B: 烤群友 PvP (必须用新版逻辑，含占位符) ===
        elif is_pvp:
            prompt = (
                f"场景：凶手把受害者（本体是【{origin_pig['name']}】，特征：{origin_feature}）"
                f"残忍地做成了【{target_food['name']}】。\n"
                f"请写一段解说，**必须使用以下占位符**：\n"
                f"1. 用 {{k}} 代表凶手名字\n"
                f"2. 用 {{v}} 代表受害者名字\n"
                f"示例：“{{k}} 狞笑着点起火，把可怜的 {{v}} 变成了滋滋作响的烤肉。”\n"
                f"要求：{base_req} 既要体现受害者({origin_pig['name']})的惨状，又要调侃凶手。风格幽默。"
            )

        # === 场景 C: 标准烤猪 PvE (回归旧版，带范例的高质量版) ===
        else:
            prompt = (
                f"现在进行一场【猪生终结吐槽大会】。\n"
                f"对象前世：【{origin_pig['name']}】（特征：{origin_feature}）\n"
                f"对象今生：【{target_food['name']}】\n\n"
                
                f"请写一段40字以内的神吐槽。必须严格遵守以下【对比公式】：\n"
                f"“曾经你(前世特征/地位)...如今你(死后状态/口感)...”\n\n"
                
                f"参考范例（学习这种语气）：\n"
                f"- “曾经你是丛林里的一方霸主野猪，如今却成为培根在我的平底锅里滋滋作响。别说，比起你的獠牙，还是你的油脂更迷人。”\n"
                f"- “生前你是个除了吃就是睡的大懒猪，没想到变成红烧肉后，这层肥膘反而成了精华，真是懒猪有懒福。”\n\n"
                
                f"要求：\n"
                f"1. 必须同时提到“生前”和“死后”的反差。\n"
                f"2. 风格要毒舌、幽默、带点地狱笑话，不要纯夸好吃。\n"
                f"3. 严禁出现“这道菜”、“这道美食”这种客套话，直接对话（用“你”）。\n"
                f"4. {base_req}"
            )

        response = await self.client.chat.completions.create(
            model=plugin_config.rollpig_model,
            messages=[
                {"role": "system", "content": "你是一个擅长黑色幽默、说话刻薄但好笑的脱口秀演员。"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content.strip().strip('"').replace("\n", "")

roast_manager = RoastManager()