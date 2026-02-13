import json
import random
import datetime
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Optional

from nonebot import on_command, require, get_bot
from nonebot.adapters.onebot.v11 import Event, MessageSegment, Message, GroupMessageEvent, Bot
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import Config  
from .roast_manager import roast_manager 

# 确保依赖插件先被 NoneBot 注册
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_localstore")

from nonebot_plugin_htmlrender import template_to_pic
import nonebot_plugin_localstore as store

# --- 引入 PIL ---
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ================= 配置与文案区域 =================

TOMORROW_TEXTS = [
    "天机不可泄露，但我闻到了一股红烧味...",
    "明日运势：大概率是一只特立独行的猪。",
    "不要问明天，明天你会变瘦（确信）。",
    "水晶球显示，明天你的猪槽里会有好吃的。",
    "明天的猪猪正在赶来的路上，据说是坐火箭来的。",
    "睡觉吧，梦里什么猪都有。",
    "根据星象，明天你可能会进化成更高级的形态。",
    "塔罗牌告诉我，明天的小猪身上有金色的光芒✨",
    "我夜观天象，明日宜养猪，忌烤猪。",
    "根据猪猪星历，明天是‘吃饱不愁’的黄道吉日。",
    "水晶猪猪球显示：明日财运与饲料量成正比。",
    "温馨提示：明天小猪的体重取决于你今天的投喂。"  
    "占卜结果显示：明天的你，猪格魅力+100%✨",
    "猪神悄悄告诉我：明天有人要‘猪’力全开哦。",
    "明日预告：你将解锁‘人间小猪’限定皮肤🐷",
    "根据猪猪星象，明天是你的‘变身日’，敬请期待。",
    "温馨提示：明天的你，请离厨房远一点🔪",
    "小道消息：明天你的床会格外有‘猪’引力。",
    "据说明天的你，看到饲料会莫名兴奋...",
    "预警：明天你可能会对泥坑产生特殊兴趣🕳️",
    "剧透一下：明天你的‘哼哼’声会异常悦耳。",
    "放心，明天的你绝对不会变成小猪佩奇...大概吧。",
    "我保证，明天的你肯定不会胖成球——才怪！",
    "据可靠情报，明天你绝不会想赖床...真的吗？",
    "明天的你：我肯定能管住嘴！🐷：不，你不能。",
    "预言：明天你会说自己‘猪’事顺利（物理）。",
    "明天的你，连自己都会觉得‘猪’么可爱。",
    "偷偷告诉你：明天你的鼻子会有点痒...",
    "剧透禁止！但我可以提示：明天记得带纸巾🧻",
    "明天的惊喜正在加载中...当前进度：99%（猪化）",
    "准备好迎接‘全新’的自己了吗？🐷",
    "明天的你，会重新思考‘猪生’的意义。",
    "猪生三问：我是谁？我在哪？明天我是什么猪？",
    "你将亲身体验：什么叫‘笨猪先飞’🐷✈️",
    "明天过后，你会深刻理解‘猪队友’这个词。",
    "预告：明天的你将获得‘猪’一样的睡眠质量。",
    "想提前知道？先学三声猪叫来听听🐷🐷🐷",
    "明天的你已经在我手里了，拿零食来换！",
    "如果现在告诉我你最喜欢的饲料，我就...还是不说。",
    "给你三个提示：哼哼、咕噜、呼...猜到了吗？",
    "明天的你正在发送好友申请，是否通过？✅"
]

# 拒绝烧烤的随机文案 (次数耗尽)
ROAST_LIMIT_TEXTS = [
    "手中的打火机没油了，明天再来吧。",
    "烧烤摊老板下班了，请明日赶早。",
    "再烤下去城管要来贴罚单了，休息一下吧。",
    "你的烧烤技能进入了冷却时间 (0:00 刷新)。",
    "这只猪看起来太可怜了，你决定今天放过它。",
]

FOOD_PIG_IDS = ["roasted-pig", "bacon", "mc_porkchop", "pork-skewer"]

# ========================================================

