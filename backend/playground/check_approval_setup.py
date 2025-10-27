#!/usr/bin/env python3
"""
审批功能配置检查脚本

检查项:
1. 配置文件是否存在
2. App ID 和 App Secret 是否已配置
3. Token 是否可以正常获取
4. 权限是否正确配置
5. 服务端口是否可访问
"""

import sys
import os
import json
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.feishu.client import FeishuClient


class ApprovalSetupChecker:
    """审批配置检查器"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "src" / "config" / "labor_hour.json"
        self.config = None
        self.client = None
        self.checks_passed = 0
        self.checks_failed = 0
    
    def print_header(self, text):
        """打印标题"""
        print(f"\n{'=' * 80}")
        print(f"  {text}")
        print(f"{'=' * 80}\n")
    
    def print_check(self, name, passed, message=""):
        """打印检查结果"""
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if message:
            print(f"   {message}")
        
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
    
    def check_config_file(self):
        """检查配置文件"""
        self.print_header("1️⃣  配置文件检查")
        
        # 检查文件是否存在
        exists = self.config_path.exists()
        self.print_check(
            "配置文件存在",
            exists,
            f"路径: {self.config_path}" if exists else "未找到 labor_hour.json"
        )
        
        if not exists:
            return False
        
        # 检查文件是否可读
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.print_check("配置文件格式正确", True, "JSON 格式有效")
            return True
        except json.JSONDecodeError as e:
            self.print_check("配置文件格式正确", False, f"JSON 解析失败: {e}")
            return False
        except Exception as e:
            self.print_check("配置文件可读", False, str(e))
            return False
    
    def check_credentials(self):
        """检查凭证配置"""
        self.print_header("2️⃣  凭证配置检查")
        
        if not self.config:
            self.print_check("跳过凭证检查", False, "配置文件未加载")
            return False
        
        # 检查 feishu 配置节
        feishu_config = self.config.get('feishu', {})
        
        # 检查 app_id
        app_id = feishu_config.get('app_id', '')
        has_app_id = bool(app_id and app_id != 'your_app_id')
        self.print_check(
            "App ID 已配置",
            has_app_id,
            f"App ID: {app_id[:20]}..." if has_app_id else "请配置真实的 App ID"
        )
        
        # 检查 app_secret
        app_secret = feishu_config.get('app_secret', '')
        has_app_secret = bool(app_secret and app_secret != 'your_app_secret')
        self.print_check(
            "App Secret 已配置",
            has_app_secret,
            f"App Secret: {app_secret[:10]}..." if has_app_secret else "请配置真实的 App Secret"
        )
        
        # 检查 bitable_url
        bitable_url = feishu_config.get('bitable_url', '')
        has_bitable = bool(bitable_url and 'feishu.cn/base/' in bitable_url)
        self.print_check(
            "Bitable URL 已配置",
            has_bitable,
            bitable_url if has_bitable else "请配置多维表格 URL"
        )
        
        return has_app_id and has_app_secret
    
    def check_token(self):
        """检查 Token 获取"""
        self.print_header("3️⃣  Token 获取检查")
        
        if not self.config:
            self.print_check("跳过 Token 检查", False, "配置文件未加载")
            return False
        
        try:
            feishu_config = self.config.get('feishu', {})
            app_id = feishu_config.get('app_id')
            app_secret = feishu_config.get('app_secret')
            
            self.client = FeishuClient(app_id=app_id, app_secret=app_secret)
            token = self.client.get_access_token()
            
            has_token = bool(token)
            self.print_check(
                "Token 获取成功",
                has_token,
                f"Token: {token[:30]}..." if has_token else "Token 获取失败"
            )
            
            return has_token
            
        except Exception as e:
            self.print_check("Token 获取", False, f"错误: {e}")
            return False
    
    def check_permissions(self):
        """检查权限配置"""
        self.print_header("4️⃣  权限检查")
        
        if not self.client:
            self.print_check("跳过权限检查", False, "Client 未初始化")
            return False
        
        print("💡 检查权限需要调用 API，请确保应用已授权以下权限:")
        print("   - approval:approval:readonly")
        print("   - calendar:timeoffevent:write")
        print("   - calendar:timeoffevent:readonly")
        print("   - bitable:app")
        print()
        
        # 尝试调用审批 API
        try:
            token = self.client.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 测试审批权限
            url = "https://open.feishu.cn/open-apis/approval/v4/approvals"
            params = {"page_size": 1}
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            approval_ok = result.get('code') == 0
            self.print_check(
                "审批权限 (approval:approval:readonly)",
                approval_ok,
                "可以访问审批列表" if approval_ok else f"错误: {result.get('msg', 'Unknown')}"
            )
            
        except Exception as e:
            self.print_check("审批权限检查", False, f"错误: {e}")
            approval_ok = False
        
        # 注意：日历权限检查需要实际创建事件，这里只是提示
        print("⚠️  日历权限需要实际创建事件才能验证，请通过真实审批测试")
        
        return approval_ok
    
    def check_api_service(self):
        """检查 API 服务"""
        self.print_header("5️⃣  API 服务检查")
        
        ports = [9000, 8000]  # 默认端口是 9000
        service_ok = False
        
        for port in ports:
            try:
                url = f"http://localhost:{port}/health"
                response = requests.get(url, timeout=2)
                
                if response.status_code == 200:
                    self.print_check(
                        f"API 服务运行中 (端口 {port})",
                        True,
                        f"响应: {response.text}"
                    )
                    service_ok = True
                    break
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                continue
        
        if not service_ok:
            self.print_check(
                "API 服务运行中",
                False,
                "未检测到服务，请运行: docker compose -f docker/docker-compose.yml up -d"
            )
        
        return service_ok
    
    def check_webhook_url(self):
        """检查 Webhook URL"""
        self.print_header("6️⃣  Webhook 配置检查")
        
        if not self.config:
            self.print_check("跳过 Webhook 检查", False, "配置文件未加载")
            return False
        
        webhook = self.config.get('webhook', {})
        webhook_url = webhook.get('url', '')
        
        has_webhook = bool(webhook_url and 'open.feishu.cn' in webhook_url)
        self.print_check(
            "Webhook URL 已配置",
            has_webhook,
            webhook_url if has_webhook else "请配置群机器人 Webhook URL"
        )
        
        return has_webhook
    
    def print_summary(self):
        """打印总结"""
        self.print_header("📊 检查总结")
        
        total = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total * 100) if total > 0 else 0
        
        print(f"总检查项: {total}")
        print(f"✅ 通过: {self.checks_passed}")
        print(f"❌ 失败: {self.checks_failed}")
        print(f"📈 通过率: {success_rate:.1f}%")
        print()
        
        if self.checks_failed == 0:
            print("🎉 恭喜！所有检查项都已通过！")
            print()
            print("📝 下一步:")
            print("   1. 在飞书开放平台配置事件订阅")
            print("   2. 创建请假审批模板")
            print("   3. 运行测试: python backend/playground/test_approval.py")
            print("   4. 提交真实审批进行测试")
        else:
            print("⚠️  有 {} 项检查未通过，请根据上述提示进行修复".format(self.checks_failed))
            print()
            print("💡 常见问题:")
            print("   - App ID/Secret 未配置: 编辑 backend/src/config/labor_hour.json")
            print("   - Token 获取失败: 检查 App ID 和 Secret 是否正确")
            print("   - 权限错误: 在飞书开放平台添加必要权限")
            print("   - 服务未运行: docker compose -f docker/docker-compose.yml up -d")
    
    def run_all_checks(self):
        """运行所有检查"""
        print("\n🔍 HR 小助手配置检查工具")
        print("=" * 80)
        
        # 1. 配置文件检查
        if not self.check_config_file():
            print("\n❌ 配置文件检查失败，无法继续")
            return
        
        # 2. 凭证配置检查
        self.check_credentials()
        
        # 3. Token 获取检查
        self.check_token()
        
        # 4. 权限检查
        self.check_permissions()
        
        # 5. API 服务检查
        self.check_api_service()
        
        # 6. Webhook 配置检查
        self.check_webhook_url()
        
        # 7. 打印总结
        self.print_summary()


def main():
    """主函数"""
    checker = ApprovalSetupChecker()
    checker.run_all_checks()
    
    print()
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()

