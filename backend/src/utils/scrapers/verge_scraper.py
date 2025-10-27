"""
The Verge news scraper

This module provides the VergeScraper class for scraping AI news from The Verge.
"""

import re
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any


class VergeScraper:
    """The Verge news scraper for AI-related articles"""
    
    BASE_URL = "https://www.theverge.com"
    AI_ARCHIVES_URL = "https://www.theverge.com/ai-artificial-intelligence"
    SOURCE_TAG = "Verge"
    
    def __init__(self):
        """Initialize the Verge scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
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
        """Scrape news titles and links from The Verge"""
        news_list = []
        target_dates = self.get_recent_dates()
        print(f"🔍 The Verge: 查找日期 {target_dates}")
        
        # Use the correct URL structure - only use the main AI page for now
        # The Verge uses dynamic loading for pagination, so we'll focus on the main page
        urls_to_try = [self.AI_ARCHIVES_URL]  # Just use the main AI page
        
        for page_num, url in enumerate(urls_to_try, 1):
            
            print(f"📄 正在抓取页面 {page_num}: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                print(f"📡 响应状态码: {response.status_code}")
                
                if response.status_code == 403:
                    print("⚠️  The Verge 禁止访问，跳过")
                    break
                
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Look for articles based on The Verge's actual structure
                articles = []
                
                # Method 1: Look for large article cards (featured articles)
                # These are the main story cards visible in the screenshot
                large_cards = soup.find_all('div', class_=re.compile(r'.*duet--content-cards--content-card.*'))
                for card in large_cards:
                    link = card.find('a', href=True)
                    if link and link.get('href'):
                        # Look for the title in h2 or h3 tags
                        title_elem = card.find(['h2', 'h3'])
                        if title_elem:
                            articles.append({
                                'container': card,
                                'link': link,
                                'title_elem': title_elem
                            })
                
                # Method 2: Look for any article links with substantial text
                if len(articles) < 2:  # If we don't have enough from large cards
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        
                        # Filter for article-like links
                        if (href.startswith('/') and 
                            len(text) > 20 and  # Substantial text content
                            any(keyword in text.lower() for keyword in ['ai', 'artificial intelligence', 'chatgpt', 'openai', 'anthropic', 'google', 'meta', 'tech']) and
                            not any(skip in href.lower() for skip in ['author', 'tag', 'search', 'newsletter', 'podcast'])):
                            
                            # Try to find a parent container
                            container = link.parent
                            while container and container.name in ['span', 'em', 'strong']:
                                container = container.parent
                            
                            articles.append({
                                'container': container or link.parent,
                                'link': link,
                                'title_elem': link
                            })
                
                # Method 3: Look specifically for headline patterns
                if len(articles) < 2:
                    headlines = soup.find_all(['h1', 'h2', 'h3'], string=re.compile(r'.*(AI|artificial intelligence|Anthropic|OpenAI|ChatGPT|Altman).*', re.I))
                    for headline in headlines:
                        link = headline.find('a', href=True) or headline.find_parent('a', href=True)
                        if link:
                            articles.append({
                                'container': headline.parent,
                                'link': link,
                                'title_elem': headline
                            })
                
                print(f"📋 页面 {page_num} 找到 {len(articles)} 个文章")
                
                found_in_page = 0
                for article in articles:
                    try:
                        container = article['container']
                        link_block = article['link']
                        title_elem = article['title_elem']
                        
                        title = title_elem.text.strip()
                        href = link_block.get('href')
                        
                        if not title or not href:
                            continue
                        
                        # Make sure href is a full path
                        if href.startswith('/'):
                            href = href
                        elif not href.startswith('http'):
                            continue  # Skip invalid links
                        
                        # Look for content description in the container
                        content_preview = ""
                        if container:
                            # Try to find description paragraphs
                            desc_paragraphs = container.find_all('p')
                            for p in desc_paragraphs:
                                text = p.text.strip()
                                if text and len(text) > 20:
                                    content_preview = text[:200]
                                    break
                        
                        # Look for time information
                        time_elem = None
                        if container:
                            time_elem = container.find('time')
                            if not time_elem:
                                # Look for date strings in text
                                time_strings = container.find_all(string=re.compile(r'Aug \d+|2025'))
                                if time_strings:
                                    # Use recent date as fallback
                                    news_date = self.get_today_date()
                                else:
                                    news_date = self.get_today_date()
                            else:
                                datetime_attr = time_elem.get('datetime')
                                if datetime_attr:
                                    try:
                                        if 'T' in datetime_attr:
                                            news_date = datetime.strptime(datetime_attr.split('T')[0], "%Y-%m-%d").strftime("%Y-%m-%d")
                                        else:
                                            news_date = datetime_attr
                                    except:
                                        news_date = self.get_today_date()
                                else:
                                    news_date = self.get_today_date()
                        else:
                            news_date = self.get_today_date()
                        
                        # Filter for AI/tech related content and recent dates
                        if (news_date in target_dates and title and href and
                            any(keyword in title.lower() or keyword in href.lower() 
                                for keyword in ['ai', 'artificial intelligence', 'chatgpt', 'openai', 'google', 'meta', 'tech'])):
                            
                            print(f"✅ 找到文章: {news_date}, {title[:50]}...")
                            news_item = {
                                'title': title,
                                'href': href,
                                'news_time': news_date,
                                'date': news_date,
                                'tag': self.SOURCE_TAG
                            }
                            
                            # Add content preview if available
                            if content_preview:
                                news_item['content_preview'] = content_preview
                                
                            news_list.append(news_item)
                            found_in_page += 1
                            
                    except Exception as e:
                        print(f"❌ 处理文章时出错: {e}")
                        continue
                
                print(f"📊 页面 {page_num} 找到 {found_in_page} 篇目标日期的文章")
                
                if found_in_page == 0 and page_num > 1:
                    break  # If no articles found and not first page, stop
                    
            except Exception as e:
                print(f"❌ 抓取页面 {page_num} 时出错: {e}")
                continue

        print(f"🎯 总共找到 {len(news_list)} 篇 The Verge 文章")
        return news_list
    
    def get_news_content(self, news_href: str) -> str:
        """Extract content from a news article"""
        total_url = f'{self.BASE_URL}{news_href}'
        
        try:
            response = requests.get(total_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try multiple content selectors
            paragraphs = soup.find_all('div', class_='duet--article--article-body-component')
            if not paragraphs:
                # Fallback selector
                paragraphs = soup.find_all('p')
                
            contents = []
            for paragraph in paragraphs:
                text = paragraph.text.strip()
                if text and len(text) > 10:  # Filter out short text
                    contents.append(text)
            
            return "\n".join(contents)
        except Exception as e:
            print(f"❌ 获取文章内容失败: {total_url}, 错误: {e}")
            return "无法获取文章内容"
    
    def get_news_list(self) -> List[Dict[str, Any]]:
        """Get complete news list with content"""
        news_list = self.get_title_and_link_list()
        news_content_list = []
        
        for news in tqdm(news_list, desc="⚡ Getting Verge news content"):
            news_content = self.get_news_content(news['href'])
            news['link'] = f'{self.BASE_URL}{news["href"]}'
            news['content'] = news_content
            news_content_list.append(news)
        
        return news_content_list


def get_news_list():
    """Legacy function for backward compatibility"""
    scraper = VergeScraper()
    return scraper.get_news_list()


if __name__ == "__main__":
    scraper = VergeScraper()
    news = scraper.get_news_list()
    print(f"✅ 获取到 {len(news)} 篇新闻")
    for item in news:
        print(f"  - {item['title']}")
