"""
翻译执行器
负责调用大模型API执行翻译任务（不涉及译文分配）
支持暂停/继续/停止控制
"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from loguru import logger

from app.services.translation.deepseek_service import DeepSeekTranslationService


class TranslationExecutor:
    """翻译执行器类"""
    
    def __init__(self, api_key: str, control_flags: Optional[Dict] = None):
        """
        初始化翻译执行器
        
        Args:
            api_key: DeepSeek API Key
            control_flags: 控制标志字典 {"paused": bool, "stopped": bool}
        """
        self.deepseek_service = DeepSeekTranslationService(api_key=api_key)
        self.control_flags = control_flags or {"paused": False, "stopped": False}
        logger.info("翻译执行器初始化成功")
    
    async def translate_single_task(
        self,
        task: Dict[str, Any],
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        翻译单个任务（包括聚合任务和独立任务）
        
        Args:
            task: 任务信息
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            翻译结果
        """
        task_id = task.get("task_id")
        is_aggregated = task.get("is_aggregated", False)
        
        try:
            # 获取待翻译文本
            if is_aggregated:
                # 组合块：使用聚合后的文本
                source_text = task.get("aggregated_text", "")
                logger.debug(f"翻译组合任务 {task_id}: {len(source_text)} 字符")
            else:
                # 独立块：使用原始文本
                source_text = task.get("source_text", "")
                logger.debug(f"翻译独立任务 {task_id}: {len(source_text)} 字符")
            
            if not source_text or not source_text.strip():
                logger.warning(f"任务 {task_id} 没有待翻译文本")
                return {
                    "task_id": task_id,
                    "status": "skipped",
                    "error": "没有待翻译文本"
                }
            
            # 调用翻译服务
            translated_text = await self.deepseek_service.translate_text_async(
                text=source_text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=task.get("context", "body"),
                element_type=task.get("element_type", "paragraph"),
                task_id=task_id,
            )
            
            return {
                "task_id": task_id,
                "is_aggregated": is_aggregated,
                "source_text": source_text,
                "translated_text": translated_text,
                "status": "success",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"翻译任务 {task_id} 失败: {str(e)}")
            return {
                "task_id": task_id,
                "is_aggregated": is_aggregated,
                "source_text": task.get("aggregated_text" if is_aggregated else "source_text", ""),
                "translated_text": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def translate_batch_tasks(
        self,
        tasks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        批量翻译任务（带并发控制和暂停/停止支持）
        【重要修改】使用队列模式代替gather，实现真正的暂停/停止
        
        Args:
            tasks: 任务列表
            source_lang: 源语言
            target_lang: 目标语言
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数
            
        Returns:
            翻译结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        total_tasks = len(tasks)
        completed_tasks = 0
        results = []
        pending_tasks = list(tasks)  # 待处理任务队列
        active_tasks = set()  # 正在执行的任务
        
        async def translate_with_semaphore(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            nonlocal completed_tasks
            
            try:
                # 检查是否被停止
                if self.control_flags.get("stopped"):
                    logger.info(f"任务 {task.get('task_id')} 因停止信号跳过")
                    return None
                
                # 等待暂停解除
                while self.control_flags.get("paused") and not self.control_flags.get("stopped"):
                    logger.debug(f"翻译已暂停，等待恢复...")
                    await asyncio.sleep(0.5)
                
                # 再次检查停止信号
                if self.control_flags.get("stopped"):
                    logger.info(f"任务 {task.get('task_id')} 暂停后被停止")
                    return None
                
                async with semaphore:
                    result = await self.translate_single_task(task, source_lang, target_lang)
                    
                    completed_tasks += 1
                    if progress_callback:
                        progress = (completed_tasks / total_tasks) * 100
                        progress_callback(progress, completed_tasks, total_tasks, result, "translation")
                    
                    return result
            except asyncio.CancelledError:
                logger.warning(f"任务 {task.get('task_id')} 被取消")
                return None
        
        # 【关键修改】使用边执行边创建的模式，而不是一次性启动所有任务
        task_index = 0
        
        while task_index < len(pending_tasks) or active_tasks:
            # 检查停止信号
            if self.control_flags.get("stopped"):
                logger.warning("检测到停止信号，取消所有正在执行的任务")
                # 取消所有正在执行的任务
                for active_task in active_tasks:
                    active_task.cancel()
                # 等待所有任务结束
                if active_tasks:
                    await asyncio.gather(*active_tasks, return_exceptions=True)
                break
            
            # 检查暂停信号
            if self.control_flags.get("paused"):
                logger.debug("翻译已暂停，等待恢复...")
                await asyncio.sleep(0.5)
                continue
            
            # 启动新任务（如果还有待处理的任务且未达到并发上限）
            while task_index < len(pending_tasks) and len(active_tasks) < max_concurrent:
                task = pending_tasks[task_index]
                task_coro = translate_with_semaphore(task)
                active_task = asyncio.create_task(task_coro)
                active_tasks.add(active_task)
                task_index += 1
            
            # 等待任意一个任务完成
            if active_tasks:
                done, active_tasks = await asyncio.wait(
                    active_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 处理完成的任务结果
                for done_task in done:
                    try:
                        result = await done_task
                        if result is not None:
                            results.append(result)
                    except asyncio.CancelledError:
                        logger.debug("任务被取消")
                    except Exception as e:
                        logger.error(f"任务异常: {str(e)}")
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        skipped_count = sum(1 for r in results if r["status"] == "skipped")
        stopped_count = total_tasks - len(results)
        
        logger.info(
            f"批量翻译完成: 总数={total_tasks}, 成功={success_count}, "
            f"失败={failed_count}, 跳过={skipped_count}, 停止={stopped_count}"
        )
        
        return results
    
    async def translate_by_priority(
        self,
        tasks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        按优先级分组批量翻译
        
        Args:
            tasks: 任务列表
            source_lang: 源语言
            target_lang: 目标语言
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数
            
        Returns:
            翻译结果列表
        """
        # 按优先级分组
        high_priority = [t for t in tasks if t.get("priority") == "high"]
        normal_priority = [t for t in tasks if t.get("priority") == "normal"]
        low_priority = [t for t in tasks if t.get("priority") == "low"]
        
        all_results = []
        total_tasks = len(tasks)
        completed_tasks = 0
        
        # 分优先级批量翻译
        for priority_group, priority_name in [
            (high_priority, "高"),
            (normal_priority, "中"),
            (low_priority, "低")
        ]:
            if not priority_group:
                continue
            
            logger.info(f"开始翻译优先级【{priority_name}】任务: {len(priority_group)} 个")
            
            # 定义带全局进度的回调
            def group_progress_callback(progress, current, total, result=None, phase: str = "translation"):
                global_completed = completed_tasks + current
                global_progress = (global_completed / total_tasks) * 100
                if progress_callback:
                    progress_callback(global_progress, global_completed, total_tasks, result, phase)
            
            results = await self.translate_batch_tasks(
                tasks=priority_group,
                source_lang=source_lang,
                target_lang=target_lang,
                max_concurrent=max_concurrent,
                progress_callback=group_progress_callback
            )
            
            all_results.extend(results)
            completed_tasks += len(results)
            
            logger.info(f"优先级【{priority_name}】翻译完成")
        
        return all_results
    
    def translate_batch_sync(
        self,
        tasks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        max_concurrent: int = 5,
        use_priority: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        同步方式批量翻译（内部调用异步方法）
        
        Args:
            tasks: 任务列表
            source_lang: 源语言
            target_lang: 目标语言
            max_concurrent: 最大并发数
            use_priority: 是否按优先级分组
            progress_callback: 进度回调函数
            
        Returns:
            翻译结果列表
        """
        if use_priority:
            return asyncio.run(
                self.translate_by_priority(
                    tasks=tasks,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    max_concurrent=max_concurrent,
                    progress_callback=progress_callback
                )
            )
        else:
            return asyncio.run(
                self.translate_batch_tasks(
                    tasks=tasks,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    max_concurrent=max_concurrent,
                    progress_callback=progress_callback
                )
            )
