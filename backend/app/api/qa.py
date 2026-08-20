"""
论文 AI 问答接口
POST /api/v1/qa/ask —— SSE 流式返回回答
"""
import json
from typing import Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from app.services.qa_service import stream_answer

router = APIRouter()


class QARequest(BaseModel):
    pdf_name: str
    question: str
    history: Optional[List[Dict[str, str]]] = None


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@router.post("/qa/ask")
async def ask_paper(request: QARequest):
    """
    针对某篇已解析 PDF 进行 AI 问答（SSE 流式返回）

    返回帧：
      data: {"type":"delta","content":"..."}  逐 token 文本
      data: {"type":"done"}                    结束
      data: {"type":"error","message":"..."}   出错
    """
    async def event_generator():
        try:
            async for token in stream_answer(request.pdf_name, request.question, request.history):
                yield _sse({"type": "delta", "content": token})
            yield _sse({"type": "done"})
        except Exception as e:
            logger.error(f"AI 问答失败: {e}")
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
