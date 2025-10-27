"""
工时填写检查服务

类似新闻推送服务，直接通过群组配置推送工时检查结果
不需要走API路由
"""

import hashlib
import base64
import hmac
import time
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
from collections import defaultdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.feishu.client import FeishuClient
from utils.feishu.bitable import BitableAPI
from utils.feishu.card import CardBuilder


class LaborHourChecker:
    """工时填写检查器"""
    
    def __init__(self, app_id: str, app_secret: str, bitable_url: str):
        """
        初始化工时检查器
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            bitable_url: 多维表格URL
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.bitable_url = bitable_url
        
        # 初始化飞书客户端
        self.feishu_client = FeishuClient(app_id=app_id, app_secret=app_secret)
        
        # 初始化Bitable API
        self.bitable = BitableAPI(client=self.feishu_client, url=bitable_url)
        
        print(f"✅ 工时检查器初始化成功")
    
    def get_bitable_url(self) -> str:
        """获取多维表格URL"""
        return self.bitable_url
    
    def check_users_filled(self, date_str: str = None) -> Dict[str, Any]:
        """
        检查用户填写情况
        
        Args:
            date_str: 检查日期，格式 YYYY-MM-DD，默认为今天
        
        Returns:
            检查结果字典
        """
        if not date_str:
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            date_str = now.strftime('%Y-%m-%d')
        
        print(f"🔍 正在检查 {date_str} 的工时填写情况...")
        
        result = self.bitable.check_users_filled(date_str=date_str)
        
        return result
    
    def check_week_summary(self, end_date_str: str = None) -> Dict[str, Any]:
        """
        检查一周的工时填写情况（周一至周五）
        
        Args:
            end_date_str: 周五日期，格式 YYYY-MM-DD，默认为本周五
        
        Returns:
            周总结字典，包含每天的填写情况和统计
        """
        tz = pytz.timezone('Asia/Shanghai')
        
        if not end_date_str:
            # 获取本周五的日期
            now = datetime.now(tz)
            # 获取今天是星期几（0=周一, 6=周日）
            weekday = now.weekday()
            # 计算到本周五的天数差
            days_to_friday = 4 - weekday  # 4是周五
            friday = now + timedelta(days=days_to_friday)
            end_date_str = friday.strftime('%Y-%m-%d')
        
        # 解析周五日期
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = tz.localize(end_date)
        
        # 计算周一日期
        start_date = end_date - timedelta(days=4)  # 周一到周五是4天差
        
        print(f"📊 正在检查 {start_date.strftime('%Y-%m-%d')} 至 {end_date_str} 的工时填写情况...")
        
        # 检查每一天的填写情况
        daily_results = {}
        user_fill_count = defaultdict(int)  # 每个人填写的天数
        user_info_map = {}  # 存储用户信息
        total_work_days = 0
        
        for i in range(5):  # 周一到周五
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            result = self.bitable.check_users_filled(date_str=date_str)
            daily_results[date_str] = result
            
            # 如果不是节假日，统计填写情况
            if not result.get('is_holiday'):
                total_work_days += 1
                
                # 统计每个人的填写天数
                for name in result.get('filled', []):
                    user_fill_count[name] += 1
                    
                # 收集用户信息（为了后续@人）
                for user_info in result.get('not_filled_with_id', []):
                    name = user_info['name']
                    user_id = user_info.get('user_id', '')
                    if name not in user_info_map and user_id:
                        user_info_map[name] = user_id
        
        # 计算统计数据
        all_users = set()
        for result in daily_results.values():
            if not result.get('is_holiday'):
                all_users.update(result.get('filled', []))
                all_users.update([u['name'] for u in result.get('not_filled_with_id', [])])
        
        # 分类用户：全勤、部分填写、完全未填写
        perfect_users = []  # 全勤
        partial_users = []  # 部分填写
        never_filled_users = []  # 完全未填写
        
        for user in all_users:
            fill_count = user_fill_count.get(user, 0)
            if fill_count == total_work_days:
                perfect_users.append(user)
            elif fill_count > 0:
                partial_users.append({'name': user, 'days': fill_count, 'total': total_work_days})
            else:
                never_filled_users.append(user)
        
        summary = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date_str,
            'total_work_days': total_work_days,
            'daily_results': daily_results,
            'all_users': list(all_users),
            'perfect_users': sorted(perfect_users),
            'partial_users': sorted(partial_users, key=lambda x: x['days'], reverse=True),
            'never_filled_users': sorted(never_filled_users),
            'user_info_map': user_info_map,
            'total_users': len(all_users),
            'perfect_count': len(perfect_users),
            'partial_count': len(partial_users),
            'never_filled_count': len(never_filled_users)
        }
        
        print(f"✅ 周总结完成: {total_work_days} 个工作日, {len(all_users)} 人, 全勤 {len(perfect_users)} 人")
        
        return summary


class LaborHourPublisher:
    """工时检查结果发布器 - 发送到飞书群组"""
    
    def __init__(self, webhook_url: str, webhook_secret: str):
        """
        初始化工时发布器
        
        Args:
            webhook_url: 飞书群机器人 webhook URL
            webhook_secret: 飞书群机器人密钥
        """
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        
        print(f"✅ 工时发布器初始化成功")
    
    def generate_signature(self) -> tuple:
        """生成飞书API签名（如果配置了secret）"""
        timestamp = int(time.time())
        
        # 如果没有配置secret或secret是示例值，返回None
        if not self.webhook_secret or self.webhook_secret == "your_webhook_secret":
            return timestamp, None
        
        string_to_sign = f'{timestamp}\n{self.webhook_secret}'
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), 
            digestmod=hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(hmac_code).decode('utf-8')
        return timestamp, signature
    
    def create_labor_hour_card(self, result: Dict[str, Any], date: str, bitable_url: str = None) -> Dict[str, Any]:
        """创建工时填写情况卡片"""
        
        # 根据填写率选择颜色
        fill_rate = result['fill_rate']
        if fill_rate >= 1.0:
            header_template = "green"
        elif fill_rate >= 0.8:
            header_template = "orange"
        else:
            header_template = "red"
        
        # 构建卡片元素
        elements = []
        
        # 统计信息和提示文案合并
        total = len(result['filled']) + len(result['not_filled'])
        filled = len(result['filled'])
        
        # 未填写人员列表 - 使用@功能
        if result['not_filled']:
            # 添加合并的提示文案
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**[已填写{filled}/{total}人] 请以下同学尽快填写工时:**",
                    "tag": "lark_md"
                }
            })
            
            # 构建@人员的内容
            mention_content = ""
            not_filled_with_id = result.get('not_filled_with_id', [])
            
            if not_filled_with_id:
                for user_info in not_filled_with_id:
                    user_id = user_info.get('user_id', '')
                    name = user_info['name']
                    if user_id:
                        mention_content += f"<at id={user_id}></at>  "
                    else:
                        mention_content += f"{name}  "
            else:
                for name in result['not_filled']:
                    mention_content += f"{name}  "
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": mention_content,
                    "tag": "lark_md"
                }
            })
        else:
            # 全部已填写
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**[已填写{filled}/{total}人] 所有同学都已填写工时**",
                    "tag": "lark_md"
                }
            })
        
        # 例外日期和请假人员（如果有）
        extra_info = []
        if result.get('exception_day'):
            extra_info.append(f"例外: " + "、".join(result['exception_day']))
        if result.get('on_leave'):
            extra_info.append(f"请假: " + "、".join(result['on_leave']))
        
        if extra_info:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "content": " | ".join(extra_info),
                    "tag": "lark_md"
                }
            })
        
        # 添加底部按钮 - 链接到多维表格（更宽）
        if bitable_url:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": "立即填写工时",
                            "tag": "plain_text"
                        },
                        "url": bitable_url,
                        "type": "primary",
                        "width": "default",
                        "size": "medium"
                    }
                ]
            })
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "template": header_template,
                    "title": {
                        "content": f"📮 工时速递｜{date}",
                        "tag": "plain_text"
                    }
                },
                "elements": elements
            }
        }
        
        return card
    
    def create_week_summary_card(self, summary: Dict[str, Any], bitable_url: str = None) -> Dict[str, Any]:
        """创建周总结卡片"""
        
        start_date = summary['start_date']
        end_date = summary['end_date']
        total_work_days = summary['total_work_days']
        perfect_users = summary['perfect_users']
        partial_users = summary['partial_users']
        never_filled_users = summary['never_filled_users']
        user_info_map = summary['user_info_map']
        
        # 根据完成情况选择颜色
        perfect_rate = len(perfect_users) / len(summary['all_users']) if summary['all_users'] else 0
        if perfect_rate >= 0.8:
            header_template = "green"
        elif perfect_rate >= 0.5:
            header_template = "orange"
        else:
            header_template = "red"
        
        # 构建卡片元素
        elements = []
        
        # 统计概览
        elements.append({
            "tag": "div",
            "text": {
                "content": f"**本周工作日: {total_work_days} 天**\n**总人数: {summary['total_users']} 人**",
                "tag": "lark_md"
            }
        })
        
        elements.append({"tag": "hr"})
        
        # 全勤人员
        if perfect_users:
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**✅ 全勤人员 ({len(perfect_users)}人)**",
                    "tag": "lark_md"
                }
            })
            
            # 构建全勤人员列表
            perfect_content = "  ".join(perfect_users)
            elements.append({
                "tag": "div",
                "text": {
                    "content": perfect_content,
                    "tag": "lark_md"
                }
            })
            
            elements.append({"tag": "hr"})
        
        # 部分填写人员
        if partial_users:
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**⚠️ 部分填写人员 ({len(partial_users)}人)**",
                    "tag": "lark_md"
                }
            })
            
            # 构建部分填写人员列表，显示填写天数
            partial_content = ""
            for user_info in partial_users:
                name = user_info['name']
                days = user_info['days']
                total = user_info['total']
                partial_content += f"{name}({days}/{total})  "
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": partial_content,
                    "tag": "lark_md"
                }
            })
            
            elements.append({"tag": "hr"})
        
        # 完全未填写人员
        if never_filled_users:
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**❌ 完全未填写人员 ({len(never_filled_users)}人)**",
                    "tag": "lark_md"
                }
            })
            
            # 构建@人员的内容
            never_filled_content = ""
            for name in never_filled_users:
                user_id = user_info_map.get(name, '')
                if user_id:
                    never_filled_content += f"<at id={user_id}></at>  "
                else:
                    never_filled_content += f"{name}  "
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": never_filled_content,
                    "tag": "lark_md"
                }
            })
            
            elements.append({"tag": "hr"})
        
        # 每日详情
        elements.append({
            "tag": "div",
            "text": {
                "content": "**📅 每日详情**",
                "tag": "lark_md"
            }
        })
        
        daily_results = summary['daily_results']
        for date_str in sorted(daily_results.keys()):
            result = daily_results[date_str]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_name = ['周一', '周二', '周三', '周四', '周五'][date_obj.weekday()]
            
            if result.get('is_holiday'):
                status = "节假日"
                fill_info = ""
            else:
                filled_count = len(result.get('filled', []))
                not_filled_count = len(result.get('not_filled', []))
                total = filled_count + not_filled_count
                fill_info = f" - {filled_count}/{total}人"
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"{weekday_name} {date_str}{fill_info if fill_info else ' - ' + status}",
                    "tag": "lark_md"
                }
            })
        
        # 添加底部按钮
        if bitable_url:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": "查看详细工时",
                            "tag": "plain_text"
                        },
                        "url": bitable_url,
                        "type": "primary",
                        "width": "default",
                        "size": "medium"
                    }
                ]
            })
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "template": header_template,
                    "title": {
                        "content": f"📮 工时周报｜{start_date} ~ {end_date}",
                        "tag": "plain_text"
                    }
                },
                "elements": elements
            }
        }
        
        return card
    
    def send_card(self, card: Dict[str, Any]) -> requests.Response:
        """发送卡片到飞书群组"""
        try:
            timestamp, sign = self.generate_signature()
            
            # 根据是否有签名，决定是否添加签名字段
            if sign:
                data = {
                    "timestamp": timestamp,
                    "sign": sign,
                    **card
                }
                print(f"🔐 使用签名验证发送消息")
            else:
                data = card
                print(f"📤 不使用签名验证发送消息")
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(self.webhook_url, json=data, headers=headers)
            
            # 解析响应内容
            try:
                response_data = response.json()
                print(f"📋 飞书响应: {response_data}")
            except:
                print(f"📋 原始响应: {response.text}")
            
            if response.status_code == 200:
                # 检查飞书的业务状态码
                if response_data.get('code') == 0:
                    print(f"✅ 工时检查结果发送成功")
                else:
                    print(f"❌ 飞书返回错误: code={response_data.get('code')}, msg={response_data.get('msg')}")
            else:
                print(f"❌ HTTP请求失败: {response.status_code}, {response.text}")
            
            return response
            
        except Exception as e:
            print(f"❌ 发送卡片时发生错误: {e}")
            raise e
    
    def publish_check_result(self, result: Dict[str, Any], date: str, bitable_url: str = None) -> Optional[requests.Response]:
        """发布工时检查结果，如果是节假日或全部已填写则不发送"""
        # 如果是节假日，不发送消息
        if result.get('is_holiday'):
            print(f"📅 {date} 是节假日，跳过发送消息")
            return None
        
        # 如果所有人都已填写，不发送消息
        if not result.get('not_filled'):
            print(f"✅ 所有人都已填写工时，跳过发送消息")
            return None
        
        # 创建并发送卡片
        card = self.create_labor_hour_card(result, date, bitable_url)
        return self.send_card(card)
    
    def publish_week_summary(self, summary: Dict[str, Any], bitable_url: str = None) -> requests.Response:
        """发布周总结"""
        card = self.create_week_summary_card(summary, bitable_url)
        return self.send_card(card)


class LaborHourService:
    """工时检查服务 - 整合检查和发布功能"""
    
    def __init__(self, app_id: str, app_secret: str, bitable_url: str, 
                 webhook_url: str, webhook_secret: str):
        """
        初始化工时检查服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            bitable_url: 多维表格URL
            webhook_url: 群机器人 webhook URL
            webhook_secret: 群机器人密钥
        """
        self.checker = LaborHourChecker(app_id, app_secret, bitable_url)
        self.publisher = LaborHourPublisher(webhook_url, webhook_secret)
        
        print(f"🚀 工时检查服务初始化完成")
    
    def run_check_and_publish(self, date_str: str = None) -> Dict[str, Any]:
        """
        运行工时检查并发布结果
        
        Args:
            date_str: 检查日期，格式 YYYY-MM-DD，默认为今天
        
        Returns:
            检查结果
        """
        print("=" * 80)
        print(f"🚀 开始执行工时检查")
        
        # 获取检查日期
        if not date_str:
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            date_str = now.strftime('%Y-%m-%d')
        
        print(f"   检查日期: {date_str}")
        
        try:
            # 1. 检查工时填写情况
            result = self.checker.check_users_filled(date_str)
            
            # 2. 打印结果
            if result.get('is_holiday'):
                print(f"\n📅 {date_str} 是节假日，无需检查工时填写，跳过发送")
                print(f"\n✅ 工时检查完成")
                print("=" * 80)
                
                return {
                    "status": "success",
                    "date": date_str,
                    "result": result,
                    "sent": False,
                    "reason": "holiday"
                }
            
            print(f"\n📊 检查结果:")
            print(f"   应填写人数: {len(result['filled']) + len(result['not_filled'])}")
            print(f"   已填写: {len(result['filled'])} 人")
            print(f"   未填写: {len(result['not_filled'])} 人")
            print(f"   填写率: {result['fill_rate']:.1%}")
            
            # 如果所有人都已填写，跳过发送
            if not result.get('not_filled'):
                print(f"\n✅ 所有人都已填写工时，跳过发送消息")
                print(f"\n✅ 工时检查完成")
                print("=" * 80)
                
                return {
                    "status": "success",
                    "date": date_str,
                    "result": result,
                    "sent": False,
                    "reason": "all_filled"
                }
            
            # 3. 发布到飞书群组
            print(f"\n📤 正在发送结果到飞书群组...")
            bitable_url = self.checker.get_bitable_url()
            print(f"   Bitable URL: {bitable_url}")
            response = self.publisher.publish_check_result(result, date_str, bitable_url)
            
            print(f"\n✅ 工时检查完成")
            print("=" * 80)
            
            return {
                "status": "success",
                "date": date_str,
                "result": result,
                "sent": response.status_code == 200
            }
            
        except Exception as e:
            print(f"\n❌ 工时检查失败: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "date": date_str,
                "message": str(e)
            }
    
    def run_week_summary_and_publish(self, end_date_str: str = None) -> Dict[str, Any]:
        """
        运行周总结并发布
        
        Args:
            end_date_str: 周五日期，格式 YYYY-MM-DD，默认为本周五
        
        Returns:
            周总结结果
        """
        print("=" * 80)
        print(f"🚀 开始执行周总结")
        
        try:
            # 1. 检查周总结
            summary = self.checker.check_week_summary(end_date_str)
            
            # 2. 打印结果
            print(f"\n📊 周总结:")
            print(f"   周期: {summary['start_date']} ~ {summary['end_date']}")
            print(f"   工作日: {summary['total_work_days']} 天")
            print(f"   总人数: {summary['total_users']} 人")
            print(f"   全勤: {summary['perfect_count']} 人")
            print(f"   部分填写: {summary['partial_count']} 人")
            print(f"   完全未填写: {summary['never_filled_count']} 人")
            
            # 3. 发布到飞书群组
            print(f"\n📤 正在发送周总结到飞书群组...")
            bitable_url = self.checker.get_bitable_url()
            response = self.publisher.publish_week_summary(summary, bitable_url)
            
            print(f"\n✅ 周总结完成")
            print("=" * 80)
            
            return {
                "status": "success",
                "summary": summary,
                "sent": response.status_code == 200 if response else False
            }
            
        except Exception as e:
            print(f"\n❌ 周总结失败: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "message": str(e)
            }


def run_labor_hour_check_from_config(date_str: str = None):
    """
    从配置文件读取参数并运行工时检查
    
    Args:
        date_str: 检查日期，格式 YYYY-MM-DD，默认为今天
    
    配置文件路径: backend/config/labor_hour.json
    """
    try:
        # 读取配置文件
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'labor_hour.json'
        )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 提取配置
        app_id = config['feishu']['app_id']
        app_secret = config['feishu']['app_secret']
        bitable_url = config['bitable']['url']
        webhook_url = config['webhook']['url']
        webhook_secret = config['webhook']['secret']
        
        # 创建服务实例
        service = LaborHourService(
            app_id=app_id,
            app_secret=app_secret,
            bitable_url=bitable_url,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret
        )
        
        # 运行检查
        result = service.run_check_and_publish(date_str)
        
        return result
        
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        print("💡 请创建配置文件 backend/config/labor_hour.json")
        return None
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    run_labor_hour_check_from_config()

