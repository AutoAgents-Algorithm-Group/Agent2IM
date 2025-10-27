#!/usr/bin/env python3
"""
测试请假检测功能

测试场景：
1. 检查指定日期的工时填写情况
2. 验证请假人员是否被正确识别
3. 验证请假人员是否被排除（不会被@提醒）
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.feishu.client import FeishuClient
from src.utils.feishu.bitable import BitableAPI
import json


def test_leave_detection(date_str=None):
    """
    测试请假检测
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD，默认为今天
    """
    print("=" * 80)
    print("🧪 测试请假检测功能")
    print("=" * 80)
    print()
    
    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'src/config/labor_hour.json'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建飞书客户端
    feishu = config['feishu']
    client = FeishuClient(app_id=feishu['app_id'], app_secret=feishu['app_secret'])
    
    # 创建 Bitable API
    bitable = BitableAPI(client, url=config['bitable']['url'])
    
    # 确定检查日期
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 检查日期: {date_str}")
    print()
    
    # 执行工时检查（包含请假检测）
    print("🔍 开始检查工时填写情况...")
    print()
    
    result = bitable.check_users_filled(date_str=date_str)
    
    print()
    print("=" * 80)
    print("📊 检查结果")
    print("=" * 80)
    print()
    
    # 显示基本统计
    filled = result.get('filled', [])
    not_filled = result.get('not_filled', [])
    not_filled_with_id = result.get('not_filled_with_id', [])
    on_leave = result.get('on_leave', [])
    on_leave_from_calendar = result.get('on_leave_from_calendar', [])
    exception_day = result.get('exception_day', [])
    fill_rate = result.get('fill_rate', 0)
    is_holiday = result.get('is_holiday', False)
    
    if is_holiday:
        print("🎉 今天是节假日，无需检查")
        return
    
    print(f"📈 填写率: {fill_rate*100:.1f}%")
    print()
    
    print(f"✅ 已填写: {len(filled)} 人")
    if filled:
        for name in filled:
            print(f"   - {name}")
    print()
    
    print(f"❌ 未填写: {len(not_filled)} 人")
    if not_filled_with_id:
        for user in not_filled_with_id:
            print(f"   - {user['name']} (ID: {user.get('user_id', 'N/A')})")
    print()
    
    # 重点：请假人员
    print("🏖️  请假人员检测:")
    print("-" * 40)
    
    if on_leave_from_calendar:
        print(f"✅ 从日历检测到 {len(on_leave_from_calendar)} 人请假:")
        for name in on_leave_from_calendar:
            print(f"   📅 {name} - 已从未填写列表中移除")
        print()
        print("💡 这些人员不会收到工时提醒！")
    else:
        print("ℹ️  未检测到请假人员")
    
    if on_leave and not on_leave_from_calendar:
        print(f"ℹ️  从配置文件检测到 {len(on_leave)} 人请假:")
        for name in on_leave:
            print(f"   - {name}")
    
    print()
    
    # 例外日期人员
    if exception_day:
        print(f"ℹ️  例外日期人员 ({len(exception_day)} 人):")
        for name in exception_day:
            print(f"   - {name}")
        print()
    
    # 最终会被@的人员
    print("=" * 80)
    print("📢 最终提醒结果")
    print("=" * 80)
    print()
    
    if not_filled:
        print(f"⚠️  需要提醒的人员 ({len(not_filled)} 人):")
        for user in not_filled_with_id:
            print(f"   @{user['name']}")
    else:
        print("✅ 所有人都已填写工时（或已请假）")
    
    print()
    print("=" * 80)
    
    return result


def test_specific_user_leave(user_name, user_id, date_str):
    """
    测试特定用户的请假状态
    
    Args:
        user_name: 用户名
        user_id: 用户 open_id
        date_str: 日期字符串
    """
    print()
    print("=" * 80)
    print(f"🔍 测试用户 {user_name} 的请假状态")
    print("=" * 80)
    print()
    
    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'src/config/labor_hour.json'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建飞书客户端和 Bitable API
    feishu = config['feishu']
    client = FeishuClient(app_id=feishu['app_id'], app_secret=feishu['app_secret'])
    bitable = BitableAPI(client, url=feishu['bitable_url'])
    
    print(f"👤 用户: {user_name}")
    print(f"🆔 User ID: {user_id}")
    print(f"📅 日期: {date_str}")
    print()
    
    # 检查请假状态
    is_on_leave = bitable.check_user_on_leave(user_id, date_str)
    
    if is_on_leave:
        print(f"✅ {user_name} 在 {date_str} 请假")
        print(f"💡 此人员不会被@提醒填写工时")
    else:
        print(f"❌ {user_name} 在 {date_str} 未请假")
        print(f"⚠️  如果未填写工时，将会被@提醒")
    
    print()
    print("=" * 80)
    
    return is_on_leave


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试请假检测功能')
    parser.add_argument('--date', help='检查日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--user', help='测试特定用户的请假状态', default=None)
    parser.add_argument('--user-id', help='用户的 open_id', default=None)
    
    args = parser.parse_args()
    
    if args.user and args.user_id:
        # 测试特定用户
        date_str = args.date or datetime.now().strftime('%Y-%m-%d')
        test_specific_user_leave(args.user, args.user_id, date_str)
    else:
        # 测试整体工时检查
        test_leave_detection(args.date)
    
    print()
    print("🎉 测试完成！")
    print()


if __name__ == '__main__':
    main()

