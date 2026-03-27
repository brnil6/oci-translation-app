from __future__ import annotations

import json
import logging
import time
from typing import Generator

logger = logging.getLogger(__name__)

from core.auth import get_oci_config, get_signer
from core.config import (
    COMPARTMENT_ID,
    ENDPOINT,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
)
from core.models import TranslateRequest, TranslateResponse
from core.prompt import build_system_prompt, build_user_prompt


def _api_format(model_id: str) -> str:
    """Return the OCI GenAI API format for a given model ID."""
    mid = model_id.lower()
    if mid.startswith("cohere") and "command-a" not in mid:
        return "COHERE"
    if mid.startswith("cohere"):
        return "COHEREV2"
    return "GENERIC"


def _build_chat_detail(req: TranslateRequest, *, stream: bool = False):
    """Build an OCI ChatDetails object for the given request."""
    import oci.generative_ai_inference.models as models

    system_prompt = build_system_prompt(req.source_language, req.target_language)
    user_prompt = build_user_prompt(req.text)
    fmt = _api_format(req.model_id)

    if fmt == "COHERE":
        chat_request = models.CohereChatRequest(
            message=f"{system_prompt}\n\n{user_prompt}",
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            api_format="COHERE",
            is_stream=stream,
        )
    elif fmt == "COHEREV2":
        chat_request = models.CohereChatRequestV2(
            messages=[
                models.CohereSystemMessageV2(
                    content=[models.CohereTextContentV2(text=system_prompt)]
                ),
                models.CohereUserMessageV2(
                    content=[models.CohereTextContentV2(text=user_prompt)]
                ),
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            api_format="COHEREV2",
            is_stream=stream,
        )
    else:
        chat_request = models.GenericChatRequest(
            messages=[
                models.SystemMessage(
                    content=[models.TextContent(text=system_prompt)]
                ),
                models.UserMessage(
                    content=[models.TextContent(text=user_prompt)]
                ),
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            api_format="GENERIC",
            is_stream=stream,
        )

    return models.ChatDetails(
        compartment_id=COMPARTMENT_ID,
        serving_mode=models.OnDemandServingMode(model_id=req.model_id),
        chat_request=chat_request,
    )


def _get_client():
    """Create an OCI GenerativeAiInferenceClient."""
    import oci.generative_ai_inference

    signer = get_signer()
    oci_config = get_oci_config()
    return oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=oci_config, signer=signer, service_endpoint=ENDPOINT,
    )


def _extract_translated_text(chat_resp, fmt: str) -> str:
    """Extract the translated text from a chat response object."""
    if fmt == "COHERE":
        return chat_resp.text.strip()
    if fmt == "COHEREV2":
        # CohereChatResponseV2 has .message (CohereAssistantMessageV2) with .content list
        for content in chat_resp.message.content:
            if hasattr(content, "text") and content.text:
                return content.text.strip()
        return ""
    # GENERIC
    return chat_resp.choices[0].message.content[0].text.strip()


def translate_sync(req: TranslateRequest) -> TranslateResponse:
    """Synchronous translation using OCI GenAI Python SDK."""
    client = _get_client()
    chat_detail = _build_chat_detail(req, stream=False)

    start = time.perf_counter()
    response = client.chat(chat_detail)
    elapsed_ms = (time.perf_counter() - start) * 1000

    fmt = _api_format(req.model_id)
    translated = _extract_translated_text(response.data.chat_response, fmt)

    return TranslateResponse(
        translated_text=translated,
        source_language=req.source_language,
        target_language=req.target_language,
        model_id=req.model_id,
        latency_ms=round(elapsed_ms, 2),
    )


def translate_stream(req: TranslateRequest) -> Generator[str, None, None]:
    """Streaming translation using OCI SDK with SSE — yields text chunks, then "[DONE]"."""
    client = _get_client()
    chat_detail = _build_chat_detail(req, stream=True)
    fmt = _api_format(req.model_id)

    response = client.chat(chat_detail)

    # When is_stream=True, response.data is an SSEClient with .events()
    for event in response.data.events():
        data = event.data.strip()
        if data == "[DONE]":
            break
        if not data:
            continue
        try:
            chunk = json.loads(data)
            chat_resp = chunk.get("chatResponse", {})
            if fmt == "COHERE":
                text = chat_resp.get("text", "")
            elif fmt == "COHEREV2":
                msg = chat_resp.get("message", {})
                content_list = msg.get("content", [])
                text = ""
                for c in content_list:
                    if c.get("type") == "TEXT":
                        text = c.get("text", "")
                        break
            else:
                choices = chat_resp.get("choices", [])
                if choices:
                    delta = choices[0].get("message", {}).get("content", [])
                    text = delta[0].get("text", "") if delta else ""
                else:
                    text = ""
            if text:
                yield text
        except json.JSONDecodeError:
            continue
    yield "[DONE]"
