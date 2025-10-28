"""
飞书调度器相关 API

提供调度器状态查询和任务列表查询接口
"""

from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/feishu/schedule", tags=["feishu-schedule"])

# 调度器实例（由 main.py 注入）
_unified_scheduler: Optional[object] = None
_reminder_scheduler: Optional[object] = None


def set_schedulers(unified=None, reminder=None):
    """设置调度器实例（由 main.py 调用）"""
    global _unified_scheduler, _reminder_scheduler
    _unified_scheduler = unified
    _reminder_scheduler = reminder


@router.get("/status")
def get_scheduler_status():
    """
    获取定时任务调度器状态
    
    返回：
    - status: 运行状态（running/stopped/not_initialized）
    - type: 调度器类型（unified/reminder/none）
    - job_count: 任务数量
    - timezone: 时区
    """
    if _unified_scheduler:
        is_running = _unified_scheduler.scheduler.running
        job_count = len(_unified_scheduler.scheduler.get_jobs())
        scheduler_type = "unified"
        timezone = _unified_scheduler.timezone
    elif _reminder_scheduler:
        is_running = _reminder_scheduler.scheduler.running
        job_count = len(_reminder_scheduler.scheduler.get_jobs())
        scheduler_type = "reminder"
        timezone = _reminder_scheduler.timezone
    else:
        return {
            "status": "not_initialized",
            "message": "定时任务调度器未初始化"
        }
    
    return {
        "status": "running" if is_running else "stopped",
        "type": scheduler_type,
        "job_count": job_count,
        "timezone": timezone,
        "message": "定时任务调度器运行正常" if is_running else "定时任务调度器已停止"
    }


@router.get("/jobs")
def get_scheduler_jobs():
    """
    获取所有定时任务列表
    
    返回：
    - status: 状态
    - type: 调度器类型
    - job_count: 任务数量
    - jobs: 任务列表（包含 id, name, next_run_time, trigger）
    """
    if _unified_scheduler:
        jobs = _unified_scheduler.scheduler.get_jobs()
        scheduler_type = "unified"
    elif _reminder_scheduler:
        jobs = _reminder_scheduler.scheduler.get_jobs()
        scheduler_type = "reminder"
    else:
        return {
            "status": "error",
            "message": "定时任务调度器未初始化",
            "jobs": []
        }
    
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "ok",
        "type": scheduler_type,
        "job_count": len(job_list),
        "jobs": job_list
    }

