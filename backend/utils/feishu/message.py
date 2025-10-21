"""
飞书消息发送API
"""

import json
import requests


class MessageAPI:
    """飞书消息发送API"""
    
    def __init__(self, client):
        """
        初始化消息API
        
        Args:
            client: FeishuClient实例
        """
        self.client = client
    
    def send_text_to_group(self, message: str, chat_id: str):
        """发送文本消息到飞书群组"""
        try:
            access_token = self.client.get_access_token()
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
    
    def reply_text(self, message: str, message_id: str):
        """回复特定消息"""
        try:
            access_token = self.client.get_access_token()
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
    
    def send_card_to_group(self, card: dict, chat_id: str):
        """发送交互式卡片到飞书群组"""
        try:
            access_token = self.client.get_access_token()
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
    
    def reply_card(self, card: dict, message_id: str):
        """使用交互式卡片回复特定消息"""
        try:
            access_token = self.client.get_access_token()
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
    
    def update_card(self, card: dict, message_id: str):
        """更新已发送的交互式卡片"""
        try:
            access_token = self.client.get_access_token()
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
    
    def send_card_with_mention(self, card: dict, chat_id: str, user_ids: list):
        """发送带@提醒的交互式卡片到群组"""
        try:
            access_token = self.client.get_access_token()
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"receive_id_type": "chat_id"}
            
            # 在卡片内容中添加@提醒
            mention_text = " ".join([f"<at user_id=\"{uid}\"></at>" for uid in user_ids])
            
            # 修改卡片添加@提醒
            if "elements" in card and len(card["elements"]) > 0:
                # 在第一个元素前插入@提醒
                mention_element = {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": mention_text
                    }
                }
                card["elements"].insert(0, mention_element)
            
            data = {
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card)
            }
            
            response = requests.post(url, headers=headers, json=data, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 带@提醒的交互卡片发送成功")
            else:
                print(f"❌ 带@提醒的交互卡片发送失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 发送带@提醒的交互卡片失败: {e}")
            return None
    
    def send_private_card(self, card: dict, user_id: str):
        """发送私信给指定用户"""
        try:
            access_token = self.client.get_access_token()
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"receive_id_type": "user_id"}
            
            data = {
                "receive_id": user_id,
                "msg_type": "interactive",
                "content": json.dumps(card)
            }
            
            response = requests.post(url, headers=headers, json=data, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                print(f"✅ 私信发送成功")
            else:
                print(f"❌ 私信发送失败: {result}")
            
            return result
        except Exception as e:
            print(f"❌ 私信发送失败: {e}")
            return None

