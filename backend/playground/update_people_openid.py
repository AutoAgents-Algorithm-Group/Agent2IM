#!/usr/bin/env python3
"""
自动获取人员 open_id 并更新到 people.json

功能:
1. 从 Bitable 获取所有人员的 open_id
2. 匹配 people.json 中的姓名
3. 自动更新 people.json，添加 open_id 字段
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.feishu.client import FeishuClient
from src.utils.feishu.bitable import BitableAPI


def main():
    print("=" * 80)
    print("🔄 更新人员 open_id 到 people.json")
    print("=" * 80)
    
    # 读取配置
    config_path = Path(__file__).parent.parent / 'src' / 'config' / 'labor_hour.json'
    people_config_path = Path(__file__).parent.parent / 'src' / 'config' / 'people.json'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    with open(people_config_path, 'r', encoding='utf-8') as f:
        people_config = json.load(f)
    
    # 创建飞书客户端
    feishu = config['feishu']
    client = FeishuClient(app_id=feishu['app_id'], app_secret=feishu['app_secret'])
    bitable = BitableAPI(client, url=config['bitable']['url'])
    
    print("\n📋 从多维表格获取人员 open_id...")
    
    # 获取最近的记录来建立映射
    records = bitable.get_records(page_size=500)
    
    # 建立姓名到 open_id 的映射
    name_to_openid = {}
    
    for record in records:
        fields = record.get('fields', {})
        user_info = fields.get('员工', {})
        
        if isinstance(user_info, dict):
            user_name = user_info.get('name', '')
            user_id = user_info.get('id', '')
            if user_name and user_id:
                name_to_openid[user_name] = user_id
        elif isinstance(user_info, list) and len(user_info) > 0:
            user_name = user_info[0].get('name', '')
            user_id = user_info[0].get('id', '')
            if user_name and user_id:
                name_to_openid[user_name] = user_id
    
    print(f"✅ 获取到 {len(name_to_openid)} 个人员的 open_id")
    
    # 更新 people.json
    print("\n🔄 更新 people.json...")
    updated_count = 0
    not_found = []
    
    for person in people_config['people']:
        name = person['name']
        if name in name_to_openid:
            person['open_id'] = name_to_openid[name]
            print(f"   ✅ {name}: {name_to_openid[name]}")
            updated_count += 1
        else:
            not_found.append(name)
            print(f"   ⚠️ {name}: 未找到 open_id")
    
    # 保存更新后的配置
    with open(people_config_path, 'w', encoding='utf-8') as f:
        json.dump(people_config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ 更新完成！")
    print(f"   成功更新: {updated_count} 人")
    if not_found:
        print(f"   未找到: {len(not_found)} 人 ({', '.join(not_found)})")
    print(f"   配置文件: {people_config_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()

