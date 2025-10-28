import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.service.feishu import LaborHourManager


def main():
    """测试月度总结"""
    # month=10 表示查询 09-28 到 10-27
    LaborHourManager.monthly_summary(
        month=10,
        mention_users=["刘华鑫"]
    )

if __name__ == '__main__':
    main()