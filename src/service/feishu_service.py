import json
import requests
import time
from typing import Dict, Any
from .autoagents_service import AutoAgentsService


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
        
        # 检查必要配置
        if not self.app_id or not self.app_secret:
            raise ValueError("缺少必要的飞书配置: FEISHU_APP_ID, FEISHU_APP_SECRET")
    
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
    
    # ========== 消息处理相关方法 ==========
    
    def process_message(self, data: Dict[str, Any]) -> bool:
        """处理飞书消息"""
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

            print(f"🚀 开始处理AI请求...")

            # 清理用户消息，移除@机器人的部分
            cleaned_message = text.replace('@bot', '').replace('@机器人', '').strip()
            import re
            cleaned_message = re.sub(r'@[^\s]+', '', cleaned_message).strip()

            if not cleaned_message:
                ai_response = "请问您需要什么帮助？"
            else:
                # 获取 AI 回复
                ai_response = self.ai_service.invoke(cleaned_message)
            
            # 获取消息信息用于回复
            event = data.get('event', {})
            message = event.get('message', {})
            
            message_id = message.get('message_id', '')
            chat_id = message.get('chat_id', '')
            
            # 发送AI回复 - 优先使用回复功能
            if message_id:
                result = self.reply_message(ai_response, message_id)
                print(f"📤 使用回复功能，结果: {result}")
            elif chat_id:
                result = self.send_message_to_group(ai_response, chat_id)
                print(f"📤 使用发送功能，结果: {result}")
            
            return True
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            return False