import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.utils.feishu.bitable import BitableAPI
from datetime import datetime, timedelta

def main():
    """测试节假日检测功能"""
    
    print("=" * 80)
    print("🎯 节假日检测测试")
    print("=" * 80)
    print()
    
    # 测试日期列表
    test_dates = [
        "2025-10-01",  # 国庆节
        "2025-10-02",  # 国庆节
        "2025-10-03",  # 国庆节
        "2025-10-06",  # 国庆节最后一天
        "2025-10-08",  # 国庆后第一个工作日
        "2025-09-27",  # 国庆前调休（周六上班）
        "2025-09-28",  # 周日
        "2025-09-29",  # 周一工作日
        "2025-05-01",  # 劳动节
        "2025-01-01",  # 元旦
        "2025-12-25",  # 普通工作日（圣诞节不是中国法定节假日）
    ]
    
    print("📅 测试日期列表:")
    print()
    
    for date_str in test_dates:
        is_hol = BitableAPI.is_holiday(date_str)
        status = "🎉 节假日" if is_hol else "💼 工作日"
        print(f"  {date_str} → {status}")
    
    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)

if __name__ == '__main__':
    main()

