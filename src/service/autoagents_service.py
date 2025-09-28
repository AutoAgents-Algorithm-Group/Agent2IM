from autoagents_core.client import ChatClient


class AutoAgentsService:
    """AutoAgents AI服务类"""
    
    def __init__(self, agent_id: str, auth_key: str, auth_secret: str):
        """初始化AutoAgents服务"""
        self.client = ChatClient(
            agent_id=agent_id,
            personal_auth_key=auth_key,
            personal_auth_secret=auth_secret
        )
    
    def invoke(self, prompt: str) -> str:
        """调用AutoAgents生成回复"""
        try:
            content=""
            
            for event in self.client.invoke(prompt=prompt):
                if event['type'] == 'start_bubble':
                    print(f"💭 开始处理消息气泡 {event['bubble_id']}")

                elif event['type'] == 'token':
                    content+=event['content']
                    
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