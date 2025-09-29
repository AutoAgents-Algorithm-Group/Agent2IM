import json
import requests
import time
import datetime
import pytz
import re
from typing import Dict, Any, Set
from .autoagents_service import AutoAgentsService


class EventManager:
    """全局事件去重管理器"""
    
    def __init__(self):
        # 全局事件去重缓存（生产环境建议使用Redis）
        self.processed_events: Set[str] = set()
        self.event_timestamps: dict = {}  # 记录事件处理时间，用于清理过期事件
    
    def is_event_processed(self, event_id: str) -> bool:
        """检查事件是否已处理"""
        return event_id in self.processed_events

    def mark_event_processed(self, event_id: str):
        """标记事件已处理"""
        self.processed_events.add(event_id)
        self.event_timestamps[event_id] = time.time()

    def cleanup_old_events(self):
        """清理10分钟以前的事件记录"""
        current_time = time.time()
        expired_events = [
            event_id for event_id, timestamp in self.event_timestamps.items()
            if current_time - timestamp > 600  # 10分钟
        ]
        
        for event_id in expired_events:
            self.processed_events.discard(event_id)
            self.event_timestamps.pop(event_id, None)
        
        if expired_events:
            print(f"🧹 清理了 {len(expired_events)} 个过期事件记录")


# 全局事件管理器实例
event_manager = EventManager()


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