__plugin_meta__ = PluginMetadata(
    name="今天是什么小猪",
    description="抽取属于自己的小猪",
    usage="""
    🐷 基础指令：
    今日小猪 / 今天是什么小猪 - 抽取今天的命运之猪
    随机小猪 - 随机看一张猪图
    找猪 -  从 PigHub 模糊搜索猪猪图
    
    🔮 趣味指令：
    明日小猪 - 预测明天的猪猪运势
    昨日小猪 - 查看昨天抽到了什么
    今日烤猪 - 把今天的猪做成美食（慎用！）
    
    📊 统计指令：
    我的猪圈 - 查看解锁进度
    本周小猪 - 生成本周猪猪总结长图
    """,
    type="application",
    homepage="https://github.com/Felis2026/nonebot-plugin-rollpig",
    supported_adapters={"~onebot.v11"},
    config=Config,
)

PLUGIN_DIR = Path(__file__).parent
PIGINFO_PATH = PLUGIN_DIR / "resource" / "pig.json"
IMAGE_DIR = PLUGIN_DIR / "resource" / "image"
RES_DIR = PLUGIN_DIR / "resource"
DATA_FILE = store.get_plugin_data_file("pig_data.json")

pighub_images = []

# --- 核心数据管理类 ---
class PigDataManager:
    def __init__(self):
        self.file = DATA_FILE
        # 结构: { "history": {...}, "collection": {...}, "usage": {"date": {"user_id": count}} }
        self.data = self._load()

    def _load(self):
        if not self.file.exists():
            default_data = {"history": {}, "collection": {}, "usage": {}}
            self.file.write_text(json.dumps(default_data, ensure_ascii=False, indent=2), encoding="utf-8")
            return default_data
        try:
            return json.loads(self.file.read_text("utf-8"))
        except Exception:
            return {"history": {}, "collection": {}, "usage": {}}

    def save(self):
        self.file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_today_pig(self, user_id: str) -> Optional[dict]:
        today = datetime.date.today().isoformat()
        return self.data["history"].get(today, {}).get(user_id)

    def set_today_pig(self, user_id: str, pig_data: dict):
        today = datetime.date.today().isoformat()
        if today not in self.data["history"]:
            self.data["history"][today] = {}
        self.data["history"][today][user_id] = pig_data
        
        if "collection" not in self.data: self.data["collection"] = {}
        if user_id not in self.data["collection"]: self.data["collection"][user_id] = []
        if pig_data["id"] not in self.data["collection"][user_id]:
            self.data["collection"][user_id].append(pig_data["id"])
        self.save()

    def get_pig_by_date(self, user_id: str, date_str: str) -> Optional[dict]:
        return self.data["history"].get(date_str, {}).get(user_id)
    
    def get_user_collection(self, user_id: str) -> List[str]:
        return self.data.get("collection", {}).get(user_id, [])

    def check_roast_usage(self, user_id: str) -> bool:
        """检查今日是否还有烤群友次数 (True=有, False=无)"""
        today = datetime.date.today().isoformat()
        if "usage" not in self.data: self.data["usage"] = {}
        if today not in self.data["usage"]: self.data["usage"] = {today: {}} # 重置当天
        
        # 清理旧日期 usage (偷懒做法：只保留今天)
        if len(self.data["usage"]) > 1:
            self.data["usage"] = {today: {}}

        count = self.data["usage"][today].get(user_id, 0)
        return count < 1  # 限制 1 次

    def increment_roast_usage(self, user_id: str):
        today = datetime.date.today().isoformat()
        if today not in self.data["usage"]: self.data["usage"] = {today: {}}
        current = self.data["usage"][today].get(user_id, 0)
        self.data["usage"][today][user_id] = current + 1
        self.save()

    def clean_old_history(self, days_to_keep=14):
        today = datetime.date.today()
        dates_to_del = []
        for date_str in self.data["history"].keys():
            try:
                d = datetime.date.fromisoformat(date_str)
                if (today - d).days > days_to_keep:
                    dates_to_del.append(date_str)
            except ValueError:
                continue
        for d in dates_to_del: del self.data["history"][d]
        self.save()

data_manager = PigDataManager()

# --- 载入资源 ---
def load_resource_json(path, default):
    if not path.exists(): return default
    return json.loads(path.read_text("utf-8"))

PIG_LIST = load_resource_json(PIGINFO_PATH, [])

def find_image_file(pig_id: str) -> Path | None:
    exts = ["png", "jpg", "jpeg", "webp", "gif"]
    for ext in exts:
        file = IMAGE_DIR / f"{pig_id}.{ext}"
        if file.exists(): return file
    return None

def get_pig_by_id(pig_id: str) -> Optional[dict]:
    for p in PIG_LIST:
        if p["id"] == pig_id: return p
    return None

# ================= 指令处理区域 =================

