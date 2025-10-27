"""
日志配置模块 - 使用 loguru

统一管理项目日志，支持控制台和文件输出，提供阶段标记功能
"""

import sys
from pathlib import Path
from loguru import logger as _logger
from ..models import Stage


class Logger:
    """
    日志管理器
    
    封装 loguru 的日志功能，提供统一的日志接口
    支持阶段标记、文件轮转、彩色输出等功能
    """
    
    def __init__(self):
        """初始化日志管理器"""
        # 移除默认的 handler
        _logger.remove()
        
        # 获取项目根目录（backend/）
        self.project_root = Path(__file__).parent.parent.parent
        self.log_dir = self.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 配置默认的 extra 值（使用枚举的值而不是枚举本身）
        _logger.configure(extra={"stage": Stage.SYSTEM.value})
        
        # 配置日志格式
        self._setup_handlers()
        
        # 导出 logger 实例
        self.logger = _logger
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 详细的日志格式（用于文件）
        file_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[stage]: <10}</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 简化的控制台格式
        console_format = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <7}</level> | "
            "<cyan>{extra[stage]: <10}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 添加控制台输出 (INFO 及以上级别)
        _logger.add(
            sys.stdout,
            format=console_format,
            level="INFO",
            colorize=True,
            enqueue=True,  # 异步写入
            backtrace=True,
            diagnose=True
        )
        
        # 添加调试日志文件 (DEBUG 及以上级别)
        # 每次运行创建新的日志文件（使用时间戳到秒）
        _logger.add(
            self.log_dir / "debug_{time:YYYY-MM-DD}.log",
            format=file_format,
            level="DEBUG",
            rotation="00:00",  # 每天午夜轮转
            retention="7 days",  # 保留 7 天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # 添加错误日志文件 (ERROR 及以上级别)
        _logger.add(
            self.log_dir / "error_{time:YYYY-MM-DD}.log",
            format=file_format,
            level="ERROR",
            rotation="00:00",
            retention="30 days",  # 错误日志保留 30 天
            compression="zip",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
    
    def get_logger(self, name: str = None):
        """
        获取 logger 实例
        
        Args:
            name: logger 名称，通常使用 __name__
            
        Returns:
            logger 实例
        """
        if name:
            return self.logger.bind(name=name)
        return self.logger
    
    def set_stage(self, stage: Stage):
        """
        设置当前日志阶段
        
        Args:
            stage: 阶段名称，如 Stage.LABOR_CHECK, Stage.FEISHU_API 等
            
        Returns:
            绑定了阶段信息的 logger
            
        Example:
            >>> from src.utils.logging import set_stage
            >>> from src.models import Stage
            >>> 
            >>> log = set_stage(Stage.LABOR_CHECK)
            >>> log.info("开始检查工时")
            # 输出: 17:30:00 | INFO    | 工时检查   | 开始检查工时
        """
        # 传递枚举的值（中文字符串）而不是枚举对象本身
        return self.logger.bind(stage=stage.value)


# 创建全局日志管理器实例
logger_manager = Logger()

# 导出常用的实例和方法
logger = logger_manager.logger
get_logger = logger_manager.get_logger
set_stage = logger_manager.set_stage


# 使用示例和测试
if __name__ == '__main__':
    print("=" * 80)
    print("日志系统测试")
    print("=" * 80 + "\n")
    
    # 基本使用（默认系统级别阶段）
    logger.debug("这是一条 DEBUG 消息（只在文件中显示）")
    logger.info("这是一条 INFO 消息")
    logger.success("这是一条 SUCCESS 消息")
    logger.warning("这是一条 WARNING 消息")
    logger.error("这是一条 ERROR 消息")
    
    print("\n" + "=" * 80)
    print("使用阶段标记")
    print("=" * 80 + "\n")
    
    # 使用阶段标记 - 系统初始化
    init_log = set_stage(Stage.INIT)
    init_log.info("系统初始化开始")
    init_log.success("配置加载完成")
    
    # 飞书 API 调用
    feishu_log = set_stage(Stage.FEISHU_API)
    feishu_log.info("正在获取访问令牌...")
    feishu_log.success("访问令牌获取成功")
    
    # 工时检查
    labor_log = set_stage(Stage.LABOR_CHECK)
    labor_log.info("开始检查 2025-10-27 的工时")
    labor_log.warning("发现 9 人未填写工时")
    labor_log.success("工时检查完成")
    
    # 请假检查
    leave_log = set_stage(Stage.LEAVE_CHECK)
    leave_log.info("检查未填写人员的请假状态...")
    leave_log.success("找到 1 人请假，已从提醒名单中移除")
    
    # 消息发送
    msg_log = set_stage(Stage.MESSAGE_SEND)
    msg_log.info("正在发送工时提醒消息...")
    msg_log.success("消息发送成功")
    
    # 定时任务
    scheduler_log = set_stage(Stage.SCHEDULER)
    scheduler_log.info("定时任务 [工时检查] 已触发")
    scheduler_log.success("任务执行完成")
    
    # 使用上下文管理器（推荐）
    print("\n使用上下文管理器：\n")
    with logger.contextualize(stage=Stage.BITABLE):
        logger.info("正在查询多维表格...")
        logger.success("查询成功，找到 422 条记录")
    
    # 审批处理
    approval_log = set_stage(Stage.APPROVAL)
    approval_log.info("收到审批回调")
    approval_log.success("审批处理完成，已创建请假日历")
    
    # 异常日志
    print("\n测试异常日志：\n")
    try:
        result = 1 / 0
    except Exception as e:
        error_log = set_stage(Stage.ERROR)
        error_log.exception("发生除零错误")
    
    print("\n" + "=" * 80)
    print(f"日志文件保存在: {logger_manager.log_dir}")
    print("=" * 80)

