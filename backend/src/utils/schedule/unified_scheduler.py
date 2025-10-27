"""
统一定时任务调度器

支持新闻推送和工时检查任务
"""

import json
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz

import sys
import os

from src.service.news_service import run_news_and_publish
from src.service.labor_hour_service import run_labor_hour_check_from_config, LaborHourService
import json as json_lib


class UnifiedScheduler:
    """统一定时任务调度器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化统一调度器
        
        Args:
            config_dir: 配置文件目录路径
        """
        # 配置文件目录
        if config_dir is None:
            # 从 src/utils/schedule/ 回到 src/config/
            current_dir = Path(__file__).parent.parent.parent
            config_dir = current_dir / "config"
        else:
            config_dir = Path(config_dir)
        
        self.config_dir = config_dir
        
        # 加载配置
        self.load_config()
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        
        print(f"📅 统一定时任务调度器初始化完成")
        print(f"   配置目录: {self.config_dir}")
        print(f"   时区: {self.timezone}")
    
    def load_config(self):
        """加载配置文件"""
        config_file = self.config_dir / "scheduled_tasks.json"
        
        # 如果不存在，尝试使用example文件
        if not config_file.exists():
            example_file = self.config_dir / "scheduled_tasks.example.json"
            if example_file.exists():
                print(f"⚠️ 未找到 scheduled_tasks.json，使用示例配置")
                config_file = example_file
            else:
                print(f"❌ 未找到配置文件")
                self.config = {"timezone": "Asia/Shanghai", "tasks": []}
                self.timezone = "Asia/Shanghai"
                return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.timezone = self.config.get("timezone", "Asia/Shanghai")
            print(f"✅ 成功加载配置文件: {config_file}")
            
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            self.config = {"timezone": "Asia/Shanghai", "tasks": []}
            self.timezone = "Asia/Shanghai"
    
    def setup_tasks(self):
        """设置所有定时任务"""
        try:
            tasks = self.config.get("tasks", [])
            
            for task in tasks:
                if not task.get("enabled", False):
                    print(f"⏭️ 跳过禁用的任务: {task.get('name')}")
                    continue
                
                task_id = task.get("id")
                task_name = task.get("name")
                task_type = task.get("type")
                schedule_config = task.get("schedule", "00:00")
                
                # 根据任务类型选择执行函数
                if task_type == "news":
                    job_func = self.run_news_task
                elif task_type == "labor_hour":
                    check_date = task.get("check_date", "today")
                    job_func = lambda cd=check_date: self.run_labor_hour_task(cd)
                elif task_type == "labor_week_summary":
                    job_func = self.run_week_summary_task
                else:
                    print(f"⚠️ 未知的任务类型: {task_type}")
                    continue
                
                # 添加定时任务
                # 处理 cron 表达式和普通时间
                if schedule_config == "cron":
                    # 使用cron表达式
                    cron_expr = task.get("cron", "0 0 * * *")
                    cron_parts = cron_expr.split()
                    if len(cron_parts) == 5:
                        trigger = CronTrigger(
                            minute=cron_parts[0],
                            hour=cron_parts[1],
                            day=cron_parts[2],
                            month=cron_parts[3],
                            day_of_week=cron_parts[4],
                            timezone=self.timezone
                        )
                        schedule_desc = f"cron({cron_expr})"
                    else:
                        print(f"⚠️ 无效的 cron 表达式: {cron_expr}")
                        continue
                else:
                    # 普通时间格式 HH:MM
                    hour, minute = map(int, schedule_config.split(":"))
                    trigger = CronTrigger(
                        hour=hour,
                        minute=minute,
                        timezone=self.timezone
                    )
                    schedule_desc = f"每天 {schedule_config}"
                
                self.scheduler.add_job(
                    job_func,
                    trigger=trigger,
                    id=task_id,
                    name=task_name,
                    replace_existing=True
                )
                
                print(f"✅ 已添加定时任务: {task_name} ({schedule_desc})")
            
            print(f"\n📅 共添加 {len(self.scheduler.get_jobs())} 个定时任务")
            
        except Exception as e:
            print(f"❌ 设置定时任务失败: {e}")
            raise e
    
    def run_news_task(self):
        """执行新闻推送任务"""
        try:
            print(f"\n{'='*80}")
            print(f"⏰ 执行定时任务: 新闻推送")
            print(f"   时间: {datetime.now(pytz.timezone(self.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            results = run_news_and_publish()
            
            if results:
                success_count = sum(1 for r in results.values() if hasattr(r, 'status_code') and r.status_code == 200)
                print(f"\n✅ 新闻推送任务完成：{success_count}/{len(results)} 个群组发送成功")
            else:
                print(f"\n⚠️ 新闻推送任务完成，但未发送任何消息")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 新闻推送任务失败: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
    
    def run_labor_hour_task(self, check_date: str = "today"):
        """执行工时检查任务"""
        try:
            print(f"\n{'='*80}")
            print(f"⏰ 执行定时任务: 工时检查")
            print(f"   时间: {datetime.now(pytz.timezone(self.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   检查日期: {check_date}")
            print(f"{'='*80}\n")
            
            result = run_labor_hour_check_from_config()
            
            if result and result.get('status') == 'success':
                print(f"\n✅ 工时检查任务完成")
            else:
                print(f"\n⚠️ 工时检查任务完成，但可能存在问题")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 工时检查任务失败: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
    
    def run_week_summary_task(self):
        """执行周总结任务"""
        try:
            print(f"\n{'='*80}")
            print(f"⏰ 执行定时任务: 工时周报")
            print(f"   时间: {datetime.now(pytz.timezone(self.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            # 读取配置文件
            config_file = self.config_dir / "labor_hour.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json_lib.load(f)
            
            # 创建服务实例
            service = LaborHourService(
                app_id=config['feishu']['app_id'],
                app_secret=config['feishu']['app_secret'],
                bitable_url=config['bitable']['url'],
                webhook_url=config['webhook']['url'],
                webhook_secret=config['webhook']['secret']
            )
            
            # 运行周总结
            result = service.run_week_summary_and_publish()
            
            if result and result.get('status') == 'success':
                print(f"\n✅ 工时周报任务完成")
            else:
                print(f"\n⚠️ 工时周报任务完成，但可能存在问题")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 工时周报任务失败: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
    
    def start(self):
        """启动调度器"""
        try:
            self.setup_tasks()
            self.scheduler.start()
            
            print(f"\n🚀 统一定时任务调度器已启动")
            print(f"   时区: {self.timezone}")
            print(f"   任务数量: {len(self.scheduler.get_jobs())}")
            
            # 打印所有任务的下次执行时间
            for job in self.scheduler.get_jobs():
                print(f"   📌 {job.name} - 下次执行: {job.next_run_time}")
            
        except Exception as e:
            print(f"❌ 启动调度器失败: {e}")
            raise e
    
    def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            print(f"🛑 统一定时任务调度器已停止")
        except Exception as e:
            print(f"❌ 停止调度器失败: {e}")
    
    def list_jobs(self):
        """列出所有任务"""
        jobs = self.scheduler.get_jobs()
        print(f"\n📋 当前定时任务列表 (共 {len(jobs)} 个):")
        for job in jobs:
            print(f"   ID: {job.id}")
            print(f"   名称: {job.name}")
            print(f"   下次执行: {job.next_run_time}")
            print(f"   ---")
        return jobs


if __name__ == '__main__':
    import time
    
    # 创建调度器
    scheduler = UnifiedScheduler()
    
    # 启动调度器
    scheduler.start()
    
    print("\n⏹️  按 Ctrl+C 停止调度器\n")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭调度器...")
        scheduler.stop()
        print("👋 再见！")

