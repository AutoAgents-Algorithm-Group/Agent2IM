import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

import yaml
from src.service.feishu.labor_hour import LaborHourChecker
from src.utils.feishu.client import FeishuClient

def main():
    """测试 exclude_members 功能"""
    
    # 读取配置
    config_path = os.path.join(backend_dir, 'src', 'config', 'labor_hour.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("=" * 80)
    print("📋 配置信息")
    print("=" * 80)
    
    # 显示配置
    chat_id = config.get('group_chat', {}).get('chat_id')
    exclude_members = config.get('group_chat', {}).get('exclude_members', [])
    exceptions = config.get('group_chat', {}).get('exceptions', {})
    
    print(f"群聊ID: {chat_id}")
    print(f"排除成员: {exclude_members}")
    print(f"例外配置: {exceptions}")
    print()
    
    # 创建检查器
    checker = LaborHourChecker(
        app_id=config['feishu']['app_id'],
        app_secret=config['feishu']['app_secret'],
        bitable_url=config['bitable']['url'],
        chat_id=chat_id,
        exclude_members=exclude_members,
        exceptions=exceptions
    )
    
    print("=" * 80)
    print("🔍 检查器状态")
    print("=" * 80)
    print(f"exclude_members 类型: {type(checker.exclude_members)}")
    print(f"exclude_members 内容: {checker.exclude_members}")
    print(f"exclude_members 数量: {len(checker.exclude_members)}")
    print()
    
    # 获取群成员
    print("=" * 80)
    print("👥 获取群成员列表")
    print("=" * 80)
    member_info = checker.get_chat_members_info()
    
    print(f"\n实际获取到的成员数量: {len(member_info)}")
    print(f"成员列表:")
    for i, member in enumerate(member_info, 1):
        print(f"  {i}. {member['name']} ({member['open_id'][:20]}...)")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    
    # 验证
    member_names = [m['name'] for m in member_info]
    excluded_found = []
    for name in exclude_members:
        if name in member_names:
            excluded_found.append(name)
    
    if excluded_found:
        print(f"\n⚠️  警告：以下排除成员仍在列表中: {excluded_found}")
        print("   exclude_members 功能未生效！")
    else:
        print(f"\n✅ 成功：所有排除成员都已过滤")
        print(f"   排除的成员: {', '.join(exclude_members)}")

if __name__ == '__main__':
    main()

