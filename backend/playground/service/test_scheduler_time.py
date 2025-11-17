"""
测试调度器时间诊断脚本
检查Python/APScheduler看到的时间和星期
"""
import sys
from pathlib import Path
from datetime import datetime
import pytz

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

print("=" * 80)
print("🕐 时间诊断工具")
print("=" * 80)

# 1. 系统时间
import time
print(f"\n1️⃣ 系统时间")
print(f"   time.time(): {time.time()}")
print(f"   time.localtime(): {time.strftime('%Y-%m-%d %H:%M:%S %A', time.localtime())}")

# 2. Python datetime
print(f"\n2️⃣ Python datetime")
now = datetime.now()
print(f"   datetime.now(): {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
print(f"   weekday (0=Mon, 6=Sun): {now.weekday()}")
print(f"   isoweekday (1=Mon, 7=Sun): {now.isoweekday()}")

# 3. 时区感知的时间
print(f"\n3️⃣ 时区感知 (Asia/Shanghai)")
tz = pytz.timezone('Asia/Shanghai')
now_tz = datetime.now(tz)
print(f"   datetime.now(tz): {now_tz.strftime('%Y-%m-%d %H:%M:%S %A %Z')}")
print(f"   weekday: {now_tz.weekday()}")
print(f"   timestamp: {now_tz.timestamp()}")

# 4. APScheduler cron 解析
print(f"\n4️⃣ APScheduler CronTrigger 测试")
from apscheduler.triggers.cron import CronTrigger

# 周一10:30的任务
trigger_monday = CronTrigger(
    minute=30,
    hour=10,
    day_of_week=0,  # 0 = 周一
    timezone='Asia/Shanghai'
)
next_run_monday = trigger_monday.get_next_fire_time(None, now_tz)
print(f"   周一10:30任务 (day_of_week=0)")
print(f"   下次执行: {next_run_monday}")

# 周一到周五19:30的任务
trigger_weekday = CronTrigger(
    minute=30,
    hour=19,
    day_of_week='0-4',  # 0-4 = 周一到周五
    timezone='Asia/Shanghai'
)
next_run_weekday = trigger_weekday.get_next_fire_time(None, now_tz)
print(f"\n   周一至周五19:30任务 (day_of_week=0-4)")
print(f"   下次执行: {next_run_weekday}")

# 5. 测试配置文件中的cron表达式
print(f"\n5️⃣ 配置文件中的 cron 表达式")
test_crons = [
    ("30 10 * * 1", "周一10:30检查周五"),
    ("30 19 * * 1-5", "周一至周五19:30"),
    ("30 10 * * 2-5", "周二至周五10:30"),
]

for cron_expr, desc in test_crons:
    parts = cron_expr.split()
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone='Asia/Shanghai'
    )
    next_run = trigger.get_next_fire_time(None, now_tz)
    print(f"\n   {desc}")
    print(f"   cron: {cron_expr}")
    print(f"   下次执行: {next_run}")

print("\n" + "=" * 80)

