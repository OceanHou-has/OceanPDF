import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

from app.core.config import settings
from app.services.pdf_id_mapper import get_pdf_id_mapper


class DPSService:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.DPS_SERVICE_URL).rstrip("/")

    def get_output_path(self, pdf_name: str) -> Path:
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        parsed_dir = Path("storage/parsed") / pdf_id
        parsed_dir.mkdir(parents=True, exist_ok=True)
        return parsed_dir / "dps.json"

    async def _get_health(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        url = f"{self.base_url}/health"
        async with session.get(url) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"DPS /health HTTP {resp.status}: {text[:2000]}")
            try:
                return json.loads(text)
            except Exception as e:
                raise RuntimeError(f"DPS /health 返回非JSON: {text[:2000]}") from e

    @staticmethod
    def _is_ready(health: Dict[str, Any], need_ocr: bool) -> bool:
        layout_status = (health.get("layout_status") or {}).get("status")
        ocr_status = (health.get("ocr_status") or {}).get("status")

        layout_ready = layout_status == "ready"
        if not need_ocr:
            return layout_ready
        return layout_ready and ocr_status == "ready"

    async def wait_until_ready(self, need_ocr: bool) -> Dict[str, Any]:
        timeout_total = float(settings.DPS_HEALTH_TIMEOUT_SEC)
        interval = float(settings.DPS_HEALTH_POLL_INTERVAL_SEC)
        max_attempts = int(settings.DPS_HEALTH_MAX_ATTEMPTS)
        t0 = time.monotonic()
        attempt = 0
        last_error = ""
        last_health: Dict[str, Any] = {}

        client_timeout = aiohttp.ClientTimeout(total=float(settings.DPS_HTTP_TIMEOUT_SEC))
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            while True:
                attempt += 1
                last_error = ""
                try:
                    health = await self._get_health(session)
                    if self._is_ready(health, need_ocr=need_ocr):
                        return health
                    last_health = health
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"[DPS] 健康检查失败 attempt={attempt}: {last_error}")

                # 最多检查 max_attempts 次，尽快提示用户
                if attempt >= max_attempts:
                    break

                elapsed = time.monotonic() - t0
                if elapsed >= timeout_total:
                    break
                await asyncio.sleep(interval)

        elapsed = round(time.monotonic() - t0, 1)
        if last_error:
            raise RuntimeError(
                f"DPS模型未就绪：无法连接DPS服务（已检查{attempt}次，耗时{elapsed}s）。"
                f"请确认DPS服务已启动。最后错误: {last_error[:200]}"
            )
        not_ready = []
        layout_status = (last_health.get("layout_status") or {}).get("status")
        ocr_status = (last_health.get("ocr_status") or {}).get("status")
        if layout_status != "ready":
            not_ready.append(f"版面模型({layout_status})")
        if need_ocr and ocr_status != "ready":
            not_ready.append(f"OCR模型({ocr_status})")
        raise RuntimeError(
            f"DPS模型未就绪：{'、'.join(not_ready) or '模型加载中'}（已检查{attempt}次，耗时{elapsed}s）。"
            f"请等待DPS服务完成模型加载后重试。"
        )

    async def analyze_pdf(
        self,
        pdf_path: str,
        pdf_name: str,
        *,
        with_ocr: Optional[bool] = None,
        ocr_min_conf: Optional[float] = None,
        ocr_return_regions: Optional[bool] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        output_path = self.get_output_path(pdf_name)
        with_ocr = bool(settings.DPS_WITH_OCR if with_ocr is None else with_ocr)
        ocr_min_conf = float(settings.DPS_OCR_MIN_CONF if ocr_min_conf is None else ocr_min_conf)
        ocr_return_regions = bool(
            settings.DPS_OCR_RETURN_REGIONS if ocr_return_regions is None else ocr_return_regions
        )

        if output_path.exists() and not force:
            try:
                size = os.path.getsize(output_path)
            except Exception:
                size = None

            if with_ocr:
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    raw = payload.get("raw") if isinstance(payload, dict) else None
                    if not isinstance(raw, dict):
                        raw = payload if isinstance(payload, dict) else {}
                    pages = raw.get("pages") or []
                    total_boxes = sum(len((p or {}).get("boxes") or []) for p in pages)
                    nonempty = sum(
                        1
                        for p in pages
                        for b in ((p or {}).get("boxes") or [])
                        if str((b or {}).get("ocr_text") or "").strip()
                    )
                    if total_boxes > 0 and nonempty == 0:
                        logger.warning(f"[DPS] OCR为空，重新调用: {pdf_name}")
                    else:
                        logger.info(f"[DPS] 结果已存在: {pdf_name}")
                        return {
                            "success": True,
                            "already_exists": True,
                            "pdf_name": pdf_name,
                            "dps_json_path": str(output_path),
                            "with_ocr": with_ocr,
                            "ocr_min_conf": ocr_min_conf,
                            "ocr_return_regions": ocr_return_regions,
                        }
                except Exception as e:
                    logger.warning(f"[DPS] 校验失败，重新调用: {pdf_name}")
            else:
                logger.info(f"[DPS] 结果已存在: {pdf_name}")
                return {
                    "success": True,
                    "already_exists": True,
                    "pdf_name": pdf_name,
                    "dps_json_path": str(output_path),
                    "with_ocr": with_ocr,
                    "ocr_min_conf": ocr_min_conf,
                    "ocr_return_regions": ocr_return_regions,
                }

        pdf_size = None
        try:
            pdf_size = os.path.getsize(pdf_path)
        except Exception:
            pass

        logger.info(f"[DPS] 开始分析: {pdf_name} | OCR={with_ocr}")

        await self.wait_until_ready(need_ocr=with_ocr)

        url = (
            f"{self.base_url}/analyze"
            f"?with_ocr={'true' if with_ocr else 'false'}"
            f"&ocr_min_conf={ocr_min_conf}"
            f"&ocr_return_regions={'true' if ocr_return_regions else 'false'}"
        )

        client_timeout = aiohttp.ClientTimeout(total=float(settings.DPS_HTTP_TIMEOUT_SEC))
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            form = aiohttp.FormData()
            with open(pdf_path, "rb") as f:
                form.add_field(
                    "file",
                    f,
                    filename=Path(pdf_path).name,
                    content_type="application/pdf",
                )
                t0 = time.monotonic()
                async with session.post(url, data=form) as resp:
                    text = await resp.text()
                    elapsed = time.monotonic() - t0
                    if resp.status != 200:
                        raise RuntimeError(f"DPS /analyze HTTP {resp.status}: {text[:4000]}")
                    try:
                        data = json.loads(text)
                    except Exception as e:
                        raise RuntimeError(f"DPS /analyze 返回非JSON: {text[:4000]}") from e

        if data.get("status") != "success":
            raise RuntimeError(f"DPS /analyze 返回status!=success: {str(data)[:2000]}")

        meta = {
            "base_url": self.base_url,
            "with_ocr": with_ocr,
            "ocr_min_conf": ocr_min_conf,
            "ocr_return_regions": ocr_return_regions,
            "req_id": data.get("req_id"),
            "elapsed_sec": data.get("elapsed_sec"),
            "pages": len(data.get("pages") or []),
        }

        logger.info(f"✅ [DPS] 分析成功: {pdf_name} | {meta.get('pages')}页 | 耗时: {meta.get('elapsed_sec'):.2f}s")

        payload = {
            "pdf_name": pdf_name,
            "generated_at": int(time.time()),
            "meta": meta,
            "raw": data,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "already_exists": False,
            "pdf_name": pdf_name,
            "dps_json_path": str(output_path),
            "req_id": meta.get("req_id"),
            "elapsed_sec": meta.get("elapsed_sec"),
            "pages": meta.get("pages"),
            "with_ocr": with_ocr,
            "ocr_min_conf": ocr_min_conf,
            "ocr_return_regions": ocr_return_regions,
        }
