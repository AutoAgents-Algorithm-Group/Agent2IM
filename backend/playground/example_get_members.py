"""
简单示例：获取飞书群聊成员列表
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.feishu.service import FeishuService


def main():
    # 配置信息
    APP_ID = os.getenv("FEISHU_APP_ID", "cli_xxx")
    APP_SECRET = os.getenv("FEISHU_APP_SECRET", "xxx")
    CHAT_ID = os.getenv("FEISHU_CHAT_ID", "oc_xxx")
    
    # 创建飞书服务
    feishu_service = FeishuService(
        app_id=APP_ID,
        app_secret=APP_SECRET
    )
    
    # 获取群聊所有成员
    print(f"正在获取群聊 {CHAT_ID} 的成员列表...\n")
    members = feishu_service.message.get_all_chat_members(CHAT_ID)
    
    if members:
        print(f"\n群聊成员列表（共 {len(members)} 人）：")
        print("-" * 60)
        for i, member in enumerate(members, 1):
            name = member.get('name', '未知')
            member_id = member.get('member_id', 'N/A')
            print(f"{i:3d}. {name:20s} (ID: {member_id})")
        print("-" * 60)
    else:
        print("❌ 获取成员列表失败，请检查：")
        print("  1. APP_ID 和 APP_SECRET 是否正确")
        print("  2. CHAT_ID 是否正确")
        print("  3. 机器人是否在该群聊中")
        print("  4. 应用是否有 'im:chat:member:readonly' 权限")


if __name__ == "__main__":
    main()

