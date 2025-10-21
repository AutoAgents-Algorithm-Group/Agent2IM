"""
事件管理器模块
用于全局事件去重管理
"""

import time
from typing import Set


class EventManager:
    """全局事件去重管理器"""
    
    def __init__(self):
        # 全局事件去重缓存（生产环境建议使用Redis）
        self.processed_events: Set[str] = set()
        self.event_timestamps: dict = {}  # 记录事件处理时间，用于清理过期事件
    
    def is_event_processed(self, event_id: str) -> bool:
        """检查事件是否已处理"""
        return event_id in self.processed_events

    def mark_event_processed(self, event_id: str):
        """标记事件已处理"""
        self.processed_events.add(event_id)
        self.event_timestamps[event_id] = time.time()

    def cleanup_old_events(self):
        """清理10分钟以前的事件记录"""
        current_time = time.time()
        expired_events = [
            event_id for event_id, timestamp in self.event_timestamps.items()
            if current_time - timestamp > 600  # 10分钟
        ]
        
        for event_id in expired_events:
            self.processed_events.discard(event_id)
            self.event_timestamps.pop(event_id, None)
        
        if expired_events:
            print(f"🧹 清理了 {len(expired_events)} 个过期事件记录")


# 全局事件管理器实例
event_manager = EventManager()