# 1. 今日小猪
cmd_today = on_command("今天是什么小猪", aliases={"今日小猪"}, block=True)

@cmd_today.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    pig = data_manager.get_today_pig(user_id)
    
    if not pig:
        if not PIG_LIST:
            await cmd_today.finish("猪圈塌房了（数据缺失）")
            return
        pig = random.choice(PIG_LIST)
        data_manager.set_today_pig(user_id, pig)
        if random.randint(1, 20) == 1: data_manager.clean_old_history()

    await send_rendered_pig(cmd_today, event, pig)


# 2. 随机小猪
cmd_roll = on_command("随机小猪", block=True)

@cmd_roll.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()): 
    global pighub_images
    if not pighub_images:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://pighub.top/api/all-images")
                data = resp.json()
                if data and data.get("images"): pighub_images = data["images"]
        except Exception: pass
    
    if not pighub_images:
        await cmd_roll.finish("连不上 PigHub...")
        return
    
    text = args.extract_plain_text().strip()
    try: count = int(text) if text else 1
    except ValueError: count = 1
    count = max(1, min(count, 10)) 

    if count == 1:
        pig = random.choice(pighub_images)
        image_url = "https://pighub.top/data/" + pig["thumbnail"].split("/")[-1]
        await cmd_roll.finish(MessageSegment.reply(event.message_id) + MessageSegment.image(image_url))
        return

    messages = []
    for _ in range(count):
        pig = random.choice(pighub_images)
        image_url = "https://pighub.top/data/" + pig["thumbnail"].split("/")[-1]
        messages.append({
            "type": "node",
            "data": {
                "name": "随机小猪Bot", 
                "uin": event.self_id, 
                "content": Message(pig["title"]) + MessageSegment.image(image_url)
            }
        })
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=messages)
    else:
        await cmd_roll.finish("私聊暂不支持多张连发。")


# 2.5 找猪
cmd_find = on_command("找猪", aliases={"搜猪"}, block=True)

@cmd_find.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    global pighub_images
    if not pighub_images: await cmd_find.finish("请先发送「随机小猪」初始化！")

    keyword = args.extract_plain_text().strip()
    if not keyword: await cmd_find.finish("请加上关键词，如：/找猪 玩偶")

    found_pigs = [pig for pig in pighub_images if keyword.lower() in pig["title"].lower()]
    if not found_pigs: await cmd_find.finish(f"没找到叫「{keyword}」的猪。")

    messages = []
    count = min(len(found_pigs), 10) 
    for i in range(count):
        pig = found_pigs[i]
        image_url = "https://pighub.top/data/" + pig["thumbnail"].split("/")[-1]
        messages.append({
            "type": "node",
            "data": {
                "name": "搜猪小助手", "uin": event.self_id,
                "content": Message(pig["title"]) + MessageSegment.image(image_url)
            }
        })
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=messages)


# 3. 明日小猪
cmd_tmr = on_command("明日小猪", block=True)
@cmd_tmr.handle()
async def _(event: Event):
    await cmd_tmr.finish(MessageSegment.reply(event.message_id) + random.choice(TOMORROW_TEXTS))


# 4. 昨日小猪
cmd_yest = on_command("昨日小猪", block=True)
@cmd_yest.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    pig = data_manager.get_pig_by_date(user_id, yesterday)
    
    if not pig: await cmd_yest.finish(MessageSegment.reply(event.message_id) + "你昨天没抽猪。")
    msg = f"你昨天是一只【{pig['name']}】！"
    await send_rendered_pig(cmd_yest, event, pig, extra_text=msg)


# 5. 今日烤猪 (二次变身 + AI焦炭)
cmd_roast = on_command("今日烤猪", block=True)

@cmd_roast.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    original_pig = data_manager.get_today_pig(user_id)
    
    if not original_pig:
        await cmd_roast.finish(MessageSegment.reply(event.message_id) + "你连猪都不是，怎么烤？")
        return
    
    # 🔴 修改点：如果已经是食材，变成焦炭 (Burnt)
    if original_pig["id"] in FOOD_PIG_IDS:
        # 定义虚拟的焦炭猪
        burnt_pig = {"id": "burnt", "name": "焦炭", "description": "黑乎乎的一坨", "analysis": "再烤就着火了"}
        
        # 调用 AI 生成吐槽 (传入 is_burnt 逻辑由 target_id="burnt" 触发)
        text = await roast_manager.get_roast_text(original_pig, burnt_pig)
        
        # 发送纯文本吐槽 (焦炭就不发图了，或者你可以做张图)
        await cmd_roast.finish(MessageSegment.reply(event.message_id) + text)
        return
    
    food_id = random.choice(FOOD_PIG_IDS)
    food_pig_template = get_pig_by_id(food_id)
    if not food_pig_template: return

    roast_text = await roast_manager.get_roast_text(original_pig, food_pig_template)
    roasted_pig_data = food_pig_template.copy()
    roasted_pig_data["analysis"] = roast_text 
    
    await send_rendered_pig(cmd_roast, event, roasted_pig_data)


