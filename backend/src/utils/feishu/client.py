"""
飞书API客户端
处理访问令牌获取和基础API调用
"""

import time
import requests
from src.utils.logging import set_stage
from src.models import Stage


class FeishuClient:
    """飞书API客户端"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        
        # 初始化日志
        self.log = set_stage(Stage.FEISHU_AUTH)
        
        # 访问令牌缓存
        self._access_token_cache = {
            "token": None,
            "expires_at": 0
        }
    
    def get_access_token(self) -> str:
        """获取飞书访问令牌"""
        current_time = time.time()
        
        # 如果令牌还有效，直接返回缓存的令牌
        if (self._access_token_cache["token"] and 
            current_time < self._access_token_cache["expires_at"]):
            return self._access_token_cache["token"]
        
        # 获取新的访问令牌
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                token = result["tenant_access_token"]
                expires_in = result.get("expire", 7200)  # 默认2小时
                
                # 缓存令牌，提前10分钟过期
                self._access_token_cache["token"] = token
                self._access_token_cache["expires_at"] = current_time + expires_in - 600
                
                self.log.success(f"✅ 获取访问令牌成功")
                return token
            else:
                raise Exception(f"获取访问令牌失败: {result}")
        except Exception as e:
            self.log.error(f"❌ 获取飞书访问令牌失败: {e}")
            raise e

