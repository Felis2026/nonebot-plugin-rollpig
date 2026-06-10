from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    # --- AI 烤猪配置 ---
    rollpig_ai_enabled: bool = False  # 是否开启 AI 生成
    rollpig_deepseek_key: Optional[str] = None  # DeepSeek API Key
    rollpig_deepseek_base: str = "https://api.deepseek.com" # Base URL
    rollpig_model: str = "deepseek-chat" # 模型名称
    rollpig_roast_cooldown_hours: float = 8.0  # 烤群友普通模式冷却时长（小时）
    rollpig_storage_backend: str = "local"  # local / cloud
    rollpig_cloud_api_url: Optional[str] = None
    rollpig_cloud_token: Optional[str] = None
    rollpig_cloud_timeout: float = 3.0
    rollpig_cloud_strict_mode: bool = True  # true=云端异常直接失败；false=读接口可安全兜底，写接口仍提示稍后重试

    # --- 小猪资源云端同步 ---
    # 默认指向 FelisLab 静态资源包；同步失败时只回退到本地缓存/插件内置资源，不影响 Bot 启动。
    rollpig_resource_sync_enabled: bool = True
    rollpig_resource_manifest_url: str = "https://pig.felislab.cc/resources/rollpig/manifest.json"
    rollpig_resource_sync_interval_hours: int = 24
    rollpig_resource_sync_timeout: float = 10.0
    rollpig_resource_max_file_size: int = 10 * 1024 * 1024
    # 私有资源包是公有全量包之上的 overlay；Felis 版默认启用 PJSK 私有包，可用 .env 覆盖或设空关闭。
    rollpig_private_resource_manifest_url: Optional[str] = "https://pig.felislab.cc/resources/rollpig-pjsk/manifest.json"
    rollpig_private_resource_token: Optional[str] = None

    # --- 代理设置 (可选，如果服务器在国内连不上API) ---
    rollpig_proxy: Optional[str] = None
