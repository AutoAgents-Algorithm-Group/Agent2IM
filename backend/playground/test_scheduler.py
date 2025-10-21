#!/usr/bin/env python3
"""
定时任务测试脚本
用于测试飞书定时提醒功能
"""

import sys
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.schedule import ReminderScheduler


def test_task_execution():
    """手动测试任务执行"""
    print("=" * 60)
    print("定时任务测试脚本")
    print("=" * 60)
    
    try:
        # 创建调度器
        config_dir = current_dir / "config"
        scheduler = ReminderScheduler(config_dir=str(config_dir))
        
        # 初始化飞书服务
        print("\n正在初始化飞书服务...")
        scheduler.init_feishu_service(ai_service=None)
        
        print("\n" + "=" * 60)
        print("选择要测试的任务:")
        print("=" * 60)
        print("1. 测试晚上9点群聊提醒")
        print("2. 测试晚上11点私信提醒")
        print("3. 测试早上10点群聊补填提醒")
        print("4. 显示配置信息")
        print("5. 测试多维表格连接")
        print("0. 退出")
        print("=" * 60)
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == "1":
            print("\n🚀 开始测试：晚上9点群聊提醒")
            scheduler.task_evening_first_reminder()
            
        elif choice == "2":
            print("\n🚀 开始测试：晚上11点私信提醒")
            scheduler.task_evening_second_reminder()
            
        elif choice == "3":
            print("\n🚀 开始测试：早上10点群聊补填提醒")
            scheduler.task_morning_makeup_reminder()
            
        elif choice == "4":
            print("\n📋 配置信息:")
            print(f"   应用ID: {scheduler.app_id}")
            print(f"   群聊ID: {scheduler.group_chat_id}")
            print(f"   表格链接: {scheduler.form_url}")
            print(f"   多维表格Token: {scheduler.bitable_app_token}")
            print(f"   数据表ID: {scheduler.bitable_table_id}")
            print(f"   时区: {scheduler.timezone}")
            
            print(f"\n👥 活跃人员列表:")
            people = scheduler.get_active_people()
            for person in people:
                print(f"   - {person.get('name')} ({person.get('user_id')})")
                if person.get('exceptions'):
                    print(f"     例外: {', '.join(person.get('exceptions', []))}")
                if person.get('frequency'):
                    print(f"     频率: {person.get('frequency')}")
            
            print(f"\n📨 消息模板:")
            templates = scheduler.message_config.get("templates", {})
            for template_id, template in templates.items():
                print(f"   - {template_id}: {template.get('name')}")
            
        elif choice == "5":
            print("\n🔗 测试多维表格连接...")
            if not scheduler.bitable_app_token or not scheduler.bitable_table_id:
                print("❌ 多维表格配置不完整，请检查 task.json 中的配置")
            else:
                records = scheduler.feishu_service.get_bitable_records(
                    scheduler.bitable_app_token,
                    scheduler.bitable_table_id
                )
                print(f"✅ 成功获取 {len(records)} 条记录")
                if records:
                    print("\n前3条记录示例:")
                    for i, record in enumerate(records[:3], 1):
                        print(f"   {i}. {record}")
            
        elif choice == "0":
            print("\n👋 再见!")
            return
            
        else:
            print("\n❌ 无效的选项")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_scheduler_startup():
    """测试调度器启动"""
    print("=" * 60)
    print("测试调度器启动")
    print("=" * 60)
    
    try:
        # 创建调度器
        config_dir = current_dir / "config"
        scheduler = ReminderScheduler(config_dir=str(config_dir))
        
        # 初始化飞书服务
        scheduler.init_feishu_service(ai_service=None)
        
        # 启动调度器
        scheduler.start()
        
        print("\n✅ 调度器启动成功")
        print("\n📋 任务列表:")
        scheduler.list_jobs()
        
        print("\n💡 提示: 按 Ctrl+C 停止调度器")
        
        # 保持运行
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭调度器...")
        scheduler.stop()
        print("✅ 调度器已停止")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n请选择测试模式:")
    print("1. 手动测试任务执行")
    print("2. 测试调度器启动（实际运行定时任务）")
    print("0. 退出")
    
    mode = input("\n请输入选项 (0-2): ").strip()
    
    if mode == "1":
        test_task_execution()
    elif mode == "2":
        test_scheduler_startup()
    elif mode == "0":
        print("👋 再见!")
    else:
        print("❌ 无效的选项")

