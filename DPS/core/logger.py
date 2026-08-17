"""日志工具模块"""
import time
from typing import Any


def now_ts() -> str:
    """获取当前时间戳字符串"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def log_kv(title: str, value: Any) -> None:
    """打印键值对日志"""
    print(f"[{now_ts()}] {title}: {value}")


# 全局logger实例
logger = {
    "log_kv": log_kv,
    "now_ts": now_ts,
}
