#!/usr/bin/env python3
"""
定时任务启动脚本 - 简化版
用于快速测试定时提醒功能
"""

import sys
import time
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.schedule.scheduler import ReminderScheduler


def main():
    print("=" * 80)
    print("  飞书定时任务调度器 - 测试启动")
    print("=" * 80)
    
    try:
        # 配置目录
        config_dir = backend_dir / "config"
        
        print(f"\n📂 配置目录: {config_dir}")
        print(f"   - task.json")
        print(f"   - message.json")
        print(f"   - people.json")
        
        # 创建调度器
        print("\n🔧 正在初始化调度器...")
        scheduler = ReminderScheduler(config_dir=str(config_dir))
        
        # 初始化飞书服务
        print("\n🔧 正在初始化飞书服务...")
        scheduler.init_feishu_service(ai_service=None)
        
        print("\n" + "=" * 80)
        print("  选择测试模式")
        print("=" * 80)
        print("1. 手动触发任务（立即执行一次）")
        print("2. 启动定时调度器（按配置时间自动执行）")
        print("3. 查看配置信息")
        print("4. 测试Bitable连接")
        print("0. 退出")
        print("=" * 80)
        
        choice = input("\n请选择 (0-4): ").strip()
        
        if choice == "1":
            manual_trigger_task(scheduler)
            
        elif choice == "2":
            start_scheduler(scheduler)
            
        elif choice == "3":
            show_config(scheduler)
            
        elif choice == "4":
            test_bitable_connection(scheduler)
            
        elif choice == "0":
            print("\n👋 再见!")
            return
        else:
            print("\n❌ 无效的选项")
            
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def manual_trigger_task(scheduler):
    """手动触发任务"""
    print("\n" + "=" * 80)
    print("  手动触发任务")
    print("=" * 80)
    print("1. 晚上9点群聊提醒")
    print("2. 晚上11点私信提醒")
    print("3. 早上10点群聊补填提醒")
    print("0. 返回")
    print("=" * 80)
    
    task_choice = input("\n请选择任务 (0-3): ").strip()
    
    if task_choice == "1":
        print("\n🚀 开始执行：晚上9点群聊提醒")
        scheduler.tasks.evening_first_reminder()
        
    elif task_choice == "2":
        print("\n🚀 开始执行：晚上11点私信提醒")
        scheduler.tasks.evening_second_reminder()
        
    elif task_choice == "3":
        print("\n🚀 开始执行：早上10点群聊补填提醒")
        scheduler.tasks.morning_makeup_reminder()
        
    elif task_choice == "0":
        return
    else:
        print("\n❌ 无效的选项")
    
    print("\n✅ 任务执行完成")


def start_scheduler(scheduler):
    """启动定时调度器"""
    print("\n" + "=" * 80)
    print("  启动定时调度器")
    print("=" * 80)
    
    try:
        scheduler.start()
        
        print("\n" + "=" * 80)
        print("  调度器运行中...")
        print("=" * 80)
        print("\n💡 提示:")
        print("   - 任务将按配置的时间自动执行")
        print("   - 按 Ctrl+C 停止调度器")
        print("   - 日志会实时显示任务执行情况")
        print("\n" + "=" * 80)
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭调度器...")
        scheduler.stop()
        print("✅ 调度器已停止")


def show_config(scheduler):
    """显示配置信息"""
    print("\n" + "=" * 80)
    print("  配置信息")
    print("=" * 80)
    
    # 飞书配置
    print("\n📱 飞书配置:")
    print(f"   应用ID: {scheduler.app_id}")
    print(f"   应用密钥: {'*' * 20}")
    print(f"   群聊ID: {scheduler.group_chat_id}")
    print(f"   表单URL: {scheduler.form_url}")
    print(f"   时区: {scheduler.timezone}")
    
    # 多维表格配置
    print("\n📊 多维表格配置:")
    print(f"   App Token: {scheduler.bitable_app_token}")
    print(f"   Table ID: {scheduler.bitable_table_id}")
    
    # 任务配置
    print("\n📋 定时任务:")
    tasks = scheduler.task_config.get("tasks", [])
    for task in tasks:
        status = "✅ 启用" if task.get("enabled") else "❌ 禁用"
        print(f"   {status} - {task.get('name')} (每天 {task.get('time')})")
    
    # 人员配置
    print("\n👥 人员列表:")
    people = scheduler.people_config.get("people", [])
    print(f"   总人数: {len(people)}")
    
    active_count = sum(1 for p in people if not p.get('off', False))
    print(f"   在职人数: {active_count}")
    print(f"   请假人数: {len(people) - active_count}")
    
    # 显示前5个人员
    print("\n   前5名人员:")
    for i, person in enumerate(people[:5], 1):
        status = "🏖️ 请假" if person.get('off', False) else "✅ 在职"
        exceptions = person.get('exceptions', [])
        exc_str = f" (例外: {', '.join(exceptions)})" if exceptions else ""
        print(f"   {i}. {person.get('name')} - {status}{exc_str}")
    
    # 消息模板
    print("\n📨 消息模板:")
    templates = scheduler.message_config.get("templates", {})
    for template_id, template in templates.items():
        print(f"   - {template.get('name', template_id)}")


def test_bitable_connection(scheduler):
    """测试Bitable连接"""
    print("\n" + "=" * 80)
    print("  测试多维表格连接")
    print("=" * 80)
    
    if not scheduler.bitable_app_token or not scheduler.bitable_table_id:
        print("\n❌ 多维表格配置不完整")
        print("   请检查 task.json 中的配置:")
        print(f"   - bitable_app_token: {scheduler.bitable_app_token or '未配置'}")
        print(f"   - bitable_table_id: {scheduler.bitable_table_id or '未配置'}")
        return
    
    try:
        print(f"\n🔗 正在连接多维表格...")
        print(f"   App Token: {scheduler.bitable_app_token}")
        print(f"   Table ID: {scheduler.bitable_table_id}")
        
        # 这里需要根据实际的API来调整
        # 暂时先显示配置信息
        print("\n✅ 配置已加载")
        print("   注意: 实际连接测试需要在任务执行时进行")
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

