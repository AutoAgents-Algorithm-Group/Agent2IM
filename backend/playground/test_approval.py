#!/usr/bin/env python3
"""
测试审批事件处理

使用方法:
    python test_approval.py
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.service.approval_service import create_approval_service_from_config


def test_url_verification():
    """测试 URL 验证"""
    print("=" * 80)
    print("测试 1: URL 验证")
    print("=" * 80)
    
    data = {
        "type": "url_verification",
        "challenge": "test_challenge_12345"
    }
    
    print(f"📨 模拟 URL 验证请求")
    print(f"   Challenge: {data['challenge']}")
    print(f"\n✅ 期望响应: {{'challenge': '{data['challenge']}'}}")
    print()


def test_approval_event():
    """测试审批事件处理"""
    print("=" * 80)
    print("测试 2: 审批通过事件")
    print("=" * 80)
    
    # 模拟审批通过事件
    data = {
        "type": "event_callback",
        "event_id": "test_event_001",
        "event": {
            "type": "approval_instance",
            "status": "APPROVED",
            "approval_code": "7C468A54-8745-2245-9675-08654A59C265",
            "instance_code": "81D31358-93AF-92C6-7425-01A5D67C4E71",
            "user_id": "ou_9210e6e39f53c7658a5fe518783a2f3e",
            "open_id": "ou_9210e6e39f53c7658a5fe518783a2f3e"
        }
    }
    
    print(f"📨 模拟审批通过事件")
    print(f"   审批定义: {data['event']['approval_code']}")
    print(f"   实例编码: {data['event']['instance_code']}")
    print(f"   申请人: {data['event']['user_id']}")
    print(f"   状态: {data['event']['status']}")
    print()
    
    try:
        # 创建审批服务
        approval_service = create_approval_service_from_config()
        
        # 处理事件
        result = approval_service.handle_approval_event(data)
        
        print(f"\n📊 处理结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_rejected_approval():
    """测试审批拒绝事件（应该被忽略）"""
    print("\n" + "=" * 80)
    print("测试 3: 审批拒绝事件（应该被忽略）")
    print("=" * 80)
    
    data = {
        "type": "event_callback",
        "event_id": "test_event_002",
        "event": {
            "type": "approval_instance",
            "status": "REJECTED",
            "approval_code": "7C468A54-8745-2245-9675-08654A59C265",
            "instance_code": "81D31358-93AF-92C6-7425-01A5D67C4E72",
            "user_id": "ou_9210e6e39f53c7658a5fe518783a2f3e",
            "open_id": "ou_9210e6e39f53c7658a5fe518783a2f3e"
        }
    }
    
    print(f"📨 模拟审批拒绝事件")
    print(f"   状态: {data['event']['status']}")
    print()
    
    try:
        approval_service = create_approval_service_from_config()
        result = approval_service.handle_approval_event(data)
        
        print(f"\n📊 处理结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n✅ 预期行为: 审批状态为 REJECTED，应该跳过处理")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


def test_create_timeoff_calendar():
    """测试直接创建请假日历"""
    print("\n" + "=" * 80)
    print("测试 4: 直接创建请假日历")
    print("=" * 80)
    
    try:
        approval_service = create_approval_service_from_config()
        
        # 测试参数
        user_id = "ou_9210e6e39f53c7658a5fe518783a2f3e"
        start_time = "2025-10-27"
        end_time = "2025-10-28"
        title = "请假中(全天) / Time Off"
        description = "测试请假日历创建"
        
        print(f"📅 创建请假日历:")
        print(f"   用户: {user_id}")
        print(f"   开始: {start_time}")
        print(f"   结束: {end_time}")
        print(f"   标题: {title}")
        print()
        
        result = approval_service._create_timeoff_event(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            title=title,
            description=description
        )
        
        print(f"\n📊 创建结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('status') == 'success':
            print(f"\n✅ 请假日历创建成功!")
            print(f"   日历事件ID: {result.get('event_id')}")
        else:
            print(f"\n⚠️ 创建失败: {result.get('message')}")
            print(f"\n💡 可能的原因:")
            print(f"   1. Token 已过期")
            print(f"   2. 缺少日历权限")
            print(f"   3. 用户 ID 不正确")
            print(f"   4. 时间参数错误")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("\n")
    print("🧪 审批事件处理测试")
    print("=" * 80)
    print()
    
    # 测试 1: URL 验证
    test_url_verification()
    
    # 测试 2: 审批通过事件
    test_approval_event()
    
    # 测试 3: 审批拒绝事件
    test_rejected_approval()
    
    # 测试 4: 直接创建请假日历
    test_create_timeoff_calendar()
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("   1. 在飞书开放平台配置事件订阅")
    print("   2. 订阅 approval_instance 事件")
    print("   3. 配置回调地址: https://your-domain.com/feishu/approval/callback")
    print("   4. 确保应用有审批和日历权限")
    print()


if __name__ == '__main__':
    main()

