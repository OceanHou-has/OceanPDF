"""
论文 AI 问答服务
1. 从已解析 PDF 的结果中拼接论文全文上下文
2. 复用通用 LLM 客户端进行流式问答
"""
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger

from app.services.document_parser.layout_paths import get_layout_json_path
from app.services.translation.llm_service import create_translation_service

# 拼接论文上下文时的最大字符数（超出截断，避免超过模型上下文窗口）
MAX_CONTEXT_CHARS = 20000

# 多轮对话历史最多回传的轮数
MAX_HISTORY_TURNS = 8

# 版面结果中作为正文/标题/摘要保留的标签
_KEEP_LABELS = {
    "doc_title", "title", "text", "abstract", "paragraph_title", "section_title",
    "section_title_2", "section_title_3", "figure_caption", "table_caption", "figure_title", "table_title",
}
# 版面结果中需要跳过的标签（参考文献、图表本体、公式、页眉页脚等）
_SKIP_LABELS = {
    "reference", "figure", "table", "equation", "formula", "header", "footer", "footnote", "abandon",
}

SYSTEM_PROMPT = (
    "你是一位专业的学术论文阅读助手，帮助用户理解一篇论文。"
    "你会收到论文的完整内容以及用户的问题。请遵循以下要求：\n"
    "1. 用中文回答；\n"
    "2. 回答紧扣论文内容，不要编造论文中不存在的信息；\n"
    "3. 如果论文内容不足以回答，请如实说明；\n"
    "4. 适当引用论文中的原文、章节标题或术语，帮助用户定位；\n"
    "5. 解释尽量通俗易懂，但保留必要的专业准确性。"
)


def _read_llm_config() -> Dict:
    """读取本地翻译/LLM 配置（与翻译功能共用同一份配置）"""
    config_file = Path("storage/config/translation_config.json")
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取 LLM 配置失败: {e}")
    return {}


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n……（论文内容过长，已截断）"


def _sort_key_box(box: Dict):
    coord = box.get("coordinate") or [0, 0, 0, 0]
    return (coord[1], coord[0])


def build_paper_context(pdf_name: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    拼接论文全文上下文。

    优先使用版面分析结果（{provider}.json / dps.json），其 boxes 携带整段文本
    ocr_text 与 label；不存在时回退到 parsed.json 的逐元素文本。
    """
    # 1) 优先使用版面结果中的整段文本
    try:
        layout_path = get_layout_json_path(pdf_name)
        if layout_path.exists():
            with open(layout_path, "r", encoding="utf-8") as f:
                layout = json.load(f)

            parts: List[str] = []
            pages = (layout.get("raw") or {}).get("pages") or []
            for page in pages:
                boxes = page.get("boxes") or []
                for box in sorted(boxes, key=_sort_key_box):
                    label = (box.get("label") or "").strip()
                    text = (box.get("ocr_text") or "").strip()
                    if not text:
                        continue
                    if label in _SKIP_LABELS:
                        continue
                    if label in {"doc_title", "title"}:
                        parts.append(f"【标题】{text}")
                    elif label in {"paragraph_title", "section_title", "section_title_2", "section_title_3"}:
                        parts.append(f"\n【章节】{text}")
                    elif label == "abstract":
                        parts.append(f"【摘要】{text}")
                    elif label in {"figure_caption", "table_caption", "figure_title", "table_title"}:
                        parts.append(f"[图注/表注] {text}")
                    else:
                        parts.append(text)

            result = "\n".join(parts)
            if result.strip():
                return _truncate(result, max_chars)
    except Exception as e:
        logger.warning(f"读取版面结果失败，回退 parsed.json: {e}")

    # 2) 回退到 parsed.json
    from app.services.pdf_id_mapper import get_pdf_id_mapper
    mapper = get_pdf_id_mapper()
    pdf_id = mapper.get_or_create_id(pdf_name)
    parsed_path = Path("storage/parsed") / pdf_id / "parsed.json"
    if not parsed_path.exists():
        raise FileNotFoundError(f"未找到解析结果: {pdf_name}")

    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed = json.load(f)

    parts: List[str] = []
    for page in parsed.get("pages", []):
        elements = page.get("elements") or []
        for el in sorted(elements, key=lambda e: ((e.get("bbox") or [0, 0, 0, 0])[1], (e.get("bbox") or [0, 0, 0, 0])[0])):
            text = (el.get("text") or "").strip()
            if not text or el.get("type") == "abandon" or el.get("element_type") == "image":
                continue
            parts.append(text)

    return _truncate("\n".join(parts), max_chars)


def _build_messages(context: str, question: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """组装问答 messages：system + 论文上下文 + 历史对话 + 当前问题"""
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({
        "role": "user",
        "content": f"以下是论文的完整内容，请仔细阅读：\n\n{context}\n\n（论文内容结束）",
    })

    for item in (history or [])[-MAX_HISTORY_TURNS:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})
    return messages


async def stream_answer(
    pdf_name: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> AsyncGenerator[str, None]:
    """流式回答：逐 token yield 文本片段"""
    config = _read_llm_config()
    model_config = config.get("model_config") or {}
    api_key = (model_config.get("api_key") or config.get("deepseek_api_key") or "").strip()
    if not api_key:
        raise ValueError("未配置 LLM API Key，请先在「设置」中完成翻译/LLM 配置")

    context = build_paper_context(pdf_name)
    service = create_translation_service(api_key, {
        "provider": model_config.get("provider"),
        "base_url": model_config.get("base_url"),
        "model": model_config.get("model"),
    })

    messages = _build_messages(context, question, history)
    async for token in service.chat_stream_async(messages):
        yield token
