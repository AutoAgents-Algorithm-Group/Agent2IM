#!/usr/bin/env python3
"""
日志系统集成示例

展示如何在实际代码中集成日志系统
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging import set_stage, logger
from src.models import Stage


# ============================================================================
# 示例 1: 在 FeishuClient 中集成
# ============================================================================

class FeishuClientExample:
    """飞书客户端示例"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        
        # 使用初始化阶段
        init_log = set_stage(Stage.INIT)
        init_log.success("飞书客户端初始化完成")
    
    def get_access_token(self) -> str:
        """获取访问令牌"""
        # 使用飞书认证阶段
        auth_log = set_stage(Stage.FEISHU_AUTH)
        auth_log.info("正在获取访问令牌...")
        
        try:
            # 模拟API调用
            token = "mock_token_123456"
            auth_log.success("✅ 访问令牌获取成功")
            return token
        except Exception as e:
            auth_log.error(f"❌ 获取令牌失败: {e}")
            raise
    
    def query_bitable(self, table_id: str):
        """查询多维表格"""
        # 使用多维表格阶段
        bitable_log = set_stage(Stage.BITABLE)
        bitable_log.info(f"正在查询多维表格 {table_id}...")
        
        try:
            # 模拟查询
            records = [{'id': i} for i in range(100)]
            bitable_log.success(f"✅ 查询成功，找到 {len(records)} 条记录")
            return records
        except Exception as e:
            bitable_log.error(f"❌ 查询失败: {e}")
            raise


# ============================================================================
# 示例 2: 在 LaborHourService 中集成
# ============================================================================

class LaborHourServiceExample:
    """工时检查服务示例"""
    
    def __init__(self):
        # 每个服务可以有自己的默认日志阶段
        self.log = set_stage(Stage.LABOR_CHECK)
        self.log.info("工时检查服务启动")
    
    def check_labor_hours(self, date_str: str):
        """检查工时填写情况"""
        self.log.info(f"开始检查 {date_str} 的工时")
        
        # 1. 模拟查询数据
        with logger.contextualize(stage=Stage.BITABLE):
            logger.info("正在查询工时数据...")
            filled = 7
            not_filled = 9
            logger.success(f"✅ 查询完成: 已填 {filled} 人，未填 {not_filled} 人")
        
        # 2. 检查请假状态
        leave_log = set_stage(Stage.LEAVE_CHECK)
        leave_log.info("正在检查请假状态...")
        on_leave = 1
        leave_log.success(f"✅ {on_leave} 人请假")
        
        # 3. 发送提醒
        if not_filled > 0:
            self.log.warning(f"⚠️ 发现 {not_filled} 人未填写")
            
            msg_log = set_stage(Stage.MESSAGE_SEND)
            msg_log.info("正在发送提醒消息...")
            msg_log.success("✅ 消息发送成功")
        else:
            self.log.success("✅ 所有人已填写工时")
        
        return {'filled': filled, 'not_filled': not_filled, 'on_leave': on_leave}


# ============================================================================
# 示例 3: 在 API 路由中集成
# ============================================================================

def handle_approval_callback(data: dict):
    """处理审批回调"""
    # Webhook 接收
    webhook_log = set_stage(Stage.WEBHOOK)
    webhook_log.info("收到审批回调请求")
    webhook_log.debug(f"回调数据: {data}")
    
    # 审批处理
    approval_log = set_stage(Stage.APPROVAL_CALLBACK)
    
    try:
        approval_log.info("解析审批数据...")
        approval_code = data.get('approval_code')
        status = data.get('status')
        
        approval_log.info(f"审批类型: {approval_code}")
        approval_log.info(f"审批状态: {status}")
        
        if status == 'APPROVED':
            approval_log.success("✅ 审批已通过，正在创建日历事件...")
            # 创建日历事件
            approval_log.success("✅ 日历事件创建成功")
        else:
            approval_log.info(f"审批状态为 {status}，跳过处理")
        
        return {'code': 0, 'msg': 'success'}
        
    except Exception as e:
        error_log = set_stage(Stage.EXCEPTION)
        error_log.exception("审批回调处理失败")
        return {'code': -1, 'msg': str(e)}


