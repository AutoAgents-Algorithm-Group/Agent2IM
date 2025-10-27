"""
审批事件处理服务

监听飞书审批事件，当审批通过时自动创建请假日历
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

from src.utils.feishu.client import FeishuClient


class ApprovalService:
    """审批服务 - 处理审批事件并创建请假日历"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化审批服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.client = FeishuClient(app_id=app_id, app_secret=app_secret)
        
        print(f"✅ 审批服务初始化成功")
    
    def handle_approval_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理审批事件
        
        Args:
            event_data: 审批事件数据
        
        Returns:
            处理结果
        """
        try:
            # 获取事件类型
            event_type = event_data.get('event', {}).get('type')
            
            if event_type == 'approval_instance':
                # 审批实例事件
                return self._handle_approval_instance(event_data)
            else:
                print(f"⚠️ 未知的审批事件类型: {event_type}")
                return {"status": "ignored", "reason": f"unknown event type: {event_type}"}
                
        except Exception as e:
            print(f"❌ 处理审批事件失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _handle_approval_instance(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理审批实例事件
        
        Args:
            event_data: 审批事件数据
        
        Returns:
            处理结果
        """
        try:
            event = event_data.get('event', {})
            
            # 获取审批状态
            status = event.get('status')
            
            # 只处理审批通过的情况
            if status != 'APPROVED':
                print(f"⏭️ 审批状态为 {status}，跳过处理")
                return {"status": "ignored", "reason": f"approval status is {status}"}
            
            print(f"✅ 收到审批通过事件")
            
            # 获取审批定义编码（用于判断是否是请假审批）
            approval_code = event.get('approval_code', '')
            
            # 请假审批白名单（只处理这些审批类型）
            LEAVE_APPROVAL_CODES = [
                'A9D489DC-5F55-4418-99F1-01E1CE734CA1',  # HR小助手 - 请假申请
            ]
            
            # 只处理白名单中的审批类型
            if approval_code and approval_code not in LEAVE_APPROVAL_CODES:
                print(f"⏭️ 审批类型 {approval_code} 不在处理范围内，跳过")
                return {"status": "ignored", "reason": f"approval_code {approval_code} not in whitelist"}
            
            # 获取审批实例编码
            instance_code = event.get('instance_code', '')
            
            # 获取申请人信息
            user_id = event.get('user_id', '')
            open_id = event.get('open_id', '')
            
            print(f"📋 审批信息:")
            print(f"   审批定义: {approval_code}")
            print(f"   实例编码: {instance_code}")
            print(f"   申请人: {user_id} / {open_id}")
            
            # 获取审批详情以提取请假信息
            approval_detail = self._get_approval_detail(instance_code)
            
            if not approval_detail:
                return {"status": "error", "message": "无法获取审批详情"}
            
            # 提取请假信息
            leave_info = self._extract_leave_info(approval_detail)
            
            if not leave_info:
                print(f"⚠️ 未能从审批中提取到请假信息")
                return {"status": "ignored", "reason": "not a leave approval"}
            
            # 创建请假日历
            calendar_result = self._create_timeoff_event(
                user_id=leave_info['user_id'],
                start_time=leave_info['start_time'],
                end_time=leave_info['end_time'],
                title=leave_info.get('title', '请假中(全天) / Time Off'),
                description=leave_info.get('description', '请假审批已通过')
            )
            
            if calendar_result.get('status') == 'success':
                print(f"✅ 请假日历创建成功")
                return {
                    "status": "success",
                    "message": "请假日历创建成功",
                    "calendar_event_id": calendar_result.get('event_id')
                }
            else:
                return calendar_result
                
        except Exception as e:
            print(f"❌ 处理审批实例事件失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _get_approval_detail(self, instance_code: str) -> Optional[Dict[str, Any]]:
        """
        获取审批详情
        
        Args:
            instance_code: 审批实例编码
        
        Returns:
            审批详情
        """
        try:
            token = self.client.get_tenant_access_token()
            
            url = f"https://open.feishu.cn/open-apis/approval/v4/instances/{instance_code}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get('code') == 0:
                return result.get('data', {})
            else:
                print(f"❌ 获取审批详情失败: {result.get('msg')}")
                return None
                
        except Exception as e:
            print(f"❌ 获取审批详情异常: {e}")
            return None
    
    def _extract_leave_info(self, approval_detail: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从审批详情中提取请假信息
        
        Args:
            approval_detail: 审批详情
        
        Returns:
            请假信息 {user_id, start_time, end_time, title, description}
        """
        try:
            # 获取审批表单
            form = approval_detail.get('form', [])
            
            leave_info = {
                'user_id': approval_detail.get('open_id', ''),
                'start_time': None,
                'end_time': None,
                'title': '请假中(全天) / Time Off',
                'description': '请假审批已通过'
            }
            
            # 从表单中提取请假信息
            for field in form:
                field_id = field.get('id', '')
                field_type = field.get('type', '')
                field_value = field.get('value', '')
                
                # 请假开始时间
                if 'start' in field_id.lower() or '开始' in field.get('name', ''):
                    if field_type == 'dateInterval':
                        # 日期区间类型
                        try:
                            value_obj = json.loads(field_value) if isinstance(field_value, str) else field_value
                            leave_info['start_time'] = value_obj.get('start')
                            leave_info['end_time'] = value_obj.get('end')
                        except:
                            pass
                    elif field_type == 'date':
                        leave_info['start_time'] = field_value
                
                # 请假结束时间
                elif 'end' in field_id.lower() or '结束' in field.get('name', ''):
                    if field_type == 'date':
                        leave_info['end_time'] = field_value
                
                # 请假原因
                elif 'reason' in field_id.lower() or '原因' in field.get('name', ''):
                    leave_info['description'] = f"请假原因: {field_value}"
            
            # 验证必填字段
            if leave_info['start_time'] and leave_info['end_time'] and leave_info['user_id']:
                return leave_info
            else:
                print(f"⚠️ 请假信息不完整: {leave_info}")
                return None
                
        except Exception as e:
            print(f"❌ 提取请假信息失败: {e}")
            return None
    
    def _create_timeoff_event(self, user_id: str, start_time: str, end_time: str, 
                             title: str, description: str) -> Dict[str, Any]:
        """
        创建请假日历事件
        
        Args:
            user_id: 用户ID (open_id)
            start_time: 开始时间 (YYYY-MM-DD 或时间戳)
            end_time: 结束时间 (YYYY-MM-DD 或时间戳)
            title: 日程标题
            description: 日程描述
        
        Returns:
            创建结果
        """
        try:
            token = self.client.get_tenant_access_token()
            
            url = "https://open.feishu.cn/open-apis/calendar/v4/timeoff_events"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 转换时间格式为时间戳（秒级）
            start_timestamp = self._convert_to_timestamp(start_time)
            end_timestamp = self._convert_to_timestamp(end_time)
            
            data = {
                "user_id": user_id,
                "timezone": "Asia/Shanghai",
                "start_time": str(start_timestamp),
                "end_time": str(end_timestamp),
                "title": title,
                "description": description
            }
            
            print(f"📅 创建请假日历:")
            print(f"   用户: {user_id}")
            print(f"   开始: {start_time} ({start_timestamp})")
            print(f"   结束: {end_time} ({end_timestamp})")
            
            response = requests.post(
                f"{url}?user_id_type=open_id",
                headers=headers,
                json=data
            )
            
            result = response.json()
            
            if result.get('code') == 0:
                event_id = result.get('data', {}).get('timeoff_event_id', '')
                print(f"✅ 请假日历创建成功: {event_id}")
                return {
                    "status": "success",
                    "event_id": event_id
                }
            else:
                print(f"❌ 创建请假日历失败: {result.get('msg')}")
                print(f"   详情: {result}")
                return {
                    "status": "error",
                    "message": result.get('msg'),
                    "code": result.get('code')
                }
                
        except Exception as e:
            print(f"❌ 创建请假日历异常: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _convert_to_timestamp(self, time_str: str) -> int:
        """
        转换时间为时间戳（秒级）
        
        Args:
            time_str: 时间字符串 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 或时间戳)
        
        Returns:
            时间戳（秒）
        """
        try:
            # 如果已经是时间戳，直接返回
            if time_str.isdigit():
                return int(time_str)
            
            # 解析日期字符串
            tz = pytz.timezone('Asia/Shanghai')
            
            if ' ' in time_str:
                # 包含时间
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            else:
                # 只有日期，设置为当天00:00:00
                dt = datetime.strptime(time_str, '%Y-%m-%d')
            
            # 添加时区信息
            dt = tz.localize(dt)
            
            # 转换为时间戳
            return int(dt.timestamp())
            
        except Exception as e:
            print(f"❌ 时间格式转换失败: {time_str}, {e}")
            # 返回当前时间戳作为fallback
            return int(datetime.now().timestamp())


def create_approval_service_from_config(config_path: str = None) -> ApprovalService:
    """
    从配置文件创建审批服务实例
    
    Args:
        config_path: 配置文件路径，默认为 backend/src/config/labor_hour.json
    
    Returns:
        ApprovalService 实例
    """
    import os
    
    if config_path is None:
        # 默认使用工时配置文件中的 feishu 配置
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'labor_hour.json'
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    app_id = config['feishu']['app_id']
    app_secret = config['feishu']['app_secret']
    
    return ApprovalService(app_id=app_id, app_secret=app_secret)

