<div align="center">
    <a href="https://github.com/Bearlele/nonebot-plugin-rollpig">
        <img src="https://raw.githubusercontent.com/Bearlele/nonebot-plugin-rollpig/refs/heads/main/PigLogo.jpeg" width="310" alt="logo">
    </a>
    <h2>🐖 nonebot-plugin-rollpig 🐖</h2>
    今天是什么小猪 🐽
    本项目基于 Bearlele/nonebot-plugin-rollpig 修改，增添部分新功能
</div>

### 🐖 食用方法 🐖

环境要求：Python `>=3.10`

使用 pip 安装：

```bash
pip install -U "git+https://github.com/Felis2026/nonebot-plugin-rollpig.git@felis-dev"

```

或者使用 pip fixed-tag 安装：

```bash
pip install -U "git+https://github.com/Felis2026/nonebot-plugin-rollpig.git@v0.6.2"

```

或者直接 **Download ZIP**

---

### 🐷 使用 🐷

**今日小猪 / 今天是什么小猪** - 抽取今天属于你的小猪类型 🐖

* 每个用户每天只能抽取一次 🐽
* 重复抽取不会改变结果 🐷
* 按日期自然重置（跨天后可重新抽取）🐖
* 重复抽到已解锁小猪会提升专家等级（EX Lv.），连续重复时下一次抽到新猪的概率会逐步提高

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
* 若你今天是 **人类**、**熟食形态**（如烤猪/培根/猪排/猪肉串/烤乳猪/猪堡包/猪油）、**吃掉了** 或 **猪售罄**，会被拦截，不再继续烧烤

**烤群友** - 在群聊中烤一位群友（需 `@` 或回复目标）🍢

* 规则：成功 60% / 逃脱 30% / 反噬 10%
* 冷却：每位用户默认 8 小时一次（可通过 `ROLLPIG_ROAST_COOLDOWN_HOURS` 调整）
* 常规模式目标限制：目标需先抽过今日小猪，且不能是 **人类**、**熟食形态**、**吃掉了** 或 **猪售罄**
* 失败文案会按发起者当前状态区分（人类/熟食/吃掉了/猪售罄/未抽猪/普通形态）
* 后门口令（普通用户每日 1 次，强制成功）：`打点后厨` / `偷换烤架` / `贿赂主厨` / `加急生火`（兼容写法：`加急生活`）
* 后门口令（superuser 无限次，强制成功）：`强行点火`
* 后门仅绕过 CD 与概率判定，不绕过目标资格（目标仍需已抽猪，且不能是 **人类** / **熟食形态** / **吃掉了** / **猪售罄**）
* 指令示例：`烤群友 加急生火 @某人` / 回复目标后发送 `烤群友 强行点火`

**我的猪圈** - 查看解锁进度与专家等级摘要 📊

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

# 如果你想启用云同步，可自行部署 rollpig-cloud：
# https://github.com/Felis2026/rollpig-cloud
# 也可以联系维护者（QQ：3397152010）申请接入现有 API
#
# (可选) 存储后端，默认 local；启用云同步时改为 cloud
ROLLPIG_STORAGE_BACKEND=cloud

# (可选) rollpig-cloud 服务地址
ROLLPIG_CLOUD_API_URL=http://127.0.0.1:8011

# (可选) rollpig-cloud Bearer Token
ROLLPIG_CLOUD_TOKEN=replace-with-token

# (可选) 云端请求超时（秒）
ROLLPIG_CLOUD_TIMEOUT=3.0

# (可选) 云端请求严格模式，默认 true
ROLLPIG_CLOUD_STRICT_MODE=true

# (可选) 小猪资源云端同步，默认启用并指向 FelisLab 资源包
ROLLPIG_RESOURCE_SYNC_ENABLED=true
ROLLPIG_RESOURCE_MANIFEST_URL=https://pig.felislab.cc/resources/rollpig/manifest.json
ROLLPIG_RESOURCE_SYNC_INTERVAL_HOURS=24
ROLLPIG_RESOURCE_SYNC_TIMEOUT=10.0

# (可选) 私有资源 overlay，Felis 版默认指向 PJSK 私有包
# 私有包会叠加在公有全量资源包之上；如需关闭可设为空字符串
ROLLPIG_PRIVATE_RESOURCE_MANIFEST_URL=https://pig.felislab.cc/resources/rollpig-pjsk/manifest.json

# (可选) 私有资源 Bearer Token；静态公开资源可不填
ROLLPIG_PRIVATE_RESOURCE_TOKEN=replace-with-token

