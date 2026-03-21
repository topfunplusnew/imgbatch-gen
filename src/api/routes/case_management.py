"""案例管理API路由

管理员API:
- POST /api/v1/admin/cases - 创建案例
- GET /api/v1/admin/cases - 获取案例列表
- GET /api/v1/admin/cases/{id} - 获取案例详情
- PUT /api/v1/admin/cases/{id} - 更新案例
- DELETE /api/v1/admin/cases/{id} - 删除案例
- POST /api/v1/admin/cases/{id}/toggle - 切换发布状态

用户API:
- GET /api/v1/cases - 获取已发布案例列表
- GET /api/v1/cases/{id} - 获取案例详情
- POST /api/v1/cases/{id}/use - 记录案例使用次数
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger
import json
from pathlib import Path

from ...database import get_db_manager
from ...database.models import Case
from ..auth import RequiredAuthDependency, OptionalAuthDependency
from ...config.settings import settings


# ==================== 路由定义 ====================

router = APIRouter(prefix="/api/v1/cases", tags=["案例管理"])
admin_router = APIRouter(prefix="/api/v1/admin/cases", tags=["管理员-案例管理"])


# ==================== 权限验证 ====================


async def require_admin(user: dict = Depends(RequiredAuthDependency())):
    """验证管理员权限"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ==================== 请求模型 ====================


class CreateCaseRequest(BaseModel):
    """创建案例请求"""
    title: str = Field(..., min_length=1, max_length=200, description="案例标题")
    description: Optional[str] = Field(None, description="案例描述")
    category: str = Field(..., description="行业分类")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    prompt: str = Field(..., description="提示词")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    parameters: Optional[dict] = Field(default_factory=dict, description="生成参数")
    provider: Optional[str] = Field(None, description="Provider名称")
    model: Optional[str] = Field(None, description="模型名称")
    is_published: bool = Field(True, description="是否发布")
    sort_order: int = Field(0, description="排序权重")


