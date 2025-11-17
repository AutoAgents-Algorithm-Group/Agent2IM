"""
测试审批日历创建功能

使用真实的审批事件数据测试日历创建是否成功
"""

import sys
import os
import json
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.service.feishu.approval import create_approval_service_from_config


def main():
    """测试审批事件处理 - 使用真实的审批事件数据"""
    
    print("=" * 80)
    print("🧪 测试审批日历创建功能")
    print("=" * 80)
    
    # 真实的审批事件数据（从实际日志中获取）
    sample_event = {
        "uuid": "746c08e22ecb3cdcdf35ace8604c40c5",
        "event": {
            "app_id": "cli_a875a7a04178100c",
            "approval_code": "A9D489DC-5F55-4418-99F1-01E1CE734CA1",
            "employee_id": "ab435gf8",
            "open_id": "ou_4658964394c36b15d4952a9b9cb3f33f",
            "user_id": "",  # 审批事件中为空，代码会使用 open_id
            "instance_code": f"TEST-{int(time.time())}",  # 使用唯一的测试实例编码
            "leave_type": "年假",
            "leave_start_time": "2025-11-17 00:00:00",
            "leave_end_time": "2025-11-18 00:00:00",
            "leave_reason": "🧪 测试审批日历创建功能",
            "type": "leave_approval"
        },
        "type": "event_callback"
    }
    
    print("\n📋 测试事件信息:")
    print(f"   审批类型: {sample_event['event']['leave_type']}")
    print(f"   申请人 employee_id: {sample_event['event']['employee_id']}")
    print(f"   申请人 open_id: {sample_event['event']['open_id']}")
    print(f"   请假时间: {sample_event['event']['leave_start_time']} ~ {sample_event['event']['leave_end_time']}")
    print(f"   实例编码: {sample_event['event']['instance_code']}")
    
    print("\n" + "=" * 80)
    print("1️⃣ 初始化审批服务...")
    print("=" * 80)
    
    try:
        approval_service = create_approval_service_from_config()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("2️⃣ 处理审批事件...")
    print("=" * 80)
    
    try:
        result = approval_service.handle_approval_event(sample_event)
        
        print("\n" + "=" * 80)
        print("3️⃣ 处理结果")
        print("=" * 80)
        
        print(f"\n状态: {result.get('status')}")
        
        if result.get('status') == 'success':
            print(f"\n{'='*80}")
            print(f"✅✅✅ 测试成功！日历事件已创建 ✅✅✅")
            print(f"{'='*80}")
            print(f"\n事件ID: {result.get('calendar_event_id', 'N/A')}")
            print(f"\n🎉 审批日历创建功能正常工作！")
            print(f"💡 请在飞书日历中查看该请假日程")
            
        elif result.get('status') == 'error':
            print(f"\n{'='*80}")
            print(f"❌❌❌ 测试失败 ❌❌❌")
            print(f"{'='*80}")
            print(f"\n错误信息: {result.get('message')}")
            if result.get('code'):
                print(f"错误码: {result.get('code')}")
            
            # 根据错误码给出建议
            error_code = result.get('code')
            error_msg = result.get('message', '')
            
            print(f"\n🔍 错误分析:")
            if error_code == 99992361 or 'cross app' in error_msg:
                print(f"   问题: open_id cross app")
                print(f"\n   💡 可能原因:")
                print(f"      ❌ open_id 不属于当前应用")
                print(f"      ❌ 审批事件的 app_id 与配置文件不一致")
                print(f"\n   🔧 解决方案:")
                print(f"      1. ✅ 已修改配置文件使用 cli_a875a7a04178100c")
                print(f"      2. ⚠️  检查 app_secret 是否正确")
                print(f"      3. 💡 在飞书审批事件订阅中启用 user_id 字段")
                
            elif error_code == 99991401 or 'permission' in error_msg.lower():
                print(f"   问题: 权限不足")
                print(f"\n   🔧 解决方案:")
                print(f"      1. 登录飞书开放平台: https://open.feishu.cn/app")
                print(f"      2. 找到应用: cli_a875a7a04178100c")
                print(f"      3. 权限管理 → 申请 'calendar:calendar' 权限")
                print(f"      4. 发布新版本或请管理员审批")
                
            else:
                print(f"   ⚠️  检查项:")
                print(f"      □ 飞书应用是否有日历权限")
                print(f"      □ app_id 和 app_secret 是否正确")
                print(f"      □ open_id 是否有效")
                
        else:
            print(f"\n⚠️ 处理被跳过")
            print(f"原因: {result.get('reason', result.get('message'))}")
        
        print(f"\n📋 完整结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ 测试过程异常:")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
