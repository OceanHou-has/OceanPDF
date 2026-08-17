"""OCR识别服务"""
import os
import re
import tempfile
import time
from typing import Dict, Any, List

from core.logger import log_kv
from core.model_loader import model_loader
from utils.bbox_utils import normalize_bbox, to_xy_points, bbox_from_points
from utils.env_utils import env_get_int, env_get_float, env_get_str, bool_from_env


class OCRService:
    """OCR识别服务"""
    
    @staticmethod
    def as_list(v):
        """转换为列表"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, tuple):
            return list(v)
        if hasattr(v, "tolist"):
            try:
                out = v.tolist()
                if isinstance(out, list):
                    return out
                return [out]
            except Exception:
                return []
        try:
            return list(v)
        except Exception:
            return []
    
    @staticmethod
    def result_to_json(res) -> Dict:
        """将结果转换为JSON"""
        if isinstance(res, dict):
            return res
        if hasattr(res, "json"):
            try:
                j = res.json
                if isinstance(j, dict):
                    return j
            except Exception:
                pass
        return {}
    
    @staticmethod
    def safe_call(fn, call_kwargs: dict):
        """安全调用（自动移除不支持的参数）"""
        kwargs = dict(call_kwargs or {})
        removed = []
        last_err = None
        
        for _ in range(len(kwargs) + 1):
            try:
                return fn(**kwargs)
            except TypeError as e:
                last_err = e
                msg = str(e) or repr(e)
                m = re.search(r"unexpected keyword argument ['\"]([^'\"]+)['\"]", msg)
                bad_key = m.group(1) if m else None
                if bad_key and bad_key in kwargs:
                    kwargs.pop(bad_key, None)
                    removed.append(bad_key)
                    continue
                break
        
        if removed:
            log_kv("调用参数不被支持，已自动移除", {
                "fn": getattr(fn, "__name__", str(fn)),
                "removed": removed
            })
        
        if last_err is not None:
            raise last_err
        return fn(**kwargs)
    
    @staticmethod
    def recognize(content: bytes, filename: str, file_ext: str, req_id: str) -> Dict[str, Any]:
        """OCR识别"""
        # 确保模型已加载
        if model_loader.ocr_model is None:
            raise RuntimeError("OCR 模型未加载")
        
        tmp_path = None
        try:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, prefix="ocr_") as f:
                f.write(content)
                tmp_path = f.name
            
            # 执行 OCR 识别
            t0 = time.time()
            ocr_model = model_loader.ocr_model
            
            if hasattr(ocr_model, "predict"):
                log_kv("调用 OCR 模型.predict", {"req_id": req_id})
                predict_kwargs = OCRService._build_predict_kwargs()
                if predict_kwargs:
                    log_kv("OCR predict 参数", {"req_id": req_id, **predict_kwargs})
                    ocr_results = OCRService.safe_call(
                        lambda **kw: ocr_model.predict(tmp_path, **kw),
                        predict_kwargs
                    )
                else:
                    ocr_results = ocr_model.predict(tmp_path)
            elif hasattr(ocr_model, "ocr"):
                log_kv("调用 OCR 模型.ocr", {"req_id": req_id})
                ocr_results = ocr_model.ocr(tmp_path, cls=bool_from_env("OCR_USE_ANGLE_CLS", True))
            else:
                raise RuntimeError(f"OCR 模型不可调用: {type(ocr_model)}")
            
            dt = round(time.time() - t0, 3)
            
            # 解析结果
            results = OCRService._parse_ocr_results(ocr_results, req_id)
            
            response = {
                "status": "success",
                "req_id": req_id,
                "filename": filename,
                "elapsed_sec": dt,
                "total_pages": len(results),
                "results": results,
            }
            
            log_kv("OCR 请求完成", {"req_id": req_id, "pages": len(results), "elapsed_sec": dt})
            return response
            
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    log_kv("删除临时文件失败", {"req_id": req_id, "tmp_path": tmp_path, "err": repr(e)})
    
    @staticmethod
    def _build_predict_kwargs() -> Dict:
        """构建predict参数"""
        kwargs = {}
        param_mappings = [
            ("OCR_PREDICT_BATCH_SIZE", "batch_size", env_get_int),
            ("OCR_PREDICT_LIMIT_SIDE_LEN", "limit_side_len", env_get_int),
            ("OCR_PREDICT_LIMIT_TYPE", "limit_type", env_get_str),
            ("OCR_PREDICT_THRESH", "thresh", env_get_float),
            ("OCR_PREDICT_BOX_THRESH", "box_thresh", env_get_float),
            ("OCR_PREDICT_UNCLIP_RATIO", "unclip_ratio", env_get_float),
            ("OCR_PREDICT_MAX_CANDIDATES", "max_candidates", env_get_int),
        ]
        
        for env_name, param_name, getter_func in param_mappings:
            value = getter_func(env_name)
            if value is not None:
                kwargs[param_name] = value
        
        return kwargs
    
    @staticmethod
    def _parse_ocr_results(ocr_results, req_id: str) -> List[Dict]:
        """解析OCR结果"""
        results = []
        
        if not isinstance(ocr_results, list):
            log_kv("OCR 返回非 list，尝试包装", {"req_id": req_id, "type": type(ocr_results).__name__})
            ocr_results = [ocr_results]
        
        for page_idx, page_result in enumerate(ocr_results):
            text_regions = []
            page_index = page_idx
            
            # 提取文本区域信息
            if hasattr(page_result, "rec_texts"):
                text_regions = OCRService._extract_from_attributes(page_result, req_id, page_idx)
            else:
                page_json = OCRService.result_to_json(page_result)
                text_regions, page_index = OCRService._extract_from_json(
                    page_json, page_result, req_id, page_idx
                )
            
            # 计算平均置信度
            avg_confidence = (
                sum(r["confidence"] for r in text_regions) / len(text_regions)
                if text_regions else 0.0
            )
            
            results.append({
                "page_index": page_index,
                "text_regions": text_regions,
                "avg_confidence": round(avg_confidence, 4),
                "total_texts": len(text_regions),
            })
            
            log_kv("OCR 页面结果", {
                "req_id": req_id,
                "page_idx": page_idx,
                "texts_count": len(text_regions),
                "avg_confidence": round(avg_confidence, 4),
            })
        
        return results
    
    @staticmethod
    def _extract_from_attributes(page_result, req_id: str, page_idx: int) -> List[Dict]:
        """从属性提取OCR结果"""
        rec_texts = OCRService.as_list(getattr(page_result, "rec_texts", None))
        rec_scores = OCRService.as_list(getattr(page_result, "rec_scores", None))
        rec_polys = OCRService.as_list(getattr(page_result, "rec_polys", None))
        rec_boxes = OCRService.as_list(getattr(page_result, "rec_boxes", None))
        dt_polys = OCRService.as_list(getattr(page_result, "dt_polys", None))
        dt_scores = OCRService.as_list(getattr(page_result, "dt_scores", None))
        
        log_kv("OCR page_result 属性长度", {
            "req_id": req_id,
            "page_idx": page_idx,
            "rec_texts": len(rec_texts),
            "rec_scores": len(rec_scores),
            "rec_polys": len(rec_polys),
            "rec_boxes": len(rec_boxes),
            "dt_polys": len(dt_polys),
            "dt_scores": len(dt_scores),
        })
        
        text_regions = []
        for i in range(len(rec_texts)):
            text = rec_texts[i]
            confidence = (
                float(rec_scores[i]) if i < len(rec_scores) else
                (float(dt_scores[i]) if i < len(dt_scores) else 0.0)
            )
            poly_raw = (
                rec_polys[i] if i < len(rec_polys) else
                (dt_polys[i] if i < len(dt_polys) else None)
            )
            bbox_raw = rec_boxes[i] if i < len(rec_boxes) else None
            
            poly = to_xy_points(poly_raw)
            bbox = normalize_bbox(bbox_raw)
            if not bbox and poly:
                bbox = bbox_from_points(poly)
            
            text_regions.append({
                "text": text,
                "confidence": confidence,
                "bbox": bbox,
                "poly": poly
            })
        
        return text_regions
    
    @staticmethod
    def _extract_from_json(page_json: Dict, page_result, req_id: str, page_idx: int):
        """从JSON提取OCR结果"""
        text_regions = []
        page_index = page_idx
        
        base = None
        if isinstance(page_json, dict):
            res = page_json.get("res")
            base = res if isinstance(res, dict) else page_json
            pruned = base.get("prunedResult") if isinstance(base, dict) else None
            if isinstance(pruned, dict):
                base = pruned
            pruned2 = base.get("pruned_result") if isinstance(base, dict) else None
            if isinstance(pruned2, dict):
                base = pruned2
            try:
                pi = res.get("page_index") if isinstance(res, dict) else None
                if pi is not None and not isinstance(pi, bool):
                    page_index = int(float(pi))
            except Exception:
                pass
        
        log_kv("OCR page_result json 概览", {
            "req_id": req_id,
            "page_idx": page_idx,
            "page_result_type": type(page_result).__name__,
            "page_json_keys": list(page_json.keys())[:80] if isinstance(page_json, dict) else None,
            "base_keys": list(base.keys())[:80] if isinstance(base, dict) else None,
        })
        
        if isinstance(base, dict):
            text_regions = OCRService._extract_from_base_dict(base, req_id, page_idx)
        elif isinstance(page_result, list):
            text_regions = OCRService._extract_from_list(page_result)
        
        return text_regions, page_index
    
    @staticmethod
    def _extract_from_base_dict(base: Dict, req_id: str, page_idx: int) -> List[Dict]:
        """从base字典提取"""
        rec_texts = OCRService.as_list(base.get("rec_texts"))
        rec_scores = OCRService.as_list(base.get("rec_scores"))
        rec_polys = OCRService.as_list(base.get("rec_polys"))
        rec_boxes = OCRService.as_list(base.get("rec_boxes"))
        dt_polys = OCRService.as_list(base.get("dt_polys"))
        dt_scores = OCRService.as_list(base.get("dt_scores"))
        
        log_kv("OCR base 字段长度", {
            "req_id": req_id,
            "page_idx": page_idx,
            "rec_texts": len(rec_texts),
            "rec_scores": len(rec_scores),
            "rec_polys": len(rec_polys),
            "rec_boxes": len(rec_boxes),
            "dt_polys": len(dt_polys),
            "dt_scores": len(dt_scores),
        })
        
        text_regions = []
        for i in range(len(rec_texts)):
            text = rec_texts[i]
            confidence = (
                float(rec_scores[i]) if i < len(rec_scores) else
                (float(dt_scores[i]) if i < len(dt_scores) else 0.0)
            )
            poly_raw = (
                rec_polys[i] if i < len(rec_polys) else
                (dt_polys[i] if i < len(dt_polys) else None)
            )
            bbox_raw = rec_boxes[i] if i < len(rec_boxes) else None
            
            poly = to_xy_points(poly_raw)
            bbox = normalize_bbox(bbox_raw)
            if not bbox and poly:
                bbox = bbox_from_points(poly)
            
            text_regions.append({
                "text": text,
                "confidence": confidence,
                "bbox": bbox,
                "poly": poly
            })
        
        return text_regions
    
    @staticmethod
    def _extract_from_list(page_result: List) -> List[Dict]:
        """从列表提取"""
        text_regions = []
        for item in page_result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                poly = item[0]
                txt = item[1][0] if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1 else ""
                conf = float(item[1][1]) if isinstance(item[1], (list, tuple)) and len(item[1]) >= 2 else 0.0
                
                xs = []
                ys = []
                if isinstance(poly, (list, tuple)):
                    for p in poly:
                        if isinstance(p, (list, tuple)) and len(p) >= 2:
                            xs.append(float(p[0]))
                            ys.append(float(p[1]))
                
                bbox = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
                poly2 = to_xy_points(poly)
                bbox2 = bbox if bbox else bbox_from_points(poly2)
                
                text_regions.append({
                    "text": txt,
                    "confidence": conf,
                    "bbox": bbox2,
                    "poly": poly2
                })
        
        return text_regions
