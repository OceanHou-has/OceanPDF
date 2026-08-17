"""环境变量工具"""
import os


def bool_from_env(name: str, default: bool) -> bool:
    """从环境变量读取布尔值"""
    v = os.getenv(name)
    if v is None:
        return default
    s = v.strip().lower()
    if s in ("1", "true", "yes", "y", "t"):
        return True
    if s in ("0", "false", "no", "n", "f"):
        return False
    return default


def env_get_int(name: str):
    """从环境变量读取整数"""
    raw = os.getenv(name)
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def env_get_float(name: str):
    """从环境变量读取浮点数"""
    raw = os.getenv(name)
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def env_get_str(name: str):
    """从环境变量读取字符串"""
    raw = os.getenv(name)
    if raw is None:
        return None
    s = raw.strip()
    return s if s else None
