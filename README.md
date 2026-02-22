<div align="center">
    <a href="https://github.com/Bearlele/nonebot-plugin-rollpig">
        <img src="https://raw.githubusercontent.com/Bearlele/nonebot-plugin-rollpig/refs/heads/main/PigLogo.jpeg" width="310" alt="logo">
    </a>
    <h2>🐖 nonebot-plugin-rollpig 🐖</h2>
    今天是什么小猪 🐽
    本项目基于 Bearlele/nonebot-plugin-rollpig 修改，增添部分新功能
</div>

### 🐖 食用方法 🐖

使用 pip 安装：

```bash
pip install nonebot_plugin_rollpig

```

或者使用 nb-cli 安装：

```bash
nb plugin install nonebot_plugin_rollpig

```

或者直接 **Download ZIP**

---

### 🐷 使用 🐷

**今日小猪 / 今天是什么小猪** - 抽取今天属于你的小猪类型 🐖

* 每个用户每天只能抽取一次 🐽
* 重复抽取不会改变结果 🐷
* 按日期自然重置（跨天后可重新抽取）🐖

**随机小猪** - 从 PigHub 随机获取一张猪猪图 🐖

* 支持参数数量（`随机小猪 3`），最多 10 张
* 群聊下多张会合并转发，私聊下自动降级为单张

**找猪 / 搜猪** - 从 PigHub 按关键词搜索猪猪图 🔎

* 例如：`找猪 玩偶`
* 群聊返回最多 10 条，私聊返回第 1 条并提示总数

**明日小猪** - 预测明天的猪猪运势 🔮

**昨日小猪** - 查看昨天抽到了什么 📜

**今日烤猪** - 把今天的猪做成美食（慎用！）🔥

* 支持 **AI 生成**：开启开关且配置 Key 后，会根据猪猪类型生成“烤后感言”
* 若你今天是 **人类** 或 **熟食形态**（烤猪/培根/猪排/猪肉串），会被拦截，不再继续烧烤

**烤群友** - 在群聊中烤一位群友（需 `@` 或回复目标）🍢

* 规则：成功 60% / 逃脱 30% / 反噬 10%
* 冷却：每位用户 8 小时一次
* 目标限制：目标需先抽过今日小猪，且不能是 **人类** 或 **熟食形态**
* 失败文案会按发起者当前状态区分（人类/熟食/未抽猪/普通形态）

**我的猪圈** - 查看解锁进度 📊

**本周小猪** - 生成本周猪猪总结长图 🖼️

---

### ⚙️ 配置方法 (可选) ⚙️

如果你想开启 **“AI 烤猪”** 功能（让文案不再千篇一律），请在 Bot 根目录的 `.env` 文件中添加以下配置：

```properties
# 开启 AI 生成开关 (默认关闭)
ROLLPIG_AI_ENABLED=true

# 填入 DeepSeek API Key
ROLLPIG_DEEPSEEK_KEY=sk-xxxxxxxxxxxxxxxx

# (可选) 自定义模型名称，默认 deepseek-chat
ROLLPIG_MODEL=deepseek-chat

# (可选) 自定义 API 地址
ROLLPIG_DEEPSEEK_BASE=https://api.deepseek.com

```

说明：

* 仅设置 `ROLLPIG_DEEPSEEK_KEY` 不会触发 AI，需同时开启 `ROLLPIG_AI_ENABLED=true`
* 未开启 AI 或未配置 Key 时，会自动回退到本地文案模板

---

### 🐖 新增小猪 🐖

插件资源路径：

```
nonebot_plugin_rollpig/resource

```

* **pig.json** 小猪信息，例如：

```json
[
    {
        "id": "pig",
        "name": "猪",
        "description": "普通小猪",
        "analysis": "你性格温和，喜欢简单的生活，容易满足。在别人眼中可能有些慵懒，但你知道如何享受生活的美好。"
    }
]

```

* **image/** 小猪图片
* 图片命名需和信息中的 `id` 一致
* 支持图片类型：`["png", "jpg", "jpeg", "webp", "gif"]`



---

### 🐽 目录结构示例 🐽

```
nonebot_plugin_rollpig/
├─ __init__.py
├─ config.py         # 配置文件
├─ roast_manager.py  # AI 烤猪管理器
├─ resource/
│   ├─ pig.json
│   └─ image/
│       └─ pig.png

```

---

### 🐖 注意事项 🐖

* 新增小猪时只需在 `pig.json` 添加对象，并将对应图片放到 `image/` 文件夹即可 🐷
* 图片自动按 id 匹配，无需在 JSON 中写图片后缀 🐖

