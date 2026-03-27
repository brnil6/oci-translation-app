from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from core.models import TranslateRequest, TranslateResponse
from core.translator import translate_stream, translate_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Translation API", version="1.0.0")


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    try:
        return translate_sync(req)
    except Exception as e:
        logger.exception("Sync translation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate/stream")
def translate_sse(req: TranslateRequest):
    def event_generator():
        try:
            for chunk in translate_stream(req):
                if chunk == "[DONE]":
                    yield "data: [DONE]\n\n"
                else:
                    yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.exception("Stream translation failed")
            yield f"data: {{\"error\": \"{e}\"}}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
