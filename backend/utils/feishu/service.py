"""
飞书服务主类
整合所有飞书相关功能
"""

import json
import time
import datetime
import pytz
import re
from typing import Dict, Any, Set

from .client import FeishuClient
from .message import MessageAPI
from .bitable import BitableAPI
from .card import CardBuilder
from .typing_handler import TypingEffectHandler


class FeishuService:
    """飞书AI机器人核心服务类"""
    
    def __init__(self, app_id: str, app_secret: str, ai_service=None):
        """
        初始化飞书服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            ai_service: AI服务实例（可选，定时任务不需要）
        """
        # 创建飞书客户端
        self.client = FeishuClient(app_id, app_secret)
        
        # 创建各个API模块
        self.message = MessageAPI(self.client)
        self.bitable = BitableAPI(self.client)
        
        # AI服务（可选）
        self.ai_service = ai_service
        
        # 消息去重：记录已处理的消息ID
        self.processed_messages: Set[str] = set()
        
        # 会话管理：为每个聊天维护对话历史
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 检查必要配置
        if not app_id or not app_secret:
            raise ValueError("缺少必要的飞书配置: app_id, app_secret")
    
    # ========== 数据清理相关方法 ==========
    
    def cleanup_expired_data(self):
        """清理过期的消息ID和会话数据"""
        current_time = time.time()
        
        # 清理超过1小时的已处理消息ID
        if len(self.processed_messages) > 1000:
            message_list = list(self.processed_messages)
            self.processed_messages = set(message_list[len(message_list)//2:])
            print(f"🧹 清理过期消息ID，当前保留: {len(self.processed_messages)} 条")
        
        # 清理超过2小时无交互的会话
        expired_chats = []
        for chat_id, session in self.chat_sessions.items():
            if current_time - session['last_interaction'] > 7200:  # 2小时
                expired_chats.append(chat_id)
        
        for chat_id in expired_chats:
            del self.chat_sessions[chat_id]
        
        if expired_chats:
            print(f"🧹 已清理 {len(expired_chats)} 个过期会话")
    
    # ========== 消息处理相关方法 ==========
    
    def process_message(self, data: Dict[str, Any]) -> bool:
        """处理飞书消息和交互事件"""
        try:
            # 定期清理过期数据
            self.cleanup_expired_data()
            
            # 检查是否是交互卡片事件
            if self._is_card_interaction_event(data):
                return self._handle_card_interaction(data)
            
            # 处理飞书消息事件
            event = data.get('event', {})
            if not event:
                return False

            message = event.get('message', {})
            if not message:
                return False

            # 获取消息ID
            message_id = message.get('message_id', '')
            if not message_id:
                print("⚠️ 消息ID为空，跳过处理")
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

            print(f"🚀 开始处理AI请求...")

            # 获取chat_id以维护会话
            chat_id = message.get('chat_id', '')
            
            # 清理用户消息，移除@机器人的部分
            cleaned_message = text.replace('@bot', '').replace('@机器人', '').strip()
            cleaned_message = re.sub(r'@[^\s]+', '', cleaned_message).strip()

            if not cleaned_message:
                ai_response = "请问您需要什么帮助？"
            else:
                # 初始化会话（如果不存在）
                if chat_id not in self.chat_sessions:
                    self.chat_sessions[chat_id] = {
                        'messages': [],
                        'last_interaction': time.time()
                    }
                
                # 添加用户消息到会话历史
                self.chat_sessions[chat_id]['messages'].append({
                    'role': 'user',
                    'content': cleaned_message,
                    'timestamp': time.time(),
                    'message_id': message_id
                })
                
                # 获取 AI 回复
                if self.ai_service:
                    ai_response = self.ai_service.invoke(cleaned_message)
                else:
                    ai_response = "AI服务未配置，无法回复"
                
                # 添加AI回复到会话历史
                self.chat_sessions[chat_id]['messages'].append({
                    'role': 'assistant', 
                    'content': ai_response,
                    'timestamp': time.time()
                })
                
                # 更新最后交互时间
                self.chat_sessions[chat_id]['last_interaction'] = time.time()
                
                # 清理过期会话（保持最近50条消息）
                if len(self.chat_sessions[chat_id]['messages']) > 50:
                    self.chat_sessions[chat_id]['messages'] = self.chat_sessions[chat_id]['messages'][-50:]
            
            # 创建北京时间戳
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = datetime.datetime.now(beijing_tz)
            timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建交互式卡片
            card = CardBuilder.create_ai_response_card(
                ai_response=ai_response,
                user_message=cleaned_message,
                timestamp=timestamp
            )
            
            # 发送AI回复
            if message_id:
                result = self.message.reply_card(card, message_id)
                print(f"📤 使用交互卡片回复，结果: {result}")
            elif chat_id:
                result = self.message.send_card_to_group(card, chat_id)
                print(f"📤 使用交互卡片发送，结果: {result}")
            
            return True
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            return False
    
    def _is_card_interaction_event(self, data: Dict[str, Any]) -> bool:
        """检查是否是交互卡片事件"""
        event = data.get('event', {})
        return event.get('type') == 'card_action_trigger'
    
    def _handle_card_interaction(self, data: Dict[str, Any]) -> bool:
        """处理交互卡片按钮点击事件"""
        try:
            event = data.get('event', {})
            action = event.get('action', {})
            action_value = action.get('value', {})
            
            action_type = action_value.get('action')
            message_id = event.get('message_id', '')
            
            print(f"🎯 收到交互卡片事件: {action_type}")
            
            if action_type == 'feedback':
                feedback_type = action_value.get('type', '')
                response_text = self._handle_feedback(feedback_type)
                if message_id:
                    self.message.reply_text(response_text, message_id)
                    
            elif action_type == 'regenerate':
                original_question = action_value.get('original_question', '')
                if original_question and self.ai_service:
                    print(f"🔄 重新生成回答: {original_question}")
                    new_response = self.ai_service.invoke(original_question)
                    
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    beijing_time = datetime.datetime.now(beijing_tz)
                    timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                    card = CardBuilder.create_ai_response_card(
                        ai_response=new_response,
                        user_message=original_question,
                        timestamp=f"{timestamp} (重新生成)"
                    )
                    
                    if message_id:
                        self.message.reply_card(card, message_id)
                
            elif action_type == 'continue':
                continue_message = "很高兴为您继续服务！请直接输入您的新问题，记得@我哦~"
                if message_id:
                    self.message.reply_text(continue_message, message_id)
                    
            elif action_type == 'copy':
                copy_message = "内容已准备好复制。您可以通过长按消息选择复制功能。"
                if message_id:
                    self.message.reply_text(copy_message, message_id)
            
            return True
            
        except Exception as e:
            print(f"❌ 处理交互卡片事件失败: {e}")
            return False
    
    def _handle_feedback(self, feedback_type: str) -> str:
        """处理用户反馈"""
        if feedback_type == 'helpful':
            return "感谢您的反馈！很高兴我的回答对您有帮助。如有其他问题，随时@我！"
        else:
            return "感谢您的反馈！我会继续努力提供更好的服务。如有其他需要，请随时告诉我！"
    
    # ========== 异步消息处理方法 ==========
    
    async def process_message_async(self, data: dict, event_id: str):
        """异步处理消息的后台任务 - 打字效果版本"""
        try:
            print(f"🚀 开始异步处理消息 (Event: {event_id})")
            result = await self.process_with_typing_effect(data)
            
            if result:
                print(f"✅ 异步消息处理完成 (Event: {event_id})")
            else:
                print(f"ℹ️ 异步消息未处理（不符合触发条件）(Event: {event_id})")
                
        except Exception as e:
            print(f"❌ 异步处理消息失败 (Event: {event_id}): {e}")

    async def process_with_typing_effect(self, data: dict):
        """处理消息并实现打字效果"""
        try:
            event = data.get('event', {})
            if not event:
                return False

            message = event.get('message', {})
            if not message:
                return False

            message_type = message.get('message_type', '')
            if message_type != 'text':
                return False

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

            mentions = message.get('mentions', [])
            is_mentioned = len(mentions) > 0

            trigger_keywords = ['@bot', '@机器人', '@AI']
            has_trigger = any(keyword in text for keyword in trigger_keywords)

            if not (is_mentioned or has_trigger):
                return False

            print(f"⌨️ 开始流式生成AI回复...")

            chat_id = message.get('chat_id', '')
            message_id = message.get('message_id', '')
            
            cleaned_message = text.replace('@bot', '').replace('@机器人', '').strip()
            cleaned_message = re.sub(r'@[^\s]+', '', cleaned_message).strip()

            if not cleaned_message:
                static_response = "请问您需要什么帮助？"
                beijing_tz = pytz.timezone('Asia/Shanghai')
                beijing_time = datetime.datetime.now(beijing_tz)
                timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                
                card = CardBuilder.create_ai_response_card(
                    ai_response=static_response,
                    user_message=cleaned_message,
                    timestamp=timestamp
                )
                self.message.reply_card(card, message_id)
                return True
            else:
                if chat_id not in self.chat_sessions:
                    self.chat_sessions[chat_id] = {
                        'messages': [],
                        'last_interaction': time.time()
                    }
                
                self.chat_sessions[chat_id]['messages'].append({
                    'role': 'user',
                    'content': cleaned_message,
                    'timestamp': time.time(),
                    'message_id': message_id
                })
                
                beijing_tz = pytz.timezone('Asia/Shanghai')
                beijing_time = datetime.datetime.now(beijing_tz)
                timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                
                typing_handler = TypingEffectHandler(self.message, message_id, cleaned_message, timestamp)
                
                if self.ai_service:
                    final_content = self.ai_service.invoke_stream(
                        cleaned_message, 
                        callback=typing_handler.handle_stream_event
                    )
                else:
                    final_content = "AI服务未配置，无法回复"
                
                self.chat_sessions[chat_id]['messages'].append({
                    'role': 'assistant', 
                    'content': final_content,
                    'timestamp': time.time()
                })
                
                self.chat_sessions[chat_id]['last_interaction'] = time.time()
                
                if len(self.chat_sessions[chat_id]['messages']) > 50:
                    self.chat_sessions[chat_id]['messages'] = self.chat_sessions[chat_id]['messages'][-50:]
            
            return True
            
        except Exception as e:
            print(f"❌ 处理打字效果失败: {e}")
            return False
    
    # ========== 静态方法 ==========
    
    @staticmethod
    def create_dynamic_services(agent_id: str, auth_key: str, auth_secret: str, app_id: str, app_secret: str):
        """动态创建服务实例"""
        try:
            from service.autoagents_service import AutoAgentsService
            
            # 创建动态AI服务
            dynamic_ai_service = AutoAgentsService(
                agent_id=agent_id,
                auth_key=auth_key,
                auth_secret=auth_secret
            )
            
            # 创建动态飞书服务
            dynamic_feishu_service = FeishuService(
                app_id=app_id,
                app_secret=app_secret,
                ai_service=dynamic_ai_service
            )
            
            return dynamic_feishu_service
        except Exception as e:
            print(f"❌ 创建动态服务失败: {e}")
            return None

