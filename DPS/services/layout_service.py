"""版面分析服务"""
import os
import tempfile
import time
from typing import Dict, Any, List

from core.logger import log_kv
from core.config import config
from core.model_loader import model_loader
from utils.bbox_utils import normalize_boxes, boxes_merge_large
from utils.import_utils import try_import_fitz
from utils.env_utils import bool_from_env


class LayoutService:
    """版面分析服务"""
    
    @staticmethod
    def pdf_page_dims(pdf_path: str, zoom: float) -> Dict[int, Dict[str, float]]:
        """获取PDF页面尺寸"""
        fitz = try_import_fitz()
        if fitz is None:
            return {}
        try:
            doc = fitz.open(pdf_path)
            dims = {}
            for i in range(len(doc)):
                r = doc[i].rect
                pdf_w = float(r.width)
                pdf_h = float(r.height)
                rendered_w = int(pdf_w * float(zoom))
                rendered_h = int(pdf_h * float(zoom))
                dims[i] = {
                    "width": rendered_w,
                    "height": rendered_h,
                    "rendered_width": rendered_w,
                    "rendered_height": rendered_h,
                    "pdf_width": pdf_w,
                    "pdf_height": pdf_h,
                }
            return dims
        except Exception as e:
            log_kv("读取 PDF 页面尺寸失败", {"pdf": pdf_path, "zoom": zoom, "err": repr(e)})
            return {}
    
    @staticmethod
    def _scale_bbox(bbox, scale_x: float, scale_y: float) -> List[float]:
        if not (isinstance(bbox, list) and len(bbox) >= 4):
            return bbox
        try:
            return [
                float(bbox[0]) * scale_x,
                float(bbox[1]) * scale_y,
                float(bbox[2]) * scale_x,
                float(bbox[3]) * scale_y,
            ]
        except Exception:
            return bbox

    @staticmethod
    def _convert_page_to_pdf_coords(page_data: Dict[str, Any], req_id: str) -> Dict[str, Any]:
        dims = page_data.get("_dims") or {}
        rendered_w = float(dims.get("rendered_width") or page_data.get("width") or 0)
        rendered_h = float(dims.get("rendered_height") or page_data.get("height") or 0)
        pdf_w = float(dims.get("pdf_width") or 0)
        pdf_h = float(dims.get("pdf_height") or 0)

        if rendered_w <= 0 or rendered_h <= 0 or pdf_w <= 0 or pdf_h <= 0:
            page_data.pop("_dims", None)
            return page_data

        scale_x = pdf_w / rendered_w
        scale_y = pdf_h / rendered_h

        for box in page_data.get("boxes") or []:
            if isinstance(box, dict):
                box["coordinate"] = LayoutService._scale_bbox(
                    box.get("coordinate"), scale_x, scale_y
                )

        for region in page_data.get("ocr_text_regions") or []:
            if isinstance(region, dict):
                region["bbox"] = LayoutService._scale_bbox(
                    region.get("bbox"), scale_x, scale_y
                )

        page_data["width"] = pdf_w
        page_data["height"] = pdf_h
        page_data["coordinate_space"] = "pdf_points"
        page_data["source_render"] = {
            "zoom": float(config.render_zoom),
            "width": rendered_w,
            "height": rendered_h,
        }
        page_data.pop("_dims", None)

        log_kv("DPS bbox converted to PDF points", {
            "req_id": req_id,
            "page_index": page_data.get("page_index"),
            "scale_x": round(scale_x, 6),
            "scale_y": round(scale_y, 6),
            "pdf_width": round(pdf_w, 2),
            "pdf_height": round(pdf_h, 2),
        })
        return page_data

    @staticmethod
    def extract_page_index_and_boxes(page_json: Dict, fallback_page_idx: int):
        """提取页面索引和边界框"""
        if not isinstance(page_json, dict):
            return fallback_page_idx, []

        def _to_int(v, default: int) -> int:
            if isinstance(v, bool):
                return default
            if isinstance(v, (int, float)):
                return int(v)
            if isinstance(v, str):
                try:
                    return int(float(v.strip()))
                except Exception:
                    return default
            return default

        res = page_json.get("res")
        if isinstance(res, dict):
            page_index = _to_int(res.get("page_index", fallback_page_idx), fallback_page_idx)
            boxes = res.get("boxes")
            if boxes is None:
                lay = res.get("layout_det_res")
                if isinstance(lay, dict):
                    boxes = lay.get("boxes")
            return page_index, normalize_boxes(boxes)

        page_index = _to_int(page_json.get("page_index", fallback_page_idx), fallback_page_idx)
        boxes = page_json.get("boxes")
        return page_index, normalize_boxes(boxes)
    
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
                if hasattr(j, "keys") and hasattr(j, "get"):
                    try:
                        keys = list(j.keys())
                        return {k: j.get(k) for k in keys}
                    except Exception:
                        pass
            except Exception:
                pass
        if hasattr(res, "to_json"):
            try:
                j = res.to_json()
                if isinstance(j, dict):
                    return j
                if hasattr(j, "keys") and hasattr(j, "get"):
                    try:
                        keys = list(j.keys())
                        return {k: j.get(k) for k in keys}
                    except Exception:
                        pass
            except Exception:
                pass
        return {}
    
    @staticmethod
    def analyze_pdf(
        content: bytes,
        filename: str,
        req_id: str,
        with_ocr: bool = False,
        ocr_min_conf: float = 0.0,
        ocr_return_regions: bool = False,
    ) -> Dict[str, Any]:
        """分析PDF文档（可选附带OCR）"""
        # 确保模型已加载
        if model_loader.layout_model is None:
            raise RuntimeError("版面分析模型未加载")
        
        tmp_path = None
        pdf_doc = None
        try:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="doclayout_") as f:
                f.write(content)
                tmp_path = f.name
            
            # 获取页面尺寸
            dims_map = LayoutService.pdf_page_dims(tmp_path, config.render_zoom)
            log_kv("PDF 页面尺寸", {"req_id": req_id, "zoom": config.render_zoom, "pages": len(dims_map)})
            
            # 执行版面分析
            t0 = time.time()
            model = model_loader.layout_model
            
            if hasattr(model, "predict"):
                log_kv("调用版面分析模型.predict", {"req_id": req_id, "layout_nms": config.layout_nms})
                try:
                    results = model.predict(
                        tmp_path,
                        batch_size=1,
                        layout_nms=config.layout_nms,
                        layout_merge_bboxes_mode="large",
                    )
                except TypeError:
                    log_kv("predict 不支持 layout_merge_bboxes_mode，自动忽略", {"req_id": req_id})
                    results = model.predict(tmp_path, batch_size=1, layout_nms=config.layout_nms)
            elif callable(model):
                log_kv("调用版面分析模型(__call__)", {"req_id": req_id})
                results = model(tmp_path)
            else:
                raise RuntimeError(f"版面分析模型不可调用: {type(model)}")
            
            dt = round(time.time() - t0, 3)
            
            # 处理结果
            merged = {
                "status": "success",
                "req_id": req_id,
                "filename": filename,
                "elapsed_sec": dt,
                "pages": []
            }
            
            if not isinstance(results, list):
                log_kv("版面分析返回非 list，尝试包装", {"req_id": req_id, "type": type(results).__name__})
                results = [results]
            
            # 如果需要OCR，提前打开PDF文档（复用对象，避免重复打开）
            pdf_doc = None
            if with_ocr and model_loader.ocr_model is not None:
                fitz = try_import_fitz()
                if fitz is not None:
                    pdf_doc = fitz.open(tmp_path)
                    log_kv("OCR优化：已打开PDF文档对象", {"req_id": req_id, "pages": len(pdf_doc)})
            
            total_pages = len(results)
            
            # 第一阶段：处理所有页面的版面分析结果
            log_kv("阶段1：处理版面分析结果", {"req_id": req_id, "total_pages": total_pages})
            pages_data = []  # 存储所有页面的版面数据
            
            for i, page_result in enumerate(results):
                page_json = LayoutService.result_to_json(page_result)
                page_index, boxes = LayoutService.extract_page_index_and_boxes(page_json, fallback_page_idx=i)
                before_merge = len(boxes)
                boxes = boxes_merge_large(boxes)
                if before_merge != len(boxes):
                    log_kv("large 模式过滤内嵌小框", {
                        "req_id": req_id,
                        "page_index": page_index,
                        "before": before_merge,
                        "after": len(boxes)
                    })
                
                # 为每个box添加DPS_block_id（表示DPS模型返回的原始顺序）
                # 每页从1开始编号，这是模型输出的阅读顺序
                for idx, box in enumerate(boxes, start=1):
                    if isinstance(box, dict):
                        box["DPS_block_id"] = idx
                
                # 为需要阅读顺序的元素类型分配reading_order（基于DPS_block_id顺序）
                # 可排序类型：标题、段落、列表等
                sortable_labels = {
                    "doc_title", "paragraph_title", "abstract", "text"
                }
                
                reading_order = 1
                for box in boxes:
                    if isinstance(box, dict):
                        label = box.get("label", "")
                        # 只给可排序类型分配reading_order
                        if label in sortable_labels:
                            box["reading_order"] = reading_order
                            reading_order += 1
                        else:
                            # 其他类型（图表、公式等）不参与阅读顺序
                            box["reading_order"] = None
                
                log_kv("DPS阅读顺序已标记", {
                    "req_id": req_id,
                    "page_index": page_index,
                    "boxes_count": len(boxes),
                    "sortable_count": reading_order - 1,
                })
                
                # 获取页面尺寸
                dims = dims_map.get(page_index) or dims_map.get(i) or {}
                width = dims.get("width", 0)
                height = dims.get("height", 0)
                
                pages_data.append({
                    "page_index": page_index,
                    "boxes": boxes,
                    "width": width,
                    "height": height,
                    "_dims": dims,
                })
            
            # 第二阶段：批量执行OCR识别（如果需要）
            all_ocr_regions = []  # 存储所有页面的OCR结果
            ocr_start_time = 0.0  # 初始化时间变量
            if with_ocr and model_loader.ocr_model is not None and pdf_doc is not None:
                log_kv("阶段2：批量OCR识别", {"req_id": req_id, "total_pages": total_pages})
                ocr_start_time = time.time()
                
                for i, page_data in enumerate(pages_data):
                    page_index = page_data["page_index"]
                    
                    # 记录OCR进度
                    ocr_progress = ((i + 1) * 100) // total_pages
                    elapsed = time.time() - ocr_start_time
                    avg_time = elapsed / (i + 1)
                    remaining = avg_time * (total_pages - i - 1)
                    
                    log_kv("OCR进度", {
                        "req_id": req_id,
                        "current_page": i + 1,
                        "total_pages": total_pages,
                        "progress": f"{ocr_progress}%",
                        "elapsed_sec": round(elapsed, 2),
                        "avg_per_page": round(avg_time, 2),
                        "estimated_remaining": round(remaining, 2),
                    })
                    
                    # 只执行OCR识别，获取text_regions
                    ocr_regions = LayoutService._batch_ocr_recognize(
                        pdf_doc, page_index, req_id
                    )
                    all_ocr_regions.append(ocr_regions)
            
            # 第三阶段：批量分配OCR文本到版面框
            if with_ocr and len(all_ocr_regions) > 0:
                log_kv("阶段3：批量分配OCR文本", {"req_id": req_id, "total_pages": total_pages})
                
                for i, page_data in enumerate(pages_data):
                    boxes = page_data["boxes"]
                    ocr_regions = all_ocr_regions[i] if i < len(all_ocr_regions) else []
                    
                    # 分配OCR文本到版面框
                    boxes = LayoutService._assign_ocr_to_boxes(boxes, ocr_regions, ocr_min_conf)
                    page_data["boxes"] = boxes
                    
                    if ocr_return_regions:
                        page_data["ocr_text_regions"] = ocr_regions
            
            # 组装最终结果
            for page_data in pages_data:
                page_data = LayoutService._convert_page_to_pdf_coords(page_data, req_id)
                log_kv("页面结果", {
                    "req_id": req_id,
                    "page_index": page_data["page_index"],
                    "width": page_data["width"],
                    "height": page_data["height"],
                    "boxes": len(page_data["boxes"]),
                })
                
                merged["pages"].append(page_data)
            
            # 验证OCR结果
            if with_ocr and len(all_ocr_regions) > 0:
                total_ocr_time = time.time() - ocr_start_time
                total_boxes = sum(len(p.get("boxes", [])) for p in merged["pages"])
                total_ocr_chars = sum(
                    len(b.get("ocr_text", ""))
                    for p in merged["pages"]
                    for b in p.get("boxes", [])
                )
                boxes_with_text = sum(
                    1
                    for p in merged["pages"]
                    for b in p.get("boxes", [])
                    if (b.get("ocr_text") or "").strip()
                )
                
                log_kv("OCR完成统计", {
                    "req_id": req_id,
                    "total_pages": total_pages,
                    "total_ocr_time": round(total_ocr_time, 2),
                    "avg_time_per_page": round(total_ocr_time / total_pages, 2),
                    "total_boxes": total_boxes,
                    "boxes_with_text": boxes_with_text,
                    "total_chars": total_ocr_chars,
                    "coverage_rate": f"{(boxes_with_text * 100 // total_boxes) if total_boxes > 0 else 0}%"
                })
                
                if total_ocr_chars == 0:
                    log_kv("⚠️ 警告：OCR未识别到任何文本", {
                        "req_id": req_id,
                        "total_boxes": total_boxes,
                        "possible_reasons": ["PDF是扫描件", "图像质量差", "OCR模型未加载", "置信度阈值过高"]
                    })
            
            log_kv("请求完成", {"req_id": req_id, "pages": len(merged["pages"]), "elapsed_sec": dt})
            return merged
            
        finally:
            # 关闭PDF文档对象
            if pdf_doc is not None:
                try:
                    pdf_doc.close()
                    log_kv("PDF文档对象已关闭", {"req_id": req_id})
                except Exception as e:
                    log_kv("关闭PDF文档对象失败", {"req_id": req_id, "err": repr(e)})
            
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    log_kv("删除临时文件失败", {"req_id": req_id, "tmp_path": tmp_path, "err": repr(e)})
    
    @staticmethod
    def _batch_ocr_recognize(pdf_doc, page_index: int, req_id: str):
        """批量OCR识别：只执行OCR识别，返回text_regions，不分配到版面框
        
        Args:
            pdf_doc: PDF文档对象(fitz.Document)
            page_index: 页面索引
            req_id: 请求ID
            
        Returns:
            text_regions: OCR识别的文本区域列表
        """
        try:
            t_page = time.time()
            # 渲染PDF页面为图像
            fitz = try_import_fitz()
            if fitz is None:
                return []
            
            page = pdf_doc[page_index]
            mat = fitz.Matrix(config.render_zoom, config.render_zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            log_kv("OCR page rendered", {
                "req_id": req_id,
                "page_index": page_index,
                "pix": f"{pix.width}x{pix.height}",
                "elapsed_sec": round(time.time() - t_page, 3),
            })
            
            # 使用OCR模型识别
            import cv2
            import numpy as np
            nparr = np.frombuffer(img_data, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_bgr is None:
                return []
            
            # 调用OCR模型
            ocr_model = model_loader.ocr_model
            t_infer = time.time()
            log_kv("OCR inference start", {
                "req_id": req_id,
                "page_index": page_index,
                "model": type(ocr_model).__name__,
                "image_shape": img_bgr.shape if img_bgr is not None else None,
            })
            
            if hasattr(ocr_model, "predict"):
                ocr_results = ocr_model.predict(img_bgr)
            elif hasattr(ocr_model, "ocr"):
                # 尝试调用OCR
                try:
                    use_angle_cls = bool_from_env("OCR_USE_ANGLE_CLS", True)
                    ocr_results = ocr_model.ocr(img_bgr, cls=use_angle_cls)
                except TypeError as e:
                    if "cls" in str(e):
                        ocr_results = ocr_model.ocr(img_bgr)
                    else:
                        raise
            else:
                return []
            log_kv("OCR inference done", {
                "req_id": req_id,
                "page_index": page_index,
                "elapsed_sec": round(time.time() - t_infer, 3),
            })
            
            # 解析OCR结果
            ocr_result = ocr_results[0] if isinstance(ocr_results, list) and len(ocr_results) == 1 else ocr_results
            
            # 提取文本区域
            text_regions = []
            
            # 处理 OCRResult 对象（PaddleOCR 3.x 返回类字典对象）
            if hasattr(ocr_result, 'get'):
                dt_polys = ocr_result.get('dt_polys', [])
                rec_texts = ocr_result.get('rec_texts', ocr_result.get('rec_text', []))
                rec_scores = ocr_result.get('rec_scores', ocr_result.get('rec_score', []))
                
                # 确保列表长度一致
                max_len = max(len(dt_polys), len(rec_texts))
                while len(rec_texts) < max_len:
                    rec_texts.append("")
                while len(rec_scores) < max_len:
                    rec_scores.append(0.0)
                
                for i, poly in enumerate(dt_polys):
                    txt = rec_texts[i] if i < len(rec_texts) else ""
                    conf = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                    
                    # 计算bbox
                    xs = []
                    ys = []
                    if poly is not None:
                        for p in poly:
                            if isinstance(p, (list, tuple, np.ndarray)) and len(p) >= 2:
                                xs.append(float(p[0]))
                                ys.append(float(p[1]))
                    
                    bbox = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
                    if bbox and txt:  # 只添加有文本内容的区域
                        text_regions.append({
                            "text": txt,
                            "confidence": conf,
                            "bbox": bbox
                        })
            
            # 处理传统列表格式（旧版PaddleOCR）
            elif isinstance(ocr_result, list) and len(ocr_result) > 0:
                for item in ocr_result:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        poly = item[0]
                        txt = item[1][0] if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1 else ""
                        conf = float(item[1][1]) if isinstance(item[1], (list, tuple)) and len(item[1]) >= 2 else 0.0
                        
                        # 计算bbox
                        xs = []
                        ys = []
                        if isinstance(poly, (list, tuple)):
                            for p in poly:
                                if isinstance(p, (list, tuple)) and len(p) >= 2:
                                    xs.append(float(p[0]))
                                    ys.append(float(p[1]))
                        
                        bbox = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
                        if bbox and txt:
                            text_regions.append({
                                "text": txt,
                                "confidence": conf,
                                "bbox": bbox
                            })
            
            return text_regions
            
        except Exception as e:
            log_kv("OCR批量识别失败", {"req_id": req_id, "page_index": page_index, "err": repr(e)})
            return []
    
    @staticmethod
    def _add_ocr_to_boxes(boxes, pdf_doc_or_path, page_index: int, req_id: str, min_conf: float):
        """为版面框添加OCR识别结果
        
        Args:
            boxes: 版面框列表
            pdf_doc_or_path: PDF文档对象(fitz.Document)或PDF文件路径(str)
            page_index: 页面索引
            req_id: 请求ID
            min_conf: 最低置信度
        """
        from services.ocr_service import OCRService
        
        try:
            # 渲染PDF页面为图像
            fitz = try_import_fitz()
            if fitz is None:
                log_kv("OCR失败：fitz未安装", {"req_id": req_id, "page_index": page_index})
                return boxes, []
            
            # 支持传入已打开的文档对象或路径（向后兼容）
            if isinstance(pdf_doc_or_path, str):
                # 旧方式：传入路径，需要打开文档
                doc = fitz.open(pdf_doc_or_path)
                should_close = True
            else:
                # 新方式：直接使用已打开的文档对象
                doc = pdf_doc_or_path
                should_close = False
            
            page = doc[page_index]
            mat = fitz.Matrix(config.render_zoom, config.render_zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 使用OCR模型识别
            import cv2
            import numpy as np
            nparr = np.frombuffer(img_data, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_bgr is None:
                log_kv("OCR失败：图像解码失败", {"req_id": req_id, "page_index": page_index})
                return boxes, []
            
            # 调用OCR模型
            ocr_model = model_loader.ocr_model
            log_kv("准备调用OCR", {
                "req_id": req_id,
                "page_index": page_index,
                "ocr_model_type": type(ocr_model).__name__,
                "has_ocr_method": hasattr(ocr_model, "ocr"),
                "img_shape": img_bgr.shape if img_bgr is not None else None
            })
            
            if hasattr(ocr_model, "ocr"):
                # 尝试调用OCR，先尝试带cls参数，如果失败则不带参数
                try:
                    use_angle_cls = bool_from_env("OCR_USE_ANGLE_CLS", True)
                    log_kv("调用OCR（带cls）", {"req_id": req_id, "page_index": page_index, "use_angle_cls": use_angle_cls})
                    ocr_results = ocr_model.ocr(img_bgr, cls=use_angle_cls)
                    log_kv("OCR调用成功", {"req_id": req_id, "page_index": page_index})
                except TypeError as e:
                    # 如果cls参数不被支持，尝试不带参数调用
                    if "cls" in str(e):
                        log_kv("OCR模型不支持cls参数，使用默认调用", {"req_id": req_id, "page_index": page_index})
                        ocr_results = ocr_model.ocr(img_bgr)
                    else:
                        raise
            else:
                log_kv("OCR失败：模型不支持ocr方法", {"req_id": req_id})
                return boxes, []
            
            # 解析OCR结果
            log_kv("OCR原始结果类型", {
                "req_id": req_id,
                "page_index": page_index,
                "ocr_results_type": type(ocr_results).__name__,
                "ocr_results_len": len(ocr_results) if isinstance(ocr_results, (list, tuple)) else "N/A",
                "ocr_results_first_item_type": type(ocr_results[0]).__name__ if isinstance(ocr_results, (list, tuple)) and len(ocr_results) > 0 else "N/A"
            })
            
            # 关键：检查ocr_results的结构
            if isinstance(ocr_results, list) and len(ocr_results) > 0:
                first_item = ocr_results[0]
                log_kv("检查第一个OCR结果项", {
                    "req_id": req_id,
                    "page_index": page_index,
                    "first_item_type": type(first_item).__name__,
                    "has_dt_polys": hasattr(first_item, 'dt_polys'),
                    "has_rec_texts": hasattr(first_item, 'rec_texts'),
                    "has_rec_text": hasattr(first_item, 'rec_text'),
                    "first_item_attrs": [attr for attr in dir(first_item) if not attr.startswith('_')][:30]
                })
            
            ocr_result = ocr_results[0] if isinstance(ocr_results, list) and len(ocr_results) == 1 else ocr_results
            
            log_kv("OCR解析后结果", {
                "req_id": req_id,
                "page_index": page_index,
                "ocr_result_type": type(ocr_result).__name__,
                "ocr_result_len": len(ocr_result) if isinstance(ocr_result, (list, tuple)) else "N/A",
                "ocr_result_sample": str(ocr_result)[:500] if ocr_result else "empty"
            })
            
            # 提取文本区域
            text_regions = []
            
            # 处理 OCRResult 对象（PaddleOCR 3.x 返回类字典对象）
            # 使用字典访问方式而非属性访问
            if hasattr(ocr_result, 'get'):
                # 使用字典方式访问OCRResult对象
                dt_polys = ocr_result.get('dt_polys', [])
                rec_texts = ocr_result.get('rec_texts', ocr_result.get('rec_text', []))
                rec_scores = ocr_result.get('rec_scores', ocr_result.get('rec_score', []))
                
                log_kv("OCRResult属性解析", {
                    "req_id": req_id,
                    "page_index": page_index,
                    "dt_polys_len": len(dt_polys),
                    "rec_texts_len": len(rec_texts),
                    "rec_scores_len": len(rec_scores),
                    "has_rec_texts": hasattr(ocr_result, 'rec_texts'),
                    "has_rec_text": hasattr(ocr_result, 'rec_text'),
                })
                
                # 确保列表长度一致
                max_len = max(len(dt_polys), len(rec_texts))
                while len(rec_texts) < max_len:
                    rec_texts.append("")
                while len(rec_scores) < max_len:
                    rec_scores.append(0.0)
                
                for i, poly in enumerate(dt_polys):
                    txt = rec_texts[i] if i < len(rec_texts) else ""
                    conf = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                    
                    # 计算bbox
                    xs = []
                    ys = []
                    if poly is not None:
                        for p in poly:
                            if isinstance(p, (list, tuple, np.ndarray)) and len(p) >= 2:
                                xs.append(float(p[0]))
                                ys.append(float(p[1]))
                    
                    bbox = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
                    if bbox and txt:  # 只添加有文本内容的区域
                        text_regions.append({
                            "text": txt,
                            "confidence": conf,
                            "bbox": bbox
                        })
            
            # 处理传统列表格式（旧版PaddleOCR）
            elif isinstance(ocr_result, list) and len(ocr_result) > 0:
                for item in ocr_result:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        poly = item[0]
                        txt = item[1][0] if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1 else ""
                        conf = float(item[1][1]) if isinstance(item[1], (list, tuple)) and len(item[1]) >= 2 else 0.0
                        
                        # 计算bbox
                        xs = []
                        ys = []
                        if isinstance(poly, (list, tuple)):
                            for p in poly:
                                if isinstance(p, (list, tuple)) and len(p) >= 2:
                                    xs.append(float(p[0]))
                                    ys.append(float(p[1]))
                        
                        bbox = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
                        if bbox and txt:  # 只添加有文本内容的区域
                            text_regions.append({
                                "text": txt,
                                "confidence": conf,
                                "bbox": bbox
                            })
            
            log_kv("版面分析附带OCR结果", {
                "req_id": req_id,
                "page_index": page_index,
                "text_regions_extracted": len(text_regions),
                "min_conf": min_conf,
            })
            
            if len(text_regions) == 0:
                log_kv("⚠️ 警告：当前页OCR未提取到任何文本区域", {
                    "req_id": req_id,
                    "page_index": page_index,
                    "ocr_result_type": type(ocr_result).__name__,
                    "ocr_result_len": len(ocr_result) if isinstance(ocr_result, (list, tuple)) else "N/A",
                })
            
            # 将OCR结果分配给版面框
            boxes = LayoutService._assign_ocr_to_boxes(boxes, text_regions, min_conf)
            
            # 统计本页OCR结果
            ocr_chars = sum(len(b.get("ocr_text", "")) for b in boxes)
            boxes_with_ocr = sum(1 for b in boxes if (b.get("ocr_text") or "").strip())
            
            log_kv("页面OCR完成", {
                "req_id": req_id,
                "page_index": page_index,
                "total_boxes": len(boxes),
                "boxes_with_text": boxes_with_ocr,
                "total_chars": ocr_chars,
                "ocr_regions": len(text_regions),
            })
            
            return boxes, text_regions
            
        except Exception as e:
            log_kv("OCR处理失败", {"req_id": req_id, "page_index": page_index, "err": repr(e)})
            import traceback
            log_kv("OCR错误堆栈", {"req_id": req_id, "traceback": traceback.format_exc()})
            return boxes, []
        finally:
            # 如果是在函数内部打开的文档，需要关闭
            if 'should_close' in locals() and should_close and 'doc' in locals():
                try:
                    doc.close()
                except Exception:
                    pass
    
    @staticmethod
    def _assign_ocr_to_boxes(boxes, text_regions, min_conf: float):
        """将OCR文本区域分配给版面框"""
        if not boxes:
            return boxes
        if not text_regions:
            for b in boxes:
                if isinstance(b, dict):
                    b["ocr_text"] = ""
                    b["ocr_avg_confidence"] = 0.0
            return boxes
        
        # 过滤低置信度的OCR结果
        valid_regions = []
        for r in text_regions:
            if not isinstance(r, dict):
                continue
            conf = r.get("confidence", 0.0)
            bbox = r.get("bbox")
            if not (isinstance(bbox, list) and len(bbox) >= 4):
                continue
            try:
                if float(conf) < float(min_conf):
                    continue
            except Exception:
                pass
            valid_regions.append(r)
        
        # 为每个版面框分配包含的OCR文本
        for b in boxes:
            if not isinstance(b, dict):
                continue
            c = b.get("coordinate")
            if not (isinstance(c, list) and len(c) >= 4):
                b["ocr_text"] = ""
                b["ocr_avg_confidence"] = 0.0
                continue
            try:
                x0, y0, x1, y1 = float(c[0]), float(c[1]), float(c[2]), float(c[3])
            except Exception:
                b["ocr_text"] = ""
                b["ocr_avg_confidence"] = 0.0
                continue
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0
            
            # 找到包含在该版面框内的所有OCR文本区域
            hits = []
            for r in valid_regions:
                rb = r.get("bbox")
                try:
                    rx0, ry0, rx1, ry1 = float(rb[0]), float(rb[1]), float(rb[2]), float(rb[3])
                except Exception:
                    continue
                cx = (rx0 + rx1) * 0.5
                cy = (ry0 + ry1) * 0.5
                if cx >= x0 and cx <= x1 and cy >= y0 and cy <= y1:
                    hits.append(r)
            
            # 按位置排序（从上到下，从左到右）
            hits.sort(key=lambda r: ((float(r["bbox"][1]) + float(r["bbox"][3])) * 0.5, (float(r["bbox"][0]) + float(r["bbox"][2])) * 0.5))
            texts = [str(r.get("text") or "") for r in hits if (r.get("text") or "") != ""]
            confs = []
            for r in hits:
                try:
                    confs.append(float(r.get("confidence", 0.0)))
                except Exception:
                    pass
            b["ocr_text"] = " ".join(texts)  # 用空格连接
            b["ocr_avg_confidence"] = (sum(confs) / len(confs)) if confs else 0.0
        
        return boxes
