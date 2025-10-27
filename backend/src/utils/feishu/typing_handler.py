"""
打字效果处理器
"""

from .card import CardBuilder


class TypingEffectHandler:
    """打字效果处理器"""
    
    def __init__(self, message_api, reply_to_message_id: str, user_message: str, timestamp: str):
        """
        初始化打字效果处理器
        
        Args:
            message_api: MessageAPI实例
            reply_to_message_id: 要回复的消息ID
            user_message: 用户消息
            timestamp: 时间戳
        """
        self.message_api = message_api
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
                    error_card = CardBuilder.create_ai_response_card(
                        ai_response="抱歉，AI服务暂时不可用，请稍后再试。",
                        user_message=self.user_message,
                        timestamp=self.timestamp
                    )
                    self.message_api.reply_card(error_card, self.reply_to_message_id)
                
        except Exception as e:
            print(f"❌ 处理流式事件失败: {e}")
    
    def _send_initial_card(self):
        """发送初始卡片"""
        try:
            card = CardBuilder.create_typing_card(self.current_content, is_typing=True, timestamp=self.timestamp)
            result = self.message_api.reply_card(card, self.reply_to_message_id)
            
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
                
            card = CardBuilder.create_typing_card(self.current_content, is_typing=is_typing, timestamp=self.timestamp)
            self.message_api.update_card(card, self.sent_message_id)
            
        except Exception as e:
            print(f"❌ 更新卡片失败: {e}")

