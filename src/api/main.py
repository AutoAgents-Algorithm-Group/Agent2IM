import os
import sys
import json
import time
import datetime
import pytz
import re
from pathlib import Path as PathLib
from fastapi import FastAPI, Request, Path, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from typing import Set

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

# 全局事件去重缓存（生产环境建议使用Redis）
processed_events: Set[str] = set()
event_timestamps: dict = {}  # 记录事件处理时间，用于清理过期事件

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

def is_event_processed(event_id: str) -> bool:
    """检查事件是否已处理"""
    return event_id in processed_events

def mark_event_processed(event_id: str):
    """标记事件已处理"""
    processed_events.add(event_id)
    event_timestamps[event_id] = time.time()

def cleanup_old_events():
    """清理10分钟以前的事件记录"""
    current_time = time.time()
    expired_events = [
        event_id for event_id, timestamp in event_timestamps.items()
        if current_time - timestamp > 600  # 10分钟
    ]
    
    for event_id in expired_events:
        processed_events.discard(event_id)
        event_timestamps.pop(event_id, None)
    
    if expired_events:
        print(f"🧹 清理了 {len(expired_events)} 个过期事件记录")

async def process_message_async(feishu_service, data: dict, event_id: str):
    """异步处理消息的后台任务 - 打字效果版本"""
    try:
        print(f"🚀 开始异步处理消息 (Event: {event_id})")
        
        # 直接处理消息并实现打字效果（不发送思考中卡片）
        result = await process_with_typing_effect(feishu_service, data)
        
        if result:
            print(f"✅ 异步消息处理完成 (Event: {event_id})")
        else:
            print(f"ℹ️ 异步消息未处理（不符合触发条件）(Event: {event_id})")
            
    except Exception as e:
        print(f"❌ 异步处理消息失败 (Event: {event_id}): {e}")

async def process_with_typing_effect(feishu_service, data: dict):
    """处理消息并实现打字效果"""
    try:
        # 处理飞书消息事件
        event = data.get('event', {})
        if not event:
            return False

        message = event.get('message', {})
        if not message:
            return False

        # 获取消息基本信息
        message_type = message.get('message_type', '')
        if message_type != 'text':
            return False

        # 获取消息内容
        content = message.get('content', '{}')
        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except:
                content_data = {"text": content}
        else:
            content_data = content

        text = content_data.get('text', '').strip()
        if not text:
            return False

        # 检查是否@了机器人
        mentions = message.get('mentions', [])
        is_mentioned = len(mentions) > 0

        # 检查消息中是否包含@bot关键词
        trigger_keywords = ['@bot', '@机器人', '@AI']
        has_trigger = any(keyword in text for keyword in trigger_keywords)

        if not (is_mentioned or has_trigger):
            return False

        print(f"⌨️ 开始流式生成AI回复...")

        # 获取chat_id以维护会话
        chat_id = message.get('chat_id', '')
        message_id = message.get('message_id', '')
        
        # 清理用户消息，移除@机器人的部分
        cleaned_message = text.replace('@bot', '').replace('@机器人', '').strip()
        cleaned_message = re.sub(r'@[^\s]+', '', cleaned_message).strip()

        if not cleaned_message:
            # 静态回复，直接发送
            static_response = "请问您需要什么帮助？"
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = datetime.datetime.now(beijing_tz)
            timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            
            card = feishu_service.create_ai_response_card(
                ai_response=static_response,
                user_message=cleaned_message,
                timestamp=timestamp
            )
            feishu_service.reply_with_card(card, message_id)
            return True
        else:
            # 初始化会话（如果不存在）
            if chat_id not in feishu_service.chat_sessions:
                feishu_service.chat_sessions[chat_id] = {
                    'messages': [],
                    'last_interaction': time.time()
                }
            
            # 添加用户消息到会话历史
            feishu_service.chat_sessions[chat_id]['messages'].append({
                'role': 'user',
                'content': cleaned_message,
                'timestamp': time.time(),
                'message_id': message_id
            })
            
            # 创建北京时间戳
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = datetime.datetime.now(beijing_tz)
            timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建打字效果处理器
            typing_handler = TypingEffectHandler(feishu_service, message_id, cleaned_message, timestamp)
            
            # 使用流式调用
            final_content = feishu_service.ai_service.invoke_stream(
                cleaned_message, 
                callback=typing_handler.handle_stream_event
            )
            
            # 添加AI回复到会话历史
            feishu_service.chat_sessions[chat_id]['messages'].append({
                'role': 'assistant', 
                'content': final_content,
                'timestamp': time.time()
            })
            
            # 更新最后交互时间
            feishu_service.chat_sessions[chat_id]['last_interaction'] = time.time()
            
            # 清理过期会话（保持最近50条消息）
            if len(feishu_service.chat_sessions[chat_id]['messages']) > 50:
                feishu_service.chat_sessions[chat_id]['messages'] = feishu_service.chat_sessions[chat_id]['messages'][-50:]
        
        return True
        
    except Exception as e:
        print(f"❌ 处理打字效果失败: {e}")
        return False

