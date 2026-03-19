"""Batch image-generation routes."""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from loguru import logger
import os
import tempfile
from typing import List, Optional

from ...database import get_db_manager
from ...engine import TaskManager
from ...extractor import get_extractor
from ...matcher import get_matcher
from ...models.image import ImageParams
from ...models.task import BatchTask
from ...parsers import get_parser
from ...workflows import build_pdf_prompt
from .chat import _require_api_key


router = APIRouter(prefix="/api/v1", tags=["batch"])


def get_task_manager(request: Request) -> TaskManager:
    """Return the shared task manager."""
    return request.app.state.task_manager


def _apply_default_params(params: ImageParams, default_params: Optional[dict]) -> ImageParams:
    if not default_params:
        return params
    if "width" in default_params:
        params.width = default_params["width"]
    if "height" in default_params:
        params.height = default_params["height"]
    if "style" in default_params:
        params.style = default_params["style"]
    if "quality" in default_params:
        params.quality = default_params["quality"]
    if "n" in default_params:
        params.n = default_params["n"]
    return params


@router.post("/batch", response_model=BatchTask)
async def batch_generate(
    prompts: Optional[List[str]] = None,
    file: Optional[UploadFile] = File(None),
    provider: Optional[str] = None,
    default_params: Optional[dict] = None,
    task_manager: TaskManager = Depends(get_task_manager),
    http_request: Request = None,
):
    """Submit a batch image-generation job."""
    try:
        db_manager = get_db_manager()
        api_key = _require_api_key(http_request)
        params_list: List[ImageParams] = []
        user_inputs: List[str] = []

        user_request_data = {
            "type": "batch_generation",
            "prompts": prompts or [],
            "provider": provider,
            "default_params": default_params or {},
            "file_upload": file.filename if file else None,
        }

        extractor = get_extractor(api_key=api_key)
        matcher = get_matcher(api_key=api_key)

        if file:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(file.filename or "")[1],
            ) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name

            try:
                file_ext = os.path.splitext(file.filename or "")[1].lower()

                if file_ext == ".pdf":
                    pdf_prompt = await build_pdf_prompt(
                        tmp_file_path,
                        user_instruction="",
                        api_key=api_key,
                    )
                    prompt_candidates = pdf_prompt.page_prompts or [pdf_prompt.prompt]

                    for prompt_text in prompt_candidates:
                        params = ImageParams(
                            prompt=prompt_text,
                            width=1024,
                            height=1024,
                            style=pdf_prompt.style,
                            quality="standard",
                            n=1,
                            provider=provider,
                            api_key=api_key,
                            extra_params={
                                "document_context": {
                                    "source": "pdf",
                                    "page_count": pdf_prompt.page_count,
                                    "summary": pdf_prompt.summary,
                                    "workflow": pdf_prompt.source,
                                }
                            },
                        )
                        params = _apply_default_params(params, default_params)
                        try:
                            params = await matcher.enhance_params(params, prompt_text)
                        except Exception as e:
                            logger.warning(f"PDF page prompt enhancement failed, skipping: {str(e)}")
                        params_list.append(params)
                        user_inputs.append(prompt_text)
                else:
                    parser = get_parser(tmp_file_path)
                    parsed_data = parser.parse(tmp_file_path)

                    for item in parsed_data:
                        prompt_text = item.get("prompt", "")
                        if not prompt_text:
                            continue

                        params = await extractor.extract(prompt_text)
                        params = _apply_default_params(params, default_params)
                        if provider:
                            params.provider = provider
                        params.api_key = api_key
                        params = await matcher.enhance_params(params, prompt_text)
                        params_list.append(params)
                        user_inputs.append(prompt_text)
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        if prompts:
            for prompt_text in prompts:
                if not prompt_text:
                    continue

                params = await extractor.extract(prompt_text)
                params = _apply_default_params(params, default_params)
                if provider:
                    params.provider = provider
                params.api_key = api_key
                params = await matcher.enhance_params(params, prompt_text)
                params_list.append(params)
                user_inputs.append(prompt_text)

        if not params_list:
            raise HTTPException(status_code=400, detail="娌℃湁鏈夋晥鐨勮緭鍏ユ暟鎹?")

        try:
            user_request = await db_manager.create_user_request(
                user_id="anonymous",
                user_ip=http_request.client.host if http_request else "127.0.0.1",
                user_agent=http_request.headers.get("user-agent", "") if http_request else "",
                request_type="batch_generation",
                status="processing",
                request_data=user_request_data,
            )
            logger.info(f"Batch user request created: {user_request.id}")
        except Exception as e:
            logger.warning(f"Failed to create batch user request: {str(e)}")
            user_request = None

        batch_task = await task_manager.create_batch_task(
            params_list,
            user_inputs,
            user_request.id if user_request else None,
        )

        if user_request:
            batch_task.user_request_id = user_request.id
            for task in batch_task.tasks:
                task.user_request_id = user_request.id
                try:
                    await db_manager.create_generation_record(
                        user_request_id=user_request.id,
                        provider=task.params.provider,
                        model=task.params.model or "",
                        prompt=task.params.prompt,
                        width=task.params.width,
                        height=task.params.height,
                        n=task.params.n,
                        call_mode="batch",
                        status="pending",
                    )
                    logger.info(f"Saved generation record for batch subtask: {task.task_id}")
                except Exception as e:
                    logger.warning(f"Failed to save batch generation record: {str(e)}")

        return batch_task

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"鎵归噺鐢熷浘澶辫触: {str(e)}")
