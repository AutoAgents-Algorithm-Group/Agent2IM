"""
配置加载器
"""

import json
from pathlib import Path


class ConfigLoader:
    """配置文件加载器"""
    
    def __init__(self, config_dir: str):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
    
    def load_json(self, filename: str) -> dict:
        """加载JSON配置文件"""
        try:
            config_path = self.config_dir / filename
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 加载配置文件成功: {filename}")
            return config
        except Exception as e:
            print(f"❌ 加载配置文件失败 {filename}: {e}")
            return {}

