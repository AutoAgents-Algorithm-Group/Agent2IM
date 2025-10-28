"""
飞书审批回调 API

处理飞书审批事件，自动创建请假日历
"""

import json
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import pytz

from src.utils import event_manager
from src.service.feishu.approval import create_approval_service_from_config

router = APIRouter(prefix="/feishu/approval", tags=["feishu-approval"])


@router.post("")
async def handle_approval_callback(request: Request):
    """
    飞书审批事件回调
    
    当审批通过时，自动创建请假日历
    
    事件类型：
    - url_verification: URL验证请求（首次配置webhook时）
    - event_callback: 审批事件（标准格式）
    - approval: 审批事件（飞书实际发送的格式）
    """
    try:
        # 获取请求体
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        print("=" * 80)
        print(f"📨 收到审批事件回调")
        print(f"   时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   原始数据: {json.dumps(data, ensure_ascii=False)[:500]}")
        
        # 处理URL验证请求（飞书首次配置webhook时会发送）
        if data.get('type') == 'url_verification':
            challenge = data.get('challenge', '')
            print(f"✅ URL验证请求，返回challenge: {challenge}")
            return JSONResponse(content={"challenge": challenge})
        
        # 处理审批事件
        event_type = data.get('type')
        print(f"   事件类型: {event_type}")
        
        # 兼容两种事件格式:
        # 1. type: "event_callback" (标准格式)
        # 2. type: "approval" (飞书实际发送的格式)
        if event_type in ['event_callback', 'approval']:
            # 获取事件ID（尝试多个可能的路径）
            event_id = (
                data.get('event_id') or 
                data.get('uuid') or 
                data.get('header', {}).get('event_id') or
                f"approval_{int(datetime.now().timestamp() * 1000)}"
            )
            
            print(f"   事件ID: {event_id}")
            
            # 检查事件ID是否已处理（防止重复处理）
            if event_manager.is_event_processed(event_id):
                print(f"⏭️ 事件已处理，跳过: {event_id}")
                return JSONResponse(content={"code": 0, "msg": "success"})
            
            # 标记事件为已处理
            event_manager.mark_event_processed(event_id)
            
            # 创建审批服务实例
            approval_service = create_approval_service_from_config()
            
            # 处理审批事件
            result = approval_service.handle_approval_event(data)
            
            print(f"📊 处理结果: {result}")
            print("=" * 80)
            
            return JSONResponse(content={"code": 0, "msg": "success"})
        
        else:
            print(f"⚠️ 未知的事件类型: {event_type}")
            print(f"   完整数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return JSONResponse(content={"code": 0, "msg": "unknown event type"})
            
    except Exception as e:
        print(f"❌ 处理审批回调失败: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={"code": 500, "msg": str(e)},
            status_code=500
        )

