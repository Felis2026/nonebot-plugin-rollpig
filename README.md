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
pip install -U "git+https://github.com/Felis2026/nonebot-plugin-rollpig.git@felis-dev"

```

或者使用 pip fixed-tag 安装：

```bash
pip install -U "git+https://github.com/Felis2026/nonebot-plugin-rollpig.git@v0.4.0"

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
* 冷却：每位用户默认 8 小时一次（可通过 `ROLLPIG_ROAST_COOLDOWN_HOURS` 调整）
* 常规模式目标限制：目标需先抽过今日小猪，且不能是 **人类** 或 **熟食形态**
* 失败文案会按发起者当前状态区分（人类/熟食/未抽猪/普通形态）
* 后门口令（普通用户每日 1 次，强制成功）：`打点后厨` / `偷换烤架` / `贿赂主厨` / `加急生火`（兼容写法：`加急生活`）
* 后门口令（superuser 无限次，强制成功）：`强行点火`
* 后门仅绕过 CD 与概率判定，不绕过目标资格（目标仍需已抽猪，且不能是 **人类** / **熟食形态**）
* 指令示例：`烤群友 加急生火 @某人` / 回复目标后发送 `烤群友 强行点火`

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

# (可选) 烤群友普通模式 CD（单位小时，默认 8）
ROLLPIG_ROAST_COOLDOWN_HOURS=8

```

说明：

* 仅设置 `ROLLPIG_DEEPSEEK_KEY` 不会触发 AI，需同时开启 `ROLLPIG_AI_ENABLED=true`
* 未开启 AI 或未配置 Key 时，会自动回退到本地文案模板
* `ROLLPIG_ROAST_COOLDOWN_HOURS` 仅影响普通模式；后门模式不会改写普通 CD 时间戳

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


---

## v0.4.0 更新日志

### ✨ 新功能
- **每日猪圈日报**：每晚 23:20~23:30 自动推送当日统计（最热门猪形态、烧烤狂人、最惨食材、逃脱大师、反噬之王），带随机延迟防风控
- **保护机制**：被烤 ≥2 次的最惨用户次日自动获得保护，普通烤群友被拦截；后门口令可突破保护
- **随机烤群友**：从今日抽过猪的群友中随机选一个，走完整的成功/逃脱/反噬判定
- **自动补抽**：今日烤猪时未抽猪自动补抽，体验更顺畅

### 🐛 修复
- 修复 @Bot 烤群友不触发 Bot 专属反噬的问题

### 📝 文案
- 今日烤猪拦截文案（人类/熟食）全面重写，各 6 条
- 反噬文案（通用）从 4 条扩充至 8 条
- 后门前缀文案（超级/普通）各从 4 条扩充至 6 条
- 新增保护拦截/突破文案各 5 条
- 新增随机烤群友前缀文案 5 条
- 新增每日总结模板及无数据文案 4 条

### 📦 依赖
- 启用 `nonebot-plugin-apscheduler`（定时任务支持）