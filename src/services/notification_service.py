"""通知系统业务逻辑服务

提供公告的CRUD操作、读取跟踪、推送广播等功能
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, desc, func
from loguru import logger

from ..database import get_db_manager, Announcement, UserNotification, User
from ..utils.sse_manager import get_sse_manager


class NotificationService:
    """通知系统服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.sse_manager = get_sse_manager()

    # ==================== 公告管理（管理员） ====================

    async def create_announcement(self, data: dict, admin_id: str) -> Announcement:
        """创建公告

        Args:
            data: 公告数据
            admin_id: 管理员ID

        Returns:
            Announcement: 创建的公告对象
        """
        async with self.db_manager.get_session() as session:
            announcement = Announcement(
                title=data.get("title"),
                content=data.get("content"),
                priority=data.get("priority", "normal"),
                announcement_type=data.get("announcement_type", "system"),
                is_pinned=data.get("is_pinned", False),
                is_published=data.get("is_published", True),
                target_audience=data.get("target_audience", "all"),
                cover_image_url=data.get("cover_image_url"),
                cover_image_path=data.get("cover_image_path"),
                created_by=admin_id,
            )

            # 如果设置了发布时间
            if data.get("published_at"):
                announcement.published_at = data["published_at"]
            elif data.get("is_published", True):
                announcement.published_at = datetime.utcnow()

            # 如果设置了过期时间
            if data.get("expires_at"):
                announcement.expires_at = data["expires_at"]

            session.add(announcement)
            await session.commit()
            await session.refresh(announcement)

            logger.info(f"创建公告成功: id={announcement.id}, title={announcement.title}")

            # 如果立即发布，创建用户通知记录并推送
            if announcement.is_published and announcement.published_at and announcement.published_at <= datetime.utcnow():
                await self._create_and_push_notifications(announcement)

            return announcement

    async def update_announcement(self, announcement_id: str, data: dict, admin_id: str) -> Optional[Announcement]:
        """更新公告

        Args:
            announcement_id: 公告ID
            data: 更新数据
            admin_id: 管理员ID

        Returns:
            Announcement: 更新后的公告对象，如果不存在返回None
        """
        async with self.db_manager.get_session() as session:
            # 查询公告
            result = await session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
            announcement = result.scalar_one_or_none()

            if not announcement:
                return None

            # 更新字段
            if "title" in data:
                announcement.title = data["title"]
            if "content" in data:
                announcement.content = data["content"]
            if "priority" in data:
                announcement.priority = data["priority"]
            if "announcement_type" in data:
                announcement.announcement_type = data["announcement_type"]
            if "is_pinned" in data:
                announcement.is_pinned = data["is_pinned"]
            if "is_published" in data:
                announcement.is_published = data["is_published"]
            if "target_audience" in data:
                announcement.target_audience = data["target_audience"]
            if "cover_image_url" in data:
                announcement.cover_image_url = data["cover_image_url"]
            if "cover_image_path" in data:
                announcement.cover_image_path = data["cover_image_path"]
            if "published_at" in data:
                announcement.published_at = data["published_at"]
            if "expires_at" in data:
                announcement.expires_at = data["expires_at"]

            announcement.updated_by = admin_id

            await session.commit()
            await session.refresh(announcement)

            logger.info(f"更新公告成功: id={announcement.id}")

            return announcement

    async def delete_announcement(self, announcement_id: str) -> bool:
        """删除公告

        Args:
            announcement_id: 公告ID

        Returns:
            bool: 是否删除成功
        """
        async with self.db_manager.get_session() as session:
            # 查询公告
            result = await session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
            announcement = result.scalar_one_or_none()

            if not announcement:
                return False

            # 删除公告（级联删除关联的用户通知记录）
            await session.delete(announcement)
            await session.commit()

            logger.info(f"删除公告成功: id={announcement_id}")
            return True

    async def get_announcement(self, announcement_id: str) -> Optional[Announcement]:
        """获取公告详情

        Args:
            announcement_id: 公告ID

        Returns:
            Announcement: 公告对象，如果不存在返回None
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
            return result.scalar_one_or_none()

    async def list_announcements(
        self,
        page: int = 1,
        page_size: int = 20,
        priority: Optional[str] = None,
        announcement_type: Optional[str] = None,
        is_published: Optional[bool] = None,
        target_audience: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取公告列表（管理员）

        Args:
            page: 页码
            page_size: 每页数量
            priority: 优先级筛选
            announcement_type: 类型筛选
            is_published: 发布状态筛选
            target_audience: 目标受众筛选

        Returns:
            dict: 包含列表和分页信息
        """
        async with self.db_manager.get_session() as session:
            # 构建查询条件
            conditions = []

            if priority:
                conditions.append(Announcement.priority == priority)
            if announcement_type:
                conditions.append(Announcement.announcement_type == announcement_type)
            if is_published is not None:
                conditions.append(Announcement.is_published == is_published)
            if target_audience:
                conditions.append(Announcement.target_audience == target_audience)

            # 查询总数
            count_query = select(func.count(Announcement.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # 查询列表
            query = select(Announcement)
            if conditions:
                query = query.where(and_(*conditions))

            # 排序：置顶优先，然后按优先级，最后按创建时间倒序
            query = query.order_by(
                desc(Announcement.is_pinned),
                desc(Announcement.priority),
                desc(Announcement.created_at)
            )

            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            result = await session.execute(query)
            announcements = result.scalars().all()

            return {
                "items": [a.to_dict() for a in announcements],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }

    async def publish_announcement(self, announcement_id: str) -> Optional[Announcement]:
        """发布公告

        Args:
            announcement_id: 公告ID

        Returns:
            Announcement: 发布后的公告对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
            announcement = result.scalar_one_or_none()

            if not announcement:
                return None

            announcement.is_published = True
            announcement.published_at = datetime.utcnow()

            await session.commit()
            await session.refresh(announcement)

            logger.info(f"发布公告成功: id={announcement_id}")

            # 创建用户通知记录并推送
            await self._create_and_push_notifications(announcement)

            return announcement

    # ==================== 用户通知 ====================

    async def get_my_notifications(
        self,
        user_id: str,
        user_role: str,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """获取我的通知列表

        Args:
            user_id: 用户ID
            user_role: 用户角色
            page: 页码
            page_size: 每页数量
            is_read: 是否已读筛选

        Returns:
            dict: 包含列表和分页信息
        """
        async with self.db_manager.get_session() as session:
            # 查询条件：公告已发布且未过期，且目标受众包含该用户
            now = datetime.utcnow()

            # 基础查询：已发布的公告
            announcement_conditions = [
                Announcement.is_published == True,
                Announcement.published_at <= now,
            ]

            # 未过期条件
            announcement_conditions.append(
                or_(
                    Announcement.expires_at.is_(None),
                    Announcement.expires_at > now
                )
            )

            # 目标受众条件
            audience_conditions = [
                Announcement.target_audience == "all"
            ]
            if user_role == "admin":
                audience_conditions.append(Announcement.target_audience == "admins_only")
            else:
                audience_conditions.append(Announcement.target_audience == "users_only")

            announcement_conditions.append(or_(*audience_conditions))

            # 查询总数
            count_query = select(func.count(Announcement.id)).where(and_(*announcement_conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # 查询列表
            query = select(Announcement).where(and_(*announcement_conditions))

            # 排序：置顶优先，然后按优先级，最后按发布时间倒序
            query = query.order_by(
                desc(Announcement.is_pinned),
                desc(Announcement.priority),
                desc(Announcement.published_at)
            )

            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            result = await session.execute(query)
            announcements = result.scalars().all()

            # 批量查询读取状态
            announcement_ids = [a.id for a in announcements]
            notification_result = await session.execute(
                select(UserNotification).where(
                    and_(
                        UserNotification.announcement_id.in_(announcement_ids),
                        UserNotification.user_id == user_id
                    )
                )
            )
            notifications = notification_result.scalars().all()

            # 构建读取状态映射
            read_status_map = {n.announcement_id: n for n in notifications}

            # 构建返回数据
            items = []
            for announcement in announcements:
                item = announcement.to_dict()
                notification = read_status_map.get(announcement.id)

                if notification:
                    item["is_read"] = notification.is_read
                    item["read_at"] = notification.read_at.isoformat() if notification.read_at else None
                    item["is_clicked"] = notification.is_clicked
                    item["clicked_at"] = notification.clicked_at.isoformat() if notification.clicked_at else None
                else:
                    item["is_read"] = False
                    item["read_at"] = None
                    item["is_clicked"] = False
                    item["clicked_at"] = None

                items.append(item)

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }

    async def get_unread_count(self, user_id: str, user_role: str) -> int:
        """获取未读通知数量

        Args:
            user_id: 用户ID
            user_role: 用户角色

        Returns:
            int: 未读数量
        """
        async with self.db_manager.get_session() as session:
            now = datetime.utcnow()

            # 查询条件：未读的公告
            announcement_conditions = [
                Announcement.is_published == True,
                Announcement.published_at <= now,
                or_(
                    Announcement.expires_at.is_(None),
                    Announcement.expires_at > now
                )
            ]

            # 目标受众条件
            audience_conditions = [
                Announcement.target_audience == "all"
            ]
            if user_role == "admin":
                audience_conditions.append(Announcement.target_audience == "admins_only")
            else:
                audience_conditions.append(Announcement.target_audience == "users_only")

            announcement_conditions.append(or_(*audience_conditions))

            # 查询未读数量：总公告数 - 已读数
            # 方法：LEFT JOIN user_notifications，统计未读的
            from sqlalchemy import outerjoin

            query = (
                select(func.count(Announcement.id))
                .select_from(
                    outerjoin(
                        Announcement,
                        UserNotification,
                        and_(
                            Announcement.id == UserNotification.announcement_id,
                            UserNotification.user_id == user_id
                        )
                    )
                )
                .where(
                    and_(
                        *announcement_conditions,
                        or_(
                            UserNotification.id.is_(None),
                            UserNotification.is_read == False
                        )
                    )
                )
            )

            result = await session.execute(query)
            return result.scalar() or 0

    async def mark_as_read(self, user_id: str, announcement_id: str) -> bool:
        """标记通知为已读

        Args:
            user_id: 用户ID
            announcement_id: 公告ID

        Returns:
            bool: 是否成功
        """
        async with self.db_manager.get_session() as session:
            # 查询或创建通知记录
            result = await session.execute(
                select(UserNotification).where(
                    and_(
                        UserNotification.announcement_id == announcement_id,
                        UserNotification.user_id == user_id
                    )
                )
            )
            notification = result.scalar_one_or_none()

            if notification:
                if not notification.is_read:
                    notification.is_read = True
                    notification.read_at = datetime.utcnow()
                    await session.commit()
                return True
            else:
                # 创建通知记录
                notification = UserNotification(
                    announcement_id=announcement_id,
                    user_id=user_id,
                    is_read=True,
                    read_at=datetime.utcnow(),
                    is_pushed=True,
                    pushed_at=datetime.utcnow(),
                    push_method="sse"
                )
                session.add(notification)
                await session.commit()
                return True

    async def mark_all_as_read(self, user_id: str) -> int:
        """标记所有通知为已读

        Args:
            user_id: 用户ID

        Returns:
            int: 标记为已读的数量
        """
        async with self.db_manager.get_session() as session:
            # 查询所有未读的通知记录
            result = await session.execute(
                select(UserNotification).where(
                    and_(
                        UserNotification.user_id == user_id,
                        UserNotification.is_read == False
                    )
                )
            )
            notifications = result.scalars().all()

            count = 0
            for notification in notifications:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                count += 1

            await session.commit()
            logger.info(f"用户 {user_id} 标记了 {count} 条通知为已读")
            return count

    async def mark_as_clicked(self, user_id: str, announcement_id: str) -> bool:
        """标记通知为已点击

        Args:
            user_id: 用户ID
            announcement_id: 公告ID

        Returns:
            bool: 是否成功
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(UserNotification).where(
                    and_(
                        UserNotification.announcement_id == announcement_id,
                        UserNotification.user_id == user_id
                    )
                )
            )
            notification = result.scalar_one_or_none()

            if notification:
                if not notification.is_clicked:
                    notification.is_clicked = True
                    notification.clicked_at = datetime.utcnow()
                    await session.commit()

                # 增加公告点击数
                await session.execute(
                    update(Announcement)
                    .where(Announcement.id == announcement_id)
                    .values(click_count=Announcement.click_count + 1)
                )
                await session.commit()
                return True

            return False

    async def dismiss_notification(self, user_id: str, announcement_id: str) -> bool:
        """删除/忽略通知（用户侧删除）

        Args:
            user_id: 用户ID
            announcement_id: 公告ID

        Returns:
            bool: 是否成功
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                delete(UserNotification).where(
                    and_(
                        UserNotification.announcement_id == announcement_id,
                        UserNotification.user_id == user_id
                    )
                )
            )
            await session.commit()
            return result.rowcount > 0

    async def increment_view_count(self, announcement_id: str) -> bool:
        """增加公告浏览次数

        Args:
            announcement_id: 公告ID

        Returns:
            bool: 是否成功
        """
        async with self.db_manager.get_session() as session:
            await session.execute(
                update(Announcement)
                .where(Announcement.id == announcement_id)
                .values(view_count=Announcement.view_count + 1)
            )
            await session.commit()
            return True

    # ==================== 私有方法 ====================

    async def _create_and_push_notifications(self, announcement: Announcement):
        """创建用户通知记录并推送

        Args:
            announcement: 公告对象
        """
        async with self.db_manager.get_session() as session:
            # 根据目标受众获取用户列表
            user_conditions = [User.status == "active"]

            if announcement.target_audience == "admins_only":
                user_conditions.append(User.role == "admin")
            elif announcement.target_audience == "users_only":
                user_conditions.append(User.role == "user")
            # target_audience == "all" 则不限制角色

            # 查询目标用户
            result = await session.execute(
                select(User.id).where(and_(*user_conditions))
            )
            user_ids = [row[0] for row in result.all()]

            if not user_ids:
                logger.warning(f"没有找到目标用户: audience={announcement.target_audience}")
                return

            logger.info(f"准备推送公告给 {len(user_ids)} 个用户: {announcement.title}")

            # 批量创建通知记录
            now = datetime.utcnow()
            notifications = [
                UserNotification(
                    announcement_id=announcement.id,
                    user_id=user_id,
                    is_pushed=True,
                    pushed_at=now,
                    push_method="sse"
                )
                for user_id in user_ids
            ]

            session.add_all(notifications)
            await session.commit()

            # 异步推送通知（不阻塞）
            asyncio.create_task(self._push_to_users(announcement, user_ids))

    async def _push_to_users(self, announcement: Announcement, user_ids: List[str]):
        """推送通知给用户列表

        Args:
            announcement: 公告对象
            user_ids: 用户ID列表
        """
        # 构造推送数据
        push_data = {
            "type": "new_announcement",
            "data": {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content[:200] + "..." if len(announcement.content) > 200 else announcement.content,
                "priority": announcement.priority,
                "announcement_type": announcement.announcement_type,
                "cover_image_url": announcement.cover_image_url,
                "published_at": announcement.published_at.isoformat() if announcement.published_at else None,
            }
        }

        # 逐个推送
        success_count = 0
        for user_id in user_ids:
            sent = await self.sse_manager.send_to_user(user_id, push_data, "announcement")
            if sent:
                success_count += 1

        logger.info(f"SSE推送完成: 成功 {success_count}/{len(user_ids)}")


# 全局服务实例
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取全局通知服务实例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
