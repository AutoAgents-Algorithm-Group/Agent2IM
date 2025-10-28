import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from datetime import datetime
import pytz

def test_month_calculation():
    """测试月份参数的日期计算"""
    
    print("=" * 80)
    print("🗓️  月份参数测试")
    print("=" * 80)
    print()
    
    # 测试不同月份
    test_months = [1, 2, 3, 10, 11, 12]
    
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    current_year = now.year
    
    print(f"当前年份: {current_year}")
    print()
    print("📅 各月份对应的日期范围:")
    print()
    
    for month in test_months:
        year = current_year
        
        # 计算结束日期（指定月份的27日）
        end_date = datetime(year, month, 27, tzinfo=tz)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 计算开始日期（上个月的28日）
        if month == 1:
            start_month = 12
            start_year = year - 1
        else:
            start_month = month - 1
            start_year = year
        
        start_date = datetime(start_year, start_month, 28, tzinfo=tz)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # 计算天数
        days = (end_date - start_date).days + 1
        
        print(f"  month={month:2d} → {start_date_str} ~ {end_date_str} ({days}天)")
    
    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    print()
    print("💡 使用示例:")
    print("   LaborHourManager.monthly_summary(month=10)  # 查询 09-28 到 10-27")
    print("   LaborHourManager.monthly_summary(month=11)  # 查询 10-28 到 11-27")
    print("   LaborHourManager.monthly_summary()          # 查询当前月")

if __name__ == '__main__':
    test_month_calculation()

