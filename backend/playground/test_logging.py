#!/usr/bin/env python3
"""
日志系统测试脚本

展示如何在项目中使用日志系统
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging import logger, set_stage
from src.models import Stage


def test_basic_logging():
    """测试基本日志功能"""
    print("=" * 80)
    print("1. 基本日志测试")
    print("=" * 80 + "\n")
    
    logger.debug("这是 DEBUG 级别（仅文件可见）")
    logger.info("这是 INFO 级别")
    logger.success("这是 SUCCESS 级别")
    logger.warning("这是 WARNING 级别")
    logger.error("这是 ERROR 级别")


def test_stage_logging():
    """测试阶段标记功能"""
    print("\n" + "=" * 80)
    print("2. 阶段标记测试")
    print("=" * 80 + "\n")
    
    # 系统初始化
    init_log = set_stage(Stage.INIT)
    init_log.info("正在初始化系统...")
    init_log.success("系统初始化完成")
    
    # 配置加载
    config_log = set_stage(Stage.CONFIG)
    config_log.info("正在加载配置文件...")
    config_log.success("配置加载成功")


def test_feishu_workflow():
    """模拟飞书工作流程"""
    print("\n" + "=" * 80)
    print("3. 飞书工作流程测试")
    print("=" * 80 + "\n")
    
    # 飞书认证
    auth_log = set_stage(Stage.FEISHU_AUTH)
    auth_log.info("正在获取飞书访问令牌...")
    auth_log.success("✅ 访问令牌获取成功")
    
    # 查询多维表格
    bitable_log = set_stage(Stage.BITABLE)
    bitable_log.info("正在查询工时多维表格...")
    bitable_log.success("✅ 查询成功，找到 422 条记录")
    
    # 工时检查
    labor_log = set_stage(Stage.LABOR_CHECK)
    labor_log.info("开始检查 2025-10-27 的工时填写情况")
    labor_log.info("应检查人数: 16 人")
    labor_log.warning("⚠️ 发现 9 人未填写工时")
    
    # 请假检查
    leave_log = set_stage(Stage.LEAVE_CHECK)
    leave_log.info("正在检查未填写人员的请假状态...")
    leave_log.info("查询审批系统，找到 12 条审批记录")
    leave_log.success("✅ 找到 1 人请假，已从提醒名单中移除")
    
    # 创建卡片
    card_log = set_stage(Stage.CARD_CREATE)
    card_log.info("正在生成工时提醒卡片...")
    card_log.success("✅ 卡片生成完成")
    
    # 发送消息
    msg_log = set_stage(Stage.MESSAGE_SEND)
    msg_log.info("正在发送工时提醒到飞书群组...")
    msg_log.success("✅ 消息发送成功")


def test_approval_workflow():
    """模拟审批工作流程"""
    print("\n" + "=" * 80)
    print("4. 审批工作流程测试")
    print("=" * 80 + "\n")
    
    # Webhook 回调
    webhook_log = set_stage(Stage.WEBHOOK)
    webhook_log.info("收到 Webhook 回调请求")
    
    # 审批处理
    approval_log = set_stage(Stage.APPROVAL_CALLBACK)
    approval_log.info("解析审批数据...")
    approval_log.info("审批类型: 请假审批")
    approval_log.info("审批状态: APPROVED")
    approval_log.info("申请人: ou_99b9001ef41d9ac2b19a91feff9965bd")
    approval_log.success("✅ 审批处理完成，已创建请假日历事件")


def test_scheduler_workflow():
    """模拟定时任务工作流程"""
    print("\n" + "=" * 80)
    print("5. 定时任务测试")
    print("=" * 80 + "\n")
    
    scheduler_log = set_stage(Stage.SCHEDULER)
    scheduler_log.info("定时任务调度器启动")
    scheduler_log.info("已加载 5 个定时任务")
    
    task_log = set_stage(Stage.TASK_EXEC)
    task_log.info("任务 [每日工时检查-21点] 触发")
    task_log.info("执行参数: date=2025-10-27")
    task_log.success("✅ 任务执行完成，耗时 3.2 秒")


def test_news_workflow():
    """模拟新闻爬取工作流程"""
    print("\n" + "=" * 80)
    print("6. 新闻爬取测试")
    print("=" * 80 + "\n")
    
    scraper_log = set_stage(Stage.NEWS_SCRAPER)
    scraper_log.info("开始爬取 TechCrunch 新闻...")
    scraper_log.info("正在解析 HTML...")
    scraper_log.success("✅ 爬取成功，获取 10 条新闻")
    
    process_log = set_stage(Stage.NEWS_PROCESS)
    process_log.info("正在处理新闻数据...")
    process_log.info("去重后保留 8 条新闻")
    process_log.success("✅ 新闻处理完成")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 80)
    print("7. 错误处理测试")
    print("=" * 80 + "\n")
    
    # 一般错误
    error_log = set_stage(Stage.ERROR)
    error_log.error("❌ 飞书 API 调用失败: 401 Unauthorized")
    
    # 异常捕获
    try:
        result = 1 / 0
    except Exception as e:
        exception_log = set_stage(Stage.EXCEPTION)
        exception_log.exception("捕获到异常")


def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "=" * 80)
    print("8. 上下文管理器测试")
    print("=" * 80 + "\n")
    
    # 使用 with 语句临时切换阶段
    with logger.contextualize(stage=Stage.BITABLE):
        logger.info("正在批量查询记录...")
        logger.info("第 1 页: 100 条")
        logger.info("第 2 页: 100 条")
        logger.info("第 3 页: 50 条")
        logger.success("✅ 批量查询完成")
    
    # 自动恢复到默认阶段
    logger.info("回到默认阶段")


def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "日志系统完整测试" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # 运行所有测试
    test_basic_logging()
    test_stage_logging()
    test_feishu_workflow()
    test_approval_workflow()
    test_scheduler_workflow()
    test_news_workflow()
    test_error_handling()
    test_context_manager()
    
    # 显示日志文件位置
    from src.utils.logging import logger_manager
    print("\n" + "=" * 80)
    print(f"📁 日志文件保存在: {logger_manager.log_dir}")
    print(f"   - debug_*.log: 详细调试日志（DEBUG 及以上）")
    print(f"   - error_*.log: 错误日志（ERROR 及以上）")
    print(f"   - 日志保留: debug 7天, error 30天")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()