class UpdateCaseRequest(BaseModel):
    """更新案例请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="案例标题")
    description: Optional[str] = Field(None, description="案例描述")
    category: Optional[str] = Field(None, description="行业分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    prompt: Optional[str] = Field(None, description="提示词")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    parameters: Optional[dict] = Field(None, description="生成参数")
    provider: Optional[str] = Field(None, description="Provider名称")
    model: Optional[str] = Field(None, description="模型名称")
    is_published: Optional[bool] = Field(None, description="是否发布")
    sort_order: Optional[int] = Field(None, description="排序权重")


# ==================== 响应模型 ====================


class CaseResponse(BaseModel):
    """案例响应"""
    id: str
    title: str
    description: Optional[str]
    category: str
    tags: Optional[List[str]]
    thumbnail_url: Optional[str]
    image_url: Optional[str]
    prompt: str
    negative_prompt: Optional[str]
    parameters: Optional[dict]
    provider: Optional[str]
    model: Optional[str]
    is_published: bool
    sort_order: int
    view_count: int
    use_count: int
    created_by: Optional[str]
    created_at: str
    updated_at: str


# ==================== 辅助函数 ====================


def case_to_response(case: Case) -> CaseResponse:
    """将Case模型转换为响应模型"""
    return CaseResponse(
        id=case.id,
        title=case.title,
        description=case.description,
        category=case.category,
        tags=case.tags if isinstance(case.tags, list) else [],
        thumbnail_url=case.thumbnail_url,
        image_url=case.image_url,
        prompt=case.prompt,
        negative_prompt=case.negative_prompt,
        parameters=case.parameters,
        provider=case.provider,
        model=case.model,
        is_published=case.is_published,
        sort_order=case.sort_order,
        view_count=case.view_count,
        use_count=case.use_count,
        created_by=case.created_by,
        created_at=case.created_at.isoformat() if case.created_at else "",
        updated_at=case.updated_at.isoformat() if case.updated_at else "",
    )


async def save_case_image(image_file: UploadFile, user_id: str) -> dict:
    """保存案例图片并返回URL信息"""
    from ...storage.local_storage import LocalStorage

    try:
        # 读取图片数据
        image_data = await image_file.read()

        # 创建存储实例
        storage = LocalStorage()

        # 生成唯一文件名
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = str(uuid.uuid4())
        filename = f"case_{timestamp}_{case_id[:8]}.{image_file.filename.split('.')[-1]}"

        # 保存到cases子目录
        cases_dir = Path(storage.storage_path) / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)

        file_path = cases_dir / filename

        # 保存原图
        with open(file_path, "wb") as f:
            f.write(image_data)

        # 生成缩略图
        thumbnail_url = None
        try:
            from PIL import Image
            import io

            thumbnail_data = storage._make_thumbnail(image_data)
            thumb_filename = filename.rsplit(".", 1)[0] + "_thumb.jpg"
            thumb_path = cases_dir / thumb_filename

            with open(thumb_path, "wb") as f:
                f.write(thumbnail_data)

            thumb_relative = thumb_path.relative_to(storage.storage_path)
            thumbnail_url = f"{settings.storage_url_prefix}/{thumb_relative.as_posix()}"
        except Exception as e:
            logger.warning(f"生成缩略图失败: {e}")

        # 生成URL
        relative_path = file_path.relative_to(storage.storage_path)
        image_url = f"{settings.storage_url_prefix}/{relative_path.as_posix()}"

        return {
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "image_path": str(file_path),
        }

    except Exception as e:
        logger.error(f"保存案例图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存图片失败: {str(e)}")


# ==================== 管理员API ====================


@admin_router.post("", response_model=CaseResponse, summary="创建案例")
async def create_case(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    tags: Optional[str] = Form(None),
    prompt: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    parameters: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    is_published: bool = Form(True),
    sort_order: int = Form(0),
    image: Optional[UploadFile] = File(None),
    admin: dict = Depends(require_admin),
):
    """
    创建新案例

    - 支持上传图片（自动生成缩略图）
    - 图片保存到storage/cases目录
    """
    db_manager = get_db_manager()

    # 处理标签
    tags_list = []
    if tags:
        try:
            tags_list = json.loads(tags) if isinstance(tags, str) else tags
        except:
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # 处理参数
    parameters_dict = {}
    if parameters:
        try:
            parameters_dict = json.loads(parameters) if isinstance(parameters, str) else parameters
        except:
            pass

    # 处理图片上传
    image_url = None
    thumbnail_url = None
    image_path = None

    if image:
        image_info = await save_case_image(image, admin["id"])
        image_url = image_info["image_url"]
        thumbnail_url = image_info["thumbnail_url"]
        image_path = image_info["image_path"]

    # 创建案例
    async with db_manager.get_session() as session:
        case = Case(
            title=title,
            description=description,
            category=category,
            tags=tags_list,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            parameters=parameters_dict,
            provider=provider,
            model=model,
            is_published=is_published,
            sort_order=sort_order,
            created_by=admin["id"],
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

    logger.info(f"管理员 {admin['id']} 创建案例: {case.id} - {case.title}")
    return case_to_response(case)


@admin_router.get("", response_model=List[CaseResponse], summary="获取案例列表")
async def get_admin_cases(
    category: Optional[str] = Query(None, description="行业分类筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题、描述）"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin),
):
    """
    获取案例列表（管理员）

    - 支持按分类筛选
    - 支持按发布状态筛选
    - 支持关键词搜索
    - 支持分页
    """
    from sqlalchemy import select, and_, or_

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case)

        # 构建筛选条件
        conditions = []

        if category:
            conditions.append(Case.category == category)

        if is_published is not None:
            conditions.append(Case.is_published == is_published)

        if keyword:
            search_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Case.title.like(search_pattern),
                    Case.description.like(search_pattern),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 排序和分页
        stmt = stmt.order_by(Case.sort_order.desc(), Case.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        cases = result.scalars().all()

    return [case_to_response(case) for case in cases]


@admin_router.get("/count", summary="获取案例总数")
async def get_admin_cases_count(
    category: Optional[str] = Query(None, description="行业分类筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin: dict = Depends(require_admin),
):
    """获取案例总数（用于分页）"""
    from sqlalchemy import select, func, and_, or_

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(func.count(Case.id))

        # 构建筛选条件
        conditions = []

        if category:
            conditions.append(Case.category == category)

        if is_published is not None:
            conditions.append(Case.is_published == is_published)

        if keyword:
            search_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Case.title.like(search_pattern),
                    Case.description.like(search_pattern),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await session.execute(stmt)
        count = result.scalar()

    return {"count": count}


@admin_router.get("/{case_id}", response_model=CaseResponse, summary="获取案例详情")
async def get_admin_case_detail(
    case_id: str,
    admin: dict = Depends(require_admin),
):
    """获取案例详情（管理员）"""
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")

    return case_to_response(case)


@admin_router.put("/{case_id}", response_model=CaseResponse, summary="更新案例")
async def update_case(
    case_id: str,
    body: UpdateCaseRequest,
    admin: dict = Depends(require_admin),
):
    """更新案例信息"""
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在")

        # 更新字段
        if body.title is not None:
            case.title = body.title
        if body.description is not None:
            case.description = body.description
        if body.category is not None:
            case.category = body.category
        if body.tags is not None:
            case.tags = body.tags
        if body.prompt is not None:
            case.prompt = body.prompt
        if body.negative_prompt is not None:
            case.negative_prompt = body.negative_prompt
        if body.parameters is not None:
            case.parameters = body.parameters
        if body.provider is not None:
            case.provider = body.provider
        if body.model is not None:
            case.model = body.model
        if body.is_published is not None:
            case.is_published = body.is_published
        if body.sort_order is not None:
            case.sort_order = body.sort_order

        await session.commit()
        await session.refresh(case)

    logger.info(f"管理员 {admin['id']} 更新案例: {case_id}")
    return case_to_response(case)


@admin_router.post("/{case_id}/image", response_model=CaseResponse, summary="更新案例图片")
async def update_case_image(
    case_id: str,
    image: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """更新案例图片"""
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在")

        # 保存新图片
        image_info = await save_case_image(image, admin["id"])

        case.image_url = image_info["image_url"]
        case.thumbnail_url = image_info["thumbnail_url"]
        case.image_path = image_info["image_path"]

        await session.commit()
        await session.refresh(case)

    logger.info(f"管理员 {admin['id']} 更新案例图片: {case_id}")
    return case_to_response(case)


@admin_router.delete("/{case_id}", summary="删除案例")
async def delete_case(
    case_id: str,
    admin: dict = Depends(require_admin),
):
    """删除案例"""
    from sqlalchemy import select, delete

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在")

        # 删除图片文件
        if case.image_path:
            try:
                Path(case.image_path).unlink(missing_ok=True)
                # 删除缩略图
                if case.image_path:
                    thumb_path = Path(case.image_path).parent / (Path(case.image_path).stem + "_thumb.jpg")
                    thumb_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"删除案例图片文件失败: {e}")

        # 删除数据库记录
        await session.execute(delete(Case).where(Case.id == case_id))
        await session.commit()

    logger.info(f"管理员 {admin['id']} 删除案例: {case_id}")
    return {"success": True, "message": "案例已删除"}


@admin_router.post("/{case_id}/toggle", response_model=CaseResponse, summary="切换发布状态")
async def toggle_case_publish_status(
    case_id: str,
    admin: dict = Depends(require_admin),
):
    """切换案例的发布状态"""
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在")

        case.is_published = not case.is_published
        await session.commit()
        await session.refresh(case)

    logger.info(f"管理员 {admin['id']} 切换案例发布状态: {case_id} -> {case.is_published}")
    return case_to_response(case)


# ==================== 用户API ====================


@router.get("", response_model=List[CaseResponse], summary="获取已发布案例列表")
async def get_published_cases(
    category: Optional[str] = Query(None, description="行业分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    获取已发布的案例列表（用户）

    - 只返回已发布的案例
    - 支持按分类筛选
    - 支持关键词搜索
    - 支持分页
    """
    from sqlalchemy import select, and_, or_

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.is_published == True)

        # 构建筛选条件
        conditions = [Case.is_published == True]

        if category:
            conditions.append(Case.category == category)

        if keyword:
            search_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Case.title.like(search_pattern),
                    Case.description.like(search_pattern),
                )
            )

        stmt = stmt.where(and_(*conditions))

        # 排序和分页
        stmt = stmt.order_by(Case.sort_order.desc(), Case.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        cases = result.scalars().all()

    return [case_to_response(case) for case in cases]


@router.get("/count", summary="获取已发布案例总数")
async def get_published_cases_count(
    category: Optional[str] = Query(None, description="行业分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
):
    """获取已发布案例总数（用于分页）"""
    from sqlalchemy import select, func, and_, or_

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(func.count(Case.id))

        # 构建筛选条件
        conditions = [Case.is_published == True]

        if category:
            conditions.append(Case.category == category)

        if keyword:
            search_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Case.title.like(search_pattern),
                    Case.description.like(search_pattern),
                )
            )

        stmt = stmt.where(and_(*conditions))

        result = await session.execute(stmt)
        count = result.scalar()

    return {"count": count}


