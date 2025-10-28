"""
统一定时任务调度器

支持新闻推送和工时检查任务
"""

import yaml
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz

import sys
import os

from src.service.feishu.news import run_news_and_publish
from src.service.feishu import LaborHourManager


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
        """加载配置文件 - 从 labor_hour.yaml 和 news.yaml 合并任务配置"""
        all_tasks = []
        timezone = "Asia/Shanghai"
        
        # 1. 加载 labor_hour.yaml
        labor_config_file = self.config_dir / "labor_hour.yaml"
        if labor_config_file.exists():
            try:
                with open(labor_config_file, 'r', encoding='utf-8') as f:
                    labor_config = yaml.safe_load(f)
                
                # 获取时区
                timezone = labor_config.get('schedules', {}).get('timezone', timezone)
                
                # 获取任务
                labor_tasks = labor_config.get('schedules', {}).get('tasks', [])
                all_tasks.extend(labor_tasks)
                
                print(f"✅ 成功加载 labor_hour.yaml，{len(labor_tasks)} 个任务")
            except Exception as e:
                print(f"⚠️ 加载 labor_hour.yaml 失败: {e}")
        else:
            print(f"⚠️ 未找到 labor_hour.yaml")
        
        # 2. 加载 news.yaml
        news_config_file = self.config_dir / "news.yaml"
        if news_config_file.exists():
            try:
                with open(news_config_file, 'r', encoding='utf-8') as f:
                    news_config = yaml.safe_load(f)
                
                # 获取任务
                news_tasks = news_config.get('schedules', {}).get('tasks', [])
                all_tasks.extend(news_tasks)
                
                print(f"✅ 成功加载 news.yaml，{len(news_tasks)} 个任务")
            except Exception as e:
                print(f"⚠️ 加载 news.yaml 失败: {e}")
        else:
            print(f"⚠️ 未找到 news.yaml")
        
        # 合并配置
        self.config = {
            "timezone": timezone,
            "tasks": all_tasks
        }
        self.timezone = timezone
        
        print(f"✅ 配置加载完成，共 {len(all_tasks)} 个任务")
    
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
                    offset = task.get("offset", 0)  # 默认为0（今天）
                    job_func = lambda o=offset: self.run_labor_hour_task(o)
                elif task_type == "labor_month_summary":
                    mention_users = task.get("mention_users", [])
                    job_func = lambda mu=mention_users: self.run_month_summary_task(mu)
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
    
    def run_labor_hour_task(self, offset: int = 0):
        """
        执行工时检查任务
        
        Args:
            offset: 日期偏移量，-1=昨天，0=今天，1=明天
        """
        try:
            print(f"\n{'='*80}")
            print(f"⏰ 执行定时任务: 工时检查")
            print(f"   时间: {datetime.now(pytz.timezone(self.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   日期偏移: {offset} ({'昨天' if offset == -1 else '今天' if offset == 0 else '明天' if offset == 1 else f'{offset}天'})")
            print(f"{'='*80}\n")
            
            # 使用 LaborHourManager 的统一接口
            result = LaborHourManager.check(offset=offset)
            
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
    
    def run_month_summary_task(self, mention_users: list = None):
        """执行月度总结任务"""
        try:
            print(f"\n{'='*80}")
            print(f"⏰ 执行定时任务: 工时月报")
            print(f"   时间: {datetime.now(pytz.timezone(self.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")
            if mention_users:
                print(f"   @人员: {', '.join(mention_users)}")
            print(f"{'='*80}\n")
            
            # 运行月度总结
            result = LaborHourManager.monthly_summary(mention_users=mention_users)
            
            if result and result.get('status') == 'success':
                print(f"\n✅ 工时月报任务完成")
            else:
                print(f"\n⚠️ 工时月报任务完成，但可能存在问题")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 工时月报任务失败: {e}")
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

