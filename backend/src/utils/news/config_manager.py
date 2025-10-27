import os
import yaml
from typing import Dict, Any, List


class ConfigManager:
    """配置管理器，负责读取和管理 YAML 配置文件"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为backend目录下的 config.yml
        """
        if config_path is None:
            # 获取backend/src/config目录下的 news.yml
            # 从 src/utils/news/ 回到 src/config/
            current_dir = os.path.dirname(os.path.abspath(__file__))  # src/utils/news/
            utils_dir = os.path.dirname(current_dir)  # src/utils/
            src_dir = os.path.dirname(utils_dir)  # src/
            self.config_path = os.path.join(src_dir, 'config', 'news.yml')
        else:
            self.config_path = config_path
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config if config else {}
        except FileNotFoundError:
            print(f"配置文件未找到: {self.config_path}")
            print("请确保 config.yml 文件存在并配置正确")
            return {}
        except yaml.YAMLError as e:
            print(f"配置文件格式错误: {e}")
            return {}
    
    def get(self, key_path: str, default=None):
        """获取配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 'lark.api_url'
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_lark_config(self) -> Dict[str, str]:
        """获取主要飞书配置（保持向后兼容）"""
        # 优先使用新的primary配置，如果不存在则回退到旧配置
        return {
            'api_url': self.get('lark.primary.api_url') or self.get('lark.api_url'),
            'api_secret': self.get('lark.primary.api_secret') or self.get('lark.api_secret'),
            'name': self.get('lark.primary.name') or '主群组'
        }
    
    def get_all_lark_configs(self) -> List[Dict[str, str]]:
        """获取所有飞书配置列表"""
        configs = []
        
        # 检查新格式的配置
        lark_section = self.get('lark')
        if lark_section:
            for key, config in lark_section.items():
                if isinstance(config, dict) and 'api_url' in config:
                    # 跳过无效配置
                    api_url = config.get('api_url', '')
                    api_secret = config.get('api_secret', '')
                    
                    if (api_url and not api_url.startswith('YOUR_') and 
                        api_secret and not api_secret.startswith('YOUR_')):
                        configs.append({
                            'api_url': api_url,
                            'api_secret': api_secret,
                            'name': config.get('name', f'{key}群组'),
                            'key': key
                        })
        
        # 如果没有找到新格式配置，尝试旧格式
        if not configs:
            old_api_url = self.get('lark.api_url')
            old_api_secret = self.get('lark.api_secret')
            if (old_api_url and not old_api_url.startswith('YOUR_') and 
                old_api_secret and not old_api_secret.startswith('YOUR_')):
                configs.append({
                    'api_url': old_api_url,
                    'api_secret': old_api_secret,
                    'name': '主群组',
                    'key': 'primary'
                })
        
        return configs
    
    def get_api_config(self) -> Dict[str, str]:
        """获取 API 配置"""
        return {
            'deepl_api_key': self.get('apis.deepl_api_key'),
            'openai_api_key': self.get('apis.openai_api_key')
        }
    
    def get_autoagentsai_config(self) -> Dict[str, str]:
        """获取 AutoAgents AI 配置（保持向后兼容）"""
        # 优先使用新的translate_agent配置，如果不存在则回退到旧配置
        return {
            'agent_id': self.get('apis.autoagentsai.translate_agent.agent_id') or self.get('apis.autoagentsai.agent_id'),
            'personal_auth_key': self.get('apis.autoagentsai.translate_agent.personal_auth_key') or self.get('apis.autoagentsai.personal_auth_key'),
            'personal_auth_secret': self.get('apis.autoagentsai.translate_agent.personal_auth_secret') or self.get('apis.autoagentsai.personal_auth_secret')
        }
    
    def get_ai_agent_config(self) -> Dict[str, str]:
        """获取统一AI处理 Agent 配置 (JSON格式翻译+总结)"""
        return {
            'agent_id': self.get('apis.autoagentsai.ai_agent.agent_id'),
            'personal_auth_key': self.get('apis.autoagentsai.ai_agent.personal_auth_key'),
            'personal_auth_secret': self.get('apis.autoagentsai.ai_agent.personal_auth_secret')
        }
    
    def get_supabase_config(self) -> Dict[str, str]:
        """获取 Supabase 配置"""
        return {
            'url': self.get('supabase.url'),
            'anon_key': self.get('supabase.anon_key'),
            'service_role_key': self.get('supabase.service_role_key')
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        return {
            'table_name': self.get('database.table_name', 'ai_news')
        }
    
    def validate_config(self) -> bool:
        """验证配置是否完整"""
        required_configs = [
            'lark.api_url',
            'lark.api_secret',
            'apis.autoagentsai.agent_id',
            'apis.autoagentsai.personal_auth_key',
            'apis.autoagentsai.personal_auth_secret',
            'supabase.url',
            'supabase.anon_key'
        ]
        
        missing_configs = []
        for config_key in required_configs:
            if not self.get(config_key):
                missing_configs.append(config_key)
        
        if missing_configs:
            print("以下配置项缺失或为空:")
            for config in missing_configs:
                print(f"  - {config}")
            return False
        
        return True


# 全局配置实例
config = ConfigManager()


if __name__ == '__main__':
    # 测试配置管理器
    config_mgr = ConfigManager()
    
    print("=== 配置验证 ===")
    is_valid = config_mgr.validate_config()
    print(f"配置是否完整: {is_valid}")
    
    print("\n=== 飞书配置 ===")
    lark_config = config_mgr.get_lark_config()
    for key, value in lark_config.items():
        print(f"{key}: {value}")
    
    print("\n=== AutoAgents AI 配置 ===")
    autoagentsai_config = config_mgr.get_autoagentsai_config()
    for key, value in autoagentsai_config.items():
        print(f"{key}: {value}")
    
    print("\n=== API 配置 (备用) ===")
    api_config = config_mgr.get_api_config()
    for key, value in api_config.items():
        print(f"{key}: {value}")
    
    print("\n=== Supabase 配置 ===")
    supabase_config = config_mgr.get_supabase_config()
    for key, value in supabase_config.items():
        print(f"{key}: {value}")
