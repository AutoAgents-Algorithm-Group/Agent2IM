import os
import sys
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# 添加src目录到Python路径
current_dir = Path(__file__).parent
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

@app.get("/")
def read_root():
    """根路径，显示服务状态"""
    return {
        "message": "飞书AI机器人正在运行", 
        "status": "ok",
        "version": "1.0.0"
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

    # uvicorn 