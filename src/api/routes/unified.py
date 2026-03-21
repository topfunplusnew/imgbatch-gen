"""统一生图接口 - 支持文件、对话内容、模型选择，以及多种图像操作（编辑、Blend 等）"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from typing import Optional, List, Dict, Any, Tuple
import tempfile
import os
import json
import time
import base64

from ...models.task import ImageTask, BatchTask
from ...models.image import ImageParams
from ...engine import TaskManager
from ...parsers import get_parser
from ...extractor import get_extractor
from ...matcher import get_matcher
from ...config.settings import settings
from loguru import logger
from ...providers import (
    get_provider,
    OpenAIRelayProvider,
    IdeogramProvider,
    FalAIProvider,
    MidjourneyProvider,
)
from ...database import get_db_manager
from ...workflows import build_pdf_prompt
from .chat import _require_api_key, _get_openai_client


def _debug_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: Dict[str, Any],
    run_id: str = "pre-fix",
) -> None:
    """
    追加一条 NDJSON 调试日志到本地文件（仅用于调试，不影响正常逻辑）
    
    注意：不要在这里抛异常，任何日志写入错误都应被静默忽略。
    """
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".cursor",
        "debug.log",
    )
    payload = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
    }
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # 日志失败不应影响主流程
        pass

router = APIRouter(prefix="/api/v1", tags=["unified"])


async def _extract_image_ocr_for_generation(
    *,
    image_bytes: bytes,
    filename: str,
    api_key: str,
) -> str:
    """Extract OCR/context from an uploaded image for prompt grounding."""
    if not image_bytes:
        return ""

    ext = os.path.splitext(filename or "")[1].lower().lstrip(".")
    mime = {
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "png": "png",
        "gif": "gif",
        "webp": "webp",
        "bmp": "bmp",
    }.get(ext, "png")

    model = (
        settings.assistant_ocr_model
        or settings.assistant_text_model
        or settings.openai_model
        or "gpt-4o-mini"
    )

    try:
        client = _get_openai_client(api_key)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/{mime};base64,{image_b64}"
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract grounded content from an image for downstream image generation. "
                        "Return concise plain text including: visible text (OCR), key entities, numbers, "
                        "layout/structure hints, and critical visual attributes."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请识别这张图片中的文字与关键信息，用于后续生图。"
                                "输出要求：\n"
                                "1) 保留关键 OCR 文本（标题/数字/专有名词）\n"
                                "2) 描述核心视觉元素与布局\n"
                                "3) 控制在 1200 字以内"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            max_tokens=1200,
        )
        content = ""
        if getattr(response, "choices", None):
            content = (response.choices[0].message.content or "").strip()

        if not content:
            logger.warning("[Unified] Image OCR returned empty content: {}", filename)
            return ""

        max_len = 4000
        if len(content) > max_len:
            content = content[: max_len - 3].rstrip() + "..."

        logger.info("[Unified] Image OCR extracted: file={}, chars={}", filename, len(content))
        return content
    except Exception as e:
        logger.warning(f"[Unified] Image OCR extraction failed for {filename}: {str(e)}")
        return ""


def get_task_manager(request: Request) -> TaskManager:
    """获取任务管理器（依赖注入）"""
    return request.app.state.task_manager


def determine_provider(
    model_name: Optional[str],
    provider: Optional[str],
    http_request: Request
) -> str:
    """确定使用的Provider"""
    provider_name = provider
    
    # 如果提供了模型名称，尝试从模型注册表查找
    if model_name:
        try:
            model_registry = getattr(http_request.app.state, "model_registry", None)
            if model_registry:
                mapping = model_registry.get_provider_mapping(model_name)
                if mapping:
                    provider_name = mapping.provider_type
                    logger.info(f"模型 {model_name} 自动映射到 Provider: {provider_name}")
                else:
                    logger.warning(f"模型 {model_name} 未找到对应的 Provider 映射，尝试本地 fallback")
            else:
                logger.warning("模型注册表未初始化，无法通过模型名称查找 Provider")
        except Exception as e:
            logger.warning(f"无法从模型注册表查找模型 {model_name}: {str(e)}")
    
    # 如果模型注册表中没有找到映射，尝试本地 fallback 映射
    if not provider_name and model_name:
        provider_name = _fallback_provider_mapping(model_name)
        if provider_name:
            logger.info(f"模型 {model_name} 通过本地 fallback 映射到 Provider: {provider_name}")
    
    # 如果最终还是没有 provider，使用默认值
    if not provider_name:
        provider_name = settings.default_image_provider
        logger.debug(f"未指定 Provider，使用默认值: {provider_name}")
    
    return provider_name


def _fallback_provider_mapping(model_name: str) -> Optional[str]:
    """本地 fallback Provider 映射（当模型注册表中找不到时使用）"""
    model_lower = model_name.lower()
    
    # 关键词映射规则
    if "mj" in model_lower or "midjourney" in model_lower:
        return "midjourney"
    elif "ideogram" in model_lower:
        return "ideogram"
    elif "dall" in model_lower or "gpt-image" in model_lower:
        return "openai"
    elif "qwen" in model_lower or "wanx" in model_lower or "通义" in model_lower:
        return "aliyun"
    elif "ernie-vilg" in model_lower or "文心" in model_lower:
        return "baidu"
    elif "hunyuan" in model_lower or "tencent" in model_lower:
        return "tencent"
    elif "flux" in model_lower or "replicate" in model_lower:
        return "replicate"
    elif "fal" in model_lower or "nano-banana" in model_lower:
        return "fal-ai"
    elif "doubao" in model_lower or "seedream" in model_lower:
        return "openai"
    
    return None


def is_batch_request(
    prompt: Optional[str],
    prompts: Optional[List[str]],
    all_prompts: List[str]
) -> bool:
    """
    判断是单图还是批量请求
    
    规则：
    - 如果总提示词数量 > 1 -> 批量
    - 如果总提示词数量 = 1 -> 单图
    """
    return len(all_prompts) > 1


@router.post("/generate-unified")
async def unified_generate(
    http_request: Request,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """统一生图接口

    支持：
    - 文件上传（图片、PDF、Word）
    - 对话内容（单个或列表）
    - 模型选择（model_name 自动映射到 Provider）
    - 自动判断单图或批量

    支持两种请求格式：
    1. JSON body (application/json) - 当没有文件上传时
    2. Form data (multipart/form-data) - 当有文件上传时

    根据输入自动判断：
    - 单图：单个prompt或文件解析出单条数据
    - 批量：多个prompts或文件解析出多条数据
    """
    try:
        # 获取数据库管理器
        db_manager = get_db_manager()

        # 解析请求参数（支持JSON和Form两种格式）
        content_type = http_request.headers.get("content-type", "")

        # 初始化变量
        prompt = None
        prompts_list = None
        file = None
        model_name = None
        provider = None
        width = None
        height = None
        style = None
        quality = None
        n = 1
        extra_params_dict = {}
        operation_type = "generate"
        image_file: Optional[UploadFile] = None
        mask_file: Optional[UploadFile] = None
        extra_images: List[UploadFile] = []
        operation_params: Dict[str, Any] = {}

        # #region 保存用户请求数据
        user_request_data = {
            "type": "image_generation",
            "request_data": {}
        }
        # #endregion

        if "multipart/form-data" in content_type:
            try:
                # 处理 Form Data
                form = await http_request.form()
                prompt = form.get("prompt")
                prompts_str = form.get("prompts")
                model_name = form.get("model_name")
                provider = form.get("provider")
                width = form.get("width")
                height = form.get("height")
                style = form.get("style")
                quality = form.get("quality")
                n_str = form.get("n")
                extra_params_str = form.get("extra_params")
                operation_type = (form.get("operation_type") or "generate").lower()

                # 解析常见操作参数
                for key in [
                    "task_id",
                    "custom_id",
                    "base64",
                    "base64_array",
                    "image_urls",
                    "task_ids",
                    "resolution",
                    "seed",
                    "choose_same_channel",
                    "notify_hook",
                    "state",
                    "rendering_speed",
                    "num_images",
                    "resemblance",
                    "detail",
                    "magic_prompt_option",
                    "response_format",
                    "aspect_ratio",
                    "background",
                    "moderation",
                ]:
                    value = form.get(key)
                    if value is not None:
                        operation_params[key] = value

                # 解析 prompts
                if prompts_str:
                    try:
                        prompts_list = json.loads(prompts_str)
                        if not isinstance(prompts_list, list):
                            prompts_list = [prompts_list] if prompts_list else None
                    except (json.JSONDecodeError, TypeError):
                        prompts_list = [prompts_str] if prompts_str else None

                # 解析 extra_params
                if extra_params_str:
                    try:
                        extra_params_dict = json.loads(extra_params_str)
                    except (json.JSONDecodeError, TypeError):
                        extra_params_dict = {}

                # 处理文件（FormData中的文件）
                if "file" in form:
                    file_item = form["file"]
                    # FastAPI 的 form() 返回的文件已经是 UploadFile 类型
                    if isinstance(file_item, UploadFile):
                        file = file_item
                # 专用于图像操作的文件字段
                image_candidate = form.get("image")
                logger.info(f"[DEBUG] image_candidate类型: {type(image_candidate).__name__}, 值: {image_candidate}")
                if image_candidate and hasattr(image_candidate, 'filename'):
                    image_file = image_candidate
                    logger.info(f"[DEBUG] image_file已设置: {image_file.filename}")
                mask_candidate = form.get("mask")
                if isinstance(mask_candidate, UploadFile):
                    mask_file = mask_candidate
                # 多图片字段（如 images 或 images[]）
                for img in form.getlist("images") or []:
                    if isinstance(img, UploadFile):
                        extra_images.append(img)

                # #region agent log
                _debug_log(
                    hypothesis_id="H2",
                    location="unified.py:multipart_parse",
                    message="file_fields_parsed",
                    data={
                        "operation_type": operation_type,
                        "form_keys": list(form.keys()),
                        "has_image_file": bool(image_file),
                        "has_mask_file": bool(mask_file),
                        "extra_images_count": len(extra_images),
                        "image_candidate_type": type(image_candidate).__name__ if image_candidate else None,
                    },
                    run_id="pre-fix",
                )
                # #endregion agent log

                # 类型转换
                if width:
                    try:
                        width = int(width)
                    except (ValueError, TypeError):
                        width = None
                if height:
                    try:
                        height = int(height)
                    except (ValueError, TypeError):
                        height = None
                if n_str:
                    try:
                        n = int(n_str)
                    except (ValueError, TypeError):
                        n = 1
            except Exception as e:
                logger.warning(f"解析FormData失败: {str(e)}")
                raise HTTPException(status_code=400, detail=f"请求格式错误: {str(e)}")
        else:
            # 处理 JSON Body
            try:
                body = await http_request.json()
                prompt = body.get("prompt")
                prompts_list = body.get("prompts")
                model_name = body.get("model_name")
                provider = body.get("provider")
                width = body.get("width")
                height = body.get("height")
                style = body.get("style")
                quality = body.get("quality")
                n = body.get("n", 1)
                extra_params_dict = body.get("extra_params", {})
                operation_type = (body.get("operation_type") or "generate").lower()

                # 收集操作相关参数
                for key in [
                    "task_id",
                    "custom_id",
                    "base64",
                    "base64_array",
                    "image_urls",
                    "task_ids",
                    "resolution",
                    "seed",
                    "choose_same_channel",
                    "notify_hook",
                    "state",
                    "rendering_speed",
                    "num_images",
                    "resemblance",
                    "detail",
                    "magic_prompt_option",
                    "response_format",
                    "aspect_ratio",
                    "background",
                    "moderation",
                ]:
                    if key in body:
                        operation_params[key] = body.get(key)

                # #region agent log
                _debug_log(
                    hypothesis_id="H3",
                    location="unified.py:json_parse",
                    message="json_params_parsed",
                    data={
                        "operation_type": operation_type,
                        "body_keys": list(body.keys()),
                        "operation_params_keys": list(operation_params.keys()),
                        "base64_array_raw": operation_params.get("base64_array"),
                        "base64_array_type": type(operation_params.get("base64_array")).__name__ if operation_params.get("base64_array") is not None else None,
                    },
                    run_id="pre-fix",
                )
                # #endregion agent log
            except Exception as e:
                logger.warning(f"解析JSON body失败: {str(e)}")
                raise HTTPException(status_code=400, detail=f"请求格式错误: {str(e)}")
        
        # 1. 确定使用的Provider
        provider_name = determine_provider(model_name, provider, http_request)

        # 准备用户请求数据
        user_request_data["request_data"].update({
            "operation_type": operation_type,
            "provider": provider_name,
            "model_name": model_name,
            "extra_params": extra_params_dict
        })
        
        # 2. 收集所有提示词
        all_prompts = []
        parsed_data = None
        reference_image_bytes = None
        reference_image_filename = ""
        prepared_params: List[ImageParams] = []
        prepared_user_inputs: List[str] = []
        consumed_inline_prompt = False
        api_key = _require_api_key(http_request)

        # 处理image字段（参考图片）
        if image_file and hasattr(image_file, 'filename') and image_file.filename:
            reference_image_bytes = await image_file.read()
            reference_image_filename = image_file.filename
            logger.info(f"✓ 接收到参考图片(image字段): {image_file.filename}, 大小: {len(reference_image_bytes)} bytes")

        # 处理file字段（文档或图片）
        if file and hasattr(file, 'filename') and file.filename:
            logger.info(f"接收到文件上传: {file.filename}, content_type: {file.content_type}")
            # 检查是否是图片文件
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                # 图片文件作为参考图
                reference_image_bytes = await file.read()
                reference_image_filename = file.filename or ""
                logger.info(f"✓ 识别为参考图片: {file.filename}, 大小: {len(reference_image_bytes)} bytes")
            else:
                # 非图片文件，解析为prompt
                logger.info(f"识别为文档文件，开始解析: {file.filename}")
                suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name

                try:
                    if file_ext == ".pdf":
                        pdf_prompt = await build_pdf_prompt(
                            tmp_file_path,
                            user_instruction=prompt or "",
                            api_key=api_key,
                        )
                        pdf_extra_params = dict(extra_params_dict or {})
                        pdf_extra_params["document_context"] = {
                            "source": "pdf",
                            "page_count": pdf_prompt.page_count,
                            "summary": pdf_prompt.summary,
                            "page_prompts": pdf_prompt.page_prompts,
                            "workflow": pdf_prompt.source,
                        }
                        prepared_params.append(
                            ImageParams(
                                prompt=pdf_prompt.prompt,
                                negative_prompt=pdf_prompt.negative_prompt,
                                width=width or 1024,
                                height=height or 1024,
                                style=style or pdf_prompt.style,
                                quality=quality or "standard",
                                n=n or 1,
                                provider=provider_name,
                                api_key=api_key,
                                extra_params=pdf_extra_params,
                            )
                        )
                        prepared_user_inputs.append(pdf_prompt.prompt)
                        consumed_inline_prompt = bool(prompt)
                        logger.info(
                            f"PDF converted to a single grounded prompt, page_count={pdf_prompt.page_count}, workflow={pdf_prompt.source}"
                        )
                    else:
                        parser = get_parser(tmp_file_path)
                        parsed_data = parser.parse(tmp_file_path)
                        for item in parsed_data:
                            prompt_text = item.get("prompt", "")
                            if prompt_text:
                                all_prompts.append(prompt_text)
                except Exception as e:
                    logger.error(f"文件解析失败: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)

        # 处理单个prompt
        if prompt and not consumed_inline_prompt:
            all_prompts.append(prompt)
        
        # 处理prompts列表
        if prompts_list:
            all_prompts.extend(prompts_list)
        
        # 3a. 如果是非标准生成操作（如 edit、blend 等），直接路由到对应 Provider 方法
        # 鍥剧墖鐢熸垚锛氬厛OCR鎻愬彇鍐呭锛屽啀涓庣敤鎴锋彁绀鸿瘝鍚堝苟
        if operation_type == "generate" and reference_image_bytes:
            image_ocr_text = await _extract_image_ocr_for_generation(
                image_bytes=reference_image_bytes,
                filename=reference_image_filename or "reference_image.png",
                api_key=api_key,
            )
            if image_ocr_text:
                grounding_block = (
                    "参考图片OCR/内容提取结果（生成时必须结合）:\n"
                    f"{image_ocr_text}"
                )

                if prepared_params:
                    for prepared_param in prepared_params:
                        base_prompt = (prepared_param.prompt or "").strip()
                        prepared_param.prompt = (
                            f"{base_prompt}\n\n{grounding_block}"
                            if base_prompt
                            else grounding_block
                        )

                if all_prompts:
                    all_prompts = [
                        f"{prompt_item}\n\n{grounding_block}" if prompt_item else grounding_block
                        for prompt_item in all_prompts
                    ]
                elif not prepared_params:
                    all_prompts.append(grounding_block)

                extra_params_dict = dict(extra_params_dict or {})
                extra_params_dict["reference_image_ocr"] = image_ocr_text
                logger.info(
                    "[Unified] Image OCR merged into prompt chain: prompts={}, prepared_params={}",
                    len(all_prompts),
                    len(prepared_params),
                )
            else:
                logger.warning("[Unified] Image OCR is empty, keeping original prompts")

        if operation_type != "generate":
            # 对于非 generate 操作，prompt 可能是可选的（取决于具体操作类型）
            primary_prompt = all_prompts[0] if all_prompts else None
            # #region agent log
            _debug_log(
                hypothesis_id="H1",
                location="unified.py:generate-unified",
                message="enter_non_generate_operation",
                data={
                    "operation_type": operation_type,
                    "provider_name": provider_name,
                    "has_prompt": bool(primary_prompt),
                    "has_image_file": bool(image_file),
                    "has_mask_file": bool(mask_file),
                    "has_extra_images": bool(extra_images),
                    "operation_params_keys": list(operation_params.keys()),
                },
                run_id="pre-fix",
            )
            # #endregion agent log
            return await _handle_operation(
                operation_type=operation_type,
                provider_name=provider_name,
                model_name=model_name,
                prompt=primary_prompt,
                operation_params=operation_params,
                image_file=image_file,
                mask_file=mask_file,
                extra_images=extra_images,
                extra_params=extra_params_dict,
            )
        
        # 验证输入（仅对 generate 操作）
        if not all_prompts and not prepared_params:
            raise HTTPException(status_code=400, detail="至少需要提供 prompt、prompts 或 file 中的一个")
        
        # 3. 判断是单图还是批量
        is_batch = (len(prepared_params) + len(all_prompts)) > 1
        
        # 4. 提取参数和增强
        extractor = get_extractor(api_key=api_key)
        matcher = get_matcher(api_key=api_key)
        
        params_list = list(prepared_params)
        user_inputs = list(prepared_user_inputs)

        for index, prepared_param in enumerate(params_list):
            if reference_image_bytes:
                prepared_param.extra_params["image"] = reference_image_bytes
            prepared_param.provider = provider_name
            prepared_param.api_key = api_key
            try:
                params_list[index] = await matcher.enhance_params(prepared_param, prepared_param.prompt)
            except Exception as e:
                logger.warning(f"PDF prompt enhancement failed, skipping: {str(e)}")

        for prompt_text in all_prompts:
            # 提取参数（如果失败，使用降级方案：直接使用用户输入）
            try:
                extracted_params = await extractor.extract(prompt_text)
            except Exception as e:
                logger.warning(f"参数提取失败，使用降级方案（直接使用用户输入）: {str(e)}")
                # 降级方案：直接使用用户输入创建参数
                from ...models.image import ImageParams
                extracted_params = ImageParams(
                    prompt=prompt_text,
                    width=width or 1024,
                    height=height or 1024,
                    style=style,
                    quality=quality or "standard",
                    n=n or 1,
                    provider=provider_name,
                    extra_params=extra_params_dict or {}
                )
            
            # 应用请求参数
            if width:
                extracted_params.width = width
                logger.info(f"[Unified] 应用width参数: {width}")
            if height:
                extracted_params.height = height
                logger.info(f"[Unified] 应用height参数: {height}")
            if style:
                extracted_params.style = style
                logger.info(f"[Unified] 应用style参数: {style}")
            if quality:
                extracted_params.quality = quality
                logger.info(f"[Unified] 应用quality参数: {quality}")
            if n:
                extracted_params.n = n
                logger.info(f"[Unified] 应用n参数: {n}")
            if extra_params_dict:
                extracted_params.extra_params.update(extra_params_dict)
                logger.info(f"[Unified] 应用extra_params: {list(extra_params_dict.keys())}")

            # 如果有参考图片，添加到extra_params
            if reference_image_bytes:
                extracted_params.extra_params["image"] = reference_image_bytes
                logger.info(f"✓ 已将参考图片添加到生成参数中 (大小: {len(reference_image_bytes)} bytes)")

            # 设置Provider
            extracted_params.provider = provider_name
            extracted_params.api_key = api_key

            # 增强参数（如果失败，跳过增强）
            try:
                extracted_params = await matcher.enhance_params(extracted_params, prompt_text)
            except Exception as e:
                logger.warning(f"参数增强失败，跳过增强: {str(e)}")

            params_list.append(extracted_params)
            user_inputs.append(prompt_text)
        
        # 5. 创建用户请求记录（仅用于日志和监控，不作为对话历史显示）
        # 注意：这个记录用于后台日志，不应该被前端作为"历史记录"显示
        user_request_id = None
        user_id = "anonymous"  # 默认用户ID

        # 尝试从token中获取user_id
        try:
            auth_header = http_request.headers.get("authorization", "")
            if auth_header and auth_header.startswith("Bearer "):
                from ...services.auth_service import get_auth_service
                auth_service = get_auth_service()
                token = auth_header.split(" ")[1]
                payload = auth_service.decode_token(token)
                if payload:
                    user_id = payload.get("user_id", "anonymous")
        except Exception:
            pass

        try:
            user_request = await db_manager.create_user_request(
                user_id=user_id,
                user_ip=http_request.client.host,
                user_agent=http_request.headers.get("user-agent", ""),
                request_type="image_generation",
                request_data=user_request_data["request_data"],
                status="processing"  # 标记为处理中
            )
            user_request_id = user_request.id
            logger.info(f"用户请求已创建: {user_request.id} (仅用于日志)")
        except Exception as e:
            logger.warning(f"创建用户请求记录失败: {str(e)}")
            # 不影响主要流程，继续执行
            user_request = None

        # 6. 创建任务
        if is_batch:
            # 批量任务
            batch_task = await task_manager.create_batch_task(
                params_list,
                user_inputs,
                user_request.id if user_request else None,
                user_id
            )
            # 关联用户请求ID到批量任务
            if user_request:
                batch_task.user_request_id = user_request.id
                # 保存批量任务记录到数据库
                try:
                    for task in batch_task.tasks:
                        task.user_request_id = user_request.id
                    logger.info(f"批量任务关联用户请求: {user_request.id}")
                except Exception as e:
                    logger.warning(f"关联批量任务到用户请求失败: {str(e)}")
            return batch_task
        else:
            # 单图任务
            task = task_manager.create_task(params_list[0], user_inputs[0], user_request.id if user_request else None, user_id)
            await task_manager.submit_task(task)
            # 关联用户请求ID
            if user_request:
                task.user_request_id = user_request.id
                # 保存图片生成记录到数据库
                try:
                    await db_manager.create_generation_record(
                        user_request_id=user_request.id,
                        provider=task.params.provider,
                        model=task.params.model_name or "",
                        prompt=task.params.prompt,
                        width=task.params.width,
                        height=task.params.height,
                        n=task.params.n,
                        call_mode="unified",
                        status="pending"
                    )
                    logger.info(f"图片生成记录已保存: {task.task_id}")
                except Exception as e:
                    logger.warning(f"保存图片生成记录失败: {str(e)}")

            # 移除extra_params中的bytes数据避免序列化错误
            if "image" in task.params.extra_params:
                task.params.extra_params.pop("image")
                logger.info("已从返回的任务对象中移除image数据")

            return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"统一生图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生图失败: {str(e)}")


async def _convert_uploadfile_to_bytes(upload_file: UploadFile) -> bytes:
    """将 UploadFile 转换为 bytes"""
    content = await upload_file.read()
    return content


def _parse_list_param(value: Any) -> List[str]:
    """将字符串或列表解析为字符串列表"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    # 尝试按 JSON 解析
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(v) for v in parsed]
    except Exception:
        pass
    # 逗号分隔
    if isinstance(value, str) and "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


