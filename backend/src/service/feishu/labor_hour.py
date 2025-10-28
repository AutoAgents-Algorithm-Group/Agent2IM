"""
工时填写检查服务

包含：
1. LaborHourChecker - 工时检查器（检查工时填写情况）
2. LaborHourPublisher - 工时发布器（发送卡片消息）
3. LaborHourService - 工时服务（协调检查和发布）
4. run_labor_hour_check_from_config - 从配置文件运行检查
"""

import os
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
from collections import defaultdict

from src.utils.feishu.client import FeishuClient
from src.utils.feishu.bitable import BitableAPI
from src.utils.feishu.message import MessageAPI
from src.utils.logging import set_stage
from src.models import Stage


class LaborHourChecker:
    """工时填写检查器"""
    
    def __init__(self, app_id: str, app_secret: str, bitable_url: str, leave_approval_code: str = None, 
                 chat_id: str = None, exclude_members: list = None, exceptions: dict = None):
        """
        初始化工时检查器
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            bitable_url: 多维表格URL
            leave_approval_code: 请假审批定义编码（可选，用于自动检测请假状态）
            chat_id: 群聊ID（可选，用于获取群成员列表）
            exclude_members: 排除成员列表（可选，这些成员完全不参与工时检查）
            exceptions: 例外日期配置，格式: {"姓名": ["星期一", "星期二"]}
        """
        # 初始化日志
        self.log = set_stage(Stage.LABOR_CHECK)
        
        self.app_id = app_id
        self.app_secret = app_secret
        self.bitable_url = bitable_url
        self.leave_approval_code = leave_approval_code
        self.chat_id = chat_id
        self.exclude_members = set(exclude_members or [])
        self.exceptions = exceptions or {}
        
        # 初始化飞书客户端
        self.feishu_client = FeishuClient(app_id=app_id, app_secret=app_secret)
        
        # 初始化Bitable API
        self.bitable = BitableAPI(
            client=self.feishu_client, 
            url=bitable_url,
            leave_approval_code=leave_approval_code
        )
        
        # 初始化Message API（用于获取群成员）
        self.message_api = MessageAPI(self.feishu_client)
        
        self.log.success("工时检查器初始化成功")
    
    def get_bitable_url(self) -> str:
        """获取多维表格URL"""
        return self.bitable_url
    
    def get_chat_members_info(self) -> List[Dict[str, str]]:
        """
        从群聊获取成员信息列表（包含姓名和open_id）
        
        Returns:
            成员信息列表，格式: [{"name": "张三", "open_id": "ou_xxx"}, ...]
        """
        if not self.chat_id:
            self.log.warning("未配置chat_id，无法获取群成员列表")
            return []
        
        try:
            # 使用 MessageAPI 获取所有群成员
            members = self.message_api.get_all_chat_members(self.chat_id)
            member_info = []
            excluded_count = 0
            
            for m in members:
                name = m.get('name', '')
                open_id = m.get('member_id', '')
                if name and open_id:
                    # 过滤掉排除成员
                    if name in self.exclude_members:
                        excluded_count += 1
                        continue
                    
                    member_info.append({
                        'name': name,
                        'open_id': open_id
                    })
            
            self.log.success(f"从群聊获取到 {len(member_info)} 名成员（已排除 {excluded_count} 人）")
            return member_info
        except Exception as e:
            self.log.error(f"获取群成员列表失败: {e}")
            return []
    
    def check_users_filled(self, date_str: str = None, user_names: List[str] = None, 
                          user_id_map: Dict[str, str] = None) -> Dict[str, Any]:
        """
        检查用户填写情况
        
        Args:
            date_str: 检查日期，格式 YYYY-MM-DD，默认为今天
            user_names: 人员名单列表（可选），如果不提供则从群成员列表获取
            user_id_map: 姓名到open_id的映射（可选），用于@功能和请假检测
        
        Returns:
            检查结果字典
        """
        if not date_str:
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            date_str = now.strftime('%Y-%m-%d')
        
        # 如果提供了user_names，使用提供的名单
        # 否则从群成员列表获取
        if user_names is None and self.chat_id:
            member_info = self.get_chat_members_info()
            if member_info:
                user_names = [m['name'] for m in member_info]
                # 构建姓名到open_id的映射
                user_id_map = {m['name']: m['open_id'] for m in member_info}
            else:
                self.log.warning("群成员列表为空")
                user_names = []
        
        if not user_names:
            self.log.error("没有可检查的人员名单")
            return {
                'all_filled': True,
                'filled': [],
                'not_filled': [],
                'on_leave': [],
                'exception_day': [],
                'is_holiday': False,
                'fill_rate': 1.0
            }
        
        self.log.info(f"正在检查 {date_str} 的工时填写情况...")
        
        result = self.bitable.check_users_filled(
            user_names=user_names,
            date_str=date_str,
            exceptions=self.exceptions,
            external_user_id_map=user_id_map  # 传递外部的user_id映射
        )
        
        return result
    
    def check_month_summary(self, month: int = None, user_names: List[str] = None) -> Dict[str, Any]:
        """
        检查一个月的工时填写情况
        
        Args:
            month: 月份（1-12），默认为当前月
            user_names: 人员名单列表（可选），如果不提供则从群成员列表获取
        
        Returns:
            月总结字典，包含每天的填写情况和统计
        
        说明:
            汇报周期为：上个月28日 到 这个月27日
            例如：month=10 → 查询 9月28日 到 10月27日
        
        Examples:
            check_month_summary(month=10)  # 查询 09-28 到 10-27
            check_month_summary(month=11)  # 查询 10-28 to 11-27
            check_month_summary()          # 查询当前月
        """
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        
        # 确定年份和月份
        if month is None:
            month = now.month
            year = now.year
        else:
            year = now.year
            # 如果指定的月份小于当前月份，可能是查询去年的数据
            # 但一般情况下，我们假设查询的是今年的月份
        
        # 计算结束日期（指定月份的27日）
        end_date = datetime(year, month, 27, tzinfo=tz)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 计算开始日期（上个月的28日）
        if month == 1:
            start_month = 12
            start_year = year - 1
        else:
            start_month = month - 1
            start_year = year
        
        # 固定为上个月的28日
        start_date = datetime(start_year, start_month, 28, tzinfo=tz)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # 获取人员名单和user_id映射
        user_id_map = {}
        if user_names is None and self.chat_id:
            member_info = self.get_chat_members_info()
            if member_info:
                user_names = [m['name'] for m in member_info]
                user_id_map = {m['name']: m['open_id'] for m in member_info}
            else:
                self.log.warning("群成员列表为空")
                user_names = []
        
        if not user_names:
            self.log.error("没有可统计的人员名单")
            return None
        
        self.log.info(f"正在检查 {start_date_str} 至 {end_date_str} 的工时填写情况...")
        
        # 检查每一天的填写情况
        daily_results = {}
        user_fill_count = defaultdict(int)  # 每个人填写的天数
        user_info_map = {}  # 存储用户信息（用于@人）
        total_work_days = 0
        
        # 遍历日期范围内的每一天
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            result = self.bitable.check_users_filled(
                user_names=user_names,
                date_str=date_str,
                exceptions=self.exceptions,
                external_user_id_map=user_id_map  # 传递user_id映射
            )
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
            
            current_date += timedelta(days=1)
        
        # 如果user_info_map为空，使用传入的user_id_map
        if not user_info_map and user_id_map:
            user_info_map = user_id_map
        
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
            'start_date': start_date_str,
            'end_date': end_date_str,
            'total_work_days': total_work_days,
            'daily_results': daily_results,
            'all_users': list(all_users),
            'perfect_users': sorted(perfect_users),
            'partial_users': sorted(partial_users, key=lambda x: x['days'], reverse=True),
            'never_filled_users': sorted(never_filled_users),
            'user_info_map': user_info_map,  # 用于@功能的用户ID映射
            'total_users': len(all_users),
            'perfect_count': len(perfect_users),
            'partial_count': len(partial_users),
            'never_filled_count': len(never_filled_users)
        }
        
        self.log.success(f"月总结完成: {total_work_days} 个工作日, {len(all_users)} 人, 全勤 {len(perfect_users)} 人")
        
        return summary

