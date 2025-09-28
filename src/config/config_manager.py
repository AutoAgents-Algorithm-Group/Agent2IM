import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，相对于项目根目录
        """
        self.config_file = config_file
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 找到项目根目录（包含config.yaml的目录）
        current_dir = Path(__file__).parent
        config_path = None
        
        # 向上查找配置文件
        for parent in [current_dir, current_dir.parent, current_dir.parent.parent]:
            potential_path = parent / self.config_file
            if potential_path.exists():
                config_path = potential_path
                break
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                print(f"✅ 已加载配置文件: {config_path}")
            except Exception as e:
                print(f"❌ 加载配置文件失败: {e}")
                self._config = {}
        else:
            print(f"⚠️  未找到配置文件: {self.config_file}")
            self._config = {}
    
    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        """
        获取配置值，优先级：环境变量 > 配置文件 > 默认值
        
        Args:
            key: 配置键名
            default: 默认值
            section: 配置段落（可选）
            
        Returns:
            配置值
        """
        # 首先检查环境变量
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        # 然后检查配置文件
        if section:
            config_value = self._config.get(section, {}).get(key, default)
        else:
            config_value = self._config.get(key, default)
        
        return config_value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置段落"""
        return self._config.get(section, {})
    
    def get_feishu_config(self) -> Dict[str, Any]:
        """获取飞书配置"""
        return {
            "app_id": self.get("FEISHU_APP_ID", section="feishu"),
            "app_secret": self.get("FEISHU_APP_SECRET", section="feishu")
        }
    
    def get_autoagents_config(self) -> Dict[str, Any]:
        """获取AutoAgents配置"""
        return {
            "agent_id": self.get("AUTOAGENTS_AGENT_ID", section="autoagents"),
            "auth_key": self.get("AUTOAGENTS_AUTH_KEY", section="autoagents"),
            "auth_secret": self.get("AUTOAGENTS_AUTH_SECRET", section="autoagents")
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        # 获取基本配置
        feishu_config = self.get_feishu_config()
        autoagents_config = self.get_autoagents_config()
        
        # 检查配置完整性
        feishu_configured = bool(feishu_config["app_id"] and feishu_config["app_secret"])
        autoagents_configured = bool(autoagents_config["agent_id"] and autoagents_config["auth_key"] and autoagents_config["auth_secret"])
        
        return {
            "feishu": feishu_config,
            "autoagents": autoagents_config,
            "configured": {
                "feishu": feishu_configured,
                "autoagents": autoagents_configured,
                "all": feishu_configured and autoagents_configured
            }
        }