def _validate_operation_params(
    operation_type: str,
    provider_name: str,
    prompt: Optional[str],
    operation_params: Dict[str, Any],
    image_file: Optional[UploadFile],
    mask_file: Optional[UploadFile],
) -> None:
    """根据操作类型和 Provider 验证必需参数"""
    p = provider_name.lower()
    op = operation_type.lower()
    
    def require(cond: bool, msg: str, code: str):
        if not cond:
            # #region agent log
            _debug_log(
                hypothesis_id="H2",
                location="unified.py:_validate_operation_params",
                message="validation_failed",
                data={
                    "operation_type": op,
                    "provider": p,
                    "code": code,
                    "msg": msg,
                },
                run_id="pre-fix",
            )
            # #endregion agent log
            raise HTTPException(status_code=400, detail=msg)
    
    if op == "edit":
        if p in ("openai", "dall-e"):
            require(image_file is not None, "OpenAI 图片编辑需要上传 image 文件", "openai_image_required")
            require(bool(prompt), "OpenAI 图片编辑需要提供 prompt", "openai_prompt_required")
        elif p == "ideogram":
            require(image_file is not None, "Ideogram 图片编辑需要上传 image 文件", "ideogram_image_required")
        elif p in ("fal-ai", "fal_ai"):
            require(
                bool(_parse_list_param(operation_params.get("image_urls"))),
                "Fal AI 图片编辑需要提供 image_urls 列表",
                "fal_ai_image_urls_required",
            )
            require(bool(prompt), "Fal AI 图片编辑需要提供 prompt", "fal_ai_prompt_required")
    elif op == "blend":
        require(
            bool(_parse_list_param(operation_params.get("base64_array"))),
            "Midjourney Blend 需要提供 base64_array",
            "mj_blend_base64_array_required",
        )
    elif op == "action":
        require(bool(operation_params.get("custom_id")), "Midjourney Action 需要 custom_id", "mj_action_custom_id_required")
        require(bool(operation_params.get("task_id")), "Midjourney Action 需要 task_id", "mj_action_task_id_required")
    elif op == "modal":
        require(bool(operation_params.get("mask_base64")), "Midjourney Modal 需要 mask_base64", "mj_modal_mask_required")
        require(bool(operation_params.get("task_id")), "Midjourney Modal 需要 task_id", "mj_modal_task_id_required")
    elif op == "describe":
        if p == "midjourney":
            has_b64 = bool(operation_params.get("base64")) or bool(
                _parse_list_param(operation_params.get("base64_array"))
            )
            require(has_b64, "Midjourney Describe 需要 base64 或 base64_array", "mj_describe_b64_required")
        elif p == "ideogram":
            require(image_file is not None, "Ideogram Describe 需要上传 image 文件", "ideogram_describe_image_required")
    elif op in ("remix", "reframe", "replace_background", "upscale"):
        # Ideogram 系列操作都需要 image
        require(image_file is not None, f"Ideogram {op} 操作需要上传 image 文件", f"ideogram_{op}_image_required")
    elif op == "upload_discord_images":
        require(
            bool(_parse_list_param(operation_params.get("base64_array"))),
            "upload_discord_images 需要 base64_array",
            "mj_upload_discord_base64_array_required",
        )
    elif op == "list_tasks":
        require(
            bool(_parse_list_param(operation_params.get("task_ids"))),
            "list_tasks 需要 task_ids 列表",
            "mj_list_tasks_ids_required",
        )
    elif op == "get_image_seed":
        require(bool(operation_params.get("task_id")), "get_image_seed 需要 task_id", "mj_get_image_seed_task_id_required")


