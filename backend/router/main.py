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
from utils.feishu.client import FeishuClient
from utils.feishu.bitable import BitableAPI
from utils.feishu.message import MessageAPI
from utils.feishu.card import CardBuilder
from utils.schedule import ReminderScheduler
from utils.schedule.unified_scheduler import UnifiedScheduler
from utils import event_manager
from datetime import datetime
import pytz
import os

# 创建FastAPI应用
app = FastAPI(
    title="Agent2IM",
    description="通用AI驱动的即时通讯集成平台",
    version="1.0.0"
)

# 全局定时任务调度器
reminder_scheduler = None
unified_scheduler = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化定时任务"""
    global reminder_scheduler, unified_scheduler
    
    # 获取配置文件目录
    config_dir = PathLib(__file__).parent.parent / "config"
    
    # 检查是否启用统一调度器（通过环境变量控制）
    use_unified_scheduler = os.environ.get('USE_UNIFIED_SCHEDULER', 'false').lower() == 'true'
    
    if use_unified_scheduler:
        # 使用新的统一调度器（包含新闻推送和工时检查）
        try:
            print("🚀 正在启动统一定时任务调度器...")
            unified_scheduler = UnifiedScheduler(config_dir=str(config_dir))
            unified_scheduler.start()
            print("✅ 统一定时任务调度器启动成功")
        except Exception as e:
            print(f"❌ 启动统一定时任务调度器失败: {e}")
            print("⚠️ 应用将继续运行，但定时任务功能不可用")
    else:
        # 使用旧的提醒调度器（仅工时检查提醒）
        try:
            print("🚀 正在启动定时任务调度器...")
            reminder_scheduler = ReminderScheduler(config_dir=str(config_dir))
            reminder_scheduler.init_feishu_service(ai_service=None)
            reminder_scheduler.start()
            print("✅ 定时任务调度器启动成功")
        except Exception as e:
            print(f"❌ 启动定时任务调度器失败: {e}")
            print("⚠️ 应用将继续运行，但定时任务功能不可用")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止定时任务"""
    global reminder_scheduler, unified_scheduler
    try:
        if unified_scheduler:
            print("🛑 正在停止统一定时任务调度器...")
            unified_scheduler.stop()
            print("✅ 统一定时任务调度器已停止")
        elif reminder_scheduler:
            print("🛑 正在停止定时任务调度器...")
            reminder_scheduler.stop()
            print("✅ 定时任务调度器已停止")
    except Exception as e:
        print(f"❌ 停止定时任务调度器失败: {e}")


@app.get("/")
def read_root():
    """根路径，显示服务状态"""
    # 检查哪个调度器在运行
    if unified_scheduler:
        scheduler_status = "running" if unified_scheduler.scheduler.running else "stopped"
        job_count = len(unified_scheduler.scheduler.get_jobs())
        scheduler_type = "unified"
    elif reminder_scheduler:
        scheduler_status = "running" if reminder_scheduler.scheduler.running else "stopped"
        job_count = len(reminder_scheduler.scheduler.get_jobs())
        scheduler_type = "reminder"
    else:
        scheduler_status = "not_initialized"
        job_count = 0
        scheduler_type = "none"
    
    return {
        "message": "Agent2IM - 通用AI驱动的即时通讯集成平台", 
        "status": "ok",
        "version": "1.0.0",
        "scheduler": {
            "type": scheduler_type,
            "status": scheduler_status,
            "job_count": job_count
        },
        "endpoint": {
            "feishu_webhook": "/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}",
            "labor_hour_check": "/feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}",
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
    if unified_scheduler:
        is_running = unified_scheduler.scheduler.running
        job_count = len(unified_scheduler.scheduler.get_jobs())
        scheduler_type = "unified"
        timezone = unified_scheduler.timezone
    elif reminder_scheduler:
        is_running = reminder_scheduler.scheduler.running
        job_count = len(reminder_scheduler.scheduler.get_jobs())
        scheduler_type = "reminder"
        timezone = reminder_scheduler.timezone
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


@app.get("/scheduler/jobs")
def scheduler_jobs():
    """获取所有定时任务列表"""
    if unified_scheduler:
        jobs = unified_scheduler.scheduler.get_jobs()
        scheduler_type = "unified"
    elif reminder_scheduler:
        jobs = reminder_scheduler.scheduler.get_jobs()
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

@app.get("/feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url:path}")
async def check_labor_hour(
    app_id: str = Path(..., description="飞书应用ID"),
    app_secret: str = Path(..., description="飞书应用密钥"),
    group_chat_id: str = Path(..., description="飞书群聊ID"),
    bitable_url: str = Path(..., description="多维表格URL（完整URL）"),
    date: str = None  # 查询参数，可选，默认为今天
):
    """
    检查工时填写情况并发送到飞书群
    
    示例:
    /feishu/labor_hour/cli_xxx-secret_xxx/oc_xxx/https://xxx.feishu.cn/base/xxx?table=xxx&view=xxx
    
    或带日期:
    /feishu/labor_hour/cli_xxx-secret_xxx/oc_xxx/https://xxx.feishu.cn/base/xxx?table=xxx&view=xxx?date=2025-09-30
    """
    try:
        print("=" * 80)
        print(f"📋 开始检查工时填写情况")
        print(f"   App ID: {app_id}")
        print(f"   群聊ID: {group_chat_id}")
        print(f"   Bitable URL: {bitable_url}")
        
        # 获取检查日期
        if not date:
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            date = now.strftime('%Y-%m-%d')
        
        print(f"   检查日期: {date}")
        
        # 初始化飞书客户端
        feishu_client = FeishuClient(app_id=app_id, app_secret=app_secret)
        
        # 初始化Bitable API
        bitable = BitableAPI(client=feishu_client, url=bitable_url)
        
        # 检查填写情况
        print(f"\n🔍 正在检查人员填写情况...")
        result = bitable.check_users_filled(date_str=date)
        
        # 如果是节假日
        if result.get('is_holiday'):
            message = f"🎉 {date} 是节假日，无需检查工时填写"
            print(f"\n{message}")
            
            # 发送到群聊
            message_api = MessageAPI(feishu_client)
            message_api.send_text_to_group(message, group_chat_id)
            
            return {
                "status": "success",
                "is_holiday": True,
                "message": message,
                "date": date
            }
        
        # 构建消息卡片
        print(f"\n📊 检查结果:")
        print(f"   应填写人数: {len(result['filled']) + len(result['not_filled'])}")
        print(f"   已填写: {len(result['filled'])} 人")
        print(f"   未填写: {len(result['not_filled'])} 人")
        print(f"   填写率: {result['fill_rate']:.1%}")
        
        # 创建卡片消息
        card = create_labor_hour_card(result, date, bitable_url)
        
        # 发送到群聊
        message_api = MessageAPI(feishu_client)
        response = message_api.send_card_to_group(card, group_chat_id)
        
        print(f"\n✅ 消息已发送到群聊")
        print("=" * 80)
        
        return {
            "status": "success",
            "is_holiday": False,
            "date": date,
            "result": {
                "all_filled": result['all_filled'],
                "total": len(result['filled']) + len(result['not_filled']),
                "filled": len(result['filled']),
                "not_filled": len(result['not_filled']),
                "fill_rate": f"{result['fill_rate']:.1%}",
                "on_leave": result.get('on_leave', []),
                "exception_day": result.get('exception_day', [])
            },
            "message_sent": True
        }
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
                "date": date if date else "unknown"
            },
            status_code=500
        )