class TypingEffectHandler:
    """打字效果处理器"""
    
    def __init__(self, feishu_service, reply_to_message_id: str, user_message: str, timestamp: str):
        self.feishu_service = feishu_service
        self.reply_to_message_id = reply_to_message_id
        self.user_message = user_message
        self.timestamp = timestamp
        self.current_content = ""
        self.sent_message_id = None
        self.first_token = True
        self.update_counter = 0
        
    def handle_stream_event(self, event_type: str, data, full_content=None):
        """处理流式事件"""
        try:
            if event_type == 'start_bubble':
                print(f"⌨️ 开始打字效果，气泡ID: {data}")
                
            elif event_type == 'reasoning_token':
                # 推理token通常不显示给用户
                pass
                
            elif event_type == 'token':
                token = data
                self.current_content = full_content or (self.current_content + token)
                
                if self.first_token:
                    # 发送第一个卡片
                    self._send_initial_card()
                    self.first_token = False
                else:
                    # 更新现有卡片（每几个token更新一次，避免过于频繁）
                    self.update_counter += 1
                    if self.update_counter >= 3:  # 每3个token更新一次
                        self._update_card(is_typing=True)
                        self.update_counter = 0
                
            elif event_type == 'end_bubble':
                print("⌨️ 消息气泡结束")
                
            elif event_type == 'finish':
                print("⌨️ 打字效果完成")
                self.current_content = full_content or self.current_content
                self._update_card(is_typing=False)
                
            elif event_type == 'error':
                print(f"❌ 流式处理错误: {data}")
                if not self.sent_message_id:
                    # 如果还没发送过卡片，发送错误信息
                    error_card = self.feishu_service.create_ai_response_card(
                        ai_response="抱歉，AI服务暂时不可用，请稍后再试。",
                        user_message=self.user_message,
                        timestamp=self.timestamp
                    )
                    self.feishu_service.reply_with_card(error_card, self.reply_to_message_id)
                
        except Exception as e:
            print(f"❌ 处理流式事件失败: {e}")
    
    def _send_initial_card(self):
        """发送初始卡片"""
        try:
            card = self._create_typing_card(is_typing=True)
            result = self.feishu_service.reply_with_card(card, self.reply_to_message_id)
            
            if result and result.get("code") == 0:
                self.sent_message_id = result.get("data", {}).get("message_id")
                print(f"📤 初始打字卡片已发送，消息ID: {self.sent_message_id}")
            else:
                print("❌ 初始卡片发送失败")
                
        except Exception as e:
            print(f"❌ 发送初始卡片失败: {e}")
    
    def _update_card(self, is_typing: bool = False):
        """更新卡片"""
        try:
            if not self.sent_message_id:
                return
                
            card = self._create_typing_card(is_typing=is_typing)
            self.feishu_service.update_card_message(card, self.sent_message_id)
            
        except Exception as e:
            print(f"❌ 更新卡片失败: {e}")
    
    def _create_typing_card(self, is_typing: bool = False) -> dict:
        """创建打字效果的卡片"""
        elements = []
        
        # AI回复内容
        display_content = self.current_content if self.current_content else "　"  # 使用全角空格占位
        
        # 如果正在打字，添加打字光标效果
        if is_typing and self.current_content:
            display_content += "▋"  # 打字光标
        
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": display_content
            }
        })
        
        # 底部信息栏
        footer_elements = []
        
        if is_typing:
            footer_elements.append({
                "tag": "plain_text",
                "content": "AI正在输入..."
            })
        else:
            footer_text = f"回复时间: {self.timestamp}"
            if self.current_content:
                footer_text += f" • 字数: {len(self.current_content)}"
            footer_elements.append({
                "tag": "plain_text", 
                "content": footer_text
            })
        
        if footer_elements:
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "note",
                "elements": footer_elements
            })
        
        # 构建完整的卡片
        card = {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True,
                "update_multi": False
            },
            "header": {
                "template": "indigo"
            },
            "elements": elements
        }
        
        return card

