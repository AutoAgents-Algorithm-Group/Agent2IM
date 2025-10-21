import os
import sys
import json
import time
from pathlib import Path as PathLib
from fastapi import FastAPI, Request, Path, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# 添加src目录到Python路径
current_dir = PathLib(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from utils.feishu import FeishuService
from utils.schedule import ReminderScheduler
from utils import event_manager

# 创建FastAPI应用
app = FastAPI(
    title="Agent2IM",
    description="通用AI驱动的即时通讯集成平台",
    version="1.0.0"
)

# 全局定时任务调度器
reminder_scheduler = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化定时任务"""
    global reminder_scheduler
    try:
        print("🚀 正在启动定时任务调度器...")
        
        # 获取配置文件目录
        config_dir = PathLib(__file__).parent.parent / "config"
        
        # 创建调度器实例
        reminder_scheduler = ReminderScheduler(config_dir=str(config_dir))
        
        # 初始化飞书服务（不需要AI服务）
        reminder_scheduler.init_feishu_service(ai_service=None)
        
        # 启动调度器
        reminder_scheduler.start()
        
        print("✅ 定时任务调度器启动成功")
    except Exception as e:
        print(f"❌ 启动定时任务调度器失败: {e}")
        print("⚠️ 应用将继续运行，但定时任务功能不可用")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止定时任务"""
    global reminder_scheduler
    try:
        if reminder_scheduler:
            print("🛑 正在停止定时任务调度器...")
            reminder_scheduler.stop()
            print("✅ 定时任务调度器已停止")
    except Exception as e:
        print(f"❌ 停止定时任务调度器失败: {e}")


@app.get("/")
def read_root():
    """根路径，显示服务状态"""
    scheduler_status = "running" if reminder_scheduler and reminder_scheduler.scheduler.running else "stopped"
    job_count = len(reminder_scheduler.scheduler.get_jobs()) if reminder_scheduler else 0
    
    return {
        "message": "Agent2IM - 通用AI驱动的即时通讯集成平台", 
        "status": "ok",
        "version": "1.0.0",
        "scheduler": {
            "status": scheduler_status,
            "job_count": job_count
        },
        "endpoint": {
            "feishu_webhook": "/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}",
            "example": "/feishu/webhook/agent123-key456-secret789/app111-secret222",
            "scheduler_status": "/scheduler/status",
            "scheduler_jobs": "/scheduler/jobs"
        },
        "usage": {
            "description": "完全动态路由 - 通过URL参数传递所有配置",
            "format": "/{platform}/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}",
            "note": "使用-号分隔参数，避免URL编码问题"
        },
        "features": {
            "fully_dynamic": "完全动态配置，无需配置文件",
            "fast_response": "3秒内快速响应，避免平台重试",
            "idempotency": "基于event_id的幂等处理，确保不重不漏",
            "typing_effect": "利用流式接口实现实时打字效果",
            "background_processing": "使用异步后台任务处理AI请求",
            "scheduled_reminders": "定时任务提醒功能（晚9点、晚11点、早10点）"
        }
    }


@app.get("/scheduler/status")
def scheduler_status():
    """获取定时任务调度器状态"""
    if not reminder_scheduler:
        return {
            "status": "not_initialized",
            "message": "定时任务调度器未初始化"
        }
    
    is_running = reminder_scheduler.scheduler.running
    job_count = len(reminder_scheduler.scheduler.get_jobs())
    
    return {
        "status": "running" if is_running else "stopped",
        "job_count": job_count,
        "timezone": reminder_scheduler.timezone,
        "message": "定时任务调度器运行正常" if is_running else "定时任务调度器已停止"
    }


@app.get("/scheduler/jobs")
def scheduler_jobs():
    """获取所有定时任务列表"""
    if not reminder_scheduler:
        return {
            "status": "error",
            "message": "定时任务调度器未初始化",
            "jobs": []
        }
    
    jobs = reminder_scheduler.scheduler.get_jobs()
    
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
        "job_count": len(job_list),
        "jobs": job_list
    }


@app.post("/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}")
async def feishu_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码"),
    app_id: str = Path(..., description="飞书应用ID"),
    app_secret: str = Path(..., description="飞书应用密钥")
):
    """处理飞书消息回调 - 完全动态路由"""
    try:
        # 定期清理过期事件
        event_manager.cleanup_old_events()
        
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到飞书回调数据 (Agent: {agent_id}, App: {app_id})")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print(f"🔐 处理challenge验证 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 获取event_id进行去重
        event_id = data.get('header', {}).get('event_id', '')
        if not event_id:
            print(f"⚠️ 缺少event_id，使用默认处理 (Agent: {agent_id}, App: {app_id})")
            event_id = f"dynamic_{agent_id}_{app_id}_{int(time.time() * 1000)}"
        
        # 检查事件是否已处理（幂等性）
        if event_manager.is_event_processed(event_id):
            print(f"⚠️ 事件 {event_id} 已处理过，跳过重复处理")
            return JSONResponse(content={"status": "success"}, status_code=200)
        
        # 标记事件已处理
        event_manager.mark_event_processed(event_id)
        
        # 创建动态服务实例
        dynamic_feishu_service = FeishuService.create_dynamic_services(
            agent_id, auth_key, auth_secret, app_id, app_secret
        )
        
        if not dynamic_feishu_service:
            print(f"❌ 动态服务创建失败 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(
                content={"status": "error", "message": "服务初始化失败"}, 
                status_code=500
            )
        
        # 🚀 关键：立即返回200，避免飞书重试
        print(f"⚡ 立即响应事件 {event_id}，后台异步处理")
        
        # 将消息处理加入后台任务
        background_tasks.add_task(
            dynamic_feishu_service.process_message_async, 
            data, 
            event_id
        )
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        print(f"❌ 处理回调时发生错误: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)