import os
import sys
import json
from pathlib import Path as PathLib
from fastapi import FastAPI, Request, Path
from fastapi.responses import JSONResponse
import uvicorn

# 添加src目录到Python路径
current_dir = PathLib(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from config.config_manager import ConfigManager
from service.feishu_service import FeishuService
from service.autoagents_service import AutoAgentsService

# 初始化配置和服务
config_manager = ConfigManager()
config = config_manager.get_config()

# 创建服务实例
ai_service = AutoAgentsService(
    agent_id=config['autoagents']['agent_id'],
    auth_key=config['autoagents']['auth_key'],
    auth_secret=config['autoagents']['auth_secret']
)

feishu_service = FeishuService(
    app_id=config['feishu']['app_id'],
    app_secret=config['feishu']['app_secret'],
    ai_service=ai_service
)

# 创建FastAPI应用
app = FastAPI(
    title="飞书AI机器人",
    description="基于AutoAgents的智能飞书机器人",
    version="1.0.0"
)

def create_dynamic_services(agent_id: str, auth_key: str, auth_secret: str, app_id: str = None, app_secret: str = None):
    """动态创建服务实例"""
    try:
        # 创建动态AI服务
        dynamic_ai_service = AutoAgentsService(
            agent_id=agent_id,
            auth_key=auth_key,
            auth_secret=auth_secret
        )
        
        # 使用动态或默认的飞书配置
        feishu_app_id = app_id or config['feishu']['app_id']
        feishu_app_secret = app_secret or config['feishu']['app_secret']
        
        # 创建动态飞书服务
        dynamic_feishu_service = FeishuService(
            app_id=feishu_app_id,
            app_secret=feishu_app_secret,
            ai_service=dynamic_ai_service
        )
        
        return dynamic_feishu_service
    except Exception as e:
        print(f"❌ 创建动态服务失败: {e}")
        return None

@app.get("/")
def read_root():
    """根路径，显示服务状态"""
    return {
        "message": "飞书AI机器人正在运行", 
        "status": "ok",
        "version": "1.0.0",
        "endpoints": {
            "default_webhook": "/feishu/webhook",
            "dynamic_ai_webhook": "/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}",
            "full_dynamic_webhook": "/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}",
            "examples": {
                "ai_only": "/feishu/webhook/agent123-key456-secret789",
                "full_dynamic": "/feishu/webhook/agent123-key456-secret789/app111-secret222"
            }
        },
        "usage": {
            "description": "使用动态URL可以在飞书配置中切换不同的机器人和应用",
            "formats": {
                "ai_only": "只切换AI机器人：{agent_id}-{auth_key}-{auth_secret}",
                "full_dynamic": "同时切换AI机器人和飞书应用：{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}"
            },
            "note": "使用-号分隔参数，避免URL编码问题（+号会被解析为空格）"
        }
    }

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """处理飞书消息回调"""
    try:
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到回调数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print("🔐 处理challenge验证")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 处理消息
        processed = feishu_service.process_message(data)
        
        if processed:
            print("✅ 消息处理完成")
        else:
            print("ℹ️ 消息未处理（不符合触发条件）")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        print(f"❌ 处理回调时发生错误: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )

@app.post("/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}")
async def feishu_dynamic_webhook(
    request: Request,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码")
):
    """处理飞书消息回调 - 动态机器人切换"""
    try:
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到动态回调数据 (Agent: {agent_id}): {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print(f"🔐 处理challenge验证 (Agent: {agent_id})")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 创建动态服务实例（使用默认飞书配置）
        dynamic_feishu_service = create_dynamic_services(agent_id, auth_key, auth_secret)
        
        if not dynamic_feishu_service:
            print(f"❌ 动态AI服务创建失败 (Agent: {agent_id})")
            return JSONResponse(
                content={"status": "error", "message": "AI服务初始化失败"}, 
                status_code=500
            )
        
        print(f"🚀 使用动态AI配置处理消息 (Agent: {agent_id}, 默认飞书应用)")
        
        # 处理消息
        processed = dynamic_feishu_service.process_message(data)
        
        if processed:
            print(f"✅ 动态消息处理完成 (Agent: {agent_id})")
        else:
            print(f"ℹ️ 动态消息未处理（不符合触发条件）(Agent: {agent_id})")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        print(f"❌ 动态处理回调时发生错误 (Agent: {agent_id}): {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )

@app.post("/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}")
async def feishu_full_dynamic_webhook(
    request: Request,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码"),
    app_id: str = Path(..., description="飞书应用ID"),
    app_secret: str = Path(..., description="飞书应用密钥")
):
    """处理飞书消息回调 - 完全动态切换（AI机器人+飞书应用）"""
    try:
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到完全动态回调数据 (Agent: {agent_id}, App: {app_id}): {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print(f"🔐 处理challenge验证 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 创建完全动态的服务实例
        dynamic_feishu_service = create_dynamic_services(agent_id, auth_key, auth_secret, app_id, app_secret)
        
        if not dynamic_feishu_service:
            print(f"❌ 完全动态服务创建失败 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(
                content={"status": "error", "message": "完全动态服务初始化失败"}, 
                status_code=500
            )
        
        print(f"🚀 使用完全动态配置处理消息 (Agent: {agent_id}, App: {app_id})")
        
        # 处理消息
        processed = dynamic_feishu_service.process_message(data)
        
        if processed:
            print(f"✅ 完全动态消息处理完成 (Agent: {agent_id}, App: {app_id})")
        else:
            print(f"ℹ️ 完全动态消息未处理（不符合触发条件）(Agent: {agent_id}, App: {app_id})")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        print(f"❌ 完全动态处理回调时发生错误 (Agent: {agent_id}, App: {app_id}): {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

    # uvicorn 