@router.get("/categories", summary="获取所有行业分类")
async def get_case_categories():
    """获取所有行业分类（用于筛选器）"""
    # 预定义分类
    categories = [
        {"value": "电商", "label": "电商"},
        {"value": "广告", "label": "广告"},
        {"value": "动漫", "label": "动漫"},
        {"value": "室内", "label": "室内设计"},
        {"value": "logo", "label": "Logo设计"},
        {"value": "摄影", "label": "摄影"},
        {"value": "插画", "label": "插画"},
        {"value": "其他", "label": "其他"},
    ]

    return {"categories": categories}


@router.get("/{case_id}", response_model=CaseResponse, summary="获取案例详情")
async def get_case_detail(
    case_id: str,
):
    """
    获取案例详情（用户）

    - 只返回已发布的案例
    - 自动增加浏览次数
    """
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id).where(Case.is_published == True)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在或未发布")

        # 增加浏览次数
        case.view_count = (case.view_count or 0) + 1
        await session.commit()
        await session.refresh(case)

    return case_to_response(case)


@router.post("/{case_id}/use", summary="使用案例模板")
async def use_case_template(
    case_id: str,
):
    """
    记录案例使用次数

    - 用户点击"使用模板"时调用
    - 自动增加使用次数统计
    """
    from sqlalchemy import select

    db_manager = get_db_manager()

    async with db_manager.get_session() as session:
        stmt = select(Case).where(Case.id == case_id).where(Case.is_published == True)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="案例不存在或未发布")

        # 增加使用次数
        case.use_count = (case.use_count or 0) + 1
        await session.commit()

    logger.info(f"案例 {case_id} 被使用，累计使用次数: {case.use_count}")
    return {"success": True, "use_count": case.use_count}
