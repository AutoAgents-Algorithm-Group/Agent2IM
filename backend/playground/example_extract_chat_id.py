"""
示例：从飞书消息事件中提取 chat_id

这个示例展示了如何从飞书的消息回调事件中提取群聊ID (chat_id)
"""

import json

# 示例1: 完整的飞书消息事件结构
example_event_data = {
    "schema": "2.0",
    "header": {
        "event_id": "5e3702a84e847582be8db7fb73283c02",
        "event_type": "im.message.receive_v1",
        "create_time": "1608725989000",
        "token": "rvaYgkND1GOiu5MM0E1rncYC6PLtF7JV",
        "app_id": "cli_a10fbf7e738d100e",
        "tenant_key": "736588c9260f175e"
    },
    "event": {
        "sender": {
            "sender_id": {
                "union_id": "on_94a1ee5551019f18cd73d9f111898cf2",
                "user_id": "e33ggbyz",
                "open_id": "ou_84aad35d084aa403a838cf73ee18467"
            },
            "sender_type": "user",
            "tenant_key": "736588c9260f175e"
        },
        "message": {
            "message_id": "om_dc13264520392913993dd051dba21dcf",
            "root_id": "om_40eb06e7b84dc71c03e009ad3c754195",
            "parent_id": "om_d4be107c616aed9c1da8ed8068570a9f",
            "create_time": "1609073151345",
            "update_time": "1687073151345",
            "chat_id": "oc_a0553eda9014c201e6969b478895c230",  # ⭐ 这就是群聊ID
            "chat_type": "group",  # group=群聊, p2p=私聊
            "message_type": "text",
            "content": "{\"text\":\"@bot 你好，请介绍一下自己\"}",
            "mentions": [
                {
                    "key": "@bot",
                    "id": {
                        "union_id": "on_94a1ee5551019f18cd73d9f111898cf2",
                        "user_id": "e33ggbyz",
                        "open_id": "ou_84aad35d084aa403a838cf73ee18467"
                    },
                    "name": "机器人",
                    "tenant_key": "736588c9260f175e"
                }
            ]
        }
    }
}


def extract_chat_id_from_event(data: dict) -> tuple:
    """
    从飞书消息事件中提取 chat_id 和相关信息
    
    Args:
        data: 飞书消息回调事件数据
    
    Returns:
        tuple: (chat_id, chat_type, message_id, sender_id)
    """
    try:
        # 第一步：获取 event 对象
        event = data.get('event', {})
        if not event:
            print("❌ 事件数据中没有 'event' 字段")
            return None, None, None, None
        
        # 第二步：获取 message 对象
        message = event.get('message', {})
        if not message:
            print("❌ 事件数据中没有 'message' 字段")
            return None, None, None, None
        
        # 第三步：提取关键信息
        chat_id = message.get('chat_id', '')
        chat_type = message.get('chat_type', '')  # group 或 p2p
        message_id = message.get('message_id', '')
        
        # 获取发送者信息
        sender = event.get('sender', {})
        sender_id = sender.get('sender_id', {}).get('open_id', '')
        
        return chat_id, chat_type, message_id, sender_id
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return None, None, None, None


