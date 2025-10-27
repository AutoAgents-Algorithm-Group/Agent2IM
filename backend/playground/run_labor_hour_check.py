import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from src.service.labor_hour_service import run_labor_hour_check_from_config

if __name__ == '__main__':
    print("🚀 手动执行工时检查...")
    try:
        result = run_labor_hour_check_from_config()
        if result and result.get('status') == 'success':
            print(f"✅ 工时检查完成")
        else:
            print("❌ 工时检查可能失败，请检查日志")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

# 执行方式: python run_labor_hour_check.py