async def process_and_update_card(feishu_service, data: dict, processing_message_id: str):
    """处理消息并更新卡片"""
    try:
        # 处理飞书消息事件
        event = data.get('event', {})
        if not event:
            return False

        message = event.get('message', {})
        if not message:
            return False

        # 获取消息基本信息
        message_type = message.get('message_type', '')
        if message_type != 'text':
            return False

        # 获取消息内容
        content = message.get('content', '{}')
        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except:
                content_data = {"text": content}
        else:
            content_data = content

        text = content_data.get('text', '').strip()
        if not text:
            return False

        # 检查是否@了机器人
        mentions = message.get('mentions', [])
        is_mentioned = len(mentions) > 0

        # 检查消息中是否包含@bot关键词
        trigger_keywords = ['@bot', '@机器人', '@AI']
        has_trigger = any(keyword in text for keyword in trigger_keywords)

        if not (is_mentioned or has_trigger):
            return False

        print(f"🤖 开始生成AI回复...")

        # 获取chat_id以维护会话
        chat_id = message.get('chat_id', '')
        message_id = message.get('message_id', '')
        
        # 清理用户消息，移除@机器人的部分
        cleaned_message = text.replace('@bot', '').replace('@机器人', '').strip()
        import re
        cleaned_message = re.sub(r'@[^\s]+', '', cleaned_message).strip()

        if not cleaned_message:
            ai_response = "请问您需要什么帮助？"
        else:
            # 初始化会话（如果不存在）
            if chat_id not in feishu_service.chat_sessions:
                feishu_service.chat_sessions[chat_id] = {
                    'messages': [],
                    'last_interaction': time.time()
                }
            
            # 添加用户消息到会话历史
            feishu_service.chat_sessions[chat_id]['messages'].append({
                'role': 'user',
                'content': cleaned_message,
                'timestamp': time.time(),
                'message_id': message_id
            })
            
            # 获取 AI 回复
            ai_response = feishu_service.ai_service.invoke(cleaned_message)
            
            # 添加AI回复到会话历史
            feishu_service.chat_sessions[chat_id]['messages'].append({
                'role': 'assistant', 
                'content': ai_response,
                'timestamp': time.time()
            })
            
            # 更新最后交互时间
            feishu_service.chat_sessions[chat_id]['last_interaction'] = time.time()
            
            # 清理过期会话（保持最近50条消息）
            if len(feishu_service.chat_sessions[chat_id]['messages']) > 50:
                feishu_service.chat_sessions[chat_id]['messages'] = feishu_service.chat_sessions[chat_id]['messages'][-50:]
        
        # 创建北京时间戳
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.datetime.now(beijing_tz)
        timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建最终的交互式卡片
        final_card = feishu_service.create_ai_response_card(
            ai_response=ai_response,
            user_message=cleaned_message,
            timestamp=timestamp
        )
        
        # 更新原来的处理中卡片为最终结果
        if processing_message_id:
            feishu_service.update_card_message(final_card, processing_message_id)
        
        return True
        
    except Exception as e:
        print(f"❌ 处理和更新卡片失败: {e}")
        return False

