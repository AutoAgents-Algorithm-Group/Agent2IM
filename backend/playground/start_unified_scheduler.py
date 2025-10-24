#!/usr/bin/env python3
"""
启动统一定时任务调度器

包含新闻推送和工时检查任务
"""

import sys
import os
import time

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.schedule.unified_scheduler import UnifiedScheduler


def main():
    """主函数"""
    print("🚀 启动统一定时任务调度器")
    print("=" * 80)
    
    try:
        # 创建调度器实例
        scheduler = UnifiedScheduler()
        
        # 启动调度器
        scheduler.start()
        
        print("\n" + "=" * 80)
        print("✅ 调度器启动成功")
        print("⏹️  按 Ctrl+C 停止调度器")
        print("=" * 80 + "\n")
        
        # 保持运行
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n🛑 收到停止信号，正在关闭调度器...")
            scheduler.stop()
            print("👋 调度器已停止，再见！")
            
    except Exception as e:
        print(f"\n❌ 调度器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()



