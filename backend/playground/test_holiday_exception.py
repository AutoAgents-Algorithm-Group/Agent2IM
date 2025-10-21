import os
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.feishu.client import FeishuClient
from utils.feishu.bitable import BitableAPI


def test_different_dates():
    """测试不同日期的检查情况"""
    print("=" * 80)
    print("  多场景测试：节假日 + 例外日期")
    print("=" * 80)
    
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 测试多个日期
    test_dates = [
        "2025-09-30",  # 星期二（滕凯的例外日期）
        "2025-10-01",  # 国庆节
        "2025-10-20",  # 星期一（工作日）
        "2025-10-25",  # 星期六（周末）
    ]
    
    for date_str in test_dates:
        print(f"\n{'=' * 80}")
        print(f"📅 检查日期: {date_str}")
        print("=" * 80)
        
        result = bitable.check_users_filled(date_str=date_str)
        
        # 如果是节假日
        if result.get('is_holiday'):
            print(f"🎉 {result.get('message', '今天是节假日，无需检查')}")
            continue
        
        # 显示检查结果
        print(f"\n📊 检查结果:")
        print(f"  应填写人数: {len(result['filled']) + len(result['not_filled'])}")
        print(f"  已填写: {len(result['filled'])} 人")
        print(f"  未填写: {len(result['not_filled'])} 人")
        print(f"  填写率: {result['fill_rate']:.1%}")
        
        # 例外日期人员
        if result['exception_day']:
            print(f"\n📅 例外日期人员 ({len(result['exception_day'])} 人):")
            for name in result['exception_day']:
                print(f"    - {name}")
        
        # 请假人员
        if result['on_leave']:
            print(f"\n🏖️ 请假人员 ({len(result['on_leave'])} 人):")
            for name in result['on_leave']:
                print(f"    - {name}")
        
        # 填写情况
        if result['all_filled']:
            print("\n✅ 太棒了！所有应填写人员都已完成！")
        else:
            print(f"\n⚠️ 还有 {len(result['not_filled'])} 人未填写:")
            for name in result['not_filled']:
                print(f"    - {name}")


def test_holiday_api():
    """测试节假日API功能"""
    print("\n" + "=" * 80)
    print("  节假日API测试")
    print("=" * 80)
    
    test_dates = [
        ("2025-10-01", "国庆节"),
        ("2025-05-01", "劳动节"),
        ("2025-10-25", "周六"),
        ("2025-10-20", "工作日"),
    ]
    
    for date_str, expected in test_dates:
        is_holiday = BitableAPI.is_holiday(date_str)
        weekday = BitableAPI.get_weekday_name(date_str)
        status = "✅ 节假日" if is_holiday else "❌ 工作日"
        print(f"{date_str} ({weekday}) - {status} (预期: {expected})")


def test_exception_config():
    """测试例外日期配置"""
    print("\n" + "=" * 80)
    print("  例外日期配置测试")
    print("=" * 80)
    
    # 测试星期二（滕凯的例外日期）
    tuesday_dates = [
        "2025-09-30",  # 星期二
        "2025-10-07",  # 星期二
        "2025-10-14",  # 星期二
    ]
    
    print("\n🔍 测试星期二的例外人员过滤:")
    for date_str in tuesday_dates:
        weekday = BitableAPI.get_weekday_name(date_str)
        exception_people = BitableAPI._get_exception_day_people(date_str=date_str)
        
        print(f"\n{date_str} ({weekday}):")
        if exception_people:
            print(f"  例外人员: {', '.join(exception_people)}")
        else:
            print(f"  无例外人员")


if __name__ == "__main__":
    # 运行所有测试
    test_different_dates()
    test_holiday_api()
    test_exception_config()
    
    print("\n" + "=" * 80)
    print("  测试完成")
    print("=" * 80)

