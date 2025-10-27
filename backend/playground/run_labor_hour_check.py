import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from src.service.labor_hour_service import run_labor_hour_check_from_config
from src.utils.logging import set_stage
from src.models import Stage

if __name__ == '__main__':
    log = set_stage(Stage.TASK_EXEC)
    log.info("手动执行工时检查...")
    
    try:
        result = run_labor_hour_check_from_config()
        if result and result.get('status') == 'success':
            log.success(f"工时检查完成")
        else:
            log.warning("工时检查可能失败，请检查日志文件")
    except Exception as e:
        log.exception(f"执行失败: {e}")

# 执行方式: python run_labor_hour_check.py