async def send_processing_card(feishu_service, data: dict):
    """发送处理中的卡片，返回发送的消息ID"""
    try:
        event = data.get('event', {})
        message = event.get('message', {})
        
        if not message:
            return None
        
        # 检查是否是@机器人的消息
        mentions = message.get('mentions', [])
        if not mentions:
            return None
            
        message_id = message.get('message_id', '')
        
        if message_id:
            # 创建处理中卡片
            processing_card = {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "template": "indigo"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**正在思考中，请稍候...**"
                        }
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": "AI正在为您生成回答，通常需要几秒钟时间"
                            }
                        ]
                    }
                ]
            }
            
            # 发送处理中卡片并获取返回的消息ID
            result = feishu_service.reply_with_card(processing_card, message_id)
            
            if result and result.get("code") == 0:
                # 提取新发送的消息ID
                sent_message_id = result.get("data", {}).get("message_id")
                print(f"📤 处理中卡片已发送，消息ID: {sent_message_id}")
                return sent_message_id
            
        return None
            
    except Exception as e:
        print(f"❌ 发送处理中卡片失败: {e}")
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
        },
        "features": {
            "fast_response": "3秒内快速响应，避免飞书重试",
            "idempotency": "基于event_id的幂等处理，确保不重不漏",
            "typing_effect": "利用流式接口实现实时打字效果",
            "background_processing": "使用异步后台任务处理AI请求"
        }
    }

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    """处理飞书消息回调 - 快速响应版本"""
    try:
        # 定期清理过期事件
        cleanup_old_events()
        
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到回调数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print("🔐 处理challenge验证")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 获取event_id进行去重
        event_id = data.get('header', {}).get('event_id', '')
        if not event_id:
            print("⚠️ 缺少event_id，使用默认处理")
            event_id = f"fallback_{int(time.time() * 1000)}"
        
        # 检查事件是否已处理（幂等性）
        if is_event_processed(event_id):
            print(f"⚠️ 事件 {event_id} 已处理过，跳过重复处理")
            return JSONResponse(content={"status": "success"}, status_code=200)
        
        # 标记事件已处理
        mark_event_processed(event_id)
        
        # 🚀 关键：立即返回200，避免飞书重试
        print(f"⚡ 立即响应事件 {event_id}，后台异步处理")
        
        # 将消息处理加入后台任务
        background_tasks.add_task(process_message_async, feishu_service, data, event_id)
        
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
    background_tasks: BackgroundTasks,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码")
):
    """处理飞书消息回调 - 动态机器人切换 - 快速响应版本"""
    try:
        # 定期清理过期事件
        cleanup_old_events()
        
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到动态回调数据 (Agent: {agent_id}): {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print(f"🔐 处理challenge验证 (Agent: {agent_id})")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 获取event_id进行去重
        event_id = data.get('header', {}).get('event_id', '')
        if not event_id:
            print(f"⚠️ 缺少event_id，使用默认处理 (Agent: {agent_id})")
            event_id = f"dynamic_{agent_id}_{int(time.time() * 1000)}"
        
        # 检查事件是否已处理（幂等性）
        if is_event_processed(event_id):
            print(f"⚠️ 事件 {event_id} 已处理过，跳过重复处理 (Agent: {agent_id})")
            return JSONResponse(content={"status": "success"}, status_code=200)
        
        # 标记事件已处理
        mark_event_processed(event_id)
        
        # 创建动态服务实例（使用默认飞书配置）
        dynamic_feishu_service = create_dynamic_services(agent_id, auth_key, auth_secret)
        
        if not dynamic_feishu_service:
            print(f"❌ 动态AI服务创建失败 (Agent: {agent_id})")
            return JSONResponse(
                content={"status": "error", "message": "AI服务初始化失败"}, 
                status_code=500
            )
        
        # 🚀 关键：立即返回200，避免飞书重试
        print(f"⚡ 立即响应动态事件 {event_id} (Agent: {agent_id})，后台异步处理")
        
        # 将消息处理加入后台任务
        background_tasks.add_task(process_message_async, dynamic_feishu_service, data, event_id)
        
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
    background_tasks: BackgroundTasks,
    agent_id: str = Path(..., description="AutoAgents代理ID"),
    auth_key: str = Path(..., description="AutoAgents认证密钥"),
    auth_secret: str = Path(..., description="AutoAgents认证密码"),
    app_id: str = Path(..., description="飞书应用ID"),
    app_secret: str = Path(..., description="飞书应用密钥")
):
    """处理飞书消息回调 - 完全动态切换（AI机器人+飞书应用）- 快速响应版本"""
    try:
        # 定期清理过期事件
        cleanup_old_events()
        
        # 获取飞书消息回调数据
        data = await request.json()
        print(f"📥 收到完全动态回调数据 (Agent: {agent_id}, App: {app_id}): {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 如果是第一次接收到 Webhook 请求，飞书会发送 challenge 字段进行验证
        if 'challenge' in data:
            print(f"🔐 处理challenge验证 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(content={"challenge": data['challenge']}, status_code=200)
        
        # 获取event_id进行去重
        event_id = data.get('header', {}).get('event_id', '')
        if not event_id:
            print(f"⚠️ 缺少event_id，使用默认处理 (Agent: {agent_id}, App: {app_id})")
            event_id = f"full_{agent_id}_{app_id}_{int(time.time() * 1000)}"
        
        # 检查事件是否已处理（幂等性）
        if is_event_processed(event_id):
            print(f"⚠️ 事件 {event_id} 已处理过，跳过重复处理 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(content={"status": "success"}, status_code=200)
        
        # 标记事件已处理
        mark_event_processed(event_id)
        
        # 创建完全动态的服务实例
        dynamic_feishu_service = create_dynamic_services(agent_id, auth_key, auth_secret, app_id, app_secret)
        
        if not dynamic_feishu_service:
            print(f"❌ 完全动态服务创建失败 (Agent: {agent_id}, App: {app_id})")
            return JSONResponse(
                content={"status": "error", "message": "完全动态服务初始化失败"}, 
                status_code=500
            )
        
        # 🚀 关键：立即返回200，避免飞书重试
        print(f"⚡ 立即响应完全动态事件 {event_id} (Agent: {agent_id}, App: {app_id})，后台异步处理")
        
        # 将消息处理加入后台任务
        background_tasks.add_task(process_message_async, dynamic_feishu_service, data, event_id)
        
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