"""
译文分配器
负责将组合块的译文智能拆分回各个原始元素
"""
import asyncio
import re
from typing import Dict, List, Optional, Any
from loguru import logger


class TranslationDistributor:
    """译文分配器类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化译文分配器
        
        Args:
            api_key: DeepSeek API Key
        """
        self.api_key = api_key
        logger.info("译文分配器初始化成功")
    
    def _split_by_ratio(
        self,
        aggregated_translation_text: str,
        blocks: List[Dict[str, Any]],
    ) -> List[str]:
        expected_len = len(blocks)
        text = aggregated_translation_text or ""
        if expected_len <= 1:
            return [text.strip() or text or " "]

        weights = []
        for b in blocks:
            w = len(((b.get("text") or "").strip()))
            weights.append(max(w, 1))

        total_w = sum(weights) or expected_len
        if not text:
            return [" " for _ in range(expected_len)]

        total_len = len(text)
        cut_points = []
        acc = 0
        for i in range(expected_len - 1):
            acc += weights[i]
            target_pos = round(total_len * (acc / total_w))
            cut_points.append(max(1, min(total_len - 1, target_pos)))

        boundary_pattern = re.compile(r"[\s\n\r\t,，\.。!！\?？;；:：\)\]】】}]+")
        snapped = []
        last = 0
        for cp in cut_points:
            window = 40
            left = max(last + 1, cp - window)
            right = min(total_len - 1, cp + window)
            best = None
            for m in boundary_pattern.finditer(text[left:right]):
                pos = left + m.end()
                dist = abs(pos - cp)
                if best is None or dist < best[0]:
                    best = (dist, pos)
            snapped_pos = best[1] if best else cp
            snapped_pos = max(last + 1, min(total_len - 1, snapped_pos))
            snapped.append(snapped_pos)
            last = snapped_pos

        segments = []
        prev = 0
        for p in snapped:
            seg = text[prev:p].strip()
            segments.append(seg)
            prev = p
        segments.append(text[prev:].strip())

        segments = [s if s else " " for s in segments]
        if len(segments) != expected_len:
            if len(segments) > expected_len:
                merged = segments[: expected_len - 1]
                merged.append(" ".join(segments[expected_len - 1 :]).strip() or " ")
                segments = merged
            else:
                segments.extend([" " for _ in range(expected_len - len(segments))])

        return segments

    def _split_by_token(
        self,
        aggregated_translation_text: str,
        split_token: str,
        expected_len: int,
    ) -> Optional[List[str]]:
        if not split_token:
            return None
        if split_token not in (aggregated_translation_text or ""):
            return None
        raw_parts = (aggregated_translation_text or "").split(split_token)
        parts = [(p or "").strip() for p in raw_parts]
        if len(parts) == expected_len and all(parts):
            return parts
        return None
    
    async def distribute_translation(
        self,
        task: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """
        为单个组合任务分配译文
        
        Args:
            task: 翻译任务（必须是聚合任务，且已有translated_text）
            target_lang: 目标语言
            
        Returns:
            分配结果
        """
        task_id = task.get("task_id")
        
        try:
            # 验证任务类型
            if not task.get("is_aggregated"):
                logger.warning(f"任务 {task_id} 不是聚合任务，跳过分配")
                return {
                    "task_id": task_id,
                    "status": "skipped",
                    "error": "非聚合任务无需分配"
                }
            
            # 获取必要数据
            aggregated_blocks = task.get("aggregated_blocks", [])
            aggregated_source = task.get("aggregated_text", "")
            aggregated_translation = task.get("translated_text", "")
            
            if not aggregated_translation:
                logger.warning(f"任务 {task_id} 没有译文，跳过分配")
                return {
                    "task_id": task_id,
                    "status": "skipped",
                    "error": "没有译文"
                }
            
            if len(aggregated_blocks) <= 1:
                # 只有一个块，直接返回
                logger.debug(f"任务 {task_id} 只有1个块，无需分配")
                return {
                    "task_id": task_id,
                    "status": "success",
                    "distributed_translations": [
                        {
                            "block_index": 0,
                            "page_num": aggregated_blocks[0].get("page_num"),
                            "block_id": aggregated_blocks[0].get("block_id"),
                            "translated_text": aggregated_translation
                        }
                    ]
                }

            split_token = task.get("split_token") or "<<<OCEANPDF_SPLIT>>>"
            token_parts = self._split_by_token(
                aggregated_translation_text=aggregated_translation,
                split_token=split_token,
                expected_len=len(aggregated_blocks),
            )
            if token_parts:
                translated_pieces = token_parts
                logger.info(f"任务 {task_id} 分隔标记切分成功: {len(translated_pieces)} 个块")
            else:
                if split_token and split_token in aggregated_translation:
                    logger.warning(f"任务 {task_id} 分隔标记切分失败，回退到比例切分")
                    aggregated_translation = aggregated_translation.replace(split_token, " ")
                translated_pieces = self._split_by_ratio(
                    aggregated_translation_text=aggregated_translation,
                    blocks=aggregated_blocks,
                )
                logger.info(f"任务 {task_id} 比例切分完成: {len(translated_pieces)} 个块")
            
            # 构建最终结果
            distributed_translations = []
            for i, translated_piece in enumerate(translated_pieces):
                if i >= len(aggregated_blocks):
                    break
                block = aggregated_blocks[i]
                distributed_translations.append({
                    "block_index": i,
                    "page_num": block.get("page_num"),
                    "block_id": block.get("block_id"),
                    "reading_order": block.get("reading_order"),
                    "element_type": block.get("element_type"),
                    "original_text": block.get("text"),
                    "translated_text": translated_piece
                })
            
            logger.info(f"任务 {task_id} 分配完成: {len(distributed_translations)} 个块")
            
            return {
                "task_id": task_id,
                "status": "success",
                "distributed_translations": distributed_translations
            }
            
        except Exception as e:
            logger.error(f"分配任务 {task_id} 失败: {str(e)}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def distribute_batch(
        self,
        translated_tasks: List[Dict[str, Any]],
        target_lang: str,
        max_concurrent: int = 3,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        批量分配译文（仅处理聚合任务）
        
        Args:
            translated_tasks: 已翻译的任务列表
            target_lang: 目标语言
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数
            
        Returns:
            分配结果列表
        """
        # 筛选出需要分配的聚合任务
        aggregated_tasks = [
            task for task in translated_tasks
            if task.get("is_aggregated") and task.get("translated_text")
        ]
        
        if not aggregated_tasks:
            logger.info("没有需要分配的聚合任务")
            return []
        
        logger.info(f"开始批量分配: {len(aggregated_tasks)} 个聚合任务")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        total_tasks = len(aggregated_tasks)
        completed_tasks = 0
        
        async def distribute_with_semaphore(task: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal completed_tasks
            
            async with semaphore:
                result = await self.distribute_translation(task, target_lang)
                
                completed_tasks += 1
                if progress_callback:
                    progress = (completed_tasks / total_tasks) * 100
                    progress_callback(progress, completed_tasks, total_tasks, result, "distribution")
                
                return result
        
        # 并发执行所有分配任务
        distribution_tasks = [distribute_with_semaphore(task) for task in aggregated_tasks]
        results = await asyncio.gather(*distribution_tasks)
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        logger.info(
            f"批量分配完成: 总数={total_tasks}, 成功={success_count}, 失败={failed_count}"
        )
        
        return results
    
    def distribute_batch_sync(
        self,
        translated_tasks: List[Dict[str, Any]],
        target_lang: str,
        max_concurrent: int = 3,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        同步方式批量分配（内部调用异步方法）
        
        Args:
            translated_tasks: 已翻译的任务列表
            target_lang: 目标语言
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数
            
        Returns:
            分配结果列表
        """
        return asyncio.run(
            self.distribute_batch(
                translated_tasks=translated_tasks,
                target_lang=target_lang,
                max_concurrent=max_concurrent,
                progress_callback=progress_callback
            )
        )
