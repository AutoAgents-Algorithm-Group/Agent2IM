"""
飞书聊天 Webhook API

处理飞书消息回调，支持完全动态路由配置
"""

import time
from fastapi import APIRouter, Request, Path, BackgroundTasks
from fastapi.responses import JSONResponse

from src.utils.feishu import FeishuService
from src.utils import event_manager

router = APIRouter(prefix="/feishu/chat", tags=["feishu-chat"])


@router.post("/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}")
async def handle_chat_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码"),
    app_id: str = Path(..., description="飞书应用ID"),
    app_secret: str = Path(..., description="飞书应用密钥")
):
    """
    处理飞书消息回调 - 完全动态路由
    
    示例：
    POST /feishu/chat/agent123-key456-secret789/app111-secret222
    
    特性：
    - 完全动态配置，无需配置文件
    - 3秒内快速响应，避免平台重试
    - 基于event_id的幂等处理，确保不重不漏
    - 利用流式接口实现实时打字效果
    - 使用异步后台任务处理AI请求
    """
    try:
        # 定期清理过期事件
        event_manager.cleanup_old_events()
        
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到飞书聊天回调 (Agent: {agent_id}, App: {app_id})")
        
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
        print(f"❌ 处理聊天回调时发生错误: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )

