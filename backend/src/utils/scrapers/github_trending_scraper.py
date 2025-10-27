"""
GitHub Trending scraper

This module provides the GitHubTrendingScraper class for scraping trending repositories from GitHub.
"""

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
import re


class GitHubTrendingScraper:
    """GitHub Trending scraper for popular repositories"""
    
    BASE_URL = "https://github.com"
    TRENDING_URL = "https://github.com/trending"
    SOURCE_TAG = "GitHub"
    
    def __init__(self):
        """Initialize the GitHub Trending scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    @staticmethod
    def get_today_date() -> str:
        """Get today's date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_trending_repositories(self, time_range: str = "daily", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape trending repositories from GitHub
        
        Args:
            time_range: "daily", "weekly", or "monthly"
            limit: Maximum number of repositories to fetch
        """
        repos_list = []
        
        # Construct URL with time range
        url = f"{self.TRENDING_URL}?since={time_range}"
        print(f"🔍 GitHub Trending: 获取 {time_range} 热门仓库")
        print(f"📄 正在抓取页面: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find repository articles
            repo_articles = soup.find_all('article', class_='Box-row')
            if not repo_articles:
                # Try alternative selector
                repo_articles = soup.find_all('div', class_='Box-row')
            
            print(f"📋 找到 {len(repo_articles)} 个仓库")
            
            for i, article in enumerate(repo_articles[:limit]):
                try:
                    repo_info = self.parse_repository_info(article)
                    if repo_info:
                        repo_info['date'] = self.get_today_date()
                        repo_info['tag'] = self.SOURCE_TAG
                        repos_list.append(repo_info)
                        print(f"✅ 找到仓库: {repo_info['title'][:60]}...")
                        
                except Exception as e:
                    print(f"❌ 解析仓库信息失败: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ 抓取GitHub Trending失败: {e}")
            return []
        
        print(f"🎯 总共获取到 {len(repos_list)} 个热门仓库")
        return repos_list
    
    def parse_repository_info(self, article) -> Dict[str, Any]:
        """Parse repository information from article element"""
        try:
            # Repository name and link
            title_elem = article.find('h2', class_='h3 lh-condensed')
            if not title_elem:
                title_elem = article.find('h1', class_='h3 lh-condensed')
            
            if not title_elem:
                return None
            
            link_elem = title_elem.find('a')
            if not link_elem:
                return None
            
            repo_path = link_elem.get('href')
            # 清理仓库名称，去掉可能的markdown格式和多余的空白字符
            repo_name = link_elem.text.strip()
            # 移除markdown格式符号
            repo_name = repo_name.replace('**', '').replace('*', '')
            # 移除多余的空白字符和换行
            repo_name = ' '.join(repo_name.split())
            full_link = f"{self.BASE_URL}{repo_path}"
            
            # Description
            desc_elem = article.find('p', class_='col-9 color-fg-muted my-1 pr-4')
            if not desc_elem:
                desc_elem = article.find('p', class_='col-9')
            description = desc_elem.text.strip() if desc_elem else "No description available"
            
            # Programming language
            lang_elem = article.find('span', {'itemprop': 'programmingLanguage'})
            language = lang_elem.text.strip() if lang_elem else "Unknown"
            
            # Stars count
            stars_elem = article.find('a', class_='Link--muted d-inline-block mr-3')
            if not stars_elem:
                # Alternative selector for stars
                stars_elems = article.find_all('a', class_='Link--muted')
                stars_elem = stars_elems[0] if stars_elems else None
            
            stars_text = "0"
            if stars_elem:
                stars_text = stars_elem.text.strip()
                # Extract number from text like "1,234" or "1.2k"
                stars_match = re.search(r'[\d,k\.]+', stars_text)
                if stars_match:
                    stars_text = stars_match.group()
            
            # Today's stars (if available)
            today_stars_elem = article.find('span', class_='d-inline-block float-sm-right')
            today_stars = ""
            if today_stars_elem:
                today_stars_text = today_stars_elem.text.strip()
                today_stars = today_stars_text if "stars today" in today_stars_text else ""
            
            # Create repository info
            repo_info = {
                'title': repo_name,
                'link': full_link,
                'content': self.create_repo_content(repo_name, description, language, stars_text, today_stars)
            }
            
            return repo_info
            
        except Exception as e:
            print(f"❌ 解析仓库信息出错: {e}")
            return None
    
    def create_repo_content(self, name: str, description: str, language: str, stars: str, today_stars: str) -> str:
        """Create formatted content for repository"""
        content_parts = [
            f"Repository: {name}",
            f"Description: {description}",
            f"Programming Language: {language}",
            f"Total Stars: {stars}",
        ]
        
        if today_stars:
            content_parts.append(f"Today's Growth: {today_stars}")
        
        return "\n".join(content_parts)
    
    def get_repository_content(self, repo_link: str) -> str:
        """Get detailed content from repository README (simplified version)"""
        try:
            # For GitHub repos, we'll use the repository description and basic info
            # rather than trying to parse the full README
            return f"GitHub repository: {repo_link}"
        except Exception as e:
            print(f"❌ 获取仓库详情失败: {repo_link}, 错误: {e}")
            return "无法获取仓库详情"
    
    def get_news_list(self) -> List[Dict[str, Any]]:
        """Get complete repository list with content (compatible with news handler)"""
        repos_list = self.get_trending_repositories(time_range="daily", limit=5)
        
        # Process repositories to match expected format
        processed_repos = []
        for repo in tqdm(repos_list, desc="🚀 Processing GitHub trending repos"):
            try:
                # The content is already created in parse_repository_info
                processed_repos.append(repo)
            except Exception as e:
                print(f"❌ 处理仓库失败: {e}")
                continue
        
        return processed_repos


def get_news_list():
    """Legacy function for backward compatibility"""
    scraper = GitHubTrendingScraper()
    return scraper.get_news_list()


if __name__ == '__main__':
    scraper = GitHubTrendingScraper()
    repos = scraper.get_news_list()
    print(f"✅ 获取到 {len(repos)} 个热门仓库")
    for item in repos:
        print(f"  - {item['title']}")
        print(f"    {item['link']}")
        print()
