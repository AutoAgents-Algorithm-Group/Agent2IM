"""
TechCrunch news scraper

This module provides the TechCrunchScraper class for scraping AI news from TechCrunch.
"""

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any


class TechCrunchScraper:
    """TechCrunch news scraper for AI-related articles"""
    
    BASE_URL = "https://techcrunch.com"
    SOURCE_TAG = "TechCrunch"
    
    def __init__(self):
        """Initialize the TechCrunch scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    
    @staticmethod
    def get_today_date() -> str:
        """Get yesterday's date in YYYY-MM-DD format"""
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    @staticmethod
    def get_recent_dates(days: int = 3) -> List[str]:
        """Get list of recent dates for news filtering"""
        today = datetime.now()
        return [
            (today - timedelta(days=i)).strftime("%Y-%m-%d") 
            for i in range(days)
        ]
    
    def get_title_and_link_list(self) -> List[Dict[str, Any]]:
        """Scrape news titles and links from TechCrunch"""
        news_list = []
        target_dates = self.get_recent_dates()
        print(f"🔍 TechCrunch: 查找日期 {target_dates}")
        
        for page in range(1, 5):  # Limit to 4 pages
            url = f'{self.BASE_URL}/latest/page/{page}'
            print(f"📄 正在抓取页面: {url}")
            
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                ul = soup.find('ul', class_='wp-block-post-template is-layout-flow wp-block-post-template-is-layout-flow')
                
                if not ul:
                    print(f"⚠️  页面 {page} 未找到文章列表")
                    continue
                    
                items = ul.find_all('li')
                print(f"📋 页面 {page} 找到 {len(items)} 个项目")
                
                found_in_page = 0
                for item in items:
                    title_elem = item.find('h3', class_='loop-card__title')
                    if title_elem:
                        link_elem = title_elem.find('a', class_='loop-card__title-link')
                        if link_elem:
                            news_link = link_elem.get('href')
                            news_title = link_elem.text.strip()
                            
                            # Extract date from URL
                            try:
                                spans = news_link.replace("https://", "").split("/")
                                if len(spans) >= 4:
                                    news_date = "-".join(spans[1:4])  # YYYY-MM-DD format
                                    
                                    if news_date in target_dates:
                                        print(f"✅ 找到文章: {news_date}, {news_title[:50]}...")
                                        news_list.append({
                                            'title': news_title,
                                            'link': news_link,
                                            'date': news_date,
                                            'tag': self.SOURCE_TAG
                                        })
                                        found_in_page += 1
                            except Exception as e:
                                print(f"❌ 解析链接日期失败: {news_link}, 错误: {e}")
                
                print(f"📊 页面 {page} 找到 {found_in_page} 篇目标文章")
                    
            except Exception as e:
                print(f"❌ 抓取页面 {page} 时出错: {e}")
                continue
        
        print(f"🎯 总共找到 {len(news_list)} 篇 TechCrunch 文章")
        return news_list
    
    def get_news_content(self, news_link: str) -> str:
        """Extract content from a news article"""
        try:
            response = requests.get(news_link, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try multiple content selectors
            content_div = soup.find('div', class_='entry-content wp-block-post-content is-layout-constrained wp-block-post-content-is-layout-constrained')
            
            if content_div:
                paragraphs = content_div.find_all('p', class_='wp-block-paragraph')
            else:
                # Fallback selector
                paragraphs = soup.find_all('p')
            
            contents = []
            for paragraph in paragraphs:
                text = paragraph.text.strip()
                if text and len(text) > 10:  # Filter out short text
                    contents.append(text)
            
            return "\n".join(contents)
        except Exception as e:
            print(f"❌ 获取文章内容失败: {news_link}, 错误: {e}")
            return "无法获取文章内容"
    
    def get_news_list(self) -> List[Dict[str, Any]]:
        """Get complete news list with content"""
        news_list = self.get_title_and_link_list()
        news_content_list = []
        
        for news in tqdm(news_list, desc="🚀 Getting TechCrunch news content"):
            news_content = self.get_news_content(news['link'])
            news['content'] = news_content
            news_content_list.append(news)
        
        return news_content_list


def get_news_list():
    """Legacy function for backward compatibility"""
    scraper = TechCrunchScraper()
    return scraper.get_news_list()


if __name__ == '__main__':
    scraper = TechCrunchScraper()
    news = scraper.get_news_list()
    print(f"✅ 获取到 {len(news)} 篇新闻")
    for item in news:
        print(f"  - {item['title']}")