# ============================================================================
# 示例 4: 在定时任务中集成
# ============================================================================

def scheduled_labor_check():
    """定时工时检查任务"""
    scheduler_log = set_stage(Stage.SCHEDULER)
    scheduler_log.info("定时任务 [工时检查-21点] 触发")
    
    task_log = set_stage(Stage.TASK_EXEC)
    
    import time
    start_time = time.time()
    
    try:
        task_log.info("开始执行工时检查任务...")
        
        # 执行检查
        service = LaborHourServiceExample()
        result = service.check_labor_hours('2025-10-27')
        
        elapsed = time.time() - start_time
        task_log.success(f"✅ 任务执行完成，耗时 {elapsed:.2f} 秒")
        task_log.info(f"检查结果: {result}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_log = set_stage(Stage.EXCEPTION)
        error_log.exception(f"❌ 任务执行失败，耗时 {elapsed:.2f} 秒")


# ============================================================================
# 示例 5: 在新闻爬虫中集成
# ============================================================================

def scrape_news():
    """爬取新闻"""
    scraper_log = set_stage(Stage.NEWS_SCRAPER)
    scraper_log.info("开始爬取 TechCrunch 新闻...")
    
    try:
        # 模拟爬取
        scraper_log.info("正在解析 HTML...")
        scraper_log.debug("使用 BeautifulSoup 解析器")
        
        news_list = [f"News {i}" for i in range(10)]
        scraper_log.success(f"✅ 爬取成功，获取 {len(news_list)} 条新闻")
        
        # 处理新闻
        process_log = set_stage(Stage.NEWS_PROCESS)
        process_log.info("正在处理新闻数据...")
        process_log.info("去重...")
        process_log.info("格式化...")
        
        processed = news_list[:8]
        process_log.success(f"✅ 处理完成，保留 {len(processed)} 条")
        
        return processed
        
    except Exception as e:
        error_log = set_stage(Stage.EXCEPTION)
        error_log.exception("新闻爬取失败")
        return []


# ============================================================================
# 运行示例
# ============================================================================

def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("日志系统集成示例")
    print("=" * 80 + "\n")
    
    # 示例 1: 飞书客户端
    print("1️⃣ 飞书客户端示例:")
    print("-" * 80)
    client = FeishuClientExample("app_id", "app_secret")
    token = client.get_access_token()
    records = client.query_bitable("table_123")
    print()
    
    # 示例 2: 工时检查服务
    print("2️⃣ 工时检查服务示例:")
    print("-" * 80)
    service = LaborHourServiceExample()
    result = service.check_labor_hours("2025-10-27")
    print()
    
    # 示例 3: 审批回调
    print("3️⃣ 审批回调处理示例:")
    print("-" * 80)
    callback_data = {
        'approval_code': 'A9D489DC-5F55-4418-99F1-01E1CE734CA1',
        'status': 'APPROVED'
    }
    response = handle_approval_callback(callback_data)
    print()
    
    # 示例 4: 定时任务
    print("4️⃣ 定时任务示例:")
    print("-" * 80)
    scheduled_labor_check()
    print()
    
    # 示例 5: 新闻爬虫
    print("5️⃣ 新闻爬虫示例:")
    print("-" * 80)
    news = scrape_news()
    print()
    
    # 显示日志文件位置
    from src.utils.logging import logger_manager
    print("=" * 80)
    print(f"📁 日志文件保存在: {logger_manager.log_dir}")
    print(f"   - debug_{logger_manager.log_dir.name}.log")
    print(f"   - error_{logger_manager.log_dir.name}.log")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()

