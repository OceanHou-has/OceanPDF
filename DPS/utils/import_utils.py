"""动态导入工具"""
from core.logger import log_kv


def try_import_paddle():
    """尝试导入 paddle"""
    try:
        import paddle
        return paddle
    except Exception as e:
        log_kv("import paddle 失败", repr(e))
        return None


def try_import_paddleocr():
    """尝试导入 PaddleOCR"""
    try:
        from paddleocr import PaddleOCR
        return PaddleOCR
    except Exception as e:
        log_kv("import PaddleOCR 失败", repr(e))
        return None


def try_import_paddleocr_pkg():
    """尝试导入 paddleocr 包"""
    try:
        import paddleocr
        return paddleocr
    except Exception as e:
        log_kv("import paddleocr 包失败", repr(e))
        return None


def try_import_fitz():
    """尝试导入 fitz(PyMuPDF)"""
    try:
        import fitz
        return fitz
    except Exception as e:
        log_kv("import fitz(PyMuPDF) 失败", repr(e))
        return None