class LaborHourPublisher:
    """工时检查结果发布器 - 通过飞书应用发送到群组"""
    
    def __init__(self, client: FeishuClient, chat_id: str):
        """
        初始化工时发布器
        
        Args:
            client: FeishuClient实例
            chat_id: 飞书群聊ID
        """
        # 初始化日志
        self.log = set_stage(Stage.MESSAGE_SEND)
        
        self.client = client
        self.chat_id = chat_id
        
        # 初始化Message API
        self.message_api = MessageAPI(client)
        
        # hero.jpg 图片的路径（相对于此文件）
        self.hero_image_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'hero.jpg'
        )
        
        self.log.success(f"工时发布器初始化成功 (使用飞书应用发送)")
    
    def create_labor_hour_card(self, result: Dict[str, Any], date: str, bitable_url: str = None) -> Dict[str, Any]:
        """创建工时填写情况卡片"""
        
        # 标题固定使用橙黄色
        header_template = "orange"
        
        # 构建卡片元素
        elements = []
        
        # 添加头图
        # 注意：需要将 hero.jpg 上传到图床，或使用飞书图片 URL
        # 临时使用文本替代，等待配置图片 URL
        hero_image_url = "img_v3_02rf_b04562b9-99ec-4585-b30f-c4f28d9f609g"  # 请替换为实际的图片 URL
        
        elements.append({
            "tag": "img",
            "img_key": hero_image_url,
            "mode": "fit_horizontal",
            "preview": False
        })
        
        # 统计信息和提示文案合并
        total = len(result['filled']) + len(result['not_filled'])
        filled = len(result['filled'])
        
        # 未填写人员列表 - 使用@功能
        if result['not_filled']:
            # 添加合并的提示文案
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"** 请以下同学尽快填写工时（已填写{filled}/{total}人）：**",
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
    
    def send_card(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """发送卡片到飞书群组"""
        try:
            # 使用 MessageAPI 发送卡片
            result = self.message_api.send_card_to_group(card['card'], self.chat_id)
            
            if result and result.get('code') == 0:
                self.log.success(f"工时检查结果发送成功")
            else:
                self.log.error(f"工时检查结果发送失败: {result}")
            
            return result
            
        except Exception as e:
            self.log.error(f"发送卡片时发生错误: {e}")
            raise e
    
    def publish_check_result(self, result: Dict[str, Any], date: str, bitable_url: str = None) -> Optional[Dict[str, Any]]:
        """发布工时检查结果，如果是节假日或全部已填写则不发送"""
        # 如果是节假日，不发送消息
        if result.get('is_holiday'):
            self.log.info(f"{date} 是节假日，跳过发送消息")
            return None
        
        # 如果所有人都已填写，不发送消息
        if not result.get('not_filled'):
            self.log.success(f"所有人都已填写工时，跳过发送消息")
            return None
        
        # 创建并发送卡片
        card = self.create_labor_hour_card(result, date, bitable_url)
        return self.send_card(card)
    
    def create_month_summary_card(self, summary: Dict[str, Any], bitable_url: str = None, mention_users: List[str] = None) -> Dict[str, Any]:
        """创建月度总结卡片"""
        
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
                "content": f"**本月工作日: {total_work_days} 天**\n**总人数: {summary['total_users']} 人**",
                "tag": "lark_md"
            }
        })
        
        elements.append({"tag": "hr"})
        
        # 全勤人员（不@）
        if perfect_users:
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**✨ 全勤人员 ({len(perfect_users)}人)**",
                    "tag": "lark_md"
                }
            })
            
            perfect_content = "  ".join(perfect_users)
            elements.append({
                "tag": "div",
                "text": {
                    "content": perfect_content,
                    "tag": "lark_md"
                }
            })
            
            elements.append({"tag": "hr"})
        
        # 缺少填写人员（部分填写 + 完全未填写，全部@）
        incomplete_users = partial_users + [{'name': name, 'days': 0, 'total': total_work_days} for name in never_filled_users]
        if incomplete_users:
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**⚠️ 部分填写人员 ({len(incomplete_users)}人)**",
                    "tag": "lark_md"
                }
            })
            
            incomplete_content = ""
            for user_info in incomplete_users:
                name = user_info['name']
                days = user_info['days']
                total = user_info['total']
                user_id = user_info_map.get(name, '')
                
                if user_id:
                    incomplete_content += f"<at id={user_id}></at>({days}/{total})  "
                else:
                    incomplete_content += f"{name}({days}/{total})  "
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": incomplete_content,
                    "tag": "lark_md"
                }
            })
            
            elements.append({"tag": "hr"})
        
        # 填写率统计
        fill_rate = len(perfect_users) / len(summary['all_users']) if summary['all_users'] else 0
        elements.append({
            "tag": "div",
            "text": {
                "content": f"**📊 整体填写率: {fill_rate*100:.1f}%**",
                "tag": "lark_md"
            }
        })
        
        # cc: @提醒人员（如刘华鑫）
        if mention_users:
            elements.append({"tag": "hr"})
            mention_content = "cc: "
            for name in mention_users:
                user_id = user_info_map.get(name, '')
                if user_id:
                    mention_content += f"<at id={user_id}></at>  "
                else:
                    mention_content += f"{name}  "
            
            elements.append({
                "tag": "div",
                "text": {
                    "content": mention_content,
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
                        "content": f"📅 工时月报｜{start_date} ~ {end_date}",
                        "tag": "plain_text"
                    }
                },
                "elements": elements
            }
        }
        
        return card
    
    def publish_month_summary(self, summary: Dict[str, Any], bitable_url: str = None, mention_users: List[str] = None) -> Dict[str, Any]:
        """发布月度总结"""
        card = self.create_month_summary_card(summary, bitable_url, mention_users)
        return self.send_card(card)