class FeishuService:
    """飞书AI机器人核心服务类"""
    
    def __init__(self, app_id: str, app_secret: str, ai_service: AutoAgentsService):
        """
        初始化飞书服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            ai_service: AI服务实例
        """
        # 飞书配置
        self.app_id = app_id
        self.app_secret = app_secret
        
        # AI服务
        self.ai_service = ai_service
        
        # 访问令牌缓存
        self._access_token_cache = {
            "token": None,
            "expires_at": 0
        }
        
        # 消息去重：记录已处理的消息ID
        self.processed_messages: Set[str] = set()
        
        # 会话管理：为每个聊天维护对话历史
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 检查必要配置
        if not self.app_id or not self.app_secret:
            raise ValueError("缺少必要的飞书配置: FEISHU_APP_ID, FEISHU_APP_SECRET")
    
    # ========== 数据清理相关方法 ==========
    
    def cleanup_expired_data(self):
        """清理过期的消息ID和会话数据"""
        current_time = time.time()
        
        # 清理超过1小时的已处理消息ID（避免内存无限增长）
        # 注意：这里假设飞书不会在1小时后重发同一消息
        if len(self.processed_messages) > 1000:
            # 简单的清理策略：当数量超过1000时，清空一半
            # 实际使用中可以根据需要调整策略
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
            print(f"🧹 清理过期会话: {chat_id}")
        
        if expired_chats:
            print(f"🧹 已清理 {len(expired_chats)} 个过期会话")

    # ========== 交互卡片相关方法 ==========
    
    def create_ai_response_card(self, ai_response: str, user_message: str = "", timestamp: str = None) -> dict:
        """创建AI回复的交互式卡片"""
        
        # 处理长文本，自动分段
        if len(ai_response) > 1200:
            # 如果内容太长，分成多个段落
            paragraphs = self._split_long_text(ai_response, max_length=1200)
            content = paragraphs[0]
            has_more = True
        else:
            content = ai_response
            has_more = False
        
        # 创建卡片元素
        elements = []
        
        # AI回复内容 - 简洁布局
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
        
        # 如果内容被截断，添加提示
        if has_more:
            elements.append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "回答内容较长，已显示主要部分。"
                    }
                ]
            })
        
        # 底部信息栏
        footer_text = ""
        if timestamp:
            footer_text += f"回复时间: {timestamp}"
        
        # 添加字数统计
        word_count = len(ai_response)
        if word_count > 0:
            if footer_text:
                footer_text += " • "
            footer_text += f"字数: {word_count}"
        
        if footer_text:
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": footer_text
                    }
                ]
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
    
    def _split_long_text(self, text: str, max_length: int = 800) -> list:
        """将长文本分割成合适的段落"""
        if len(text) <= max_length:
            return [text]
        
        # 尝试按段落分割
        paragraphs = text.split('\n\n')
        result = []
        current = ""
        
        for para in paragraphs:
            if len(current + para) <= max_length:
                if current:
                    current += "\n\n" + para
                else:
                    current = para
            else:
                if current:
                    result.append(current)
                    current = para
                else:
                    # 单个段落太长，强制分割
                    while len(para) > max_length:
                        result.append(para[:max_length])
                        para = para[max_length:]
                    current = para
        
        if current:
            result.append(current)
        
        return result

    # ========== 飞书API相关方法 ==========
    
    def get_access_token(self) -> str:
        """获取飞书访问令牌"""
        current_time = time.time()
        
        # 如果令牌还有效，直接返回缓存的令牌
        if (self._access_token_cache["token"] and 
            current_time < self._access_token_cache["expires_at"]):
            return self._access_token_cache["token"]
        
        # 获取新的访问令牌
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                token = result["tenant_access_token"]
                expires_in = result.get("expire", 7200)  # 默认2小时
                
                # 缓存令牌，提前10分钟过期
                self._access_token_cache["token"] = token
                self._access_token_cache["expires_at"] = current_time + expires_in - 600
                
                print(f"✅ 获取访问令牌成功")
                return token
            else:
                raise Exception(f"获取访问令牌失败: {result}")
        except Exception as e:
            print(f"❌ 获取飞书访问令牌失败: {e}")
            raise e
    
    def send_message_to_group(self, message: str, chat_id: str):
        """发送消息到飞书群组"""
        try:
            access_token = self.get_access_token()
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"receive_id_type": "chat_id"}
            
            data = {
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": message})
            }
            
            response = requests.post(url, headers=headers, json=data, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 消息发送成功")
            else:
                print(f"❌ 消息发送失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return None
    
    def reply_message(self, message: str, message_id: str):
        """回复特定消息"""
        try:
            access_token = self.get_access_token()
            url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "msg_type": "text",
                "content": json.dumps({"text": message})
            }
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 消息回复成功")
            else:
                print(f"❌ 消息回复失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 回复消息失败: {e}")
            return None
    
    def reply_with_card(self, card: dict, message_id: str):
        """使用交互式卡片回复特定消息"""
        try:
            access_token = self.get_access_token()
            url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "msg_type": "interactive",
                "content": json.dumps(card)
            }
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 交互卡片回复成功")
            else:
                print(f"❌ 交互卡片回复失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 交互卡片回复失败: {e}")
            return None
    
    def send_card_to_group(self, card: dict, chat_id: str):
        """发送交互式卡片到飞书群组"""
        try:
            access_token = self.get_access_token()
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"receive_id_type": "chat_id"}
            
            data = {
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card)
            }
            
            response = requests.post(url, headers=headers, json=data, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 交互卡片发送成功")
            else:
                print(f"❌ 交互卡片发送失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 交互卡片发送失败: {e}")
            return None
    
    def update_card_message(self, card: dict, message_id: str):
        """更新已发送的交互式卡片"""
        try:
            access_token = self.get_access_token()
            url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "msg_type": "interactive",
                "content": json.dumps(card)
            }
            
            response = requests.patch(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 交互卡片更新成功")
            else:
                print(f"❌ 交互卡片更新失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 交互卡片更新失败: {e}")
            return None
    
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

            # 获取消息ID（不再用于去重，API层已处理）
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
            import re
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
                ai_response = self.ai_service.invoke(cleaned_message)
                
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
            card = self.create_ai_response_card(
                ai_response=ai_response,
                user_message=cleaned_message,
                timestamp=timestamp
            )
            
            # 发送AI回复 - 优先使用交互卡片回复功能
            if message_id:
                result = self.reply_with_card(card, message_id)
                print(f"📤 使用交互卡片回复，结果: {result}")
            elif chat_id:
                result = self.send_card_to_group(card, chat_id)
                print(f"📤 使用交互卡片发送，结果: {result}")
            
            return True
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            return False
    
    def _is_card_interaction_event(self, data: Dict[str, Any]) -> bool:
        """检查是否是交互卡片事件"""
        # 飞书交互卡片事件的标识
        event = data.get('event', {})
        return event.get('type') == 'card_action_trigger'
    
    def _handle_card_interaction(self, data: Dict[str, Any]) -> bool:
        """处理交互卡片按钮点击事件"""
        try:
            event = data.get('event', {})
            action = event.get('action', {})
            action_value = action.get('value', {})
            
            action_type = action_value.get('action')
            user_id = event.get('user_id', '')
            chat_id = event.get('chat_id', '')
            message_id = event.get('message_id', '')
            
            print(f"🎯 收到交互卡片事件: {action_type}")
            
            if action_type == 'feedback':
                # 用户点击了反馈按钮
                feedback_type = action_value.get('type', '')
                response_text = self._handle_feedback(feedback_type)
                
                # 发送反馈确认消息
                if message_id:
                    self.reply_message(response_text, message_id)
                    
            elif action_type == 'regenerate':
                # 用户点击了重新回答按钮
                original_question = action_value.get('original_question', '')
                if original_question:
                    print(f"🔄 重新生成回答: {original_question}")
                    
                    # 获取新的AI回复
                    new_response = self.ai_service.invoke(original_question)
                    
                    # 创建新的交互卡片（北京时间）
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    beijing_time = datetime.datetime.now(beijing_tz)
                    timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                    card = self.create_ai_response_card(
                        ai_response=new_response,
                        user_message=original_question,
                        timestamp=f"{timestamp} (重新生成)"
                    )
                    
                    # 发送新卡片
                    if message_id:
                        self.reply_with_card(card, message_id)
                
            elif action_type == 'continue':
                # 用户点击了继续提问按钮
                continue_message = "很高兴为您继续服务！请直接输入您的新问题，记得@我哦~"
                if message_id:
                    self.reply_message(continue_message, message_id)
                    
            elif action_type == 'copy':
                # 用户点击了复制内容按钮
                copy_message = "内容已准备好复制。您可以通过长按消息选择复制功能。"
                if message_id:
                    self.reply_message(copy_message, message_id)
            
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
    
    # ========== 新增的异步消息处理方法 ==========
    
    async def process_message_async(self, data: dict, event_id: str):
        """异步处理消息的后台任务 - 打字效果版本"""
        try:
            print(f"🚀 开始异步处理消息 (Event: {event_id})")
            
            # 直接处理消息并实现打字效果
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
                
                card = self.create_ai_response_card(
                    ai_response=static_response,
                    user_message=cleaned_message,
                    timestamp=timestamp
                )
                self.reply_with_card(card, message_id)
                return True
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
                
                # 创建北京时间戳
                beijing_tz = pytz.timezone('Asia/Shanghai')
                beijing_time = datetime.datetime.now(beijing_tz)
                timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 创建打字效果处理器
                typing_handler = TypingEffectHandler(self, message_id, cleaned_message, timestamp)
                
                # 使用流式调用
                final_content = self.ai_service.invoke_stream(
                    cleaned_message, 
                    callback=typing_handler.handle_stream_event
                )
                
                # 添加AI回复到会话历史
                self.chat_sessions[chat_id]['messages'].append({
                    'role': 'assistant', 
                    'content': final_content,
                    'timestamp': time.time()
                })
                
                # 更新最后交互时间
                self.chat_sessions[chat_id]['last_interaction'] = time.time()
                
                # 清理过期会话（保持最近50条消息）
                if len(self.chat_sessions[chat_id]['messages']) > 50:
                    self.chat_sessions[chat_id]['messages'] = self.chat_sessions[chat_id]['messages'][-50:]
            
            return True
            
        except Exception as e:
            print(f"❌ 处理打字效果失败: {e}")
            return False

    async def process_and_update_card(self, data: dict, processing_message_id: str):
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
                ai_response = self.ai_service.invoke(cleaned_message)
                
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
            
            # 创建最终的交互式卡片
            final_card = self.create_ai_response_card(
                ai_response=ai_response,
                user_message=cleaned_message,
                timestamp=timestamp
            )
            
            # 更新原来的处理中卡片为最终结果
            if processing_message_id:
                self.update_card_message(final_card, processing_message_id)
            
            return True
            
        except Exception as e:
            print(f"❌ 处理和更新卡片失败: {e}")
            return False

    async def send_processing_card(self, data: dict):
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
                result = self.reply_with_card(processing_card, message_id)
                
                if result and result.get("code") == 0:
                    # 提取新发送的消息ID
                    sent_message_id = result.get("data", {}).get("message_id")
                    print(f"📤 处理中卡片已发送，消息ID: {sent_message_id}")
                    return sent_message_id
                
            return None
                
        except Exception as e:
            print(f"❌ 发送处理中卡片失败: {e}")
            return None
    
    # ========== 静态方法 ==========
    
    @staticmethod
    def create_dynamic_services(agent_id: str, auth_key: str, auth_secret: str, app_id: str, app_secret: str):
        """动态创建服务实例"""
        try:
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