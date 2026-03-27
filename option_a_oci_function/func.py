import io
import json
import logging

from fdk import response

from core.models import TranslateRequest, TranslateResponse
from core.translator import translate_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
        req = TranslateRequest(**body)
    except Exception as e:
        return response.Response(
            ctx,
            response_data=json.dumps({"error": str(e)}),
            headers={"Content-Type": "application/json"},
            status_code=400,
        )

    try:
        result: TranslateResponse = translate_sync(req)
        return response.Response(
            ctx,
            response_data=result.model_dump_json(),
            headers={"Content-Type": "application/json"},
            status_code=200,
        )
    except Exception as e:
        logger.exception("Translation failed")
        return response.Response(
            ctx,
            response_data=json.dumps({"error": str(e)}),
            headers={"Content-Type": "application/json"},
            status_code=500,
        )
