"""
数据模型定义
"""

from enum import Enum


class Stage(str, Enum):
    """
    日志阶段标记
    
    用于标识不同的业务阶段和操作类型
    """
    # 系统级别
    SYSTEM = "系统"
    INIT = "初始化"
    CONFIG = "配置加载"
    
    # 飞书相关
    FEISHU_API = "飞书API"
    FEISHU_AUTH = "飞书认证"
    BITABLE = "多维表格"
    CARD_CREATE = "卡片生成"
    MESSAGE_SEND = "消息发送"
    
    # 工时相关
    LABOR_CHECK = "工时检查"
    LABOR_SUMMARY = "工时统计"
    LEAVE_CHECK = "请假检查"
    
    # 审批相关
    APPROVAL = "审批处理"
    APPROVAL_CALLBACK = "审批回调"
    
    # 定时任务
    SCHEDULER = "定时任务"
    TASK_EXEC = "任务执行"
    
    # 新闻爬取
    NEWS_SCRAPER = "新闻爬取"
    NEWS_PROCESS = "新闻处理"
    
    # Webhook
    WEBHOOK = "Webhook"
    EVENT_CALLBACK = "事件回调"
    
    # 错误处理
    ERROR = "错误处理"
    EXCEPTION = "异常捕获"

