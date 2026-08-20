# 外部文档解析服务适配器（各服务商的解析调用 + 结果归一化）
from .zhipu_parser import parse_pdf as zhipu_parse_pdf, normalize as zhipu_normalize

# 解析器注册表：provider_id -> (原始调用, 归一化)
PARSER_REGISTRY = {
    "zhipu": {
        "parse": zhipu_parse_pdf,
        "normalize": zhipu_normalize,
    },
}

__all__ = ["PARSER_REGISTRY"]