# 5.5 烤群友 (PvP 模式)
cmd_roast_member = on_command("烤群友", block=True)

@cmd_roast_member.handle()
async def _(bot: Bot, event: GroupMessageEvent): # 确保用 GroupMessageEvent 方便获取群名片
    attacker_id = str(event.user_id)
    
    # 1. 检查每日次数
    if not data_manager.check_roast_usage(attacker_id):
        await cmd_roast_member.finish(MessageSegment.reply(event.message_id) + random.choice(ROAST_LIMIT_TEXTS))
        return

    # 2. 提取目标 ID 和 名字
    target_id = None
    target_name = "群友" # 默认值

    # 优先检查回复
    if event.reply:
        target_id = str(event.reply.sender.user_id)
        target_name = event.reply.sender.card or event.reply.sender.nickname
    else:
        # 检查 At
        for seg in event.message:
            if seg.type == "at":
                target_id = str(seg.data["qq"])
                # 需要调 API 获取被艾特人的昵称，为了不阻塞，这里先暂时不获取，或者依赖 segment 里的显示
                # 简单处理：如果能从群成员列表拿最好，拿不到就用"对方"
                # 这里为了代码简洁，暂不额外调用 get_group_member_info，除非你想更完美
                target_name = "对方" 
                break
    
    # 尝试获取更准确的 target_name (如果 API 允许)
    if target_id:
        try:
            member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(target_id))
            target_name = member_info.get("card") or member_info.get("nickname")
        except:
            pass

    if not target_id:
        await cmd_roast_member.finish("请 At 或回复你要烤的群友！")
        return
    
    if target_id == attacker_id:
        await cmd_roast_member.finish("对自己好一点，别自焚。请发送「今日烤猪」。")
        return

    # 3. 检查目标是否是猪
    target_pig = data_manager.get_today_pig(target_id)
    if not target_pig:
        await cmd_roast_member.finish(MessageSegment.reply(event.message_id) + f"【{target_name}】今天还没抽猪，没法下嘴！")
        return
    
    if target_pig["id"] in FOOD_PIG_IDS:
        await cmd_roast_member.finish(MessageSegment.reply(event.message_id) + f"【{target_name}】已经被烤熟了，别鞭尸了。")
        return

    # 4. 消耗次数
    data_manager.increment_roast_usage(attacker_id)

    # 5. 概率判定
    roll = random.randint(1, 100)
    attacker_name = event.sender.card or event.sender.nickname

    # === 场景 A: 成功 (60%) ===
    if roll <= 60:
        food_id = random.choice(FOOD_PIG_IDS)
        food_pig_template = get_pig_by_id(food_id)
        
        # 核心修改：传入 target_name，并由 Manager 处理占位符
        text = await roast_manager.get_roast_text(
            target_pig, 
            food_pig_template, 
            operator_name=attacker_name,
            target_name=target_name  # 👈 传入受害者名字
        )
        
        # 渲染图片
        roasted_data = food_pig_template.copy()
        roasted_data["analysis"] = text
        await send_rendered_pig(cmd_roast_member, event, roasted_data)
        
    # === 场景 B: 逃脱 (30%) ===
    elif roll <= 90:
        escape_text = f"【{attacker_name}】拿着烤叉冲了过来，但【{target_name}】（{target_pig['name']}）身手敏捷，一个滑铲逃之夭夭！"
        await cmd_roast_member.finish(MessageSegment.reply(event.message_id) + escape_text)
        
    # === 场景 C: 反噬 (10%) ===
    else:
        # 检查凶手是不是猪
        attacker_pig = data_manager.get_today_pig(attacker_id)
        
        # 如果凶手自己是猪 -> 变成烤猪 (自作自受)
        if attacker_pig and attacker_pig["id"] not in FOOD_PIG_IDS:
            food_id = random.choice(FOOD_PIG_IDS)
            food_pig_template = get_pig_by_id(food_id)
            
            # 这里其实也可以传 operator_name=None 把它当成普通烤猪，或者设计特殊的“反噬Prompt”
            # 为了简单，当作普通烤猪处理
            text = await roast_manager.get_roast_text(attacker_pig, food_pig_template)
            fail_text = f"偷鸡不成蚀把米！【{attacker_name}】抓猪失败，反倒把自己摔进了火坑！\n\n" + text
            
            roasted_data = food_pig_template.copy()
            roasted_data["analysis"] = fail_text
            await send_rendered_pig(cmd_roast_member, event, roasted_data)
            
        # 如果凶手是人/已经是烤猪 -> 变成通用“烤人排”
        else:
            fail_text = f"【{attacker_name}】玩火自焚！不仅没烤到【{target_name}】，还把自己的眉毛烧没了。这就是贪吃的代价！"
            await cmd_roast_member.finish(MessageSegment.reply(event.message_id) + fail_text)


