"""
定时任务具体实现
"""

import datetime
import pytz
from typing import List, Dict


class ReminderTasks:
    """提醒任务实现"""
    
    def __init__(self, feishu_service, config_loader, config):
        """
        初始化提醒任务
        
        Args:
            feishu_service: 飞书服务实例
            config_loader: 配置加载器
            config: 任务配置
        """
        self.feishu_service = feishu_service
        self.config_loader = config_loader
        self.task_config = config.get('task', {})
        self.message_config = config.get('message', {})
        self.people_config = config.get('people', {})
        
        # 从任务配置中提取信息
        self.group_chat_id = self.task_config.get("config", {}).get("group_chat_id")
        self.form_url = self.task_config.get("config", {}).get("form_url")
        self.timezone = self.task_config.get("config", {}).get("timezone", "Asia/Shanghai")
        self.bitable_app_token = self.task_config.get("config", {}).get("bitable_app_token", "")
        self.bitable_table_id = self.task_config.get("config", {}).get("bitable_table_id", "")
    
    def create_reminder_card(self, template_id: str, user_name: str) -> dict:
        """根据模板创建提醒卡片"""
        try:
            from ..feishu.card import CardBuilder
            
            # 获取消息模板
            templates = self.message_config.get("templates", {})
            template = templates.get(template_id, {})
            
            if not template:
                print(f"⚠️ 未找到消息模板: {template_id}")
                return {}
            
            # 获取当前时间
            tz = pytz.timezone(self.timezone)
            now = datetime.datetime.now(tz)
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            current_date = now.strftime("%Y-%m-%d")
            
            # 如果是早上10点的提醒，日期应该是昨天
            if template_id == "morning_makeup":
                yesterday = now - datetime.timedelta(days=1)
                current_date = yesterday.strftime("%Y-%m-%d")
            
            # 替换变量
            content = template.get("content", "").format(
                user_name=user_name,
                time=current_time,
                date=current_date,
                form_url=self.form_url
            )
            
            footer = template.get("footer", "").format(
                time=current_time,
                date=current_date
            )
            
            # 使用卡片构建器
            button = template.get("button", {})
            card = CardBuilder.create_reminder_card(
                title=template.get("title", "提醒"),
                content=content,
                footer=footer,
                button_text=button.get("text", "立即填写"),
                button_url=button.get("url", "").format(form_url=self.form_url),
                button_type=button.get("type", "primary"),
                template_color="red" if template_id == "evening_second" else "blue"
            )
            
            return card
            
        except Exception as e:
            print(f"❌ 创建提醒卡片失败: {e}")
            return {}
    
    def get_active_people(self) -> List[Dict]:
        """获取活跃的人员列表"""
        try:
            people = self.people_config.get("people", [])
            active_people = [p for p in people if p.get("active", True)]
            print(f"📋 活跃人员数量: {len(active_people)}")
            return active_people
        except Exception as e:
            print(f"❌ 获取人员列表失败: {e}")
            return []
    
    def should_remind_today(self, person: Dict) -> bool:
        """判断今天是否需要提醒该人员"""
        try:
            tz = pytz.timezone(self.timezone)
            now = datetime.datetime.now(tz)
            weekday = now.strftime("%A").lower()
            weekday_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
            
            # 检查例外日期
            exceptions = person.get("exceptions", [])
            if weekday_cn in exceptions or weekday in exceptions:
                print(f"ℹ️ {person.get('name')} 今天是例外日期，跳过提醒")
                return False
            
            # 检查频率设置
            frequency = person.get("frequency", "")
            if frequency:
                frequency_lower = frequency.lower()
                if weekday not in frequency_lower:
                    print(f"ℹ️ {person.get('name')} 今天不在提醒频率内，跳过提醒")
                    return False
            
            return True
        except Exception as e:
            print(f"❌ 判断提醒日期失败: {e}")
            return True
    
    def get_unfilled_users(self, check_date: str = "today") -> List[Dict]:
        """获取未填写表格的用户列表"""
        try:
            active_people = self.get_active_people()
            
            tz = pytz.timezone(self.timezone)
            now = datetime.datetime.now(tz)
            
            if check_date == "yesterday":
                check_datetime = now - datetime.timedelta(days=1)
            else:
                check_datetime = now
            
            date_str = check_datetime.strftime("%Y-%m-%d")
            
            unfilled_users = []
            
            for person in active_people:
                if not self.should_remind_today(person):
                    continue
                
                user_id = person.get("user_id", "")
                if not user_id:
                    continue
                
                # 检查是否已填写
                if self.bitable_app_token and self.bitable_table_id:
                    has_filled = self.feishu_service.bitable.check_user_filled(
                        self.bitable_app_token,
                        self.bitable_table_id,
                        user_id,
                        date_str
                    )
                    
                    if not has_filled:
                        unfilled_users.append(person)
                else:
                    unfilled_users.append(person)
            
            print(f"📊 未填写表格的用户数量: {len(unfilled_users)} (检查日期: {date_str})")
            return unfilled_users
            
        except Exception as e:
            print(f"❌ 获取未填写用户列表失败: {e}")
            return []
    
    def evening_first_reminder(self):
        """任务1: 晚上9点群聊提醒"""
        try:
            print(f"\n⏰ 执行任务: 晚上9点群聊提醒")
            
            unfilled_users = self.get_unfilled_users(check_date="today")
            
            if not unfilled_users:
                print("✅ 所有用户都已填写表格，无需提醒")
                return
            
            for user in unfilled_users:
                user_name = user.get("name", "用户")
                user_id = user.get("user_id", "")
                
                card = self.create_reminder_card("evening_first", user_name)
                
                if card and user_id and self.group_chat_id:
                    self.feishu_service.message.send_card_with_mention(
                        card, 
                        self.group_chat_id, 
                        [user_id]
                    )
                    print(f"✅ 已向 {user_name} 发送群聊提醒")
            
            print(f"✅ 晚上9点群聊提醒任务完成，共提醒 {len(unfilled_users)} 人")
            
        except Exception as e:
            print(f"❌ 晚上9点群聊提醒任务失败: {e}")
    
    def evening_second_reminder(self):
        """任务2: 晚上11点私信提醒"""
        try:
            print(f"\n⏰ 执行任务: 晚上11点私信提醒")
            
            unfilled_users = self.get_unfilled_users(check_date="today")
            
            if not unfilled_users:
                print("✅ 所有用户都已填写表格，无需提醒")
                return
            
            for user in unfilled_users:
                user_name = user.get("name", "用户")
                user_id = user.get("user_id", "")
                
                card = self.create_reminder_card("evening_second", user_name)
                
                if card and user_id:
                    self.feishu_service.message.send_private_card(card, user_id)
                    print(f"✅ 已向 {user_name} 发送私信提醒")
            
            print(f"✅ 晚上11点私信提醒任务完成，共提醒 {len(unfilled_users)} 人")
            
        except Exception as e:
            print(f"❌ 晚上11点私信提醒任务失败: {e}")
    
    def morning_makeup_reminder(self):
        """任务3: 第二天早上10点群聊补填提醒"""
        try:
            print(f"\n⏰ 执行任务: 早上10点群聊补填提醒")
            
            unfilled_users = self.get_unfilled_users(check_date="yesterday")
            
            if not unfilled_users:
                print("✅ 所有用户都已填写表格，无需提醒")
                return
            
            for user in unfilled_users:
                user_name = user.get("name", "用户")
                user_id = user.get("user_id", "")
                
                card = self.create_reminder_card("morning_makeup", user_name)
                
                if card and user_id and self.group_chat_id:
                    self.feishu_service.message.send_card_with_mention(
                        card, 
                        self.group_chat_id, 
                        [user_id]
                    )
                    print(f"✅ 已向 {user_name} 发送群聊补填提醒")
            
            print(f"✅ 早上10点群聊补填提醒任务完成，共提醒 {len(unfilled_users)} 人")
            
        except Exception as e:
            print(f"❌ 早上10点群聊补填提醒任务失败: {e}")

