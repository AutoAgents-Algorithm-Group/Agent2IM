"""
定时任务调度器
"""

from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config_loader import ConfigLoader
from .tasks import ReminderTasks


class ReminderScheduler:
    """飞书表格填写提醒定时任务调度器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化定时任务调度器
        
        Args:
            config_dir: 配置文件目录路径
        """
        # 配置文件目录
        if config_dir is None:
            current_dir = Path(__file__).parent.parent.parent
            config_dir = current_dir / "config"
        else:
            config_dir = Path(config_dir)
        
        self.config_dir = config_dir
        
        # 创建配置加载器
        self.config_loader = ConfigLoader(str(config_dir))
        
        # 加载配置文件
        self.task_config = self.config_loader.load_json("task.json")
        self.message_config = self.config_loader.load_json("message.json")
        self.people_config = self.config_loader.load_json("people.json")
        
        # 提取配置
        config = self.task_config.get("config", {})
        self.app_id = config.get("app_id")
        self.app_secret = config.get("app_secret")
        self.group_chat_id = config.get("group_chat_id")
        self.form_url = config.get("form_url")
        self.timezone = config.get("timezone", "Asia/Shanghai")
        self.bitable_app_token = config.get("bitable_app_token", "")
        self.bitable_table_id = config.get("bitable_table_id", "")
        
        # 飞书服务和任务实例（稍后初始化）
        self.feishu_service = None
        self.tasks = None
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        
        print(f"📅 定时任务调度器初始化完成")
        print(f"   配置目录: {self.config_dir}")
        print(f"   时区: {self.timezone}")
    
    def init_feishu_service(self, ai_service=None):
        """初始化飞书服务"""
        try:
            from ..feishu.service import FeishuService
            
            self.feishu_service = FeishuService(
                app_id=self.app_id,
                app_secret=self.app_secret,
                ai_service=ai_service
            )
            
            # 创建任务实例
            config = {
                'task': self.task_config,
                'message': self.message_config,
                'people': self.people_config
            }
            self.tasks = ReminderTasks(self.feishu_service, self.config_loader, config)
            
            print(f"✅ 飞书服务初始化成功")
        except Exception as e:
            print(f"❌ 飞书服务初始化失败: {e}")
            raise e
    
    def setup_tasks(self):
        """设置所有定时任务"""
        try:
            tasks = self.task_config.get("tasks", [])
            
            for task in tasks:
                if not task.get("enabled", False):
                    print(f"⏭️ 跳过禁用的任务: {task.get('name')}")
                    continue
                
                task_id = task.get("id")
                task_name = task.get("name")
                time_str = task.get("time", "00:00")
                
                # 解析时间
                hour, minute = map(int, time_str.split(":"))
                
                # 根据任务ID选择执行函数
                if task_id == "task_1":
                    job_func = self.tasks.evening_first_reminder
                elif task_id == "task_2":
                    job_func = self.tasks.evening_second_reminder
                elif task_id == "task_3":
                    job_func = self.tasks.morning_makeup_reminder
                else:
                    print(f"⚠️ 未知的任务ID: {task_id}")
                    continue
                
                # 添加定时任务
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=self.timezone
                )
                
                self.scheduler.add_job(
                    job_func,
                    trigger=trigger,
                    id=task_id,
                    name=task_name,
                    replace_existing=True
                )
                
                print(f"✅ 已添加定时任务: {task_name} (每天 {time_str})")
            
            print(f"\n📅 共添加 {len(self.scheduler.get_jobs())} 个定时任务")
            
        except Exception as e:
            print(f"❌ 设置定时任务失败: {e}")
            raise e
    
    def start(self):
        """启动调度器"""
        try:
            if not self.feishu_service:
                print("⚠️ 飞书服务未初始化，尝试初始化...")
                self.init_feishu_service()
            
            self.setup_tasks()
            self.scheduler.start()
            print(f"\n🚀 定时任务调度器已启动")
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
            print(f"🛑 定时任务调度器已停止")
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

