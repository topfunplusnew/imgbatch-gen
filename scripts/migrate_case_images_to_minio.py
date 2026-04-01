"""迁移案例图片到 MinIO 并更新数据库地址。"""

import asyncio
from pathlib import Path

from loguru import logger
from sqlalchemy import select

from src.config.settings import settings
from src.database import get_db_manager
from src.database.models import Case
from src.services.media_storage_service import save_image_bytes


def _is_minio_case(case: Case) -> bool:
    image_path = (case.image_path or "").strip()
    if not image_path:
        return False

    if image_path.startswith("http://") or image_path.startswith("https://"):
        return True

    storage_root = Path(settings.storage_path)
    path = Path(image_path)
    if path.exists() or path.is_absolute() or str(path).startswith(str(storage_root)):
        return False

    return True


async def main() -> None:
    if settings.storage_type != "minio":
        raise SystemExit("请先设置 STORAGE_TYPE=minio 再执行迁移。")

    db_manager = get_db_manager()
    migrated = 0
    skipped = 0
    failed = 0

    async with db_manager.get_session() as session:
        result = await session.execute(select(Case))
        cases = result.scalars().all()

        for case in cases:
            if not case.image_path:
                skipped += 1
                logger.info("跳过案例 {}：没有 image_path", case.id)
                continue

            if _is_minio_case(case):
                skipped += 1
                logger.info("跳过案例 {}：已经是 MinIO 路径 {}", case.id, case.image_path)
                continue

            local_path = Path(case.image_path)
            if not local_path.exists():
                skipped += 1
                logger.warning("跳过案例 {}：本地图片不存在 {}", case.id, local_path)
                continue

            try:
                image_info = save_image_bytes(
                    local_path.read_bytes(),
                    source_name=local_path.name,
                    storage_task_id=f"cases/{case.id}/migration",
                    prompt=f"case-image-migration-{case.id}",
                )
                case.image_url = image_info["image_url"]
                case.thumbnail_url = image_info["thumbnail_url"]
                case.image_path = image_info["image_path"]
                migrated += 1
                logger.info("迁移案例 {} 成功 -> {}", case.id, case.image_url)
            except Exception as exc:
                failed += 1
                logger.exception("迁移案例 {} 失败: {}", case.id, exc)

        await session.commit()

    logger.info("案例图片迁移完成，成功={}，跳过={}，失败={}", migrated, skipped, failed)


if __name__ == "__main__":
    asyncio.run(main())