# 6. 我的猪圈
cmd_sty = on_command("我的猪圈", aliases={"我的小猪"}, block=True)

@cmd_sty.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    collection = data_manager.get_user_collection(user_id)
    total_pigs = len(PIG_LIST)
    user_count = len(collection)
    
    if user_count == 0:
        await cmd_sty.finish(MessageSegment.reply(event.message_id) + "你的猪圈空空如也！")
        return

    percent = int((user_count / total_pigs) * 100)
    msg = (
        f"【我的猪圈统计】\n"
        f"👑 猪圈主人：{event.sender.card or event.sender.nickname}\n"
        f"📦 已收集：{user_count} / {total_pigs} 只\n"
        f"📈 收藏率：{percent}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"继续加油，争取成为猪王！"
    )
    await cmd_sty.finish(MessageSegment.reply(event.message_id) + msg)


# 7. 本周小猪
cmd_week = on_command("本周小猪", block=True)

@cmd_week.handle()
async def _(event: Event):
    if not HAS_PIL: await cmd_week.finish("Bot 未安装 PIL 库。")

    user_id = str(event.user_id)
    today = datetime.date.today()
    
    images_to_merge = []
    texts = []
    
    for i in range(7):
        d = today - datetime.timedelta(days=(6-i))
        d_str = d.isoformat()
        pig = data_manager.get_pig_by_date(user_id, d_str)
        if pig:
            img_file = find_image_file(pig["id"])
            if img_file:
                images_to_merge.append(img_file)
                texts.append(f"{d.strftime('%m-%d')}\n{pig['name']}")
        
    if not images_to_merge:
        await cmd_week.finish(MessageSegment.reply(event.message_id) + "你这周还没抽过猪呢！")
        return

    msg = None
    try:
        item_w, item_h = 150, 150
        padding = 20
        total_w = (item_w + padding) * len(images_to_merge) + padding
        total_h = item_h + 80
        
        canvas = PILImage.new("RGB", (total_w, total_h), (255, 255, 255))
        for idx, (img_path, txt) in enumerate(zip(images_to_merge, texts)):
            img = PILImage.open(img_path).convert("RGBA")
            img = img.resize((item_w, item_h))
            x = padding + idx * (item_w + padding)
            y = padding
            canvas.paste(img, (x, y), img)
            
        from io import BytesIO
        output = BytesIO()
        canvas.save(output, format="PNG")
        
        msg = MessageSegment.reply(event.message_id) + \
              f"你这周变了 {len(images_to_merge)} 次猪！" + \
              MessageSegment.image(output.getvalue())
    except Exception:
        await cmd_week.finish("生成图片失败。")
        return

    await cmd_week.finish(msg)   


# --- 辅助渲染函数 ---
async def send_rendered_pig(matcher, event, pig_data: dict, extra_text: str = ""):
    pig_id = pig_data.get("id", "")
    avatar_file = find_image_file(pig_id)
    avatar_uri = avatar_file.as_uri() if avatar_file else ""
  
    pic = None
    try:
        pic = await template_to_pic(
            template_path=RES_DIR,
            template_name="template.html",
            templates={
                "avatar": avatar_uri,
                "name": pig_data["name"],
                "desc": pig_data["description"],
                "analysis": pig_data["analysis"],
            },
        )
    except Exception:
        await matcher.finish("图片生成失败。")
        return

    msg = MessageSegment.reply(event.message_id)
    if extra_text: msg += extra_text
    msg += MessageSegment.image(pic)
    await matcher.finish(msg)