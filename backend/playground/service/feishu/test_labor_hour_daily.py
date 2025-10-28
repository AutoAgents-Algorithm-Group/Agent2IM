import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.service.feishu import LaborHourManager


def main():
    """测试日常工时检查"""
    LaborHourManager.check(
        date_str="2025-10-28", 
        offset=2
    )

if __name__ == '__main__':
    main()