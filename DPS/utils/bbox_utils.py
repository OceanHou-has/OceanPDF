"""边界框处理工具"""
from typing import List, Dict, Any, Optional, Tuple


def to_xy_points(poly) -> List[List[float]]:
    """转换多边形坐标为XY点列表"""
    if poly is None:
        return []
    if hasattr(poly, "tolist"):
        try:
            poly = poly.tolist()
        except Exception:
            pass
    if isinstance(poly, (tuple, list)):
        if len(poly) == 0:
            return []
        if len(poly) == 4 and all(isinstance(p, (list, tuple)) and len(p) >= 2 for p in poly):
            pts = []
            for p in poly[:4]:
                try:
                    pts.append([float(p[0]), float(p[1])])
                except Exception:
                    return []
            return pts
        if len(poly) >= 8 and all(isinstance(x, (int, float, str)) for x in poly[:8]):
            pts = []
            for i in range(0, 8, 2):
                try:
                    pts.append([float(poly[i]), float(poly[i + 1])])
                except Exception:
                    return []
            return pts
    return []


def bbox_from_points(pts: List[List[float]]) -> List[float]:
    """从点列表计算边界框"""
    if not isinstance(pts, list) or not pts:
        return []
    xs = []
    ys = []
    for p in pts:
        if not (isinstance(p, (list, tuple)) and len(p) >= 2):
            continue
        try:
            xs.append(float(p[0]))
            ys.append(float(p[1]))
        except Exception:
            continue
    if not xs or not ys:
        return []
    x0 = min(xs)
    y0 = min(ys)
    x1 = max(xs)
    y1 = max(ys)
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return [x0, y0, x1, y1]


def normalize_bbox(bbox) -> List[float]:
    """归一化边界框"""
    if bbox is None:
        return []
    if hasattr(bbox, "tolist"):
        try:
            bbox = bbox.tolist()
        except Exception:
            pass
    if isinstance(bbox, (tuple, list)):
        if len(bbox) >= 4 and all(isinstance(x, (int, float, str)) for x in bbox[:4]):
            try:
                x0 = float(bbox[0])
                y0 = float(bbox[1])
                x1 = float(bbox[2])
                y1 = float(bbox[3])
            except Exception:
                return []
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0
            return [x0, y0, x1, y1]
        pts = to_xy_points(bbox)
        if pts:
            return bbox_from_points(pts)
        if len(bbox) == 4 and all(isinstance(p, (list, tuple)) and len(p) >= 2 for p in bbox):
            pts2 = []
            for p in bbox:
                try:
                    pts2.append([float(p[0]), float(p[1])])
                except Exception:
                    return []
            return bbox_from_points(pts2)
    return []


def normalize_boxes(boxes) -> List[Dict[str, Any]]:
    """归一化边界框列表"""
    if not isinstance(boxes, list):
        return []

    out = []
    for b in boxes:
        if not isinstance(b, dict):
            continue
        label = b.get("label")
        score = b.get("score", 0.0)
        coord = b.get("coordinate")
        if not (isinstance(coord, list) and len(coord) >= 4):
            bbox = b.get("bbox")
            if isinstance(bbox, list) and len(bbox) >= 4:
                coord = bbox[:4]
            else:
                pts = b.get("points")
                if isinstance(pts, list) and len(pts) >= 4:
                    xs = []
                    ys = []
                    for p in pts:
                        if isinstance(p, (list, tuple)) and len(p) >= 2:
                            xs.append(float(p[0]))
                            ys.append(float(p[1]))
                    if xs and ys:
                        coord = [min(xs), min(ys), max(xs), max(ys)]
        if not (isinstance(coord, list) and len(coord) >= 4):
            continue
        try:
            clean_coord = [float(coord[0]), float(coord[1]), float(coord[2]), float(coord[3])]
        except Exception:
            continue
        out.append(
            {
                "label": str(label) if label is not None else "text",
                "score": float(score) if score is not None else 0.0,
                "coordinate": clean_coord,
            }
        )
    return out


def boxes_merge_large(boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """合并大边界框（移除被完全包含的小框）"""
    if not isinstance(boxes, list) or len(boxes) <= 1:
        return boxes if isinstance(boxes, list) else []

    coords = []
    for i, b in enumerate(boxes):
        c = b.get("coordinate") if isinstance(b, dict) else None
        if not (isinstance(c, list) and len(c) >= 4):
            coords.append(None)
            continue
        x0, y0, x1, y1 = float(c[0]), float(c[1]), float(c[2]), float(c[3])
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        coords.append((x0, y0, x1, y1))

    removed = set()
    areas = []
    for c in coords:
        if c is None:
            areas.append(0.0)
        else:
            areas.append(max(0.0, (c[2] - c[0]) * (c[3] - c[1])))

    eps = 1e-6
    n = len(boxes)
    for i in range(n):
        ci = coords[i]
        if ci is None or i in removed:
            continue
        for j in range(n):
            if i == j:
                continue
            cj = coords[j]
            if cj is None or j in removed:
                continue
            if areas[i] + eps < areas[j]:
                continue
            if ci[0] <= cj[0] + eps and ci[1] <= cj[1] + eps and ci[2] >= cj[2] - eps and ci[3] >= cj[3] - eps:
                if areas[i] > areas[j] + eps:
                    removed.add(j)

    if not removed:
        return boxes
    return [b for idx, b in enumerate(boxes) if idx not in removed]
