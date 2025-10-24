"""
测试飞书多维表格人员填写检查功能

使用方法：
python backend/playground/test_check_fill.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.feishu.client import FeishuClient
from utils.feishu.bitable import BitableAPI


def test_single_date_check():
    """测试单个日期的填写检查"""
    print("\n" + "=" * 70)
    print("  测试1: 检查单个日期的填写情况")
    print("=" * 70)
    
    # 初始化
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 需要检查的人员名单
    user_list = [
        "石国艳",
        "徐晓东",
        "胡东利",
        "黄克胜",
        "刘安营",
        "吴文静",
        "李佳豪",
        "孙劲宇",
        "陈亮",
        "韩宇轩",
    ]
    
    # 检查2025-09-30的填写情况
    result = bitable.check_users_filled(user_list, "2025-09-30")
    
    # 显示结果
    if result['all_filled']:
        print("\n🎉 完美！所有人都已填写！")
    else:
        print(f"\n⚠️ 还有 {len(result['not_filled'])} 人未填写")
        print(f"📋 需要提醒的人员: {result['not_filled']}")
    
    return result


def test_multiple_dates_check():
    """测试多个日期的填写检查"""
    print("\n" + "=" * 70)
    print("  测试2: 检查连续多天的填写情况")
    print("=" * 70)
    
    # 初始化
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 需要检查的人员名单
    user_list = [
        "石国艳",
        "徐晓东",
        "胡东利",
        "黄克胜",
        "刘安营",
        "吴文静",
    ]
    
    # 检查最近5天的填写情况
    dates_to_check = [
        "2025-09-08",
        "2025-09-09",
        "2025-09-10",
        "2025-09-11",
        "2025-09-12",
    ]
    
    results = {}
    for date in dates_to_check:
        print(f"\n{'─' * 70}")
        result = bitable.check_users_filled(user_list, date)
        results[date] = result
    
    # 汇总统计
    print("\n" + "=" * 70)
    print("  📊 多日填写情况汇总")
    print("=" * 70)
    
    for date, result in results.items():
        status = "✅" if result['all_filled'] else "⚠️"
        print(f"{status} {date}: {result['fill_rate']*100:.1f}% ({len(result['filled'])}/{len(user_list)})")
        if result['not_filled']:
            print(f"     未填写: {', '.join(result['not_filled'])}")
    
    return results


def test_team_statistics():
    """测试团队填写统计"""
    print("\n" + "=" * 70)
    print("  测试3: 团队填写统计分析")
    print("=" * 70)
    
    # 初始化
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 需要检查的人员名单
    user_list = [
        "石国艳", "徐晓东", "胡东利", "黄克胜",
        "刘安营", "吴文静", "李佳豪", "孙劲宇",
        "陈亮", "韩宇轩",
    ]
    
    # 检查最近一周
    dates = [
        "2025-09-08", "2025-09-09", "2025-09-10",
        "2025-09-11", "2025-09-12",
    ]
    
    # 统计每个人的填写情况
    user_fill_count = {name: 0 for name in user_list}
    
    for date in dates:
        print(f"\n检查 {date}...")
        result = bitable.check_users_filled(user_list, date)
        for name in result['filled']:
            user_fill_count[name] += 1
    
    # 显示统计结果
    print("\n" + "=" * 70)
    print("  📊 个人填写统计（最近5天）")
    print("=" * 70)
    
    sorted_users = sorted(user_fill_count.items(), key=lambda x: x[1], reverse=True)
    
    for name, count in sorted_users:
        percentage = (count / len(dates)) * 100
        bar = "█" * int(percentage / 10)
        print(f"  {name:8s}: {bar:10s} {count}/{len(dates)} ({percentage:.0f}%)")
    
    # 找出需要重点关注的人员
    low_fill_users = [name for name, count in user_fill_count.items() if count < len(dates)]
    if low_fill_users:
        print(f"\n⚠️ 需要重点关注的人员（未完整填写）:")
        for name in low_fill_users:
            print(f"    - {name}: {user_fill_count[name]}/{len(dates)}")


def test_with_missing_users():
    """测试包含不存在人员的情况"""
    print("\n" + "=" * 70)
    print("  测试4: 检查包含不存在人员的情况")
    print("=" * 70)
    
    # 初始化
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 包含一些不存在的人员
    user_list = [
        "石国艳",
        "徐晓东",
        "测试人员A",  # 不存在
        "测试人员B",  # 不存在
        "胡东利",
    ]
    
    result = bitable.check_users_filled(user_list, "2025-09-30")
    
    print(f"\n💡 说明:")
    print(f"  这个测试展示了当人员名单中包含不存在的人员时的处理情况")
    print(f"  系统会正确识别出哪些人填写了，哪些人没有填写")


def main():
    """主测试函数"""
    print("\n" + "🔍" * 35)
    print("  飞书多维表格 - 人员填写检查功能测试")
    print("🔍" * 35)
    
    try:
        # 测试1: 单个日期检查
        test_single_date_check()
        
        # # 测试2: 多个日期检查
        # test_multiple_dates_check()
        
        # # 测试3: 团队统计
        # test_team_statistics()
        
        # # 测试4: 包含不存在人员
        # test_with_missing_users()
        
        print("\n" + "=" * 70)
        print("  ✅ 所有测试完成！")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

