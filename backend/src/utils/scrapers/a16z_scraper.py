"""
a16z news scraper

This module provides the A16zScraper class for scraping AI and tech insights from a16z.
"""

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any


class A16zScraper:
    """a16z scraper for AI and technology insights"""
    
    BASE_URL = "https://a16z.com"
    NEWS_URL = "https://a16z.com/news-content/"
    SOURCE_TAG = "a16z"
    
    def __init__(self):
        """Initialize the a16z scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://a16z.com/',
        }
    
    @staticmethod
    def get_today_date() -> str:
        """Get yesterday's date in YYYY-MM-DD format"""
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    @staticmethod
    def get_recent_dates(days: int = 7) -> List[str]:
        """Get list of recent dates for news filtering (7 days for a16z)"""
        today = datetime.now()
        return [
            (today - timedelta(days=i)).strftime("%Y-%m-%d") 
            for i in range(days)
        ]
    
    def get_title_and_link_list(self) -> List[Dict[str, Any]]:
        """Scrape latest content from a16z"""
        news_list = []
        target_dates = self.get_recent_dates()
        print(f"🔍 a16z: 查找日期 {target_dates}")
        
        try:
            response = requests.get(self.NEWS_URL, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for article links based on a16z structure
            # First try to find latest content section
            latest_section = soup.find('div', class_='latest') or soup.find('section')
            
            if latest_section:
                articles = latest_section.find_all('a', href=True)
            else:
                # Fallback: look for all links that look like articles
                articles = soup.find_all('a', href=True)
                # Filter for likely article links
                articles = [a for a in articles if a.get('href') and ('/' in a.get('href')) and a.text.strip()]
            
            print(f"📋 找到 {len(articles)} 个潜在文章")
            
            found_articles = 0
            seen_links = set()  # Avoid duplicates
            
            for article in articles:
                try:
                    # Extract link and title - article should be an 'a' tag
                    href = article.get('href')
                    title = article.text.strip()
                    
                    if not href or not title or len(title) < 10:
                        continue
                    
                    # Skip duplicates
                    if href in seen_links:
                        continue
                    seen_links.add(href)
                    
                    # Skip non-article links and external domains
                    if any(skip in href for skip in ['#', 'mailto:', 'tel:', 'javascript:', '/team/', '/about/', '/jobs/', '/portfolio/', '/connect']):
                        continue
                    
                    # Only allow a16z.com domain links, skip external links
                    if href.startswith('http') and not href.startswith('https://a16z.com'):
                        continue
                    
                    # Filter for AI/tech content
                    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'tech', 'enterprise', 'fintech', 'crypto', 'bio', 'health', 'startup', 'investing']
                    if not any(keyword in title.lower() for keyword in ai_keywords):
                        continue
                    
                    # Build full URL - only for a16z.com domain
                    if href.startswith('/'):
                        link = f'{self.BASE_URL}{href}'
                    elif href.startswith('https://a16z.com'):
                        link = href
                    else:
                        continue
                    
                    # For a16z, we'll consider recent articles regardless of exact date
                    # since they don't always have clear date indicators in listings
                    current_date = self.get_today_date()
                    
                    print(f"✅ 找到文章: {title[:50]}...")
                    print(f"   🔗 链接: {link}")
                    news_list.append({
                        'title': title,
                        'link': link,
                        'date': current_date,
                        'tag': self.SOURCE_TAG
                    })
                    found_articles += 1
                    
                    # Limit to prevent too many articles
                    if found_articles >= 10:
                        break
                        
                except Exception as e:
                    print(f"❌ 处理文章时出错: {e}")
                    continue
            
            print(f"📊 找到 {found_articles} 篇AI/科技文章")
                
        except Exception as e:
            print(f"❌ 抓取a16z页面时出错: {e}")
        
        print(f"🎯 总共找到 {len(news_list)} 篇 a16z 文章")
        return news_list
    
    def get_news_content(self, news_link: str) -> str:
        """Extract content from an a16z article"""
        try:
            response = requests.get(news_link, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try multiple content selectors for a16z
            content_div = soup.find('div', class_='post-content') or \
                         soup.find('div', class_='entry-content') or \
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
                if text and len(text) > 20:  # Filter out short text
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
        
        for news in tqdm(news_list, desc="💡 Getting a16z content"):
            news_content = self.get_news_content(news['link'])
            news['content'] = news_content
            news_content_list.append(news)
        
        return news_content_list


def get_news_list():
    """Legacy function for backward compatibility"""
    scraper = A16zScraper()
    return scraper.get_news_list()


if __name__ == '__main__':
    scraper = A16zScraper()
    news = scraper.get_news_list()
    print(f"✅ 获取到 {len(news)} 篇文章")
    for item in news:
        print(f"  - {item['title']}")
