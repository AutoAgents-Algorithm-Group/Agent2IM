#!/usr/bin/env python3
"""
手动运行工时周总结

使用方法:
    python run_week_summary.py              # 本周的周总结
    python run_week_summary.py 2025-10-25   # 指定某周五的周总结
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.service.labor_hour_service import LaborHourService
import json


def run_week_summary(end_date_str: str = None):
    """运行周总结"""
    try:
        # 读取配置文件
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'src',
            'config',
            'labor_hour.json'
        )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 提取配置
        app_id = config['feishu']['app_id']
        app_secret = config['feishu']['app_secret']
        bitable_url = config['bitable']['url']
        webhook_url = config['webhook']['url']
        webhook_secret = config['webhook']['secret']
        
        # 创建服务实例
        service = LaborHourService(
            app_id=app_id,
            app_secret=app_secret,
            bitable_url=bitable_url,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret
        )
        
        # 运行周总结
        result = service.run_week_summary_and_publish(end_date_str)
        
        return result
        
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        print("💡 请创建配置文件 backend/src/config/labor_hour.json")
        return None
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 获取命令行参数
    end_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    if end_date:
        print(f"📅 运行指定周五的周总结: {end_date}")
    else:
        print(f"📅 运行本周的周总结")
    
    run_week_summary("2025-10-24")

