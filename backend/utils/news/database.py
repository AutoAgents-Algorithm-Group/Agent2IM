from typing import List, Dict, Any
from supabase import create_client, Client
from .config_manager import ConfigManager

# Initialize global config manager instance
config = ConfigManager()


class NewsDatabase:
    def __init__(self):
        """初始化 Supabase 数据库连接"""
        # 获取 Supabase 配置
        supabase_config = config.get_supabase_config()
        database_config = config.get_database_config()
        
        self.url = supabase_config['url']
        self.key = supabase_config['anon_key']
        self.table_name = database_config['table_name']
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL 和 anon_key 必须在配置文件中设置")
        
        # 创建 Supabase 客户端
        self.supabase: Client = create_client(self.url, self.key)
        self.init_database()
    
    def init_database(self):
        """初始化数据库，创建 ai_news 表格（如果不存在）"""
        # 注意：在 Supabase 中，表格通常通过 Dashboard 或 SQL 编辑器创建
        # 这里我们检查表格是否存在，如果不存在则提示用户手动创建
        try:
            # 尝试查询表格以检查是否存在
            result = self.supabase.table(self.table_name).select("id").limit(1).execute()
            print(f"Supabase 数据库连接成功，表格 '{self.table_name}' 已存在")
        except Exception as e:
            print(f"表格 '{self.table_name}' 可能不存在，请在 Supabase Dashboard 中创建")
            print("建议的表格结构 SQL:")
            print(f"""
CREATE TABLE {self.table_name} (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    tag TEXT NOT NULL,
    title TEXT NOT NULL,
    zh_title TEXT NOT NULL,
    link TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""")
            print(f"错误详情: {e}")
    
    def insert_news(self, news_data: Dict[str, Any]) -> bool:
        """插入单条新闻数据"""
        try:
            data = {
                'date': news_data.get('date'),
                'tag': news_data.get('tag'),
                'title': news_data.get('title'),
                'zh_title': news_data.get('zh_title'),
                'link': news_data.get('link'),
                'content': news_data.get('content'),
                'summary': news_data.get('summary')
            }
            
            result = self.supabase.table(self.table_name).insert(data).execute()
            
            if result.data:
                return True
            else:
                print(f"数据插入失败: {result}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                print(f"数据插入失败，链接可能已存在: {e}")
            else:
                print(f"数据插入时发生错误: {e}")
            return False
    
    def insert_news_batch(self, news_list: List[Dict[str, Any]]) -> int:
        """批量插入新闻数据"""
        success_count = 0
        for news in news_list:
            if self.insert_news(news):
                success_count += 1
        
        print(f"成功插入 {success_count}/{len(news_list)} 条新闻数据")
        return success_count
    
    def get_news_by_date(self, date: str) -> List[Dict[str, Any]]:
        """根据日期获取新闻"""
        try:
            result = self.supabase.table(self.table_name).select(
                "id, date, tag, title, zh_title, link, content, summary, created_at"
            ).eq('date', date).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"根据日期获取新闻时发生错误: {e}")
            return []
    
    def get_all_news(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有新闻数据"""
        try:
            result = self.supabase.table(self.table_name).select(
                "id, date, tag, title, zh_title, link, content, summary, created_at"
            ).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"获取所有新闻时发生错误: {e}")
            return []
    
    def delete_news_by_id(self, news_id: int) -> bool:
        """根据ID删除新闻"""
        try:
            result = self.supabase.table(self.table_name).delete().eq('id', news_id).execute()
            
            if result.data:
                print(f"成功删除ID为 {news_id} 的新闻")
                return True
            else:
                print(f"未找到ID为 {news_id} 的新闻")
                return False
        except Exception as e:
            print(f"删除新闻时发生错误: {e}")
            return False
    
    def get_news_count(self) -> int:
        """获取新闻总数"""
        try:
            result = self.supabase.table(self.table_name).select(
                "id", count="exact"
            ).execute()
            
            return result.count if result.count is not None else 0
        except Exception as e:
            print(f"获取新闻总数时发生错误: {e}")
            return 0


if __name__ == '__main__':
    # 测试数据库功能
    try:
        db = NewsDatabase()
        print(f"当前数据库中有 {db.get_news_count()} 条新闻")
        
        # 测试插入示例数据
        test_news = {
            'date': '2024-01-01',
            'tag': 'AI',
            'title': 'Test News Title',
            'zh_title': '测试新闻标题',
            'link': 'https://example.com/test-news',
            'content': 'This is a test news content.',
            'summary': '这是一条测试新闻的总结。'
        }
        
        print("\n测试插入新闻...")
        success = db.insert_news(test_news)
        print(f"插入结果: {success}")
        
        print(f"插入后数据库中有 {db.get_news_count()} 条新闻")
        
    except Exception as e:
        print(f"数据库测试失败: {e}")
        print("请检查配置文件是否正确设置了 Supabase 连接信息") 