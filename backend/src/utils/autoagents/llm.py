"""
AutoAgents AI服务

负责与AutoAgents平台交互，提供AI对话能力
"""

from autoagents_core.client import ChatClient


class AutoAgentsService:
    """AutoAgents AI服务类"""
    
    def __init__(self, agent_id: str, auth_key: str, auth_secret: str):
        """
        初始化AutoAgents服务
        
        Args:
            agent_id: AutoAgents代理ID
            auth_key: 认证密钥
            auth_secret: 认证密码
        """
        self.client = ChatClient(
            agent_id=agent_id,
            personal_auth_key=auth_key,
            personal_auth_secret=auth_secret
        )
    
    def invoke(self, prompt: str) -> str:
        """
        调用AutoAgents生成回复
        
        Args:
            prompt: 用户输入的提示词
            
        Returns:
            AI生成的回复内容
        """
        try:
            content = ""
            for event in self.client.invoke(prompt=prompt):
                if event['type'] == 'start_bubble':
                    print(f"💭 开始处理消息气泡 {event['bubble_id']}")

                elif event['type'] == 'token':
                    content += event['content']
                    
                elif event['type'] == 'end_bubble':
                    print(f"✅ 消息气泡处理完成")
                    
                elif event['type'] == 'finish':
                    print(f"🎉 对话生成完成")
                    break
            
            if content:
                print(f"✅ AutoAgents回复: {content}")
                return content
            else:
                return "抱歉，我现在无法回答这个问题，请稍后再试。"
                
        except Exception as e:
            print(f"❌ AutoAgents调用失败: {e}")
            return "AI服务暂时不可用，请稍后再试。"
    
    def invoke_stream(self, prompt: str, callback=None):
        """
        调用AutoAgents生成回复（流式）
        
        Args:
            prompt: 用户输入的提示词
            callback: 回调函数，接收事件类型和内容
            
        Returns:
            完整的AI回复内容
        """
        try:
            content = ""
            
            for event in self.client.invoke(prompt=prompt):                        
                if event['type'] == 'token':
                    content += event['content']
                    if callback:
                        callback('token', event['content'], content)
                    
                elif event['type'] == 'finish':
                    print(f"🎉 对话生成完成")
                    if callback:
                        callback('finish', content)
                    break
            
            return content if content else "抱歉，我现在无法回答这个问题，请稍后再试。"
                
        except Exception as e:
            print(f"❌ AutoAgents流式调用失败: {e}")
            if callback:
                callback('error', str(e))
            return "AI服务暂时不可用，请稍后再试。"

