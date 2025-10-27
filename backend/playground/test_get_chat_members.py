"""
测试获取飞书群聊成员列表
"""

import os
import sys
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.feishu.service import FeishuService


def test_get_chat_members():
    """测试获取群聊成员列表"""
    
    # 从环境变量获取配置
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("❌ 请设置环境变量: FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return
    
    # 获取群聊ID（从环境变量或命令行参数）
    chat_id = os.getenv("FEISHU_CHAT_ID") or input("请输入群聊ID (chat_id): ").strip()
    
    if not chat_id:
        print("❌ 群聊ID不能为空")
        return
    
    print(f"\n🚀 开始获取群聊成员列表...")
    print(f"群聊ID: {chat_id}\n")
    
    # 创建飞书服务实例
    feishu_service = FeishuService(app_id=app_id, app_secret=app_secret)
    
    # 方式1: 获取第一页成员（最多50人）
    print("=" * 60)
    print("方式1: 获取第一页成员")
    print("=" * 60)
    result = feishu_service.message.get_chat_members(chat_id, page_size=50)
    
    if result:
        members = result.get("items", [])
        print(f"\n📋 成员列表（第1页）:")
        for i, member in enumerate(members, 1):
            print(f"  {i}. {member.get('name', '未知')} (ID: {member.get('member_id', 'N/A')})")
        
        print(f"\n分页信息:")
        print(f"  - 当前页成员数: {len(members)}")
        print(f"  - 是否有更多: {result.get('has_more', False)}")
        if result.get('has_more'):
            print(f"  - 下一页标记: {result.get('page_token', 'N/A')}")
    
    # 方式2: 获取所有成员（自动处理分页）
    print("\n" + "=" * 60)
    print("方式2: 获取所有成员（自动分页）")
    print("=" * 60)
    all_members = feishu_service.message.get_all_chat_members(chat_id)
    
    if all_members:
        print(f"\n📋 完整成员列表（共 {len(all_members)} 人）:")
        for i, member in enumerate(all_members, 1):
            member_info = {
                "序号": i,
                "姓名": member.get('name', '未知'),
                "ID": member.get('member_id', 'N/A'),
                "ID类型": member.get('member_id_type', 'N/A'),
                "租户Key": member.get('tenant_key', 'N/A')
            }
            print(f"  {i}. {json.dumps(member_info, ensure_ascii=False, indent=2)}")
        
        # 统计信息
        print(f"\n📊 统计信息:")
        print(f"  - 总成员数: {len(all_members)}")
        
        # 保存到文件
        output_file = f"chat_members_{chat_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_members, f, ensure_ascii=False, indent=2)
        print(f"  - 成员列表已保存到: {output_file}")
    else:
        print("❌ 获取成员列表失败")


def test_multiple_chats():
    """测试获取多个群聊的成员列表"""
    
    # 从环境变量获取配置
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("❌ 请设置环境变量: FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return
    
    # 获取多个群聊ID
    chat_ids_input = input("请输入群聊ID列表（用逗号分隔）: ").strip()
    if not chat_ids_input:
        print("❌ 群聊ID不能为空")
        return
    
    chat_ids = [cid.strip() for cid in chat_ids_input.split(',')]
    
    print(f"\n🚀 开始批量获取 {len(chat_ids)} 个群聊的成员列表...\n")
    
    # 创建飞书服务实例
    feishu_service = FeishuService(app_id=app_id, app_secret=app_secret)
    
    all_chat_members = {}
    
    for i, chat_id in enumerate(chat_ids, 1):
        print(f"\n{'=' * 60}")
        print(f"正在处理第 {i}/{len(chat_ids)} 个群聊: {chat_id}")
        print('=' * 60)
        
        members = feishu_service.message.get_all_chat_members(chat_id)
        if members:
            all_chat_members[chat_id] = members
            print(f"✅ 群聊 {chat_id} 共有 {len(members)} 名成员")
        else:
            print(f"❌ 获取群聊 {chat_id} 成员失败")
    
    # 汇总统计
    print(f"\n{'=' * 60}")
    print("📊 汇总统计")
    print('=' * 60)
    for chat_id, members in all_chat_members.items():
        print(f"  - 群聊 {chat_id}: {len(members)} 人")
    
    print(f"\n  总计: {sum(len(m) for m in all_chat_members.values())} 人（可能有重复）")
    
    # 保存到文件
    output_file = "all_chat_members.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chat_members, f, ensure_ascii=False, indent=2)
    print(f"\n  所有群聊成员已保存到: {output_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("飞书群聊成员列表获取工具")
    print("=" * 60)
    print("\n请选择测试模式:")
    print("  1. 获取单个群聊成员")
    print("  2. 批量获取多个群聊成员")
    
    choice = input("\n请输入选项 (1/2): ").strip()
    
    if choice == "1":
        test_get_chat_members()
    elif choice == "2":
        test_multiple_chats()
    else:
        print("❌ 无效的选项")