def create_labor_hour_card(result: dict, date: str, bitable_url: str = None) -> dict:
    """创建工时填写情况卡片（美化版）"""
    
    # 根据填写率选择颜色和状态
    fill_rate = result['fill_rate']
    if fill_rate >= 1.0:
        header_template = "green"
        status_emoji = "✅"
        status_text = "太棒了！所有人都已填写工时！"
    elif fill_rate >= 0.8:
        header_template = "orange"
        status_emoji = "⚠️"
        status_text = f"还有 {len(result['not_filled'])} 人未填写工时"
    else:
        header_template = "red"
        status_emoji = "❌"
        status_text = f"还有 {len(result['not_filled'])} 人未填写工时，请尽快填写！"
    
    # 构建卡片元素
    elements = []
    
    # 统计信息 - 简洁显示
    total = len(result['filled']) + len(result['not_filled'])
    filled = len(result['filled'])
    
    elements.append({
        "tag": "div",
        "text": {
            "content": f"{status_emoji} **{filled}/{total} 人已填写工时**",
            "tag": "lark_md"
        }
    })
    
    # 未填写人员列表 - 使用@功能
    if result['not_filled']:
        elements.append({"tag": "hr"})
        
        # 添加提示文案
        elements.append({
            "tag": "div",
            "text": {
                "content": "❗ **请以下同学尽快填写工时:**",
                "tag": "lark_md"
            }
        })
        
        # 构建@人员的内容
        mention_content = ""
        not_filled_with_id = result.get('not_filled_with_id', [])
        
        if not_filled_with_id:
            for user_info in not_filled_with_id:
                user_id = user_info.get('user_id', '')
                name = user_info['name']
                if user_id:
                    mention_content += f"<at id={user_id}></at>  "
                else:
                    mention_content += f"{name}  "
        else:
            for name in result['not_filled']:
                mention_content += f"{name}  "
        
        elements.append({
            "tag": "div",
            "text": {
                "content": mention_content,
                "tag": "lark_md"
            }
        })
    
    # 例外日期和请假人员（如果有）
    extra_info = []
    if result.get('exception_day'):
        extra_info.append(f"📅 例外: " + "、".join(result['exception_day']))
    if result.get('on_leave'):
        extra_info.append(f"🏖️ 请假: " + "、".join(result['on_leave']))
    
    if extra_info:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "content": " | ".join(extra_info),
                "tag": "lark_md"
            }
        })
    
    # 添加检查时间
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "content": f"⏰ 检查时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}",
            "tag": "lark_md"
        }
    })
    
    # 添加底部按钮 - 链接到多维表格
    if bitable_url:
        elements.append({
            "tag": "action",
            "layout": "bisected",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "content": "📝 立即填写工时",
                        "tag": "plain_text"
                    },
                    "url": bitable_url,
                    "type": "primary",
                    "size": "large"
                }
            ]
        })
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "header": {
                "template": header_template,
                "title": {
                    "content": f"📊 工时填写情况 - {date}",
                    "tag": "plain_text"
                }
            },
            "elements": elements
        }
    }
    
    return card


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)