class LaborHourService:
    """工时检查服务 - 整合检查和发布功能"""
    
    def __init__(self, app_id: str, app_secret: str, bitable_url: str, 
                 chat_id: str, leave_approval_code: str = None, exclude_members: list = None, exceptions: dict = None):
        """
        初始化工时检查服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            bitable_url: 多维表格URL
            chat_id: 群聊ID
            leave_approval_code: 请假审批定义编码（可选，用于自动检测请假状态）
            exclude_members: 排除成员列表（可选，这些成员完全不参与工时检查）
            exceptions: 例外日期配置，格式: {"姓名": ["星期一", "星期二"]}
        """
        # 初始化日志
        self.log = set_stage(Stage.LABOR_CHECK)
        
        # 初始化飞书客户端
        feishu_client = FeishuClient(app_id, app_secret)
        
        self.checker = LaborHourChecker(app_id, app_secret, bitable_url, leave_approval_code, chat_id, exclude_members, exceptions)
        self.publisher = LaborHourPublisher(feishu_client, chat_id)
        
        self.log.success(f"工时检查服务初始化完成")
    
    def run_check_and_publish(self, date_str: str = None) -> Dict[str, Any]:
        """
        运行工时检查并发布结果
        
        Args:
            date_str: 检查日期，格式 YYYY-MM-DD，默认为今天
        
        Returns:
            检查结果
        """
        self.log.info("=" * 80)
        self.log.info(f"开始执行工时检查")
        
        # 获取检查日期
        if not date_str:
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            date_str = now.strftime('%Y-%m-%d')
        
        self.log.info(f"   检查日期: {date_str}")
        
        try:
            # 1. 检查工时填写情况
            result = self.checker.check_users_filled(date_str)
            
            # 2. 打印结果
            if result.get('is_holiday'):
                self.log.info(f"\n{date_str} 是节假日，无需检查工时填写，跳过发送")
                self.log.info(f"\n工时检查完成")
                self.log.info("=" * 80)
                
                return {
                    "status": "success",
                    "date": date_str,
                    "result": result,
                    "sent": False,
                    "reason": "holiday"
                }
            
            self.log.info(f"\n检查结果:")
            self.log.info(f"   应填写人数: {len(result['filled']) + len(result['not_filled'])}")
            self.log.info(f"   已填写: {len(result['filled'])} 人")
            self.log.info(f"   未填写: {len(result['not_filled'])} 人")
            self.log.info(f"   填写率: {result['fill_rate']:.1%}")
            
            # 如果所有人都已填写，跳过发送
            if not result.get('not_filled'):
                self.log.info(f"\n所有人都已填写工时，跳过发送消息")
                self.log.info(f"\n工时检查完成")
                self.log.info("=" * 80)
                
                return {
                    "status": "success",
                    "date": date_str,
                    "result": result,
                    "sent": False,
                    "reason": "all_filled"
                }
            
            # 3. 发布到飞书群组
            self.log.info(f"\n正在发送结果到飞书群组...")
            bitable_url = self.checker.get_bitable_url()
            self.log.info(f"   Bitable URL: {bitable_url}")
            response = self.publisher.publish_check_result(result, date_str, bitable_url)
            
            self.log.info(f"\n工时检查完成")
            self.log.info("=" * 80)
            
            return {
                "status": "success",
                "date": date_str,
                "result": result,
                "sent": response and response.get('code') == 0
            }
            
        except Exception as e:
            self.log.info(f"\n工时检查失败: {e}")
            self.log.info("=" * 80)
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "date": date_str,
                "message": str(e)
            }
    
    def run_month_summary_and_publish(self, month: int = None, mention_users: List[str] = None) -> Dict[str, Any]:
        """
        运行月度总结并发布
        
        Args:
            month: 月份（1-12），默认为当前月
            mention_users: 需要@的人员名单列表
        
        Returns:
            月总结结果
        
        Examples:
            run_month_summary_and_publish(month=10)  # 查询 09-28 到 10-27
        """
        self.log.info("=" * 80)
        self.log.info(f"开始执行月度总结")
        
        try:
            # 1. 检查月度总结
            summary = self.checker.check_month_summary(month)
            
            # 2. 打印结果
            self.log.info(f"\n月度总结:")
            self.log.info(f"   周期: {summary['start_date']} ~ {summary['end_date']}")
            self.log.info(f"   工作日: {summary['total_work_days']} 天")
            self.log.info(f"   总人数: {summary['total_users']} 人")
            self.log.info(f"   全勤: {summary['perfect_count']} 人")
            self.log.info(f"   部分填写: {summary['partial_count']} 人")
            self.log.info(f"   完全未填写: {summary['never_filled_count']} 人")
            
            # 3. 发布到飞书群组
            self.log.info(f"\n正在发送月度总结到飞书群组...")
            bitable_url = self.checker.get_bitable_url()
            response = self.publisher.publish_month_summary(summary, bitable_url, mention_users)
            
            self.log.info(f"\n月度总结完成")
            self.log.info("=" * 80)
            
            return {
                "status": "success",
                "summary": summary,
                "sent": response and response.get('code') == 0
            }
            
        except Exception as e:
            self.log.info(f"\n月度总结失败: {e}")
            self.log.info("=" * 80)
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
    
    配置文件路径: backend/src/config/labor_hour.yaml
    """
    log = set_stage(Stage.CONFIG)
    
    try:
        # 读取配置文件
        # 从 src/service/feishu/ 回到 src/config/
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'config',
            'labor_hour.yaml'
        )
        
        log.info(f"正在加载配置文件: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        log.success("配置文件加载成功")
        
        # 提取配置
        app_id = config['feishu']['app_id']
        app_secret = config['feishu']['app_secret']
        bitable_url = config['bitable']['url']
        chat_id = config.get('group_chat', {}).get('chat_id')
        exclude_members = config.get('group_chat', {}).get('exclude_members', [])
        exceptions = config.get('group_chat', {}).get('exceptions', {})
        
        if not chat_id:
            log.error("配置文件中缺少 group_chat.chat_id")
            return None
        
        # 从 approval.yaml 读取请假审批编码
        leave_approval_code = None
        try:
            approval_config_path = os.path.join(os.path.dirname(config_path), 'approval.yaml')
            if os.path.exists(approval_config_path):
                with open(approval_config_path, 'r', encoding='utf-8') as f:
                    approval_config = yaml.safe_load(f)
                    leave_codes = approval_config.get('approval_codes', {}).get('leave', [])
                    if leave_codes:
                        leave_approval_code = leave_codes[0]  # 取第一个请假审批编码
        except Exception as e:
            log.warning(f"读取 approval.yaml 失败: {e}，将不进行请假状态检测")
        
        # 创建服务实例
        service = LaborHourService(
            app_id=app_id,
            app_secret=app_secret,
            bitable_url=bitable_url,
            chat_id=chat_id,
            leave_approval_code=leave_approval_code,
            exclude_members=exclude_members,
            exceptions=exceptions
        )
        
        # 运行检查
        result = service.run_check_and_publish(date_str)
        
        return result
        
    except FileNotFoundError:
        log.error(f"配置文件不存在: {config_path}")
        log.warning("请创建配置文件 backend/src/config/labor_hour.yaml")
        return None
    except Exception as e:
        log.exception(f"执行失败: {e}")
        return None


class LaborHourManager:
    """工时管理器 - 提供简洁的调用接口"""
    
    @classmethod
    def check(cls, date_str: str = None, offset: int = None) -> Dict[str, Any]:
        """
        检查工时填写情况并发送提醒
        
        Args:
            date_str: 基准日期，格式 YYYY-MM-DD（可选）
            offset: 日期偏移量，-1=昨天，0=今天，1=明天（可选）
        
        Returns:
            检查结果字典
        """
        tz = pytz.timezone('Asia/Shanghai')
        
        # 确定基准日期
        if date_str:
            # 解析提供的日期字符串
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
            base_date = tz.localize(base_date)
        else:
            # 使用今天作为基准
            base_date = datetime.now(tz)
        
        # 应用偏移量
        if offset is not None:
            target_date = base_date + timedelta(days=offset)
        else:
            target_date = base_date
        
        # 转换为日期字符串
        final_date_str = target_date.strftime('%Y-%m-%d')
        
        return run_labor_hour_check_from_config(final_date_str)
    
    @classmethod
    def monthly_summary(cls, month: int = None, mention_users: list = None) -> Dict[str, Any]:
        """
        生成月度工时总结
        
        Args:
            month: 月份（1-12），默认为当前月
            mention_users: 需要 @ 的用户列表
        
        Returns:
            总结结果字典
        
        Examples:
            # 生成当前月的总结
            result = LaborHourManager.monthly_summary()
            
            # 生成10月的总结（09-28 到 10-27）并 @ 用户
            result = LaborHourManager.monthly_summary(
                month=10,
                mention_users=['刘华鑫']
            )
        """
        log = set_stage(Stage.CONFIG)
        
        try:
            # 读取配置文件
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config',
                'labor_hour.yaml'
            )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 从 approval.yaml 读取请假审批编码
            leave_approval_code = None
            try:
                approval_config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    'config',
                    'approval.yaml'
                )
                if os.path.exists(approval_config_path):
                    with open(approval_config_path, 'r', encoding='utf-8') as f:
                        approval_config = yaml.safe_load(f)
                        leave_codes = approval_config.get('approval_codes', {}).get('leave', [])
                        if leave_codes:
                            leave_approval_code = leave_codes[0]
            except Exception as e:
                log.warning(f"读取 approval.yaml 失败: {e}，将不进行请假状态检测")
            
            # 创建服务实例
            service = LaborHourService(
                app_id=config['feishu']['app_id'],
                app_secret=config['feishu']['app_secret'],
                bitable_url=config['bitable']['url'],
                chat_id=config['group_chat']['chat_id'],
                leave_approval_code=leave_approval_code,
                exclude_members=config.get('group_chat', {}).get('exclude_members', []),
                exceptions=config.get('group_chat', {}).get('exceptions', {})
            )
            
            # 运行月度总结
            result = service.run_month_summary_and_publish(
                month=month,
                mention_users=mention_users
            )
            
            return result
            
        except Exception as e:
            log.exception(f"月度总结失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


if __name__ == '__main__':
    # 默认检查今天
    result = LaborHourManager.check()
    print(f"检查结果: {result.get('status')}")

