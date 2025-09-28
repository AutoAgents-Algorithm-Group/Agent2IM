#!/usr/bin/env python3
"""
飞书AI机器人测试脚本
验证系统各组件是否正常工作
"""

import sys
import os
import requests
import time
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

def test_config():
    """测试配置加载"""
    print("🔧 测试配置加载...")
    try:
        from config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"  ✅ 配置文件加载成功")
        print(f"  📋 飞书配置: {config['configured']['feishu']}")
        print(f"  🤖 AutoAgents配置: {config['configured']['autoagents']}")
        print(f"  ✅ 配置验证通过")
        
        return config
    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")
        return None

def test_services(config):
    """测试服务初始化"""
    print("\n🛠️ 测试服务初始化...")
    try:
        from service.autoagents_service import AutoAgentsService
        from service.feishu_service import FeishuService
        
        # 测试AI服务
        ai_service = AutoAgentsService(
            agent_id=config['autoagents']['agent_id'],
            auth_key=config['autoagents']['auth_key'],
            auth_secret=config['autoagents']['auth_secret']
        )
        print("  ✅ AutoAgents服务初始化成功")
        
        # 测试飞书服务
        feishu_service = FeishuService(
            app_id=config['feishu']['app_id'],
            app_secret=config['feishu']['app_secret'],
            ai_service=ai_service
        )
        print("  ✅ 飞书服务初始化成功")
        
        return ai_service, feishu_service
    except Exception as e:
        print(f"  ❌ 服务初始化失败: {e}")
        return None, None

def test_ai_service(ai_service):
    """测试AI服务"""
    print("\n🤖 测试AI服务...")
    try:
        test_prompt = "你好，请简单介绍一下自己"
        print(f"  📝 测试问题: {test_prompt}")
        
        response = ai_service.invoke(test_prompt)
        
        if response and len(response) > 10:
            print(f"  ✅ AI服务测试成功")
            print(f"  💬 AI回复: {response[:100]}{'...' if len(response) > 100 else ''}")
            return True
        else:
            print(f"  ❌ AI服务响应异常: {response}")
            return False
    except Exception as e:
        print(f"  ❌ AI服务测试失败: {e}")
        return False

def test_feishu_token(feishu_service):
    """测试飞书访问令牌"""
    print("\n🔑 测试飞书访问令牌...")
    try:
        token = feishu_service.get_access_token()
        if token:
            print(f"  ✅ 获取访问令牌成功: {token[:20]}...")
            return True
        else:
            print("  ❌ 获取访问令牌失败")
            return False
    except Exception as e:
        print(f"  ❌ 访问令牌测试失败: {e}")
        return False

def start_api_server():
    """启动API服务器"""
    print("\n🚀 启动API服务器...")
    import subprocess
    import threading
    
    def run_server():
        try:
            subprocess.run([
                sys.executable, 
                str(project_root / "src" / "API" / "main.py")
            ], cwd=project_root)
        except Exception as e:
            print(f"启动服务器失败: {e}")
    
    # 在后台线程启动服务器
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    print("  ⏳ 等待服务器启动...")
    time.sleep(3)
    
    return server_thread

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    base_url = "http://localhost:9000"
    
    try:
        # 测试根端点
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("  ✅ 根端点 (/) 测试成功")
            data = response.json()
            print(f"  📊 API版本: {data.get('version')}")
            print(f"  📊 服务状态: {data.get('status')}")
        else:
            print(f"  ❌ 根端点测试失败: {response.status_code}")
            return False
        
        # 测试webhook端点 (发送一个测试challenge)
        test_data = {"challenge": "test_challenge_123"}
        response = requests.post(f"{base_url}/feishu/webhook", json=test_data, timeout=5)
        if response.status_code == 200:
            challenge_data = response.json()
            if challenge_data.get("challenge") == "test_challenge_123":
                print("  ✅ Webhook端点 (/feishu/webhook) 测试成功")
            else:
                print(f"  ⚠️ Webhook端点响应异常: {challenge_data}")
        else:
            print(f"  ❌ Webhook端点测试失败: {response.status_code}")
            
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API端点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 飞书AI机器人 - 系统测试")
    print("=" * 60)
    
    # 测试配置
    config = test_config()
    if not config:
        print("\n❌ 配置测试失败，终止测试")
        return False
    
    # 测试服务初始化
    ai_service, feishu_service = test_services(config)
    if not ai_service or not feishu_service:
        print("\n❌ 服务初始化失败，终止测试")
        return False
    
    # 测试AI服务
    ai_ok = test_ai_service(ai_service)
    
    # 测试飞书令牌
    feishu_ok = test_feishu_token(feishu_service)
    
    # 启动API服务器并测试端点
    server_thread = start_api_server()
    api_ok = test_api_endpoints()
    
    # 测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"🔧 配置加载: ✅ 成功")
    print(f"🛠️ 服务初始化: ✅ 成功")
    print(f"🤖 AI服务: {'✅ 成功' if ai_ok else '❌ 失败'}")
    print(f"🔑 飞书令牌: {'✅ 成功' if feishu_ok else '❌ 失败'}")
    print(f"🌐 API端点: {'✅ 成功' if api_ok else '❌ 失败'}")
    
    overall_success = ai_ok and feishu_ok and api_ok
    
    if overall_success:
        print("\n🎉 所有测试通过！系统运行正常。")
        print("💡 您可以继续配置飞书Webhook来使用机器人。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接。")
    
    print(f"\n🌐 API服务地址: http://localhost:9000")
    print(f"📥 Webhook地址: http://localhost:9000/feishu/webhook")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期错误: {e}")
        sys.exit(1)
