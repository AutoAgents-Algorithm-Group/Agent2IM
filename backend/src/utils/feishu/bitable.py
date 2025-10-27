"""
飞书多维表格API
"""

import re
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict, Any
import pytz


class BitableAPI:
    """飞书多维表格API"""
    
    def __init__(self, client, app_token: str = None, table_id: str = None, url: str = None, leave_approval_code: str = None):
        """
        初始化多维表格API
        
        Args:
            client: FeishuClient实例
            app_token: 多维表格的app_token（可选）
            table_id: 表格的table_id（可选）
            url: 飞书多维表格URL，如果提供则自动解析出app_token和table_id（可选）
            leave_approval_code: 请假审批定义编码，用于请假检测（可选）
            
        示例:
            # 方式1: 直接传入URL（推荐）
            >>> bitable = BitableAPI(client, url="https://xxx.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx")
            
            # 方式2: 分别传入参数
            >>> bitable = BitableAPI(client, app_token="UfDPbov0Eal3RpsWAEBcyfe1nAb", table_id="tbla3OuZeDczpqZx")
        """
        self.client = client
        self.leave_approval_code = leave_approval_code
    
        # 如果提供了URL，优先解析URL
        if url:
            params = self.parse_url(url)
            self.app_token = params['app_token']
            self.table_id = params['table_id']
        else:
            self.app_token = app_token
            self.table_id = table_id
    
    @staticmethod
    def convert_timestamp_to_date(timestamp_ms):
        """
        将飞书时间戳（毫秒）转换为日期时间字符串
        
        Args:
            timestamp_ms: 毫秒级时间戳
            
        Returns:
            格式化的日期时间字符串 (YYYY-MM-DD HH:MM:SS)
        """
        if isinstance(timestamp_ms, (int, float)) and timestamp_ms > 0:
            return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
        return timestamp_ms
    
    def _convert_fields_timestamps(self, fields: dict) -> dict:
        """
        自动转换字段中的时间戳为可读格式
        
        Args:
            fields: 记录的字段字典
            
        Returns:
            转换后的字段字典
        """
        converted_fields = {}
        for key, value in fields.items():
            # 如果字段名包含"时间"且值是毫秒级时间戳，进行转换
            if '时间' in key and isinstance(value, (int, float)) and value > 1000000000000:
                converted_fields[key] = self.convert_timestamp_to_date(value)
                converted_fields[f"{key}_原始"] = value  # 保留原始时间戳
            else:
                converted_fields[key] = value
        return converted_fields
    
    @staticmethod
    def parse_url(url: str) -> dict:
        """
        从飞书多维表格URL中解析参数
        
        Args:
            url: 飞书多维表格URL
            
        Returns:
            包含 app_token, table_id, view_id 的字典
            
        示例:
            >>> url = "https://xxx.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
            >>> params = BitableAPI.parse_url(url)
            >>> print(params['app_token'])  # UfDPbov0Eal3RpsWAEBcyfe1nAb
            >>> print(params['table_id'])   # tbla3OuZeDczpqZx
            >>> print(params['view_id'])    # vewGyZRz6D
        """
        result = {
            'app_token': None,
            'table_id': None,
            'view_id': None
        }
        
        try:
            # 解析URL
            parsed = urlparse(url)
            
            # 提取app_token: 在 /base/ 后面的部分
            path_match = re.search(r'/base/([^?/]+)', parsed.path)
            if path_match:
                result['app_token'] = path_match.group(1)
            
            # 解析查询参数
            query_params = parse_qs(parsed.query)
            
            # 提取table_id
            if 'table' in query_params:
                result['table_id'] = query_params['table'][0]
            
            # 提取view_id (可选)
            if 'view' in query_params:
                result['view_id'] = query_params['view'][0]
            
            return result
        except Exception as e:
            print(f"❌ 解析URL失败: {e}")
            return result
    
    def get_all_records(self, view_id: str = None, convert_timestamp: bool = True):
        """
        获取多维表格的所有记录（自动分页）
        
        Args:
            view_id: 视图ID（可选）
            convert_timestamp: 是否自动转换时间戳为日期格式，默认True
            
        Returns:
            所有记录的列表
        """
        if not self.app_token or not self.table_id:
            print("❌ 缺少app_token或table_id，请在初始化时设置")
            return []
        
        all_items = []
        page_token = None
        page_num = 0
        
        try:
            while True:
                page_num += 1
                access_token = self.client.get_access_token()
                url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                params = {"page_size": 500}  # 使用最大值
                if view_id:
                    params["view_id"] = view_id
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params)
                result = response.json()
                
                if result.get("code") == 0:
                    items = result.get('data', {}).get('items', [])
                    all_items.extend(items)
                    
                    # 检查是否有下一页
                    has_more = result.get('data', {}).get('has_more', False)
                    page_token = result.get('data', {}).get('page_token')
                    
                    print(f"  获取第 {page_num} 页，{len(items)} 条记录")
                    
                    if not has_more:
                        break
                else:
                    error_code = result.get("code")
                    error_msg = result.get("msg")
                    print(f"❌ 获取多维表格记录失败")
                    print(f"   错误代码: {error_code}")
                    print(f"   错误信息: {error_msg}")
                    return []
            
            # 如果需要转换时间戳
            if convert_timestamp:
                for item in all_items:
                    if 'fields' in item:
                        item['fields'] = self._convert_fields_timestamps(item['fields'])
            
            print(f"✅ 获取多维表格所有记录成功，共 {len(all_items)} 条")
            return all_items
            
        except Exception as e:
            print(f"❌ 获取多维表格记录失败: {e}")
            return []
    
    def get_records(self, view_id: str = None, page_size: int = 100, convert_timestamp: bool = True):
        """
        获取多维表格的记录列表
        
        Args:
            view_id: 视图ID（可选）
            page_size: 每页记录数，默认100
            convert_timestamp: 是否自动转换时间戳为日期格式，默认True
        """
        if not self.app_token or not self.table_id:
            print("❌ 缺少app_token或table_id，请在初始化时设置")
            return []
        
        try:
            access_token = self.client.get_access_token()
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"page_size": page_size}
            if view_id:
                params["view_id"] = view_id
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                items = result.get('data', {}).get('items', [])
                
                # 如果需要转换时间戳
                if convert_timestamp:
                    for item in items:
                        if 'fields' in item:
                            item['fields'] = self._convert_fields_timestamps(item['fields'])
                
                print(f"✅ 获取多维表格记录成功，共 {len(items)} 条")
                return items
            else:
                error_code = result.get("code")
                error_msg = result.get("msg")
                print(f"❌ 获取多维表格记录失败")
                print(f"   错误代码: {error_code}")
                print(f"   错误信息: {error_msg}")
                print(f"   完整响应: {result}")
                
                # 针对 91402 错误给出具体建议
                if error_code == 91402:
                    print("\n💡 解决建议：")
                    print("   1. 确认应用已开通多维表格权限（bitable:app:readonly）")
                    print("   2. 在飞书开发平台发布应用新版本")
                    print("   3. 在多维表格中添加此应用为协作者")
                    print("   4. 或使用以下URL授权：")
                    print(f"      https://open.feishu.cn/open-apis/authen/v1/authorize?app_id={self.client.app_id}&redirect_uri=https://open.feishu.cn&scope=bitable:app")
                
                return []
        except Exception as e:
            print(f"❌ 获取多维表格记录失败: {e}")
            return []
    
    def search_records(self, field_name: str, field_value: str):
        """
        搜索多维表格中的特定记录
        
        Args:
            field_name: 要搜索的字段名
            field_value: 要搜索的字段值
        """
        if not self.app_token or not self.table_id:
            print("❌ 缺少app_token或table_id，请在初始化时设置")
            return []
        
        try:
            access_token = self.client.get_access_token()
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/search"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "field_names": [field_name],
                "filter": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": field_name,
                            "operator": "is",
                            "value": [field_value]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                items = result.get('data', {}).get('items', [])
                print(f"✅ 搜索多维表格记录成功，找到 {len(items)} 条")
                return items
            else:
                print(f"❌ 搜索多维表格记录失败: {result}")
                return []
        except Exception as e:
            print(f"❌ 搜索多维表格记录失败: {e}")
            return []
    
    def get_records_by_date(self, date_field: str, start_date: str, end_date: str = None, convert_timestamp: bool = True):
        """
        根据日期范围获取记录
        
        Args:
            date_field: 日期字段名（如"记录时间"）
            start_date: 开始日期，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
            end_date: 结束日期，格式同上，如果不提供则只筛选start_date当天
            convert_timestamp: 是否自动转换时间戳为日期格式，默认True
            
        Returns:
            符合条件的记录列表
            
        示例:
            # 获取某一天的记录
            records = bitable.get_records_by_date("记录时间", "2025-09-30")
            
            # 获取日期范围的记录
            records = bitable.get_records_by_date("记录时间", "2025-09-01", "2025-09-30")
        """
        if not self.app_token or not self.table_id:
            print("❌ 缺少app_token或table_id，请在初始化时设置")
            return []
        
        try:
            # 转换日期为时间戳（毫秒）
            start_ts = int(datetime.strptime(start_date[:10], '%Y-%m-%d').timestamp() * 1000)
            
            if end_date:
                # 如果有结束日期，设置为当天23:59:59
                end_dt = datetime.strptime(end_date[:10], '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                end_ts = int(end_dt.timestamp() * 1000)
            else:
                # 如果没有结束日期，设置为开始日期当天23:59:59
                start_dt = datetime.strptime(start_date[:10], '%Y-%m-%d')
                end_dt = start_dt.replace(hour=23, minute=59, second=59)
                end_ts = int(end_dt.timestamp() * 1000)
            
            # 获取所有记录（自动分页，不转换时间戳，用于筛选）
            print(f"正在获取所有记录以筛选日期...")
            all_records = self.get_all_records(convert_timestamp=False)
            
            # 筛选符合日期范围的记录
            filtered_records = []
            for record in all_records:
                fields = record.get('fields', {})
                record_time = fields.get(date_field)
                
                if isinstance(record_time, (int, float)):
                    if start_ts <= record_time <= end_ts:
                        # 如果需要转换时间戳
                        if convert_timestamp:
                            record['fields'] = self._convert_fields_timestamps(fields)
                        filtered_records.append(record)
            
            print(f"✅ 根据日期筛选成功，找到 {len(filtered_records)} 条记录")
            return filtered_records
            
        except Exception as e:
            print(f"❌ 根据日期筛选记录失败: {e}")
            return []
    
    @staticmethod
    def get_weekday_name(date_str: str) -> str:
        """
        获取日期对应的星期几
        
        Args:
            date_str: 日期字符串，格式 YYYY-MM-DD
            
        Returns:
            星期几的中文名称，如"星期一"
        """
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return weekdays[date_obj.weekday()]
    
    @staticmethod
    def is_holiday(date_str: str) -> bool:
        """
        判断是否为节假日（包括周末和法定节假日）
        
        Args:
            date_str: 日期字符串，格式 YYYY-MM-DD
            
        Returns:
            bool: 是否为节假日
        """
        try:
            # 方式1: 使用免费的中国节假日API
            url = f"https://timor.tech/api/holiday/info/{date_str}"
            response = requests.get(url, timeout=5)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                raise Exception(f"API返回状态码 {response.status_code}")
            
            result = response.json()
            
            if result.get('code') == 0:
                holiday_info = result.get('type', {})
                # type.type: 0-工作日 1-周末 2-节假日 3-调休
                is_holiday = holiday_info.get('type', 0) in [1, 2]
                
                if is_holiday:
                    holiday_name = holiday_info.get('name', '周末')
                    print(f"📅 {date_str} 是{holiday_name}，无需检查")
                
                return is_holiday
            else:
                # API返回错误代码，fallback到本地判断
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                is_weekend = date_obj.weekday() >= 5  # 5=周六, 6=周日
                if is_weekend:
                    print(f"📅 {date_str} 是周末，无需检查")
                return is_weekend
                
        except Exception as e:
            # 静默处理API错误，使用本地判断
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            is_weekend = date_obj.weekday() >= 5
            if is_weekend:
                print(f"📅 {date_str} 是周末，无需检查")
            return is_weekend
    
    @staticmethod
    def load_people_from_config(config_path: str = None, date_str: str = None):
        """
        从配置文件加载人员名单（排除请假人员和例外日期人员）
        
        Args:
            config_path: 配置文件路径，默认为 backend/config/people.json
            date_str: 日期字符串，用于判断例外日期
            
        Returns:
            list: 应该检查的人员姓名列表
        """
        if not config_path:
            # 默认配置文件路径
            # bitable.py 在 backend/utils/feishu/ 下，需要往上3层到达 backend/
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config" / "people.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 获取当天是星期几
            weekday = BitableAPI.get_weekday_name(date_str) if date_str else None
            
            # 过滤人员：排除请假的和例外日期的
            active_people = []
            for person in config.get('people', []):
                # 跳过请假的人
                if person.get('off', False):
                    continue
                
                # 检查例外日期
                exceptions = person.get('exceptions', [])
                if weekday and weekday in exceptions:
                    print(f"  ℹ️ {person['name']} 在{weekday}无需填写（例外日期）")
                    continue
                
                active_people.append(person['name'])
            
            return active_people
        except Exception as e:
            print(f"❌ 加载人员配置失败: {e}")
            return []
    
    def check_user_on_leave(self, user_id: str, date_str: str) -> bool:
        """
        检查用户在指定日期是否请假（通过查询审批系统）
        
        Args:
            user_id: 用户 open_id
            date_str: 日期字符串，格式 YYYY-MM-DD
        
        Returns:
            bool: True 表示请假，False 表示未请假
        """
        try:
            # 转换日期为时间戳（毫秒）
            tz = pytz.timezone('Asia/Shanghai')
            check_date = datetime.strptime(date_str, '%Y-%m-%d')
            check_date = tz.localize(check_date)
            
            # 查询时间范围：前后各30天（单位：毫秒）
            start_date = check_date - timedelta(days=30)
            end_date = check_date + timedelta(days=30)
            start_timestamp = int(start_date.timestamp() * 1000)  # 毫秒级时间戳
            end_timestamp = int(end_date.timestamp() * 1000)      # 毫秒级时间戳
            
            # 调用飞书审批 API 查询用户的审批实例
            token = self.client.get_access_token()
            
            url = "https://open.feishu.cn/open-apis/approval/v4/instances"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 如果没有配置请假审批编码，跳过检查
            if not self.leave_approval_code:
                return False
            
            # 飞书审批 API 不支持按申请人过滤，需要查询所有记录后手动过滤
            # 为了提升性能，将时间范围缩小到7天，page_size 设为100
            # 前后各7天
            start_date_short = check_date - timedelta(days=7)
            end_date_short = check_date + timedelta(days=7)
            start_timestamp_short = int(start_date_short.timestamp() * 1000)
            end_timestamp_short = int(end_date_short.timestamp() * 1000)
            
            params = {
                "approval_code": self.leave_approval_code,
                "start_time": str(start_timestamp_short),
                "end_time": str(end_timestamp_short),
                "page_size": 100
            }
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            # 调试信息（生产环境可关闭）
            # print(f"   📋 请求URL: {url}")
            # print(f"   📋 请求参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
            # print(f"   📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查API返回的错误
            if result.get('code') != 0:
                error_msg = result.get('msg', 'Unknown error')
                print(f"   ⚠️ 审批API返回错误: code={result.get('code')}, msg={error_msg}")
                # print(f"   📋 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return False
            
            # 检查是否有审批实例编码
            instance_codes = result.get('data', {}).get('instance_code_list', [])
            if not instance_codes:
                print(f"   ℹ️ 该用户在查询时间范围内没有审批记录")
                return False  # 没有审批记录
            
            print(f"   📋 找到 {len(instance_codes)} 条审批记录")
            
            # 遍历每个审批实例，获取详情并判断请假时间
            # 如果找到匹配的请假记录，立即返回 True
            for idx, instance_code in enumerate(instance_codes, 1):
                try:
                    # 获取审批实例详情
                    detail_url = f"https://open.feishu.cn/open-apis/approval/v4/instances/{instance_code}"
                    detail_params = {"user_id_type": "open_id"}
                    detail_response = requests.get(detail_url, headers=headers, params=detail_params)
                    detail_result = detail_response.json()
                    
                    if detail_result.get('code') != 0:
                        continue
                    
                    instance = detail_result.get('data', {})
                    
                    # 检查是否是目标用户的审批
                    if instance.get('open_id') != user_id:
                        continue
                    
                    # 只处理已通过的审批
                    if instance.get('status') != 'APPROVED':
                        continue
                    
                    # 解析审批表单（form 是 JSON 字符串）
                    form_str = instance.get('form', '[]')
                    try:
                        form_data = json.loads(form_str) if isinstance(form_str, str) else form_str
                        
                        # 查找请假表单组件（leaveGroupV2）
                        for widget in form_data:
                            if widget.get('type') == 'leaveGroupV2':
                                leave_info = widget.get('value', {})
                                
                                # 直接从 value 中获取请假时间
                                start_str = leave_info.get('start', '')  # 格式: "2025-10-24T00:00:00+08:00"
                                end_str = leave_info.get('end', '')      # 格式: "2025-10-24T12:00:00+08:00"
                                leave_type = leave_info.get('name', '')
                                
                                if start_str and end_str:
                                    # 解析 ISO 格式时间（去掉时区信息后解析）
                                    leave_start = datetime.strptime(start_str[:19], '%Y-%m-%dT%H:%M:%S')
                                    leave_end = datetime.strptime(end_str[:19], '%Y-%m-%dT%H:%M:%S')
                                    leave_start = tz.localize(leave_start)
                                    leave_end = tz.localize(leave_end)
                                    
                                    # 检查是否包含查询日期
                                    if leave_start.date() <= check_date.date() <= leave_end.date():
                                        print(f"   ✅ 检测到请假: {leave_type} ({leave_start.date()} ~ {leave_end.date()})")
                                        return True
                                        
                    except Exception as e:
                        continue
                
                except Exception as e:
                    # 单个实例查询失败，继续处理下一个
                    continue
            
            return False  # 没有找到匹配的请假记录
            
        except Exception as e:
            print(f"   ⚠️ 检查请假状态失败 ({user_id}): {e}")
            import traceback
            traceback.print_exc()
            return False  # 出错时认为未请假
    
    def check_users_filled(self, user_names: list = None, date_str: str = None, user_field: str = "员工", config_path: str = None, skip_holiday_check: bool = False):
        """
        检查指定人员名单是否都填写了某日期的记录
        
        Args:
            user_names: 人员姓名列表，如 ["张三", "李四"]。如果不提供，则从配置文件读取（排除请假人员和例外日期）
            date_str: 日期字符串，格式 YYYY-MM-DD
            user_field: 用户字段名，默认"员工"
            config_path: 配置文件路径，默认为 backend/config/people.json
            skip_holiday_check: 是否跳过节假日检查，默认False
            
        Returns:
            dict: 包含已填写、未填写人员信息的字典
            {
                'all_filled': bool,      # 是否全部填写
                'filled': [...],         # 已填写的人员列表
                'not_filled': [...],     # 未填写的人员列表
                'on_leave': [...],       # 请假的人员列表
                'exception_day': [...],  # 例外日期的人员列表
                'is_holiday': bool,      # 是否为节假日
                'fill_rate': float       # 填写率（不含请假和例外日期人员）
            }
            
        示例:
            # 方式1: 从配置文件自动读取（推荐）
            result = bitable.check_users_filled(date_str="2025-09-30")
            
            # 方式2: 手动指定人员名单
            result = bitable.check_users_filled(
                user_names=["石国艳", "徐晓东", "胡东利"], 
                date_str="2025-09-30"
            )
        """
        # 检查是否为节假日
        is_holiday = False
        if not skip_holiday_check and date_str:
            is_holiday = self.is_holiday(date_str)
            if is_holiday:
                return {
                    'all_filled': True,
                    'filled': [],
                    'not_filled': [],
                    'on_leave': [],
                    'exception_day': [],
                    'is_holiday': True,
                    'fill_rate': 1.0,
                    'message': f'{date_str} 是节假日，无需检查'
                }
        
        # 如果没有提供人员名单，从配置文件读取
        if user_names is None:
            print("📋 从配置文件读取人员名单...")
            print(f"📅 {date_str} 是{self.get_weekday_name(date_str)}")
            user_names = self.load_people_from_config(config_path, date_str)
            
            if not user_names:
                print("⚠️ 未找到有效的人员名单（所有人都请假或在例外日期）")
                return {
                    'all_filled': True,
                    'filled': [],
                    'not_filled': [],
                    'on_leave': self._get_on_leave_people(config_path),
                    'exception_day': self._get_exception_day_people(config_path, date_str),
                    'is_holiday': False,
                    'fill_rate': 1.0
                }
            
            print(f"✅ 需要检查 {len(user_names)} 名人员")
        
        if not self.app_token or not self.table_id:
            print("❌ 缺少app_token或table_id，请在初始化时设置")
            return {
                'all_filled': False,
                'filled': [],
                'not_filled': user_names,
                'on_leave': [],
                'fill_rate': 0.0
            }
        
        try:
            # 先获取最近的所有记录来建立user_id映射（用于@功能）
            print("🔍 正在获取用户ID映射...")
            all_recent_records = self.get_records(page_size=500)  # 获取最近500条记录来建立映射
            user_id_map = {}  # 存储姓名到user_id的映射
            
            for record in all_recent_records:
                fields = record.get('fields', {})
                user_info = fields.get(user_field, {})
                
                # 提取user_id
                if isinstance(user_info, dict):
                    user_name = user_info.get('name', '')
                    user_id = user_info.get('id', '')
                    if user_name and user_id and user_name not in user_id_map:
                        user_id_map[user_name] = user_id
                elif isinstance(user_info, list) and len(user_info) > 0:
                    user_name = user_info[0].get('name', '') if isinstance(user_info[0], dict) else ''
                    user_id = user_info[0].get('id', '') if isinstance(user_info[0], dict) else ''
                    if user_name and user_id and user_name not in user_id_map:
                        user_id_map[user_name] = user_id
            
            print(f"✅ 已建立 {len(user_id_map)} 个用户的ID映射")
            
            # 获取指定日期的所有记录
            records = self.get_records_by_date("记录时间", date_str, convert_timestamp=False)
            
            # 提取已填写的人员姓名
            filled_users = set()
            
            for record in records:
                fields = record.get('fields', {})
                user_info = fields.get(user_field, {})
                
                # 处理不同的用户字段格式
                if isinstance(user_info, dict):
                    user_name = user_info.get('name', '')
                elif isinstance(user_info, list) and len(user_info) > 0:
                    user_name = user_info[0].get('name', '') if isinstance(user_info[0], dict) else str(user_info[0])
                elif isinstance(user_info, str):
                    user_name = user_info
                else:
                    continue
                
                if user_name:
                    filled_users.add(user_name)
            
            # 计算已填写和未填写的人员
            filled = [name for name in user_names if name in filled_users]
            not_filled = [name for name in user_names if name not in filled_users]
            
            # 为未填写人员查找user_id（如果有的话）
            not_filled_with_id = []
            for name in not_filled:
                not_filled_with_id.append({
                    'name': name,
                    'user_id': user_id_map.get(name, '')
                })
            fill_rate = len(filled) / len(user_names) if user_names else 0.0
            all_filled = len(not_filled) == 0
            
            # 输出结果
            print(f"\n📊 {date_str} 填写情况:")
            print(f"  总人数: {len(user_names)}")
            print(f"  已填写: {len(filled)} 人")
            print(f"  未填写: {len(not_filled)} 人")
            print(f"  填写率: {fill_rate*100:.1f}%")
            
            if not_filled:
                print(f"\n⚠️ 未填写人员:")
                for name in not_filled:
                    print(f"    - {name}")
            else:
                print(f"\n✅ 所有人员都已填写！")
            
            # 获取请假人员和例外日期人员列表
            on_leave = self._get_on_leave_people(config_path)
            exception_day = self._get_exception_day_people(config_path, date_str)
            
            # 检查未填写人员中是否有人请假（从日历查询）
            on_leave_from_calendar = []
            if not_filled_with_id and date_str:
                print(f"\n🔍 检查未填写人员的请假状态...")
                for user_info in not_filled_with_id:
                    user_id = user_info.get('user_id')
                    name = user_info.get('name')
                    if user_id and self.check_user_on_leave(user_id, date_str):
                        on_leave_from_calendar.append(name)
                        print(f"   📅 {name} 在 {date_str} 请假")
                
                if on_leave_from_calendar:
                    print(f"✅ 发现 {len(on_leave_from_calendar)} 人请假")
                    # 从未填写列表中移除请假人员
                    not_filled = [name for name in not_filled if name not in on_leave_from_calendar]
                    not_filled_with_id = [u for u in not_filled_with_id if u['name'] not in on_leave_from_calendar]
                    # 重新计算填写率
                    total_expected = len(user_names) - len(on_leave_from_calendar) - len(on_leave)
                    fill_rate = len(filled) / total_expected if total_expected > 0 else 1.0
                    all_filled = len(not_filled) == 0
            
            # 合并配置文件中的请假人员和日历中的请假人员
            all_on_leave = list(set(on_leave + on_leave_from_calendar))
            
            return {
                'all_filled': all_filled,
                'filled': filled,
                'not_filled': not_filled,
                'not_filled_with_id': not_filled_with_id,  # 包含user_id的未填写人员（已排除请假）
                'on_leave': all_on_leave,
                'on_leave_from_calendar': on_leave_from_calendar,  # 从日历查询到的请假人员
                'exception_day': exception_day,
                'is_holiday': is_holiday,
                'fill_rate': fill_rate
            }
            
        except Exception as e:
            print(f"❌ 检查人员填写状态失败: {e}")
            return {
                'all_filled': False,
                'filled': [],
                'not_filled': user_names if user_names else [],
                'on_leave': [],
                'exception_day': [],
                'is_holiday': False,
                'fill_rate': 0.0
            }
    
    @staticmethod
    def _get_on_leave_people(config_path: str = None):
        """获取请假人员列表"""
        if not config_path:
            # bitable.py 在 backend/utils/feishu/ 下，需要往上3层到达 backend/
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config" / "people.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 返回请假的人员（off: true）
            on_leave = [
                person['name'] 
                for person in config.get('people', []) 
                if person.get('off', False)
            ]
            
            return on_leave
        except:
            return []
    
    @staticmethod
    def _get_exception_day_people(config_path: str = None, date_str: str = None):
        """获取例外日期的人员列表"""
        if not config_path:
            # bitable.py 在 backend/utils/feishu/ 下，需要往上3层到达 backend/
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config" / "people.json"
        
        if not date_str:
            return []
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            weekday = BitableAPI.get_weekday_name(date_str)
            
            # 返回例外日期的人员
            exception_people = [
                person['name'] 
                for person in config.get('people', []) 
                if weekday in person.get('exceptions', []) and not person.get('off', False)
            ]
            
            return exception_people
        except:
            return []