def get_chat_info_and_members(chat_id: str):
    """
    获取chat_id后，可以进一步获取群聊成员列表
    
    Args:
        chat_id: 群聊ID
    """
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from src.utils.feishu.service import FeishuService
    
    # 从环境变量获取配置
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("⚠️ 请设置环境变量: FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return
    
    # 创建飞书服务
    feishu_service = FeishuService(app_id=app_id, app_secret=app_secret)
    
    # 获取群成员列表
    print(f"\n📋 正在获取群聊 {chat_id} 的成员列表...")
    members = feishu_service.message.get_all_chat_members(chat_id)
    
    if members:
        print(f"✅ 成功获取 {len(members)} 名成员:")
        for i, member in enumerate(members[:10], 1):  # 只显示前10个
            print(f"  {i}. {member.get('name', '未知')} (ID: {member.get('member_id')})")
        
        if len(members) > 10:
            print(f"  ... 还有 {len(members) - 10} 名成员")
    else:
        print("❌ 获取成员列表失败")


def demo_usage_in_webhook():
    """
    演示：在 webhook 回调中如何使用
    """
    print("\n" + "="*80)
    print("示例：在 Webhook 回调处理函数中提取 chat_id")
    print("="*80)
    
    code_example = '''
from fastapi import FastAPI, Request
from src.utils.feishu.service import FeishuService

app = FastAPI()

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """处理飞书消息回调"""
    
    # 1. 获取回调数据
    data = await request.json()
    
    # 2. 提取 chat_id
    event = data.get('event', {})
    message = event.get('message', {})
    
    chat_id = message.get('chat_id', '')       # ⭐ 群聊ID
    chat_type = message.get('chat_type', '')   # group 或 p2p
    message_id = message.get('message_id', '') # 消息ID
    
    print(f"收到消息:")
    print(f"  - 群聊ID: {chat_id}")
    print(f"  - 聊天类型: {chat_type}")
    print(f"  - 消息ID: {message_id}")
    
    # 3. 使用 chat_id 获取群成员
    if chat_id:
        feishu_service = FeishuService(
            app_id="your_app_id",
            app_secret="your_app_secret"
        )
        
        # 获取群成员列表
        members = feishu_service.message.get_all_chat_members(chat_id)
        print(f"  - 群成员数: {len(members)}")
        
        # 发送回复到群聊
        feishu_service.message.send_text_to_group(
            f"收到消息！本群共有 {len(members)} 名成员",
            chat_id
        )
    
    return {"status": "success"}
'''
    
    print(code_example)


def demo_real_extraction():
    """
    演示：从真实事件数据中提取 chat_id
    """
    print("\n" + "="*80)
    print("示例：从真实事件数据中提取信息")
    print("="*80)
    
    # 使用示例数据
    chat_id, chat_type, message_id, sender_id = extract_chat_id_from_event(example_event_data)
    
    print(f"\n提取结果:")
    print(f"  ✅ 群聊ID (chat_id): {chat_id}")
    print(f"  ✅ 聊天类型 (chat_type): {chat_type}")
    print(f"  ✅ 消息ID (message_id): {message_id}")
    print(f"  ✅ 发送者ID (sender_id): {sender_id}")
    
    print(f"\n💡 现在你可以使用这个 chat_id 来:")
    print(f"  1. 获取群成员列表: feishu_service.message.get_all_chat_members('{chat_id}')")
    print(f"  2. 发送消息到群: feishu_service.message.send_text_to_group('消息内容', '{chat_id}')")
    print(f"  3. 发送卡片到群: feishu_service.message.send_card_to_group(card, '{chat_id}')")


def demo_complete_flow():
    """
    演示：完整的消息处理流程
    """
    print("\n" + "="*80)
    print("完整流程：接收消息 → 提取chat_id → 获取成员 → 回复")
    print("="*80)
    
    # 步骤1: 提取信息
    print("\n📥 步骤1: 从消息事件中提取信息")
    chat_id, chat_type, message_id, sender_id = extract_chat_id_from_event(example_event_data)
    print(f"  提取到 chat_id: {chat_id}")
    
    # 步骤2: 显示消息内容
    print("\n📝 步骤2: 解析消息内容")
    message = example_event_data.get('event', {}).get('message', {})
    content = json.loads(message.get('content', '{}'))
    text = content.get('text', '')
    print(f"  消息内容: {text}")
    
    # 步骤3: 提示如何获取成员
    print("\n👥 步骤3: 获取群成员列表")
    print(f"  调用: feishu_service.message.get_all_chat_members('{chat_id}')")
    print(f"  说明: 这将返回该群的所有成员信息")
    
    # 步骤4: 提示如何回复
    print("\n💬 步骤4: 回复消息到群聊")
    print(f"  方式1 - 回复原消息:")
    print(f"    feishu_service.message.reply_text('回复内容', '{message_id}')")
    print(f"  方式2 - 发送新消息到群:")
    print(f"    feishu_service.message.send_text_to_group('消息内容', '{chat_id}')")


def interactive_mode():
    """
    交互模式：输入真实的事件JSON来提取chat_id
    """
    print("\n" + "="*80)
    print("🔧 交互模式：粘贴你的飞书消息事件JSON")
    print("="*80)
    print("\n提示: 从飞书开放平台或webhook日志中复制完整的JSON数据")
    print("输入 'skip' 跳过此步骤\n")
    
    try:
        json_input = input("请粘贴JSON数据（单行）: ").strip()
        
        if json_input.lower() == 'skip':
            print("⏭️ 已跳过")
            return
        
        if not json_input:
            print("⚠️ 输入为空，使用示例数据")
            data = example_event_data
        else:
            data = json.loads(json_input)
        
        # 提取信息
        chat_id, chat_type, message_id, sender_id = extract_chat_id_from_event(data)
        
        if chat_id:
            print(f"\n✅ 成功提取:")
            print(f"  - chat_id: {chat_id}")
            print(f"  - chat_type: {chat_type}")
            
            # 询问是否获取成员
            get_members = input(f"\n是否获取该群的成员列表？(y/n): ").strip().lower()
            if get_members == 'y':
                get_chat_info_and_members(chat_id)
        else:
            print("❌ 提取失败，请检查JSON格式")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
    except Exception as e:
        print(f"❌ 处理失败: {e}")


if __name__ == "__main__":
    print("="*80)
    print("飞书消息事件中提取 chat_id 的完整指南")
    print("="*80)
    
    # 演示1: 从真实数据提取
    demo_real_extraction()
    
    # 演示2: 在 webhook 中使用
    demo_usage_in_webhook()
    
    # 演示3: 完整流程
    demo_complete_flow()
    
    # 交互模式
    print("\n" + "="*80)
    choice = input("\n是否要测试提取真实的事件数据？(y/n): ").strip().lower()
    if choice == 'y':
        interactive_mode()
    
    print("\n" + "="*80)
    print("✅ 演示完成！")
    print("\n📚 更多信息请查看:")
    print("  - backend/src/utils/feishu/service.py (第135-136行)")
    print("  - backend/src/api/main.py (webhook处理)")
    print("  - backend/playground/GET_CHAT_MEMBERS_README.md")
    print("="*80)

