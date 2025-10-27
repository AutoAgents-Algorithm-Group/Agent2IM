"""
新闻服务模块

整合新闻采集、处理和推送功能
"""

import hashlib
import base64
import hmac
import time
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from autoagents_core.client import ChatClient

import sys
import os

from src.utils.news.config_manager import ConfigManager
from src.utils.news.database import NewsDatabase
from src.utils.scrapers import (
    TechCrunchScraper,
    VergeScraper,
    GitHubTrendingScraper,
    ProductHuntScraper,
    A16zScraper,
    Kr36Scraper
)


class NewsHandler:
    """新闻处理器 - 负责采集、翻译和总结新闻"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化新闻处理器"""
        if config_manager is None:
            config_manager = ConfigManager()
        
        self.config = config_manager
        self.database = NewsDatabase()
        
        # 初始化爬虫
        self.scrapers = [
            TechCrunchScraper(),
            VergeScraper(),
            GitHubTrendingScraper(),
            ProductHuntScraper(),
            A16zScraper(),
            Kr36Scraper()
        ]
        
        # 初始化AI客户端（延迟加载）
        self._ai_client = None
        
    def get_ai_client(self) -> ChatClient:
        """获取AI客户端实例（延迟初始化）"""
        if self._ai_client is None:
            try:
                ai_config = self.config.get_ai_agent_config()
                self._ai_client = ChatClient(
                    agent_id=ai_config["agent_id"],
                    personal_auth_key=ai_config["personal_auth_key"],
                    personal_auth_secret=ai_config["personal_auth_secret"]
                )
            except Exception as e:
                print(f"❌ AI客户端初始化失败: {e}")
                print("💡 请检查 config/news.yml 中的 ai_agent 配置")
                raise e
        return self._ai_client
    
    @staticmethod
    def get_target_date() -> str:
        """获取目标日期（昨天）"""
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    def translate_title(self, title: str) -> str:
        """使用AI翻译标题"""
        prompt = f"请将以下英文新闻标题翻译成中文，只返回翻译结果，不要其他内容：\n\n{title}"
        
        try:
            client = self.get_ai_client()
            print(f"🌍 使用AI翻译标题")
            content = ""
            for event in client.invoke(prompt):
                if event['type'] == 'token':
                    content += event['content']
            return content.strip()
        except Exception as e:
            print(f"⚠️ 标题翻译失败: {e}")
            return title
    
    def summarize_content(self, content: str) -> str:
        """使用AI总结内容"""
        prompt = f"请对以下英文新闻内容用中文进行总结，总结内容不超过100个汉字，只返回总结结果：\n\n{content}"
        
        try:
            client = self.get_ai_client()
            print(f"📝 使用AI总结内容")
            summary = ""
            for event in client.invoke(prompt):
                if event['type'] == 'token':
                    summary += event['content']
            return summary.strip()
        except Exception as e:
            print(f"⚠️ 内容总结失败: {e}")
            return "新闻内容总结失败"
    
    def fetch_all_news(self) -> List[Dict[str, Any]]:
        """从所有配置的爬虫获取新闻（每个爬虫限制3条）"""
        all_news = []
        
        for scraper in self.scrapers:
            try:
                scraper_name = scraper.__class__.__name__
                print(f"📰 开始获取 {scraper_name} 新闻...")
                news_list = scraper.get_news_list()
                
                # 限制每个爬虫3条新闻
                limited_news = news_list[:3]
                all_news.extend(limited_news)
                
                print(f"✅ {scraper_name} 获取到 {len(news_list)} 篇新闻，选取前 {len(limited_news)} 篇")
            except Exception as e:
                print(f"❌ {scraper_name} 获取新闻失败: {e}")
                continue
        
        print(f"🎯 总共获取到 {len(all_news)} 篇新闻")
        return all_news
    
    def batch_process_news_with_ai(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用AI批量处理新闻（JSON格式）"""
        print(f"🤖 批量处理 {len(news_items)} 篇新闻（JSON格式）")
        
        try:
            # 准备新闻数据
            news_data = []
            for i, news_item in enumerate(news_items):
                item_data = {
                    "id": i + 1,
                    "source_name": news_item.get('tag', 'Unknown'),
                    "original_title": news_item.get('title', ''),
                    "content": news_item.get('content', '')[:1000]
                }
                news_data.append(item_data)
            
            # 创建AI查询
            query = f"""请处理以下{len(news_data)}篇新闻，对每篇新闻进行翻译和总结。

要求：
1. 对于source_name为"GitHub"或"Product Hunt"的新闻，标题不需要翻译，直接使用原标题
2. 对于其他来源的英文标题，翻译成中文
3. 对所有内容进行总结，控制在80字左右，不少于60字，不够的就扩写，够的就精简
4. 严格按照JSON格式返回，不要添加任何其他文本

返回格式（JSON数组）：
[
  {{
    "id": 1,
    "source_name": "来源名称",
    "title": "处理后的标题（中文或原文）",
    "summary": "内容总结"
  }},
  ...
]

新闻数据：
"""
            
            for item in news_data:
                query += f"""
新闻 {item['id']}:
- 来源: {item['source_name']}
- 标题: {item['original_title']}
- 内容: {item['content']}
"""
            
            # 发送到AI处理
            print("🤖 发送AI处理请求...")
            ai_result = self.summarize_content(query)
            
            print(f"🔍 AI返回长度: {len(ai_result)} 字符")
            
            # 解析JSON结果
            try:
                # 提取JSON数组
                start_idx = ai_result.find('[')
                end_idx = ai_result.rfind(']') + 1
                
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("未找到JSON数组")
                
                json_str = ai_result[start_idx:end_idx]
                parsed_results = json.loads(json_str)
                
                print(f"✅ 成功解析 {len(parsed_results)} 条结果")
                
                # 转换为最终格式
                processed_news = []
                for result in parsed_results:
                    news_id = result.get('id', 0) - 1
                    if 0 <= news_id < len(news_items):
                        original_item = news_items[news_id]
                        processed_item = {
                            "date": self.get_target_date(),
                            "title": original_item.get('title', ''),
                            "zh_title": result.get('title', original_item.get('title', '')),
                            "link": original_item.get('link', ''),
                            "content": original_item.get('content', ''),
                            "summary": result.get('summary', '无总结'),
                            "tag": result.get('source_name', original_item.get('tag', ''))
                        }
                        processed_news.append(processed_item)
                
                return processed_news
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ JSON解析失败: {e}")
                return self._create_fallback_results(news_items)
                
        except Exception as e:
            print(f"❌ AI处理失败: {e}")
            return self._create_fallback_results(news_items)
    
    def _create_fallback_results(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """创建备用结果"""
        print("🔄 使用备用方案处理新闻")
        processed_news = []
        
        for news_item in news_items:
            processed_item = {
                "date": self.get_target_date(),
                "title": news_item.get('title', ''),
                "zh_title": news_item.get('title', ''),
                "link": news_item.get('link', ''),
                "content": news_item.get('content', ''),
                "summary": "AI处理失败，无法生成总结",
                "tag": news_item.get('tag', '')
            }
            processed_news.append(processed_item)
        
        return processed_news
    
    def process_news(self) -> List[Dict[str, Any]]:
        """主方法：处理所有新闻"""
        target_date = self.get_target_date()
        print(f"🚀 开始处理 {target_date} 的新闻")
        
        # 第1步：获取所有原始新闻
        print("📥 阶段1：获取所有新闻内容")
        raw_news = self.fetch_all_news()
        
        if not raw_news:
            print("📭 没有获取到新闻数据")
            return []
        
        print(f"✅ 成功获取 {len(raw_news)} 条新闻")
        
        # 第2步：AI批量处理
        print("\n🤖 阶段2：AI批量处理（翻译 + 总结）")
        processed_news = self.batch_process_news_with_ai(raw_news)
        
        if not processed_news:
            print("❌ AI处理失败，没有获得有效结果")
            return []
        
        print(f"✅ AI处理完成，得到 {len(processed_news)} 条结果")
        
        # 第3步：保存到数据库
        print("\n💾 阶段3：保存到数据库")
        if processed_news:
            try:
                success_count = self.database.insert_news_batch(processed_news)
                print(f"💾 成功保存 {success_count}/{len(processed_news)} 条新闻到数据库")
            except Exception as e:
                print(f"❌ 数据库保存失败: {e}")
        
        print(f"✅ 新闻处理完成，共处理 {len(processed_news)} 条新闻")
        return processed_news


class FeishuNewsPublisher:
    """飞书新闻发布器 - 负责将新闻推送到飞书群组"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化飞书新闻发布器"""
        if config_manager is None:
            config_manager = ConfigManager()
        
        self.config = config_manager
        
        # 获取所有飞书配置
        self.lark_configs = self.config.get_all_lark_configs()
        
        if not self.lark_configs:
            raise ValueError("至少需要配置一个有效的飞书机器人在 config/news.yml 中")
        
        # 主要配置（向后兼容）
        primary_config = self.config.get_lark_config()
        self.api_url = primary_config['api_url']
        self.api_secret = primary_config['api_secret']
        
        print(f"🚀 初始化飞书发送器：找到 {len(self.lark_configs)} 个群组配置")
        for config in self.lark_configs:
            print(f"   📱 {config['name']} ({config['key']})")
    
    def generate_signature(self, api_secret: str = None) -> tuple:
        """生成飞书API签名"""
        if api_secret is None:
            api_secret = self.api_secret
            
        timestamp = int(time.time())
        string_to_sign = f'{timestamp}\n{api_secret}'
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), 
            digestmod=hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(hmac_code).decode('utf-8')
        return timestamp, signature
    
    def create_news_card(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建精美的新闻卡片"""
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        if not news_list:
            return {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True,
                        "enable_forward": True
                    },
                    "header": {
                        "template": "blue",
                        "title": {
                            "content": f"📱 {today_date} AI新闻播报",
                            "tag": "plain_text"
                        }
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "content": "😴 今日暂无AI新闻更新\n\n请稍后再来查看最新资讯",
                                "tag": "lark_md"
                            }
                        }
                    ]
                }
            }
        
        # 构建新闻卡片元素
        elements = []
        
        # 按来源分组新闻
        news_by_source = {}
        for news in news_list:
            source = news['tag']
            if source not in news_by_source:
                news_by_source[source] = []
            news_by_source[source].append(news)
        
        # 定义来源信息
        source_info = {
            'TechCrunch': {
                'emoji': '🗞️',
                'name': 'TechCrunch',
                'homepage': 'https://techcrunch.com'
            },
            'Verge': {
                'emoji': '🔺',
                'name': 'The Verge',
                'homepage': 'https://www.theverge.com'
            },
            'GitHub': {
                'emoji': '🐙',
                'name': 'GitHub Trending',
                'homepage': 'https://github.com/trending'
            },
            'ProductHunt': {
                'emoji': '🚀',
                'name': 'Product Hunt',
                'homepage': 'https://www.producthunt.com'
            },
            'a16z': {
                'emoji': '💡',
                'name': 'Andreessen Horowitz',
                'homepage': 'https://a16z.com/news-content/'
            },
            '36kr': {
                'emoji': '🏢',
                'name': '36氪',
                'homepage': 'https://36kr.com'
            }
        }
        
        # 为每个来源创建元素
        first_source = True
        for source, news_items in news_by_source.items():
            if not first_source:
                elements.append({"tag": "hr"})
            first_source = False
            
            # 添加来源标题
            source_data = source_info.get(source, {'emoji': '📰', 'name': source, 'homepage': '#'})
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"{source_data['emoji']} **{source_data['name']}**",
                    "tag": "lark_md"
                }
            })
            
            # 添加新闻项
            for i, news in enumerate(news_items):
                elements.append({
                    "tag": "div",
                    "text": {
                        "content": f"**{i+1}. {news['zh_title']}**\n{news['summary']}",
                        "tag": "lark_md"
                    }
                })
                
                # 阅读原文按钮
                elements.append({
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "📖 阅读原文",
                                "tag": "plain_text"
                            },
                            "url": news['link'],
                            "type": "default"
                        }
                    ]
                })
            
            # 添加主页链接
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": f"🔗 查看更多{source_data['name']}资讯",
                            "tag": "plain_text"
                        },
                        "url": source_data['homepage'],
                        "type": "primary"
                    }
                ]
            })
        
        # 添加页脚
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "content": f"🤖 *由AI新闻机器人自动播报* | ⏰ {datetime.now().strftime('%H:%M')} 更新",
                "tag": "lark_md"
            }
        })
        
        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "template": "turquoise",
                    "title": {
                        "content": f"🔥 {today_date} 每日AI新闻速览",
                        "tag": "plain_text"
                    }
                },
                "elements": elements
            }
        }
    
    def send_card_to_group(self, news_list: List[Dict[str, Any]], api_url: str, api_secret: str, group_name: str) -> requests.Response:
        """发送新闻卡片到指定飞书群组"""
        try:
            timestamp, sign = self.generate_signature(api_secret)
            card_data = self.create_news_card(news_list)
            
            data = {
                "timestamp": timestamp,
                "sign": sign,
                **card_data
            }
            
        except Exception as e:
            print(f"🔥 创建卡片时发生错误: {e}")
            data = self.create_error_card(str(e))

        headers = {"Content-Type": "application/json"}
        
        response = requests.post(api_url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 新闻卡片发送成功 → {group_name}")
        else:
            print(f"❌ 发送失败 → {group_name}: {response.status_code}, {response.text}")
        
        return response
    
    def send_to_all_groups(self, news_list: List[Dict[str, Any]]) -> Dict[str, requests.Response]:
        """发送新闻卡片到所有配置的飞书群组"""
        results = {}
        
        print(f"📤 开始向 {len(self.lark_configs)} 个群组发送新闻...")
        
        for config in self.lark_configs:
            group_name = config['name']
            api_url = config['api_url']
            api_secret = config['api_secret']
            
            print(f"📱 正在发送到 {group_name}...")
            
            try:
                response = self.send_card_to_group(news_list, api_url, api_secret, group_name)
                results[config['key']] = response
                
                if len(self.lark_configs) > 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ 发送到 {group_name} 失败: {e}")
        
        success_count = sum(1 for r in results.values() if hasattr(r, 'status_code') and r.status_code == 200)
        print(f"📊 发送完成：{success_count}/{len(self.lark_configs)} 个群组发送成功")
        
        return results
    
    def create_error_card(self, error_message: str = "新闻服务暂时不可用") -> Dict[str, Any]:
        """创建错误卡片"""
        timestamp, sign = self.generate_signature()
        
        return {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "template": "red",
                    "title": {
                        "content": "⚠️ AI新闻获取失败",
                        "tag": "plain_text"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"🔧 {error_message}\n\n请稍后重试或联系管理员检查服务状态",
                            "tag": "lark_md"
                        }
                    }
                ]
            }
        }


def run_news_and_publish():
    """运行新闻采集和发布流程"""
    try:
        # 1. 处理新闻
        handler = NewsHandler()
        news_list = handler.process_news()
        
        if not news_list:
            print("📰 今日无新闻内容")
            news_list = []
        
        # 2. 发布到飞书
        publisher = FeishuNewsPublisher()
        results = publisher.send_to_all_groups(news_list)
        
        return results
        
    except Exception as e:
        print(f"❌ 执行新闻采集和发布失败: {e}")
        return None


if __name__ == '__main__':
    run_news_and_publish()



