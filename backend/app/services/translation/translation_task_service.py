"""
翻译任务服务
负责管理和执行翻译任务
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from app.services.translation.translation_executor import TranslationExecutor
from app.services.translation.translation_distributor import TranslationDistributor
from app.services.translation.pretranslation_service import PretranslationService
from app.services.pdf_id_mapper import get_pdf_id_mapper


class TranslationTaskService:
    """翻译任务服务类"""
    
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        """
        初始化翻译任务服务
        
        Args:
            parsed_base_dir: 解析结果存储的基础目录
        """
        self.parsed_base_dir = Path(parsed_base_dir)
        self.pretrans_service = PretranslationService(parsed_base_dir)
    
    def get_translation_result_path(self, pdf_name: str, use_dps: bool = False) -> Path:
        """获取翻译结果文件路径"""
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        suffix = "_dps" if use_dps else ""
        return self.parsed_base_dir / pdf_id / f"translation{suffix}.json"
    
    def load_pretranslation_data(self, pdf_name: str, use_dps: bool = False) -> Optional[Dict]:
        """
        加载预翻译数据
        
        Args:
            pdf_name: PDF文件名
            use_dps: 是否使用DPS模式
            
        Returns:
            预翻译数据字典
        """
        pretrans_path = self.pretrans_service.get_pretranslation_json_path(pdf_name, use_dps)
        
        if not pretrans_path.exists():
            logger.error(f"预翻译文件不存在: {pretrans_path}")
            return None
        
        try:
            with open(pretrans_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载预翻译文件失败: {str(e)}")
            return None
    
    def save_translation_result(
        self,
        pdf_name: str,
        translation_data: Dict,
        use_dps: bool = False
    ) -> bool:
        """
        保存翻译结果
        
        Args:
            pdf_name: PDF文件名
            translation_data: 翻译结果数据
            use_dps: 是否使用DPS模式
            
        Returns:
            是否保存成功
        """
        result_path = self.get_translation_result_path(pdf_name, use_dps)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 【修复】Windows长路径问题：使用绝对路径并添加 \\?\ 前缀（仅Windows）
            import platform
            abs_result_path = result_path.absolute()
            
            # Windows系统且路径较长时，使用UNC路径
            if platform.system() == "Windows" and len(str(abs_result_path)) > 240:
                abs_result_path_str = f"\\\\?\\{abs_result_path}"
                logger.info(f"使用长路径模式保存翻译结果: 原长度={len(str(abs_result_path))}")
            else:
                abs_result_path_str = str(abs_result_path)
            
            # 先写入临时文件，然后重命名（原子操作）
            tmp_path = result_path.with_suffix(result_path.suffix + ".tmp")
            abs_tmp_path = tmp_path.absolute()
            
            if platform.system() == "Windows" and len(str(abs_tmp_path)) > 240:
                abs_tmp_path_str = f"\\\\?\\{abs_tmp_path}"
            else:
                abs_tmp_path_str = str(abs_tmp_path)
            
            with open(abs_tmp_path_str, 'w', encoding='utf-8') as f:
                json.dump(translation_data, f, ensure_ascii=False, indent=2)
            
            # 重命名临时文件
            import os
            if os.path.exists(abs_result_path_str):
                os.remove(abs_result_path_str)
            os.rename(abs_tmp_path_str, abs_result_path_str)
            
            logger.info(f"保存翻译结果成功: {result_path}")
            return True
        except Exception as e:
            logger.error(f"保存翻译结果失败: {str(e)}")
            logger.error(f"路径长度: {len(str(result_path))}, 路径: {result_path}")
            return False
    
    async def translate_pdf_async(
        self,
        pdf_name: str,
        api_key: str,
        use_dps: bool = False,
        max_concurrent: int = 5,
        enable_distribution: bool = True,
        progress_callback: Optional[callable] = None,
        control_flags: Optional[Dict] = None,  # 【新增】控制标志
        llm_config: Optional[Dict] = None  # 【新增】大模型厂商配置
    ) -> Dict[str, Any]:
        """
        异步翻译整个PDF（分两阶段：翻译 + 译文分配）
        
        Args:
            pdf_name: PDF文件名
            api_key: 大模型 API Key
            use_dps: 是否使用DPS模式
            max_concurrent: 最大并发数
            enable_distribution: 是否启用译文分配（针对组合块）
            progress_callback: 进度回调函数
            control_flags: 控制标志 {"paused": bool, "stopped": bool}
            llm_config: 大模型配置 {"provider": str, "base_url": str, "model": str}
            
        Returns:
            翻译结果
        """
        try:
            # 1. 加载预翻译数据
            pretrans_data = self.load_pretranslation_data(pdf_name, use_dps)
            if not pretrans_data:
                return {
                    "success": False,
                    "error": "预翻译文件不存在，请先生成预翻译文件"
                }
            
            # 2. 初始化翻译执行器（【新增】传入控制标志与大模型配置）
            translation_executor = TranslationExecutor(
                api_key=api_key,
                control_flags=control_flags,
                llm_config=llm_config
            )
            
            # 3. 准备翻译任务
            translation_tasks = pretrans_data.get("translation_tasks", [])
            if not translation_tasks:
                return {
                    "success": False,
                    "error": "没有可翻译的任务"
                }
            
            source_lang = pretrans_data.get("source_lang", "en")
            target_lang = pretrans_data.get("target_lang", "zh-CN")
            
            logger.info(
                f"开始翻译 {pdf_name}: 任务数={len(translation_tasks)}, "
                f"并发数={max_concurrent}, 模式={'DPS' if use_dps else 'Python'}, "
                f"译文分配={'启用' if enable_distribution else '禁用'}"
            )
            
            # 4. 筛选需要翻译的任务
            tasks_to_translate = [
                task for task in translation_tasks
                if task.get("translate", True)
            ]
            
            logger.info(f"共 {len(tasks_to_translate)} 个任务需要翻译")

            task_by_id = {t.get("task_id"): t for t in translation_tasks if t.get("task_id")}
            tasks_to_translate_ids = {t.get("task_id") for t in tasks_to_translate if t.get("task_id")}

            for task in translation_tasks:
                if task.get("task_id") not in tasks_to_translate_ids:
                    task["translation_status"] = "skipped"
                else:
                    task["translation_status"] = "pending"
                if "translation_error" in task:
                    task.pop("translation_error", None)

                if task.get("is_aggregated") and task.get("aggregated_blocks"):
                    for block in task["aggregated_blocks"]:
                        if "translated_text" in block:
                            block["translated_text"] = block.get("translated_text")
                if "distribution_status" in task:
                    task.pop("distribution_status", None)
                if "distribution_error" in task:
                    task.pop("distribution_error", None)

            translation_success = 0
            translation_failed = 0
            distribution_success = 0
            distribution_failed = 0
            translated_task_ids: set[str] = set()
            distributed_task_ids: set[str] = set()

            translation_result = {
                "pdf_name": pdf_name,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "parse_mode": "dps" if use_dps else "python",
                "translated_at": datetime.now().isoformat(),
                "enable_distribution": enable_distribution,
                "statistics": {
                    "total_tasks": len(translation_tasks),
                    "translated_tasks": len(tasks_to_translate),
                    "translation_success": 0,
                    "translation_failed": 0,
                    "distribution_success": 0,
                    "distribution_failed": 0,
                    "overall_success_rate": "0%"
                },
                "translation_tasks": translation_tasks
            }

            logger.info("开始写入初始翻译结果文件（pending状态）")
            self.save_translation_result(pdf_name, translation_result, use_dps)

            def update_and_persist(progress_value: float, current: int, total: int, phase: str, result: Optional[Dict[str, Any]] = None):
                nonlocal translation_success, translation_failed, distribution_success, distribution_failed
                updated = False
                
                # 创建用于SSE推送的result副本（可能需要添加distributed_results字段）
                sse_result = result.copy() if result else None

                if result and isinstance(result, dict):
                    task_id = result.get("task_id")
                    if task_id:
                        if phase == "translation":
                            if task_id not in translated_task_ids:
                                translated_task_ids.add(task_id)
                                updated = True
                                status = result.get("status")
                                if status == "success":
                                    translation_success += 1
                                elif status == "failed":
                                    translation_failed += 1

                                task = task_by_id.get(task_id)
                                if task:
                                    task["translated_text"] = result.get("translated_text")
                                    task["translation_status"] = status
                                    if result.get("error"):
                                        task["translation_error"] = result.get("error")
                                    else:
                                        task.pop("translation_error", None)
                                    
                                    # 【关键修复】确保单个任务的translated_text存在于推送数据中
                                    if sse_result and not task.get("is_aggregated"):
                                        # 单个任务：确保推送数据中包含translated_text
                                        if "translated_text" not in sse_result:
                                            sse_result["translated_text"] = task.get("translated_text", "")

                                logger.info(
                                    f"[翻译进度] {pdf_name} | {current}/{total} | "
                                    f"task_id={task_id} | status={status}"
                                )
                        elif phase == "distribution":
                            if task_id not in distributed_task_ids:
                                distributed_task_ids.add(task_id)
                                updated = True
                                status = result.get("status")
                                if status == "success":
                                    distribution_success += 1
                                elif status == "failed":
                                    distribution_failed += 1

                                task = task_by_id.get(task_id)
                                if task:
                                    task["distribution_status"] = status
                                    if status == "success" and task.get("is_aggregated") and task.get("aggregated_blocks"):
                                        dist_translations = result.get("distributed_translations", []) or []
                                        block_translation_map = {dt.get("block_id"): dt.get("translated_text") for dt in dist_translations}
                                        for block in task["aggregated_blocks"]:
                                            block_id = block.get("block_id")
                                            if block_id in block_translation_map:
                                                block["translated_text"] = block_translation_map[block_id]
                                        
                                        # 【关键修复】为SSE推送构造distributed_results字段
                                        # 将aggregated_blocks中的译文转换为前端期望的格式
                                        distributed_results = []
                                        for block in task["aggregated_blocks"]:
                                            distributed_results.append({
                                                "block_id": block.get("block_id"),
                                                "page_num": block.get("page_num"),
                                                "translated_text": block.get("translated_text", "")
                                            })
                                        if sse_result:
                                            sse_result["distributed_results"] = distributed_results
                                        
                                    if result.get("error"):
                                        task["distribution_error"] = result.get("error")
                                    else:
                                        task.pop("distribution_error", None)

                                logger.info(
                                    f"[分配进度] {pdf_name} | {current}/{total} | "
                                    f"task_id={task_id} | status={status}"
                                )

                translation_result["statistics"]["translation_success"] = translation_success
                translation_result["statistics"]["translation_failed"] = translation_failed
                translation_result["statistics"]["distribution_success"] = distribution_success
                translation_result["statistics"]["distribution_failed"] = distribution_failed
                translation_result["statistics"]["overall_success_rate"] = (
                    f"{(translation_success / len(tasks_to_translate) * 100):.2f}%" if tasks_to_translate else "0%"
                )

                if updated:
                    self.save_translation_result(pdf_name, translation_result, use_dps)
                    logger.info(
                        f"[落盘] {pdf_name} | phase={phase} | progress={progress_value:.2f}% | "
                        f"path={self.get_translation_result_path(pdf_name, use_dps)}"
                    )

                if progress_callback:
                    # 【关键修复】使用处理过的sse_result，确保包含distributed_results
                    progress_callback(progress_value, current, total, sse_result, phase)
            
            logger.info("=" * 60)
            logger.info("执行翻译任务（组合块完成后立即插队分配）")
            logger.info("=" * 60)

            translation_distributor = TranslationDistributor(api_key=api_key) if enable_distribution else None
            distribution_total = (
                sum(
                    1
                    for t in tasks_to_translate
                    if t.get("is_aggregated") and t.get("aggregated_blocks")
                )
                if enable_distribution
                else 0
            )
            distribution_completed = 0
            translation_completed = 0

            priority_rank = {"high": 0, "normal": 1, "low": 2}
            tasks_to_translate_sorted = sorted(
                tasks_to_translate,
                key=lambda t: priority_rank.get(t.get("priority", "normal"), 1),
            )

            distribution_queue: List[Dict[str, Any]] = []
            active_translation: set[asyncio.Task] = set()
            active_distribution: set[asyncio.Task] = set()
            task_meta: Dict[asyncio.Task, Dict[str, Any]] = {}

            distribution_max_concurrent = min(3, max_concurrent) if enable_distribution else 0
            translate_index = 0

            def calc_overall_progress() -> float:
                if not tasks_to_translate_sorted:
                    return 100.0
                tp = translation_completed / len(tasks_to_translate_sorted)
                if not enable_distribution or distribution_total <= 0:
                    return tp * 100
                dp = distribution_completed / distribution_total
                return tp * 70 + dp * 30

            async def run_translate_job(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                try:
                    if control_flags and control_flags.get("stopped"):
                        logger.info(f"[翻译] 跳过（已停止）: task_id={task.get('task_id')}")
                        return None

                    while control_flags and control_flags.get("paused") and not control_flags.get("stopped"):
                        logger.debug("[翻译] 已暂停，等待恢复...")
                        await asyncio.sleep(0.5)

                    if control_flags and control_flags.get("stopped"):
                        logger.info(f"[翻译] 暂停后停止: task_id={task.get('task_id')}")
                        return None

                    return await translation_executor.translate_single_task(task, source_lang, target_lang)
                except asyncio.CancelledError:
                    logger.warning(f"[翻译] 任务被取消: task_id={task.get('task_id')}")
                    return None
                except Exception as e:
                    logger.error(f"[翻译] 任务异常: task_id={task.get('task_id')} | {str(e)}")
                    return {
                        "task_id": task.get("task_id"),
                        "is_aggregated": task.get("is_aggregated", False),
                        "source_text": task.get("aggregated_text" if task.get("is_aggregated") else "source_text", ""),
                        "translated_text": None,
                        "status": "failed",
                        "error": str(e),
                    }

            async def run_distribution_job(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                try:
                    if not translation_distributor:
                        return None

                    if control_flags and control_flags.get("stopped"):
                        logger.info(f"[分配] 跳过（已停止）: task_id={task.get('task_id')}")
                        return None

                    while control_flags and control_flags.get("paused") and not control_flags.get("stopped"):
                        logger.debug("[分配] 已暂停，等待恢复...")
                        await asyncio.sleep(0.5)

                    if control_flags and control_flags.get("stopped"):
                        logger.info(f"[分配] 暂停后停止: task_id={task.get('task_id')}")
                        return None

                    return await translation_distributor.distribute_translation(task, target_lang)
                except asyncio.CancelledError:
                    logger.warning(f"[分配] 任务被取消: task_id={task.get('task_id')}")
                    return None
                except Exception as e:
                    logger.error(f"[分配] 任务异常: task_id={task.get('task_id')} | {str(e)}")
                    return {
                        "task_id": task.get("task_id"),
                        "status": "failed",
                        "error": str(e),
                    }

            logger.info(
                f"[队列初始化] translate_total={len(tasks_to_translate_sorted)} | "
                f"distribution_total={distribution_total} | max_concurrent={max_concurrent} | "
                f"distribution_max_concurrent={distribution_max_concurrent}"
            )

            while (
                translate_index < len(tasks_to_translate_sorted)
                or active_translation
                or distribution_queue
                or active_distribution
            ):
                if control_flags and control_flags.get("stopped"):
                    logger.warning("[队列] 检测到停止信号，取消所有正在执行的任务")
                    for t in list(active_translation) + list(active_distribution):
                        t.cancel()
                    if active_translation or active_distribution:
                        await asyncio.gather(*list(active_translation | active_distribution), return_exceptions=True)
                    break

                if control_flags and control_flags.get("paused"):
                    logger.debug("[队列] 已暂停，等待恢复...")
                    await asyncio.sleep(0.5)
                    continue

                total_active = len(active_translation) + len(active_distribution)
                remaining_capacity = max_concurrent - total_active

                while (
                    enable_distribution
                    and distribution_queue
                    and remaining_capacity > 0
                    and len(active_distribution) < distribution_max_concurrent
                ):
                    dist_task = distribution_queue.pop(0)
                    job = asyncio.create_task(run_distribution_job(dist_task))
                    active_distribution.add(job)
                    task_meta[job] = {"job_type": "distribution", "task": dist_task}
                    remaining_capacity -= 1

                while translate_index < len(tasks_to_translate_sorted) and remaining_capacity > 0:
                    t = tasks_to_translate_sorted[translate_index]
                    translate_index += 1
                    job = asyncio.create_task(run_translate_job(t))
                    active_translation.add(job)
                    task_meta[job] = {"job_type": "translation", "task": t}
                    remaining_capacity -= 1

                all_active = active_translation | active_distribution
                if not all_active:
                    await asyncio.sleep(0.05)
                    continue

                done, _ = await asyncio.wait(all_active, return_when=asyncio.FIRST_COMPLETED)

                for finished in done:
                    meta = task_meta.pop(finished, None) or {}
                    job_type = meta.get("job_type")
                    original_task = meta.get("task")

                    if job_type == "translation":
                        active_translation.discard(finished)
                    elif job_type == "distribution":
                        active_distribution.discard(finished)

                    try:
                        result = await finished
                    except asyncio.CancelledError:
                        result = None
                    except Exception as e:
                        logger.error(f"[队列] 任务回收异常: {str(e)}")
                        result = None

                    if job_type == "translation":
                        translation_completed += 1
                        if result is not None:
                            update_and_persist(
                                calc_overall_progress(),
                                translation_completed,
                                len(tasks_to_translate_sorted),
                                "translation",
                                result,
                            )

                        if not enable_distribution or distribution_total <= 0:
                            continue

                        task_id = (result or {}).get("task_id") if isinstance(result, dict) else None
                        task_obj = task_by_id.get(task_id) if task_id else original_task
                        effective_task_id = task_id or (task_obj.get("task_id") if task_obj else None)
                        if not task_obj or not task_obj.get("is_aggregated"):
                            continue

                        status = (result or {}).get("status")
                        has_translation = bool((result or {}).get("translated_text")) or bool(task_obj.get("translated_text"))

                        if status == "success" and has_translation:
                            distribution_queue.insert(0, task_obj)
                            logger.info(
                                f"[插队] 组合块完成后插入分配任务: task_id={effective_task_id} | "
                                f"queue_len={len(distribution_queue)}"
                            )
                        else:
                            distribution_completed += 1
                            skip_reason = "翻译失败或无译文，跳过分配"
                            update_and_persist(
                                calc_overall_progress(),
                                distribution_completed,
                                distribution_total,
                                "distribution",
                                {
                                    "task_id": effective_task_id,
                                    "status": "skipped",
                                    "error": skip_reason,
                                },
                            )
                            logger.warning(f"[分配跳过] task_id={effective_task_id} | reason={skip_reason}")

                    elif job_type == "distribution":
                        distribution_completed += 1
                        if result is not None:
                            update_and_persist(
                                calc_overall_progress(),
                                distribution_completed,
                                distribution_total if distribution_total > 0 else 0,
                                "distribution",
                                result,
                            )

            logger.info(
                f"[队列结束] translation_completed={translation_completed}/{len(tasks_to_translate_sorted)} | "
                f"distribution_completed={distribution_completed}/{distribution_total}"
            )

            distribution_results = []

            # 9. 统计总体结果
            success_count = translation_success
            failed_count = translation_failed
            
            # 10. 构建完整翻译结果
            translation_result["translated_at"] = datetime.now().isoformat()
            translation_result["statistics"]["translation_success"] = translation_success
            translation_result["statistics"]["translation_failed"] = translation_failed
            translation_result["statistics"]["distribution_success"] = distribution_success
            translation_result["statistics"]["distribution_failed"] = distribution_failed
            translation_result["statistics"]["overall_success_rate"] = f"{(success_count / len(tasks_to_translate) * 100):.2f}%" if tasks_to_translate else "0%"
            
            # 11. 保存翻译结果
            if not self.save_translation_result(pdf_name, translation_result, use_dps):
                logger.warning("翻译结果保存失败，但翻译已完成")
            
            logger.info(
                f"翻译完成: 成功={success_count}, 失败={failed_count}, "
                f"成功率={translation_result['statistics']['overall_success_rate']}"
            )
            
            return {
                "success": True,
                "data": translation_result["statistics"],
                "file_path": str(self.get_translation_result_path(pdf_name, use_dps))
            }
            
        except Exception as e:
            logger.error(f"翻译PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def translate_pdf_sync(
        self,
        pdf_name: str,
        api_key: str,
        use_dps: bool = False,
        max_concurrent: int = 5,
        enable_distribution: bool = True,
        progress_callback: Optional[callable] = None,
        llm_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        同步翻译整个PDF（内部调用异步方法）
        
        Args:
            pdf_name: PDF文件名
            api_key: 大模型 API Key
            use_dps: 是否使用DPS模式
            max_concurrent: 最大并发数
            enable_distribution: 是否启用译文分配
            progress_callback: 进度回调函数
            llm_config: 大模型配置 {"provider": str, "base_url": str, "model": str}
            
        Returns:
            翻译结果
        """
        import asyncio
        import nest_asyncio
        
        # 允许嵌套事件循环
        nest_asyncio.apply()
        
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，创建一个新的任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.translate_pdf_async(
                            pdf_name=pdf_name,
                            api_key=api_key,
                            use_dps=use_dps,
                            max_concurrent=max_concurrent,
                            enable_distribution=enable_distribution,
                            progress_callback=progress_callback,
                            llm_config=llm_config
                        )
                    )
                    return future.result()
            else:
                # 如果循环没有运行，直接运行
                return loop.run_until_complete(
                    self.translate_pdf_async(
                        pdf_name=pdf_name,
                        api_key=api_key,
                        use_dps=use_dps,
                        max_concurrent=max_concurrent,
                        enable_distribution=enable_distribution,
                        progress_callback=progress_callback,
                        llm_config=llm_config
                    )
                )
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            return asyncio.run(
                self.translate_pdf_async(
                    pdf_name=pdf_name,
                    api_key=api_key,
                    use_dps=use_dps,
                    max_concurrent=max_concurrent,
                    enable_distribution=enable_distribution,
                    progress_callback=progress_callback,
                    llm_config=llm_config
                )
            )
    
    def get_translation_result(self, pdf_name: str, use_dps: bool = False) -> Optional[Dict]:
        """
        获取翻译结果
        
        Args:
            pdf_name: PDF文件名
            use_dps: 是否使用DPS模式
            
        Returns:
            翻译结果数据
        """
        result_path = self.get_translation_result_path(pdf_name, use_dps)
        
        if not result_path.exists():
            logger.warning(f"翻译结果文件不存在: {result_path}")
            return None
        
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取翻译结果失败: {str(e)}")
            return None
