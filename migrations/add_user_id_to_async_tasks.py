"""
数据库迁移脚本：为 async_tasks 表添加 user_id 字段 (PostgreSQL)

运行方式：
    python migrations/add_user_id_to_async_tasks.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.database.async_task_manager import get_async_task_manager


async def migrate():
    """执行迁移"""
    manager = get_async_task_manager()

    print("开始迁移：为 async_tasks 表添加 user_id 字段")

    async with manager.engine.begin() as conn:
        # 检查列是否已存在 (PostgreSQL 语法)
        result = await conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_name = 'async_tasks'
            AND column_name = 'user_id'
        """))
        row = result.fetchone()

        if row[0] > 0:
            print("✓ user_id 列已存在，跳过迁移")
            return

        # 添加 user_id 列
        print("→ 添加 user_id 列...")
        await conn.execute(text(
            "ALTER TABLE async_tasks ADD COLUMN user_id VARCHAR(100)"
        ))

        # 创建索引
        print("→ 创建索引 idx_async_tasks_user_id...")
        await conn.execute(text(
            "CREATE INDEX idx_async_tasks_user_id ON async_tasks(user_id)"
        ))

        print("✓ 迁移完成！")
        print()
        print("注意：")
        print("- 现有的异步任务记录的 user_id 为 NULL")
        print("- 新创建的异步任务会自动关联到当前用户")
        print("- 如需为现有记录设置 user_id，请手动更新数据库")


async def rollback():
    """回滚迁移"""
    manager = get_async_task_manager()

    print("开始回滚：移除 async_tasks 表的 user_id 字段")

    async with manager.engine.begin() as conn:
        # PostgreSQL 支持 DROP COLUMN
        print("→ 删除索引 idx_async_tasks_user_id...")
        await conn.execute(text(
            "DROP INDEX IF EXISTS idx_async_tasks_user_id"
        ))

        print("→ 删除列 user_id...")
        await conn.execute(text(
            "ALTER TABLE async_tasks DROP COLUMN IF EXISTS user_id"
        ))

        print("✓ 回滚完成！")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="迁移 async_tasks 表，添加 user_id 字段")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")

    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