async def _handle_operation(
    operation_type: str,
    provider_name: str,
    model_name: Optional[str],
    prompt: Optional[str],
    operation_params: Dict[str, Any],
    image_file: Optional[UploadFile],
    mask_file: Optional[UploadFile],
    extra_images: List[UploadFile],
    extra_params: Dict[str, Any],
) -> Any:
    """
    根据 operation_type 和 provider 路由到不同的 Provider 方法
    
    - generate: 已在上层处理，这里只处理非标准生图操作
    """
    provider = get_provider(provider=provider_name, model_name=model_name)
    op = operation_type.lower()
    p = provider_name.lower()
    
    # #region agent log
    _debug_log(
        hypothesis_id="H1",
        location="unified.py:_handle_operation",
        message="before_validation",
        data={
            "operation_type": op,
            "provider_name": p,
            "has_prompt": bool(prompt),
            "has_image_file": bool(image_file),
            "has_mask_file": bool(mask_file),
            "operation_params": {k: (str(v)[:100] if isinstance(v, str) else v) for k, v in operation_params.items()},
            "base64_array_raw": operation_params.get("base64_array"),
            "base64_array_parsed": _parse_list_param(operation_params.get("base64_array")),
        },
        run_id="pre-fix",
    )
    # #endregion agent log
    
    # 参数验证
    _validate_operation_params(op, p, prompt, operation_params, image_file, mask_file)
    
    # OpenAI / Ideogram / FalAI 编辑
    if op == "edit":
        if isinstance(provider, OpenAIRelayProvider):
            # OpenAI 图片编辑
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            mask_bytes = (
                await _convert_uploadfile_to_bytes(mask_file) if mask_file is not None else None
            )
            return await provider.edit_image(
                image=image_bytes,
                prompt=prompt or "",
                mask=mask_bytes,
                model=operation_params.get("model") or extra_params.get("model"),
                n=int(operation_params.get("num_images") or extra_params.get("n") or 1),
                quality=operation_params.get("quality") or extra_params.get("quality"),
                response_format=operation_params.get("response_format")
                or extra_params.get("response_format"),
                aspect_ratio=operation_params.get("aspect_ratio")
                or extra_params.get("aspect_ratio"),
                background=operation_params.get("background") or extra_params.get("background"),
                moderation=operation_params.get("moderation") or extra_params.get("moderation"),
            )
        if isinstance(provider, IdeogramProvider):
            # Ideogram 编辑
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            mask_bytes = (
                await _convert_uploadfile_to_bytes(mask_file) if mask_file is not None else None
            )
            seed_val = operation_params.get("seed") or extra_params.get("seed")
            seed_int = int(seed_val) if seed_val is not None else None
            return await provider.edit_image(
                image=image_bytes,
                prompt=prompt,
                mask=mask_bytes,
                seed=seed_int,
            )
        if isinstance(provider, FalAIProvider):
            # Fal AI 编辑：使用 edit_image_and_wait，直接返回结果 URL 列表
            image_urls = _parse_list_param(operation_params.get("image_urls"))
            num_images_val = (
                operation_params.get("num_images") or extra_params.get("num_images")
            )
            num_images_int = int(num_images_val) if num_images_val is not None else None
            urls = await provider.edit_image_and_wait(
                image_urls=image_urls,
                prompt=prompt or "",
                num_images=num_images_int,
            )
            return {"image_urls": urls}
    
    # Midjourney 相关操作
    if isinstance(provider, MidjourneyProvider):
        if op == "blend":
            base64_array = _parse_list_param(operation_params.get("base64_array"))
            dimensions = operation_params.get("dimensions") or extra_params.get("dimensions")
            quality = operation_params.get("quality") or extra_params.get("quality")
            notify_hook = operation_params.get("notify_hook") or extra_params.get("notify_hook")
            state = operation_params.get("state") or extra_params.get("state")
            task_id = await provider.submit_blend(
                base64_array=base64_array,
                bot_type="MID_JOURNEY",
                dimensions=dimensions,
                quality=quality,
                notify_hook=notify_hook,
                state=state,
            )
            return {"task_id": task_id}
        if op == "action":
            choose_same_channel_raw = operation_params.get("choose_same_channel")
            choose_same_channel = (
                str(choose_same_channel_raw).lower() != "false"
                if choose_same_channel_raw is not None
                else True
            )
            return await provider.submit_action(
                custom_id=operation_params.get("custom_id"),
                task_id=operation_params.get("task_id"),
                choose_same_channel=choose_same_channel,
                notify_hook=operation_params.get("notify_hook") or extra_params.get("notify_hook"),
                state=operation_params.get("state") or extra_params.get("state"),
            )
        if op == "modal":
            return await provider.submit_modal(
                mask_base64=operation_params.get("mask_base64"),
                task_id=operation_params.get("task_id"),
                prompt=prompt,
            )
        if op == "describe":
            base64_val = operation_params.get("base64")
            base64_array = _parse_list_param(operation_params.get("base64_array"))
            task_id = await provider.submit_describe(
                base64=base64_val,
                base64_array=base64_array or None,
                bot_type="MID_JOURNEY",
                notify_hook=operation_params.get("notify_hook") or extra_params.get("notify_hook"),
                state=operation_params.get("state") or extra_params.get("state"),
            )
            return {"task_id": task_id}
        if op == "upload_discord_images":
            base64_array = _parse_list_param(operation_params.get("base64_array"))
            return await provider.upload_discord_images(base64_array)
        if op == "list_tasks":
            task_ids = _parse_list_param(operation_params.get("task_ids"))
            return await provider.list_tasks_by_condition(task_ids)
        if op == "get_image_seed":
            return await provider.get_image_seed(operation_params.get("task_id"))
    
    # Ideogram 其他操作
    if isinstance(provider, IdeogramProvider):
        if op == "remix":
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            num_images_val = (
                operation_params.get("num_images") or extra_params.get("num_images")
            )
            num_images_int = int(num_images_val) if num_images_val is not None else None
            rendering_speed = (
                operation_params.get("rendering_speed") or extra_params.get("rendering_speed")
            )
            return await provider.remix_image(
                image=image_bytes,
                prompt=prompt,
                num_images=num_images_int,
                rendering_speed=rendering_speed,
            )
        if op == "reframe":
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            resolution = operation_params.get("resolution") or extra_params.get("resolution")
            return await provider.reframe_image(
                image=image_bytes,
                resolution=resolution,
            )
        if op == "replace_background":
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            return await provider.replace_background(
                image=image_bytes,
                prompt=prompt,
            )
        if op == "upscale":
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            num_images_val = (
                operation_params.get("num_images") or extra_params.get("num_images")
            )
            num_images_int = int(num_images_val) if num_images_val is not None else None
            resemblance_val = (
                operation_params.get("resemblance") or extra_params.get("resemblance")
            )
            resemblance_int = int(resemblance_val) if resemblance_val is not None else None
            detail_val = operation_params.get("detail") or extra_params.get("detail")
            detail_int = int(detail_val) if detail_val is not None else None
            magic_prompt_option = (
                operation_params.get("magic_prompt_option")
                or extra_params.get("magic_prompt_option")
            )
            seed_val = operation_params.get("seed") or extra_params.get("seed")
            seed_int = int(seed_val) if seed_val is not None else None
            return await provider.upscale_image(
                image=image_bytes,
                prompt=prompt,
                resemblance=resemblance_int,
                detail=detail_int,
                magic_prompt_option=magic_prompt_option,
                num_images=num_images_int,
                seed=seed_int,
            )
        if op == "describe":
            image_bytes = await _convert_uploadfile_to_bytes(image_file)  # type: ignore[arg-type]
            return await provider.describe_image(image=image_bytes)
    
    # 未知或不支持的操作
    raise HTTPException(
        status_code=400,
        detail=f"不支持的操作类型: {operation_type}，或当前 Provider({provider_name}) 不支持该操作",
    )

