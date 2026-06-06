from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from nonebot import get_plugin_config
from nonebot.log import logger
import nonebot_plugin_localstore as localstore

from .config import Config


PLUGIN_DIR = Path(__file__).parent
BUILTIN_RESOURCE_DIR = PLUGIN_DIR / "resource"
BUILTIN_PIG_JSON = BUILTIN_RESOURCE_DIR / "pig.json"
BUILTIN_RULES_JSON = BUILTIN_RESOURCE_DIR / "pig_rules.json"
BUILTIN_IMAGE_DIR = BUILTIN_RESOURCE_DIR / "image"

CACHE_ROOT = localstore.get_plugin_data_dir() / "resources"
ACTIVE_RESOURCE_DIR = CACHE_ROOT / "active"
ACTIVE_IMAGE_DIR = ACTIVE_RESOURCE_DIR / "images"
STATE_FILE = CACHE_ROOT / "state.json"

PIG_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ALLOWED_IMAGE_SUFFIXES = {".png"}


@dataclass
class ResourceSyncResult:
    updated: bool
    skipped: bool
    resource_version: str = ""
    message: str = ""


class RollPigResourceManager:
    def __init__(self) -> None:
        self.pig_list: list[dict[str, Any]] = []
        self.pig_map: dict[str, dict[str, Any]] = {}
        self.food_pig_ids: set[str] = set()
        self.human_pig_ids: set[str] = set()
        self.eaten_pig_ids: set[str] = set()
        self.roast_excluded_pig_ids: set[str] = set()
        self.image_dirs: list[Path] = []
        self.resource_version: str = "builtin"

    # ================================ 资源读取与内存快照 ================================ #
    # 资源读取统一走这里，命令层继续使用 PIG_LIST/find_image_file 这类旧接口，减少侵入面。
    # 缓存资源必须完整可读，否则直接回退到插件内置资源，避免坏资源包导致 bot 启动失败。
    def reload(self) -> None:
        active_pig_json = ACTIVE_RESOURCE_DIR / "pig.json"
        if active_pig_json.exists():
            try:
                self._load_from_dir(ACTIVE_RESOURCE_DIR, resource_version=self._read_state_version())
                return
            except Exception as error:
                logger.warning(f"rollpig 云端资源缓存读取失败，回退到内置资源: {error}")

        self._load_from_builtin()

    def _load_from_builtin(self) -> None:
        self._apply_snapshot(
            pig_list=self._read_pig_json(BUILTIN_PIG_JSON),
            rules=self._read_rules_json(BUILTIN_RULES_JSON),
            image_dirs=[BUILTIN_IMAGE_DIR],
            resource_version="builtin",
        )

    def _load_from_dir(self, resource_dir: Path, *, resource_version: str) -> None:
        pig_list = self._read_pig_json(resource_dir / "pig.json")
        rules = self._read_rules_json(resource_dir / "pig_rules.json")
        self._ensure_images_exist(pig_list, [resource_dir / "images", BUILTIN_IMAGE_DIR])
        self._apply_snapshot(
            pig_list=pig_list,
            rules=rules,
            image_dirs=[resource_dir / "images", BUILTIN_IMAGE_DIR],
            resource_version=resource_version or "cloud",
        )

    def _apply_snapshot(
        self,
        *,
        pig_list: list[dict[str, Any]],
        rules: dict[str, Any],
        image_dirs: list[Path],
        resource_version: str,
    ) -> None:
        self._validate_pig_list(pig_list)
        self.pig_list = pig_list
        self.pig_map = {str(item["id"]): item for item in pig_list}
        self.food_pig_ids = self._read_id_set(rules, "food_pigs")
        self.human_pig_ids = self._read_id_set(rules, "human_pigs")
        self.eaten_pig_ids = self._read_id_set(rules, "eaten_pigs")
        self.roast_excluded_pig_ids = self._read_id_set(rules, "roast_excluded_pigs")
        self.image_dirs = image_dirs
        self.resource_version = resource_version
        logger.info(f"rollpig 资源已加载: version={resource_version}, pigs={len(pig_list)}")

    def find_image_file(self, pig_id: str) -> Path | None:
        for image_dir in self.image_dirs:
            for suffix in ALLOWED_IMAGE_SUFFIXES:
                image_file = image_dir / f"{pig_id}{suffix}"
                if image_file.exists():
                    return image_file
        return None

    def _read_state_version(self) -> str:
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return str(state.get("resource_version") or "cloud")
        except Exception:
            return "cloud"

    # ================================ 云端同步 ================================ #
    # 同步流程采用“临时目录下载 -> 完整校验 -> 原子替换 active”的方式，避免半包覆盖。
    async def sync_from_remote(self, *, force: bool = False) -> ResourceSyncResult:
        config = get_plugin_config(Config)
        if not config.rollpig_resource_sync_enabled and not force:
            return ResourceSyncResult(updated=False, skipped=True, message="资源同步未启用")

        manifest_url = str(config.rollpig_resource_manifest_url or "").strip()
        if not manifest_url:
            return ResourceSyncResult(updated=False, skipped=True, message="未配置资源 manifest URL")

        timeout = max(1.0, float(config.rollpig_resource_sync_timeout or 10.0))
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            manifest = await self._download_json(client, manifest_url, max_size=int(config.rollpig_resource_max_file_size))

            resource_version = str(manifest.get("resource_version") or "").strip()
            if not resource_version:
                raise ValueError("manifest 缺少 resource_version")
            if not force and resource_version == self._read_state_version():
                return ResourceSyncResult(
                    updated=False,
                    skipped=True,
                    resource_version=resource_version,
                    message="资源已是最新版本",
                )

            staging_dir = CACHE_ROOT / f".incoming_{int(time.time())}"
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            (staging_dir / "images").mkdir(parents=True, exist_ok=True)

            try:
                await self._download_manifest_files(
                    client,
                    manifest_url=manifest_url,
                    manifest=manifest,
                    staging_dir=staging_dir,
                    max_size=int(config.rollpig_resource_max_file_size),
                )
                pig_list = self._read_pig_json(staging_dir / "pig.json")
                self._ensure_images_exist(pig_list, [staging_dir / "images"])
                self._activate_staging_dir(staging_dir, resource_version)
            except Exception:
                if staging_dir.exists():
                    shutil.rmtree(staging_dir)
                raise

        self.reload()
        return ResourceSyncResult(
            updated=True,
            skipped=False,
            resource_version=resource_version,
            message=f"资源同步完成：{resource_version}",
        )

    async def _download_manifest_files(
        self,
        client: httpx.AsyncClient,
        *,
        manifest_url: str,
        manifest: dict[str, Any],
        staging_dir: Path,
        max_size: int,
    ) -> None:
        pig_json_meta = manifest.get("pig_json")
        if not isinstance(pig_json_meta, dict):
            raise ValueError("manifest 缺少 pig_json")
        await self._download_file_by_meta(
            client,
            manifest_url=manifest_url,
            meta=pig_json_meta,
            target=staging_dir / "pig.json",
            max_size=max_size,
        )

        optional_files = manifest.get("optional_files") or {}
        rules_meta = optional_files.get("pig_rules") if isinstance(optional_files, dict) else None
        if isinstance(rules_meta, dict):
            await self._download_file_by_meta(
                client,
                manifest_url=manifest_url,
                meta=rules_meta,
                target=staging_dir / "pig_rules.json",
                max_size=max_size,
            )

        image_items = manifest.get("images")
        if not isinstance(image_items, list):
            raise ValueError("manifest 缺少 images 列表")
        for image_meta in image_items:
            if not isinstance(image_meta, dict):
                raise ValueError("manifest images 存在非法条目")
            filename = str(image_meta.get("filename") or "")
            self._validate_image_filename(filename)
            await self._download_file_by_meta(
                client,
                manifest_url=manifest_url,
                meta=image_meta,
                target=staging_dir / "images" / filename,
                max_size=max_size,
            )

    async def _download_json(self, client: httpx.AsyncClient, url: str, *, max_size: int) -> dict[str, Any]:
        content = await self._download_bytes(client, url, max_size=max_size)
        data = json.loads(content.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("manifest 必须是 JSON object")
        return data

    async def _download_file_by_meta(
        self,
        client: httpx.AsyncClient,
        *,
        manifest_url: str,
        meta: dict[str, Any],
        target: Path,
        max_size: int,
    ) -> None:
        path = str(meta.get("path") or meta.get("filename") or "").strip()
        if not path:
            raise ValueError("manifest 文件条目缺少 path")
        url = urljoin(manifest_url, path)
        content = await self._download_bytes(client, url, max_size=max_size)

        expected_size = meta.get("size")
        if expected_size is not None and int(expected_size) != len(content):
            raise ValueError(f"文件大小校验失败: {path}")

        expected_hash = str(meta.get("sha256") or "").lower()
        actual_hash = hashlib.sha256(content).hexdigest()
        if expected_hash and actual_hash != expected_hash:
            raise ValueError(f"sha256 校验失败: {path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    async def _download_bytes(self, client: httpx.AsyncClient, url: str, *, max_size: int) -> bytes:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content
        if len(content) > max_size:
            raise ValueError(f"文件超过大小上限: {url}")
        return content

    def _activate_staging_dir(self, staging_dir: Path, resource_version: str) -> None:
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        previous_dir = CACHE_ROOT / "previous"
        if previous_dir.exists():
            shutil.rmtree(previous_dir)
        if ACTIVE_RESOURCE_DIR.exists():
            ACTIVE_RESOURCE_DIR.rename(previous_dir)
        staging_dir.rename(ACTIVE_RESOURCE_DIR)
        STATE_FILE.write_text(
            json.dumps(
                {
                    "resource_version": resource_version,
                    "synced_at": int(time.time()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # ================================ 校验与解析 ================================ #
    def _read_pig_json(self, path: Path) -> list[dict[str, Any]]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"pig.json 必须是 list: {path}")
        return data

    def _read_rules_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"pig_rules.json 必须是 object: {path}")
        return data

    def _validate_pig_list(self, pig_list: list[dict[str, Any]]) -> None:
        seen_ids: set[str] = set()
        for item in pig_list:
            if not isinstance(item, dict):
                raise ValueError("pig.json 存在非法条目")
            pig_id = str(item.get("id") or "")
            if not PIG_ID_PATTERN.match(pig_id):
                raise ValueError(f"非法 pig_id: {pig_id}")
            if pig_id in seen_ids:
                raise ValueError(f"重复 pig_id: {pig_id}")
            if not item.get("name"):
                raise ValueError(f"pig 缺少 name: {pig_id}")
            seen_ids.add(pig_id)

    def _ensure_images_exist(self, pig_list: list[dict[str, Any]], image_dirs: list[Path]) -> None:
        missing: list[str] = []
        for item in pig_list:
            pig_id = str(item.get("id") or "")
            if not any((image_dir / f"{pig_id}.png").exists() for image_dir in image_dirs):
                missing.append(pig_id)
        if missing:
            raise ValueError(f"资源包缺少图片: {', '.join(missing[:10])}")

    def _read_id_set(self, rules: dict[str, Any], key: str) -> set[str]:
        raw_items = rules.get(key) or []
        if not isinstance(raw_items, list):
            raise ValueError(f"pig_rules.{key} 必须是 list")
        result: set[str] = set()
        for raw_id in raw_items:
            pig_id = str(raw_id)
            if not PIG_ID_PATTERN.match(pig_id):
                raise ValueError(f"pig_rules.{key} 存在非法 ID: {pig_id}")
            result.add(pig_id)
        return result

    def _validate_image_filename(self, filename: str) -> None:
        path = Path(filename)
        if path.name != filename:
            raise ValueError(f"图片文件名不能包含路径: {filename}")
        if path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
            raise ValueError(f"不支持的图片格式: {filename}")
        pig_id = path.stem
        if not PIG_ID_PATTERN.match(pig_id):
            raise ValueError(f"图片文件名非法: {filename}")


pig_resource_manager = RollPigResourceManager()
