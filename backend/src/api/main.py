"""
Agent2IM - 通用AI驱动的即时通讯集成平台

主入口文件，使用 FastAPI 的 lifespan 管理应用生命周期
"""

import os
import sys
from pathlib import Path as PathLib
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

# 添加src目录到Python路径
current_dir = PathLib(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from src.utils.schedule.unified_scheduler import UnifiedScheduler
from src.api.feishu import chat, approval, schedule


# 全局调度器实例
app_state = {
    "unified_scheduler": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时初始化资源，在关闭时清理资源
    """
    # === 启动阶段 ===
    print("=" * 80)
    print("🚀 Agent2IM 正在启动...")
    print("=" * 80)
    
    # 获取配置文件目录 (从 src/api/ 回到 src/config/)
    config_dir = PathLib(__file__).parent.parent / "config"
    
    # 检查是否启用统一调度器（通过环境变量控制）
    # 如果设置了 DISABLE_SCHEDULER=true，则不启动调度器（避免与独立的scheduler服务重复）
    disable_scheduler = os.environ.get('DISABLE_SCHEDULER', 'false').lower() == 'true'
    use_unified_scheduler = os.environ.get('USE_UNIFIED_SCHEDULER', 'true').lower() == 'true'
    
    if disable_scheduler:
        print("⚠️ 环境变量 DISABLE_SCHEDULER=true，跳过启动调度器")
        print("⚠️ 请确保有独立的 scheduler 服务在运行")
    elif use_unified_scheduler:
        # 使用新的统一调度器（包含工时检查和新闻推送）
        try:
            print("🚀 正在启动统一定时任务调度器...")
            unified_scheduler = UnifiedScheduler(config_dir=str(config_dir))
            unified_scheduler.start()
            app_state["unified_scheduler"] = unified_scheduler
            
            # 注入到 schedule 路由
            schedule.set_schedulers(unified=unified_scheduler)
            
            print("✅ 统一定时任务调度器启动成功")
        except Exception as e:
            print(f"❌ 启动统一定时任务调度器失败: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ 应用将继续运行，但定时任务功能不可用")
    else:
        # 旧的调度器已废弃，不再支持
        print("⚠️ 旧的调度器（ReminderScheduler）已废弃")
        print("⚠️ 请设置环境变量 USE_UNIFIED_SCHEDULER=true 使用新的统一调度器")
        print("⚠️ 应用将继续运行，但定时任务功能不可用")
    
    print("=" * 80)
    print("✅ Agent2IM 启动完成")
    print("=" * 80)
    
    # 应用运行中...
    yield
    
    # === 关闭阶段 ===
    print("\n" + "=" * 80)
    print("🛑 Agent2IM 正在关闭...")
    print("=" * 80)
    
    try:
        if app_state["unified_scheduler"]:
            print("🛑 正在停止统一定时任务调度器...")
            app_state["unified_scheduler"].stop()
            print("✅ 统一定时任务调度器已停止")
    except Exception as e:
        print(f"❌ 停止定时任务调度器失败: {e}")
    
    print("=" * 80)
    print("👋 Agent2IM 已关闭")
    print("=" * 80)


# 创建FastAPI应用（使用 lifespan）
app = FastAPI(
    title="Agent2IM",
    description="通用AI驱动的即时通讯集成平台",
    version="1.0.0",
    lifespan=lifespan
)

# 注册飞书相关路由
app.include_router(chat.router)
app.include_router(approval.router)
app.include_router(schedule.router)


@app.get("/")
def read_root():
    """
    根路径，显示服务状态
    
    返回服务信息、调度器状态和可用端点列表
    """
    # 获取调度器状态
    unified_scheduler = app_state["unified_scheduler"]
    
    if unified_scheduler:
        scheduler_status = "running" if unified_scheduler.scheduler.running else "stopped"
        job_count = len(unified_scheduler.scheduler.get_jobs())
        scheduler_type = "unified"
    else:
        scheduler_status = "not_initialized"
        job_count = 0
        scheduler_type = "none"
    
    return {
        "service": "Agent2IM",
        "description": "通用AI驱动的即时通讯集成平台", 
        "status": "ok",
        "version": "1.0.0",
        "scheduler": {
            "type": scheduler_type,
            "status": scheduler_status,
            "job_count": job_count
        },
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "chat_webhook": "/feishu/chat/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}",
            "approval_callback": "/feishu/approval",
            "scheduler_status": "/feishu/schedule/status",
            "scheduler_jobs": "/feishu/schedule/jobs"
        },
        "features": [
            "完全动态配置，无需配置文件",
            "3秒内快速响应，避免平台重试",
            "基于event_id的幂等处理，确保不重不漏",
            "利用流式接口实现实时打字效果",
            "使用异步后台任务处理AI请求",
            "定时任务调度（新闻推送、工时检查）",
            "审批自动化（请假日历同步）"
        ]
    }


@app.get("/health")
def health_check():
    """
    健康检查接口
    
    用于 Docker 和负载均衡器的健康检查
    """
    return {
        "status": "ok",
        "message": "Service is healthy"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
