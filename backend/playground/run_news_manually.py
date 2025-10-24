#!/usr/bin/env python3
"""
手动执行AI新闻发送

快速脚本，用于手动触发新闻处理和发送
"""

import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from service.news_service import run_news_and_publish

if __name__ == '__main__':
    print("🚀 手动执行AI新闻发送...")
    try:
        results = run_news_and_publish()
        if results:
            success_count = sum(1 for r in results.values() if hasattr(r, 'status_code') and r.status_code == 200)
            print(f"✅ 新闻发送完成：{success_count}/{len(results)} 个群组发送成功")
        else:
            print("❌ 新闻发送可能失败，请检查日志")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

# 执行方式: python run_news_manually.py



