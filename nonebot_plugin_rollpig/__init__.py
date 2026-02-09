import json
import random
import datetime
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Optional

from nonebot import on_command, require, get_bot
from nonebot.adapters.onebot.v11 import Event, MessageSegment, Message, GroupMessageEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import Config  
from .roast_manager import roast_manager 

# 确保依赖插件先被 NoneBot 注册
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_localstore")

from nonebot_plugin_htmlrender import template_to_pic
import nonebot_plugin_localstore as store

# --- 引入 PIL 用于合成“本周小猪”长图 ---
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("未检测到 PIL 库，'本周小猪' 图片合成功能将不可用")

# ================= 配置与文案区域 (可编辑) =================

# 🔮 明日小猪 - 预言文案池
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

# 🍖 今日烤猪 - 随机变成的“美食猪”ID列表
# 对应 pig.json 中的 id
FOOD_PIG_IDS = ["roasted-pig", "bacon", "mc_porkchop", "pork-skewer"]

# ========================================================

# 插件配置页
__plugin_meta__ = PluginMetadata(
    name="今天是什么小猪",
    description="抽取属于自己的小猪",
    usage="""
    🐷 基础指令：
    今日小猪 / 今天是什么小猪 - 抽取今天的命运之猪
    随机小猪 - 随机看一张猪图
    
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

# 插件目录
PLUGIN_DIR = Path(__file__).parent
PIGINFO_PATH = PLUGIN_DIR / "resource" / "pig.json"
IMAGE_DIR = PLUGIN_DIR / "resource" / "image"
RES_DIR = PLUGIN_DIR / "resource"

# 数据文件 (更改为 pig_data.json)
DATA_FILE = store.get_plugin_data_file("pig_data.json")

# 缓存 PigHub 图片列表
pighub_images = []

# --- 核心数据管理类 ---
class PigDataManager:
    def __init__(self):
        self.file = DATA_FILE
        # 数据结构:
        # {
        #   "history": { "2023-10-01": { "user_id": {pig_data} } },  # 按日期存储历史
        #   "collection": { "user_id": ["pig_id_1", "pig_id_2"] }   # 用户图鉴 (Set转List存储)
        # }
        self.data = self._load()

    def _load(self):
        if not self.file.exists():
            default_data = {"history": {}, "collection": {}}
            self.file.write_text(json.dumps(default_data, ensure_ascii=False, indent=2), encoding="utf-8")
            return default_data
        try:
            return json.loads(self.file.read_text("utf-8"))
        except Exception as e:
            logger.error(f"加载猪猪数据失败: {e}")
            return {"history": {}, "collection": {}}

    def save(self):
        self.file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_today_pig(self, user_id: str) -> Optional[dict]:
        today = datetime.date.today().isoformat()
        return self.data["history"].get(today, {}).get(user_id)

    def set_today_pig(self, user_id: str, pig_data: dict):
        today = datetime.date.today().isoformat()
        if today not in self.data["history"]:
            self.data["history"][today] = {}
        
        # 1. 存入今日历史
        self.data["history"][today][user_id] = pig_data
        
        # 2. 存入用户图鉴
        if "collection" not in self.data:
            self.data["collection"] = {}
        if user_id not in self.data["collection"]:
            self.data["collection"][user_id] = []
        
        # 避免重复添加 ID
        pig_id = pig_data["id"]
        if pig_id not in self.data["collection"][user_id]:
            self.data["collection"][user_id].append(pig_id)
            
        self.save()

    def get_pig_by_date(self, user_id: str, date_str: str) -> Optional[dict]:
        return self.data["history"].get(date_str, {}).get(user_id)
    
    def get_user_collection(self, user_id: str) -> List[str]:
        return self.data.get("collection", {}).get(user_id, [])

    def clean_old_history(self, days_to_keep=14):
        """清理过久的历史记录，防止文件膨胀，保留14天"""
        today = datetime.date.today()
        dates_to_del = []
        for date_str in self.data["history"].keys():
            try:
                d = datetime.date.fromisoformat(date_str)
                if (today - d).days > days_to_keep:
                    dates_to_del.append(date_str)
            except ValueError:
                continue
        
        if dates_to_del:
            for d in dates_to_del:
                del self.data["history"][d]
            self.save()
            logger.info(f"已清理 {len(dates_to_del)} 天的旧猪猪记录")

data_manager = PigDataManager()

# --- 载入资源 ---
def load_resource_json(path, default):
    if not path.exists():
        logger.error(f"资源文件缺失: {path}")
        return default
    return json.loads(path.read_text("utf-8"))

PIG_LIST = load_resource_json(PIGINFO_PATH, [])
if not PIG_LIST:
    logger.error("猪圈空荡荡，请检查 resource/pig.json ！")

def find_image_file(pig_id: str) -> Path | None:
    exts = ["png", "jpg", "jpeg", "webp", "gif"]
    for ext in exts:
        file = IMAGE_DIR / f"{pig_id}.{ext}"
        if file.exists():
            return file
    return None

def get_pig_by_id(pig_id: str) -> Optional[dict]:
    for p in PIG_LIST:
        if p["id"] == pig_id:
            return p
    return None

# ================= 指令处理区域 =================

# 1. 今日小猪
cmd_today = on_command("今天是什么小猪", aliases={"今日小猪"}, block=True)

@cmd_today.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    
    # 尝试获取今日记录
    pig = data_manager.get_today_pig(user_id)
    
    # 如果没抽过，随机抽一只
    if not pig:
        if not PIG_LIST:
            await cmd_today.finish("猪圈塌房了（数据缺失），快联系管理员！")
            return
        pig = random.choice(PIG_LIST)
        data_manager.set_today_pig(user_id, pig)
        
        # 顺便清理一下旧数据
        if random.randint(1, 20) == 1:
            data_manager.clean_old_history()

    # 渲染并发送（带回复）
    await send_rendered_pig(cmd_today, event, pig)


# 2. 随机小猪 (PigHub) - 异步优化版
cmd_roll = on_command("随机小猪", block=True)

@cmd_roll.handle()
async def _(event: Event):
    global pighub_images
    
    # 如果缓存为空，异步获取
    if not pighub_images:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://pighub.top/api/all-images")
                data = resp.json()
                if data and data.get("images"):
                    pighub_images = data["images"]
                    logger.success(f"成功从 PigHub 缓存 {len(pighub_images)} 头猪猪")
                else:
                    logger.warning("PigHub 返回为空")
        except Exception as e:
            logger.error(f"PigHub 请求失败: {e}")
    
    if not pighub_images:
        await cmd_roll.finish("连不上 PigHub，猪猪离家出走了...")
        return

    pig = random.choice(pighub_images)
    image_url = "https://pighub.top/data/" + pig["thumbnail"].split("/")[-1]
    
    # 使用回复发送
    await cmd_roll.finish(MessageSegment.reply(event.message_id) + MessageSegment.image(image_url))


# 3. 明日小猪 (预言)
cmd_tmr = on_command("明日小猪", aliases={"明天是什么小猪"}, block=True)

@cmd_tmr.handle()
async def _(event: Event):
    text = random.choice(TOMORROW_TEXTS)
    await cmd_tmr.finish(MessageSegment.reply(event.message_id) + text)


# 4. 昨日小猪 (回顾)
cmd_yest = on_command("昨日小猪", aliases={"昨天是什么小猪"}, block=True)

@cmd_yest.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    pig = data_manager.get_pig_by_date(user_id, yesterday)
    
    if not pig:
        await cmd_yest.finish(MessageSegment.reply(event.message_id) + "你昨天还没有出生呢（并没有抽过猪）。")
    else:
        # 构造特殊文案：只发文字太单调，还是发图比较好
        msg = f"你昨天是一只【{pig['name']}】！"
        await send_rendered_pig(cmd_yest, event, pig, extra_text=msg)


# 5. 今日烤猪 (二次变身)
cmd_roast = on_command("今日烤猪", block=True)

@cmd_roast.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    original_pig = data_manager.get_today_pig(user_id)
    
    # 1. 检查是否抽过
    if not original_pig:
        await cmd_roast.finish(MessageSegment.reply(event.message_id) + "你连猪都不是，怎么烤？先发送「今日小猪」抽取身份吧。")
        return
    
    # 2. 检查是否已经是食材 (禁止套娃)
    if original_pig["id"] in FOOD_PIG_IDS:
        msg = MessageSegment.reply(event.message_id) + \
              f"住手！你已经是【{original_pig['name']}】了！再烤就变成焦炭了... (拒绝二次加工)"
        await cmd_roast.finish(msg)
        return
    
    # 3. 随机选一个美食形态
    food_id = random.choice(FOOD_PIG_IDS)
    food_pig_template = get_pig_by_id(food_id)
    
    if not food_pig_template:
        await cmd_roast.finish("烤炉坏了（找不到美食猪数据）。")
        return

    # --- 核心修改：使用 Manager 获取文案 ---
    # 提示：如果是 AI 生成，可能需要 1-2 秒，可以发个提示（可选）
    # await cmd_roast.send("🔥 正在生火...") 
    
    roast_text = await roast_manager.get_roast_text(original_pig, food_pig_template)

    # 4. 生成临时的“烤熟”数据用于渲染
    roasted_pig_data = food_pig_template.copy()
    roasted_pig_data["analysis"] = roast_text # 直接覆盖 analysis
    
    await send_rendered_pig(cmd_roast, event, roasted_pig_data)


# 6. 我的猪圈 (图鉴统计)
cmd_sty = on_command("我的猪圈", aliases={"我的小猪"}, block=True)

@cmd_sty.handle()
async def _(event: Event):
    user_id = str(event.user_id)
    collection = data_manager.get_user_collection(user_id)
    total_pigs = len(PIG_LIST)
    user_count = len(collection)
    
    if user_count == 0:
        await cmd_sty.finish(MessageSegment.reply(event.message_id) + "你的猪圈空空如也，快去抽一只吧！")
        return

    # 计算进度
    percent = int((user_count / total_pigs) * 100)
    
    msg = (
        f"【我的猪圈统计】\n"
        f"━━━━━━━━━━━━━━\n"
        f"👑 猪圈主人：{event.sender.card or event.sender.nickname}\n"
        f"📦 已收集：{user_count} / {total_pigs} 只\n"
        f"📈 收藏率：{percent}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"继续加油，争取成为猪王！"
    )
    # TODO: 未来可以升级成生成一张点亮图标的图片
    await cmd_sty.finish(MessageSegment.reply(event.message_id) + msg)


# 7. 本周小猪 (PIL 合成)
cmd_week = on_command("本周小猪", block=True)

@cmd_week.handle()
async def _(event: Event):
    if not HAS_PIL:
        await cmd_week.finish("Bot 未安装 PIL 库，无法生成长图。")
        return

    user_id = str(event.user_id)
    today = datetime.date.today()
    
    # 收集过去 7 天的图片路径
    images_to_merge = []
    texts = []
    
    for i in range(7):
        # 从 6天前 到 今天
        d = today - datetime.timedelta(days=(6-i))
        d_str = d.isoformat()
        pig = data_manager.get_pig_by_date(user_id, d_str)
        
        if pig:
            img_file = find_image_file(pig["id"])
            if img_file:
                images_to_merge.append(img_file)
                texts.append(f"{d.strftime('%m-%d')}\n{pig['name']}")
            else:
                # 有记录但没图？跳过
                pass
        # 没记录的天数不展示
        
    if not images_to_merge:
        await cmd_week.finish(MessageSegment.reply(event.message_id) + "你这周还没抽过猪呢！")
        return

    # --- PIL 绘图逻辑 ---
    msg = None
    try:
        # 设定单张小图大小
        item_w, item_h = 150, 150
        padding = 20
        # 画布宽度 = (小图宽 + 间距) * 数量 + 边距
        total_w = (item_w + padding) * len(images_to_merge) + padding
        total_h = item_h + 80 # 留出文字空间
        
        # 创建白底画布
        canvas = PILImage.new("RGB", (total_w, total_h), (255, 255, 255))
        
        # 简单粘贴
        for idx, (img_path, txt) in enumerate(zip(images_to_merge, texts)):
            # 打开并缩放图片
            img = PILImage.open(img_path).convert("RGBA")
            img = img.resize((item_w, item_h))
            
            x = padding + idx * (item_w + padding)
            y = padding
            
            # 粘贴图片 (用蒙版支持透明)
            canvas.paste(img, (x, y), img)
            
            # 暂时不画文字(需要字体文件)，或者如果你环境有默认字体也可以尝试
            # 为了稳妥，这里只发合并图，或者依赖 htmlrender 以后做更好的
            
        # 转为 BytesIO

        from io import BytesIO
        output = BytesIO()
        canvas.save(output, format="PNG")
        
        # 先构建消息，不发送
        msg = MessageSegment.reply(event.message_id) + \
              f"你这周变了 {len(images_to_merge)} 次猪！" + \
              MessageSegment.image(output.getvalue())
        
    except Exception as e:
        logger.error(f"本周小猪生成失败: {e}")
        await cmd_week.finish("生成失败，可能是图片太丑了...")
        return

    # 移出 try 块发送
    await cmd_week.finish(msg)   




# --- 辅助渲染函数 ---
async def send_rendered_pig(matcher, event, pig_data: dict, extra_text: str = ""):
    pig_id = pig_data.get("id", "")
    avatar_file = find_image_file(pig_id)

    if not avatar_file:
        logger.warning(f"未找到图片: {pig_id}.*")
        avatar_uri = ""
    else:
        avatar_uri = avatar_file.as_uri()
  
    # 1. 先尝试生成图片
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
    except Exception as e:
        logger.error(f"HTML渲染失败: {e}")
        await matcher.finish("图片生成失败，请查看后台日志。")
        return

    # 2. 图片生成成功后，再发送 (移出 try 块)
    msg = MessageSegment.reply(event.message_id)
    if extra_text:
        msg += extra_text
    msg += MessageSegment.image(pic)
    
    await matcher.finish(msg)