```

说明：

* 仅设置 `ROLLPIG_DEEPSEEK_KEY` 不会触发 AI，需同时开启 `ROLLPIG_AI_ENABLED=true`
* 未开启 AI 或未配置 Key 时，会自动回退到本地文案模板
* 后续可能会继续扩展为“云端同步文案库”模式；当前版本仍以本地模板 / AI 生成两种方式为主
* `ROLLPIG_ROAST_COOLDOWN_HOURS` 仅影响普通模式；后门模式不会改写普通 CD 时间戳
* 未配置云端时，插件默认继续使用本地 `pig_data.json` 存储，不影响单 Bot 正常运行
* `ROLLPIG_STORAGE_BACKEND=cloud` 时，`今日小猪`、图鉴成长状态、普通 CD、后门次数将在多 Bot 间同步；日报与保护按群聚合/生效
* `ROLLPIG_CLOUD_TIMEOUT` 与 `ROLLPIG_CLOUD_STRICT_MODE` 一般保持默认即可，只有明确需要调试云端行为时再调整
* `ROLLPIG_CLOUD_STRICT_MODE=false` 的含义是：读接口可使用安全兜底值；关键写接口不会偷偷回退本地，而是向用户提示“稍后再试”，避免多 Bot 数据脑裂
* `ROLLPIG_RESOURCE_SYNC_ENABLED=true` 时，插件会从云端同步 `pig.json`、图片和可选规则文件到本地缓存；同步失败会继续使用旧缓存或插件内置资源
* `ROLLPIG_PRIVATE_RESOURCE_MANIFEST_URL` 用于覆盖默认私有 overlay 地址；留空则禁用私有包
* 私有资源也会缓存到本地，优先级高于公有云端资源和插件内置资源；配置留空时不会加载私有缓存
* 超级用户可发送 `同步小猪资源` / `刷新小猪图鉴` 手动触发资源同步
* 未接入外部控制台时，群功能与日报默认开启；宿主项目可按需接管开关

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
* **pig_rules.json** 可选规则文件，用于维护熟食等特殊分类，避免污染上游兼容的 `pig.json` 基础格式
* 公有云端资源会缓存到本地 `data/localstore/nonebot_plugin_rollpig/resources/active/`，优先级高于插件内置资源；删除缓存后会自动回退到内置资源
* 私有 overlay 会缓存到本地 `data/localstore/nonebot_plugin_rollpig/resources/private_active/`，优先级高于公有包，适合维护不希望进入上游/公开包的 Bot 专属小猪



---

### 🐽 目录结构示例 🐽

```
nonebot_plugin_rollpig/
├─ __init__.py
├─ config.py           # 配置模型
├─ resource_manager.py # 云端小猪资源同步与本地缓存加载
├─ data_manager.py     # 本地 JSON 存储实现
├─ roast_manager.py    # AI 烤猪与文案生成
├─ runtime.py          # 宿主适配 / 群开关 / 运行时工具
├─ summary_service.py  # 每日总结聚合
├─ store/
│   ├─ base.py         # 存储接口定义
│   ├─ factory.py      # local / cloud 后端选择
│   ├─ local_json.py   # 本地存储适配
│   └─ cloud.py        # rollpig-cloud 云端适配
├─ resource/
│   ├─ pig.json
│   ├─ pig_rules.json
│   └─ image/
│       └─ pig.png
```

---

### 🐖 注意事项 🐖

* 新增小猪时只需在 `pig.json` 添加对象，并将对应图片放到 `image/` 文件夹即可 🐷
* 图片自动按 id 匹配，无需在 JSON 中写图片后缀 🐖


## v0.6.2 更新日志

### 🔒 私有资源 overlay
- Felis 版默认叠加 `rollpig-pjsk` 私有资源包，`.env` 可覆盖或留空关闭
- 支持公有全量包 + 私有外挂包的两层资源加载，私有图片优先级高于公有包

### 🐖 特殊形态
- 新增 `猪售罄(sold-out)` 特殊形态，今日烤猪、烤群友、随机烤群友与反噬路径均有专属拦截文案
- 新增 7 月公开小猪资源；热猪、猪咪莓蛋糕、猪咪虾寿司、猪饺纳入熟食规则

### 🔐 安全修复
- 收紧 `Pillow` 与 `python-dotenv` 依赖下限，规避 GitHub Dependabot 提示的已知漏洞版本

---

## v0.6.1 更新日志

### ☁️ 云端资源同步
- 新增云端小猪资源包同步，支持从 `manifest.json` 拉取 `pig.json`、`pig_rules.json` 与图片资源
- 同步后的资源会落到本地缓存目录，运行时优先使用缓存，云端异常时回退插件内置资源
- 新增超管命令 `同步小猪资源` / `刷新小猪图鉴`，可手动触发资源刷新

### 🧩 规则兼容
- 新增 `pig_rules.json`，将熟食、人类、吃掉了等特殊形态从基础 `pig.json` 拆出
- 烤猪判定合并内置规则与云端规则，避免新增特殊形态绕过拦截

### 🔒 私有资源 overlay
- 支持可选私有资源包，例如 `rollpig-pjsk`，在公有全量包之上追加 Bot 专属小猪
- Felis 版默认拉取 `rollpig-pjsk` 私有 overlay；可通过 `ROLLPIG_PRIVATE_RESOURCE_MANIFEST_URL` 覆盖或留空关闭

---

## v0.6.0 更新日志

### ✨ 新功能
- **抽猪伪保底**：连续抽到重复猪后，下一次抽到未解锁新猪的权重会逐步提高；抽到新猪后计数清零
- **专家等级（EX Lv.）**：每只猪记录累计抽到次数，`1~6+` 次对应 `EX Lv.0~5`
- **成长提示**：`今日小猪` 首次抽取会根据新猪 / 重复升级 / 重复未升级随机展示短提示文案
- **猪圈成长摘要**：`我的猪圈` 增加最高 EX Lv.、满级数量、本命猪、高等级小猪与连续重复次数展示

### ☁️ 云端同步
- 接入 rollpig-cloud 的 `draw-state` 状态读取流程，支持多 Bot 同步 `copies` 与 `duplicate_streak`
- `get-or-create` 仅在当天首次创建抽猪记录时更新成长状态，避免重复发送命令刷等级
- 本地 JSON 模式同步兼容新字段，未接入云端的部署仍可正常使用

### 🧩 体验优化
- `加急生火` 支持作为独立命令直达触发烤群友后门模式
- 抽猪成长提示扩充为 3 组文案池，每组 10 条，降低重复感
- 完整图鉴图片、卡图 EX Lv. 贴图与烧烤概率修正暂缓到后续版本

---

## v0.5.1 更新日志

### 🐖 资源更新
- 新增 9 只图鉴小猪：`猪厨`、`猪序员`、`404猪`、`出猪屋`、`小红猪`、`猪皮奶`、`猪宅`、`猪油`、`吃掉了`

### 🧩 规则补充
- `猪油` 现按熟食形态处理，相关烧烤拦截逻辑同步生效
- 新增 `吃掉了` 特殊形态，并补充今日烤猪 / 烤群友场景下的独立拦截逻辑

### 📝 文案优化
- 扩充人类、熟食、吃掉了、反噬、逃脱、后门、保护等场景文案池
- 优化部分特殊形态的群内反馈表现，降低误读感

---

## v0.5.0 更新日志

### ✨ 新功能
- **云端同步存储**：支持通过 `rollpig-cloud` 同步今日小猪、普通烤群友 CD、后门次数、群维度日报与保护机制
- **多 Bot / 多群协同**：在接入云端后，可跨 Bot 共享核心状态，减少多实例部署时的数据割裂

### ♻️ 重构
- **存储层重构**：抽离本地存储与云端存储接口，统一读写入口，便于后续继续扩展
- **运行时职责拆分**：新增运行时适配、摘要服务、存储工厂等模块，减少主入口文件耦合
- **宿主接入友好化**：为外部控制台预留群开关 / 日报开关接入点，未接入时保持默认可用

### 🐖 资源更新
- 新增 6 只图鉴小猪：`储蓄罐`、`烤乳猪`、`早八猪`、`复读猪`、`猪穆朗玛`、`猪堡包`

### 📝 文档与兼容性
- README 补充云端配置说明与本地 / 云端两种运行方式说明
- `nonebot-plugin-htmlrender` 依赖下限调整为 `0.6.0`，降低集成门槛

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

---

## 更早版本更新摘要

### v0.3.1
- 新增 11 只图鉴小猪及相关文案资源

### v0.3.0
- 稳定烧烤流程，完善人类 / 熟食拦截逻辑
- 统一 AI 启用条件与回退逻辑，增强异常处理与文档同步

### v0.2.9
- 同步上游“找猪”与“随机小猪多张连发”特性
- 新增 `烤群友` 与文案模板系统

### v0.2.8
- 新增 AI 烤猪能力，接入 DeepSeek
- 增加相关 `.env` 配置与文档说明

### v0.2.7
- 引入异步网络请求
- 新增昨日 / 明日 / 本周小猪、今日烤猪、我的猪圈等能力
- 引入长图总结相关依赖
