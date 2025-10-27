"""
36kr news scraper

This module provides the Kr36Scraper class for scraping tech news from 36kr.
"""

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any


class Kr36Scraper:
    """36kr scraper for Chinese tech and startup news"""
    
    BASE_URL = "https://36kr.com"
    AI_URL = "https://36kr.com/search/articles/AI"
    SOURCE_TAG = "36kr"
    
    def __init__(self):
        """Initialize the 36kr scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://36kr.com/',
            'Connection': 'keep-alive',
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
        """Scrape AI and tech news from 36kr"""
        news_list = []
        target_dates = self.get_recent_dates()
        print(f"🔍 36kr: 查找日期 {target_dates}")
        
        # Try multiple URLs
        urls_to_try = [
            "https://36kr.com/",  # Main page
            "https://36kr.com/search/articles/AI",  # AI search
            "https://36kr.com/search/articles/人工智能",  # AI search in Chinese
        ]
        
        for url in urls_to_try:
            try:
                print(f"📄 正在抓取页面: {url}")
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 403:
                    print(f"⚠️  36kr 访问被限制: {url}")
                    continue
                
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Look for article links
                articles = soup.find_all('a', href=True)
                articles = [a for a in articles if '/p/' in a.get('href', '') or '/news/' in a.get('href', '')]
                
                print(f"📋 找到 {len(articles)} 个潜在文章链接")
                
                found_articles = 0
                for article in articles:
                    try:
                        href = article.get('href')
                        title = article.text.strip()
                        
                        if not href or not title or len(title) < 5:
                            continue
                        
                        # Skip unwanted links
                        if any(skip in href for skip in ['#', 'mailto:', 'tel:', 'javascript:', '/author/', '/tag/']):
                            continue
                        
                        # Filter for AI/tech content
                        ai_keywords = ['ai', '人工智能', '机器学习', '科技', '创业', '互联网', '数据', '算法', '自动化', '数字化', '智能', '技术']
                        if not any(keyword in title.lower() for keyword in ai_keywords):
                            continue
                        
                        # Build full URL
                        if href.startswith('/'):
                            link = f'{self.BASE_URL}{href}'
                        elif href.startswith('http'):
                            link = href
                        else:
                            continue
                        
                        # Extract date from URL if possible
                        try:
                            import re
                            # 36kr URLs often have patterns like /p/2445678 or timestamp
                            # For now, use current date as we can't easily extract date
                            article_date = self.get_today_date()
                        except:
                            article_date = self.get_today_date()
                        
                        # Add to news list (skip date filtering for Chinese sites as they're less predictable)
                        print(f"✅ 找到文章: {title[:30]}...")
                        news_list.append({
                            'title': title,
                            'link': link,
                            'date': article_date,
                            'tag': self.SOURCE_TAG
                        })
                        found_articles += 1
                        
                        # Limit to prevent too many requests
                        if found_articles >= 8:
                            break
                            
                    except Exception as e:
                        print(f"❌ 处理文章时出错: {e}")
                        continue
                
                print(f"📊 从 {url} 找到 {found_articles} 篇科技文章")
                
                if found_articles > 0:
                    break  # If we found articles, don't try other URLs
                    
            except Exception as e:
                print(f"❌ 抓取36kr页面时出错: {url}, 错误: {e}")
                continue
        
        # Remove duplicates
        seen_links = set()
        unique_news = []
        for news in news_list:
            if news['link'] not in seen_links:
                seen_links.add(news['link'])
                unique_news.append(news)
        
        print(f"🎯 总共找到 {len(unique_news)} 篇 36kr 文章")
        return unique_news
    
    def get_news_content(self, news_link: str) -> str:
        """Extract content from a 36kr article"""
        try:
            response = requests.get(news_link, headers=self.headers, timeout=30)
            
            if response.status_code == 403:
                return "36kr内容访问受限"
            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try multiple content selectors for 36kr
            content_div = soup.find('div', class_='kr-rich-text-wrapper') or \
                         soup.find('div', class_='article-content') or \
                         soup.find('div', class_='content') or \
                         soup.find('article') or \
                         soup.find('main')
            
            if content_div:
                paragraphs = content_div.find_all('p')
            else:
                # Fallback to all paragraphs
                paragraphs = soup.find_all('p')
            
            contents = []
            for paragraph in paragraphs:
                text = paragraph.text.strip()
                # Filter out ads, subscribe messages, etc.
                if text and len(text) > 10 and not any(skip in text for skip in ['下载36氪', '订阅', '广告', '推广']):
                    contents.append(text)
            
            # Limit content length for processing
            full_content = "\n".join(contents)
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            
            return full_content if full_content else "无法获取文章内容"
            
        except Exception as e:
            print(f"❌ 获取文章内容失败: {news_link}, 错误: {e}")
            return "无法获取文章内容"
    
    def get_news_list(self) -> List[Dict[str, Any]]:
        """Get complete news list with content"""
        news_list = self.get_title_and_link_list()
        news_content_list = []
        
        for news in tqdm(news_list, desc="🏢 Getting 36kr content"):
            news_content = self.get_news_content(news['link'])
            news['content'] = news_content
            news_content_list.append(news)
        
        return news_content_list


def get_news_list():
    """Legacy function for backward compatibility"""
    scraper = Kr36Scraper()
    return scraper.get_news_list()


if __name__ == '__main__':
    scraper = Kr36Scraper()
    news = scraper.get_news_list()
    print(f"✅ 获取到 {len(news)} 篇文章")
    for item in news:
        print(f"  - {item['title']}")
