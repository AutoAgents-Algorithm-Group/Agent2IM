#!/usr/bin/env python3
"""
Product Hunt 爬虫

使用 Playwright 绕过 Cloudflare，并支持 domloaded 等待策略
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page
from tqdm import tqdm
import requests


class ProductHuntScraper:
    """Product Hunt 爬虫类，使用 Playwright 绕过 Cloudflare"""
    
    BASE_URL = "https://www.producthunt.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def get_current_week_number(self) -> int:
        """获取当前周数"""
        return datetime.now().isocalendar()[1]
    
    def get_title_and_link_list_with_playwright(self) -> List[Dict[str, str]]:
        """
        使用 Playwright 获取 Product Hunt 产品列表，绕过 Cloudflare
        
        Returns:
            List[Dict[str, str]]: 包含产品信息的列表
        """
        print("🎭 使用 Playwright 获取 Product Hunt 数据...")
        
        # 计算目标URL - 优先使用上周数据（因为当周数据可能不完整）
        current_year = datetime.now().year
        current_week = self.get_current_week_number()
        
        # 尝试多个可能有数据的周（从最近往前找）
        urls_to_try = []
        
        # 从上周开始往前推（避免当前周可能没有数据的问题，特别是周一凌晨）
        for weeks_back in range(1, 6):  # 从1开始，避免当前周
            target_week = current_week - weeks_back
            target_year = current_year
            
            # 处理跨年情况
            if target_week <= 0:
                target_week += 52
                target_year -= 1
            
            # 确保周数在合理范围内
            if target_week > 0 and target_week <= 52:
                urls_to_try.append(f"{self.BASE_URL}/leaderboard/weekly/{target_year}/{target_week}")
        
        print(f"🗓️ 将尝试获取最近5周的数据（跳过当前周，因为可能还没有数据）...")
        
        # 第一个 URL 尝试两次
        first_url = urls_to_try[0]
        for attempt in range(2):
            print(f"🌐 尝试访问 (第{attempt + 1}次): {first_url}")
            try:
                products = self._scrape_with_playwright(first_url)
                if products:
                    print(f"✅ 成功获取 {len(products)} 个产品")
                    return products
                else:
                    print(f"⚠️ 第{attempt + 1}次尝试未获取到产品数据")
            except Exception as e:
                print(f"❌ 第{attempt + 1}次访问失败: {e}")
                if attempt == 0:  # 第一次失败后等待一下再重试
                    print("⏳ 等待 3 秒后重试...")
                    time.sleep(3)
        
        # 如果第一个 URL 两次都失败，尝试第二个 URL
        if len(urls_to_try) > 1:
            second_url = urls_to_try[1]
            print(f"🌐 尝试访问备选URL: {second_url}")
            try:
                products = self._scrape_with_playwright(second_url)
                if products:
                    print(f"✅ 成功获取 {len(products)} 个产品")
                    return products
                else:
                    print(f"⚠️ 备选URL未获取到产品数据")
            except Exception as e:
                print(f"❌ 备选URL访问失败: {e}")
        
        print("❌ 所有URL都访问失败")
        return []
    
    def _scrape_with_playwright(self, url: str) -> List[Dict[str, str]]:
        """
        使用 Playwright 爬取指定URL的产品数据
        
        Args:
            url: 要爬取的URL
            
        Returns:
            List[Dict[str, str]]: 产品列表
        """
        try:
            with sync_playwright() as p:
                # 启动浏览器，配置反检测参数
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                    ]
                )
                
                # 创建上下文，模拟真实用户
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = context.new_page()
                
                # 注入反检测脚本
                page.add_init_script("""
                    // 移除 webdriver 标识
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // 模拟真实的 navigator 属性
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // 移除自动化标识
                    delete window.chrome.loadTimes;
                    delete window.chrome.csi;
                    delete window.chrome.app;
                """)
                
                print("🌐 正在访问页面...")
                
                # 访问页面，使用 domcontentloaded 等待策略
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                print("⏳ 等待页面加载和 Cloudflare 验证...")
                
                # 等待初始加载
                page.wait_for_timeout(random.randint(3000, 6000))
                
                # 检查是否遇到 Cloudflare
                initial_content = page.content()
                if any(cf_indicator in initial_content for cf_indicator in [
                    "Just a moment", "Checking your browser", "cf-browser-verification", 
                    "DDoS protection", "cloudflare"
                ]):
                    print("🔄 检测到 Cloudflare，等待验证完成...")
                    
                    # 更长时间的等待
                    page.wait_for_timeout(random.randint(10000, 15000))
                    
                    # 尝试重新加载页面
                    try:
                        page.reload(wait_until='domcontentloaded', timeout=30000)
                        page.wait_for_timeout(random.randint(3000, 5000))
                    except Exception as e:
                        print(f"⚠️ 重新加载失败，继续尝试: {e}")
                
                # 滚动页面以触发懒加载
                print("📜 滚动页面加载更多内容...")
                for i in range(3):
                    page.evaluate(f"window.scrollTo(0, document.body.scrollHeight/3 * {i + 1});")
                    page.wait_for_timeout(random.randint(1000, 2000))
                
                # 等待页面稳定
                page.wait_for_timeout(3000)
                
                # 获取最终页面内容，处理导航问题
                max_content_attempts = 3
                content = None
                
                for content_attempt in range(max_content_attempts):
                    try:
                        content = page.content()
                        print(f"📄 页面内容长度: {len(content)} 字符")
                        break
                    except Exception as content_error:
                        if "navigating" in str(content_error).lower():
                            print(f"⚠️ 页面正在导航中，坚持当前URL，等待后重试 ({content_attempt + 1}/{max_content_attempts})")
                            page.wait_for_timeout(random.randint(3000, 5000))
                            continue
                        else:
                            raise content_error
                
                browser.close()
                
                if not content:
                    print("❌ 无法获取页面内容，页面可能在持续导航")
                    return []
                
                # 解析页面内容
                return self._parse_product_hunt_content(content, url)
                
        except Exception as e:
            print(f"❌ Playwright 爬取失败: {e}")
            raise e
    
    def _parse_product_hunt_content(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """
        解析 Product Hunt 页面内容，提取产品信息
        
        Args:
            content: 页面HTML内容
            base_url: 基础URL
            
        Returns:
            List[Dict[str, str]]: 产品列表
        """
        soup = BeautifulSoup(content, 'lxml')
        products = []
        
        print("🔍 解析页面内容...")
        
        # 首先检查是否有"No posts for this date"的提示
        text_content = soup.get_text()
        if "No posts for this date" in text_content:
            print("⚠️ 该周没有产品数据，页面显示: 'No posts for this date'")
            return []
        
        # 专门查找Product Hunt排行榜产品 - 使用发现的正确选择器
        product_selectors = [
            # 真正的产品元素选择器（基于用户发现）
            '[data-test^="post-item-"]',  # 精确匹配 post-item-数字 格式
            'section[data-test^="post-item-"]',  # section 标签的产品项
            # 备选选择器
            '[data-test*="post-item"]',
            '[data-test*="product"]',
            '[data-testid*="product"]', 
            '.product-item',
            '.leaderboard-item',
            '[class*="product"]',
            '[class*="leaderboard"]',
            # 通用的排行榜项目选择器
            '[data-test*="item"]',
            '.item',
            'li',
            'article'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"🎯 使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                product_elements.extend(elements)
                if len(product_elements) >= 20:  # 找到足够多的元素就停止
                    break
        
        if not product_elements:
            print("🔍 未找到产品容器，尝试直接查找产品链接...")
            # 查找产品链接 - Product Hunt 的产品通常使用 /posts/ 路径
            all_links = soup.find_all('a', href=True)
            post_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # 严格筛选真正的产品链接
                if (href and 
                    '/posts/' in href and 
                    text and 
                    len(text) > 2 and 
                    len(text) < 100 and
                    not any(skip in text.lower() for skip in [
                        'login', 'signup', 'about', 'terms', 'privacy', 'help',
                        'see more', 'view all', 'launch', 'coming soon', 'archive'
                    ])):
                    post_links.append(link)
            
            print(f"🎯 找到 {len(post_links)} 个产品链接")
            
            if post_links:
                product_elements = post_links
            else:
                print("❌ 未找到任何产品元素")
                return []
        
        # 处理找到的产品元素
        seen_urls = set()
        seen_titles = set()
        
        for element in product_elements:
            try:
                # 从元素中提取产品信息
                product_info = self._extract_product_from_element(element, base_url)
                
                if product_info and product_info['link'] not in seen_urls:
                    title_key = product_info['title'].lower().strip()
                    
                    # 过滤明显不是产品的项目
                    if (len(product_info['title']) > 2 and 
                        title_key not in seen_titles and
                        not any(skip in title_key for skip in [
                            'see more', 'view all', 'launch', 'coming soon', 'archive',
                            'newsletter', 'category', 'leaderboard', 'forum'
                        ])):
                        
                        seen_urls.add(product_info['link'])
                        seen_titles.add(title_key)
                        products.append(product_info)
                        
                        # 只取前5个产品
                        if len(products) >= 5:
                            break
                            
            except Exception as e:
                print(f"⚠️ 处理产品元素时出错: {e}")
                continue
        
        print(f"✅ 成功解析 {len(products)} 个产品")
        return products
    
    def _extract_product_from_element(self, element, base_url: str) -> Optional[Dict[str, str]]:
        """
        从HTML元素中提取产品信息
        
        Args:
            element: HTML元素
            base_url: 基础URL
            
        Returns:
            Dict[str, str]: 产品信息，如果提取失败则返回None
        """
        try:
            # 查找产品链接，优先查找 /posts/ 格式的链接
            link_element = None
            
            # 方法1: 查找指向 /posts/ 的链接（这是真正的产品链接）
            post_links = element.find_all('a', href=lambda x: x and '/posts/' in x)
            if post_links:
                link_element = post_links[0]  # 取第一个产品链接
            
            # 方法2: 如果元素本身就是链接
            elif element.name == 'a':
                link_element = element
                
            # 方法3: 在元素内查找任何链接
            else:
                link_element = element.find('a', href=True)
            
            if not link_element:
                return None
            
            href = link_element.get('href', '')
            if not href:
                return None
                
            # 过滤掉明显不是产品的链接
            if any(skip in href.lower() for skip in [
                'header_nav', 'footer', 'sponsor', 'newsletter', 'category', 
                'login', 'signup', 'help', 'about', 'terms', 'privacy'
            ]):
                return None
            
            # 构建完整URL
            if href.startswith('/'):
                full_url = urljoin(self.BASE_URL, href)
            else:
                full_url = href
            
            # 提取标题 - 优先使用aria-label获取干净的产品名称
            title = ""
            
            # 方法1: 优先从链接的aria-label获取产品名称（最干净的方式）
            if link_element.get('aria-label'):
                aria_label = link_element.get('aria-label').strip()
                if aria_label:
                    # 清理aria-label，提取产品名称
                    title = aria_label
                    # 移除常见的前缀/后缀
                    title = title.replace(' on Product Hunt', '')
                    title = title.replace(' - Product Hunt', '')
                    title = title.replace('View ', '')
                    title = title.replace('See ', '')
                    title = title.replace('Visit ', '')
                    title = title.strip()
            
            # 方法2: 从post-item元素中查找其他aria-label
            if not title and 'post-item' in str(element.get('data-test', '')):
                # 查找子元素的aria-label
                for child in element.find_all(attrs={'aria-label': True}):
                    aria_label = child.get('aria-label', '').strip()
                    if aria_label and len(aria_label) > 2 and len(aria_label) < 50:
                        title = aria_label
                        # 清理标题
                        title = title.replace(' on Product Hunt', '')
                        title = title.replace(' - Product Hunt', '')
                        title = title.strip()
                        break
            
            # 方法3: 从链接文本获取（去掉多余信息）
            if not title or len(title) < 3:
                link_text = link_element.get_text().strip()
                if link_text:
                    # 只取前几个词作为产品名称
                    words = link_text.split()
                    if words:
                        # 取前1-3个有意义的词
                        title = ' '.join(words[:3])
            
            # 方法4: 从链接的title属性获取
            if not title or len(title) < 3:
                title = link_element.get('title', '') or link_element.get('alt', '')
                if title:
                    title = title.replace(' on Product Hunt', '').strip()
            
            # 清理标题
            if title:
                title = ' '.join(title.split())
                # 移除常见的后缀
                suffixes_to_remove = [
                    " - Product Hunt", " | Product Hunt", " on Product Hunt",
                    " - PH", " | PH", " (PH)"
                ]
                for suffix in suffixes_to_remove:
                    if title.endswith(suffix):
                        title = title[:-len(suffix)]
            
            if not title or len(title) < 2:
                return None
            
            # 提取日期
            date = self._extract_date_from_url(base_url)
            
            return {
                'title': title,
                'link': full_url,
                'date': date,
                'tag': "Product Hunt"
            }
            
        except Exception as e:
            print(f"⚠️ 提取产品信息失败: {e}")
            return None
    
    def _extract_date_from_url(self, url: str) -> str:
        """从URL中提取日期信息"""
        try:
            # URL格式: /leaderboard/weekly/2024/52
            parts = url.split('/')
            if len(parts) >= 6 and 'weekly' in parts:
                year = int(parts[-2])
                week = int(parts[-1])
                
                # 计算该周的开始日期
                jan_1 = datetime(year, 1, 1)
                week_start = jan_1 + timedelta(weeks=week-1)
                week_start = week_start - timedelta(days=week_start.weekday())
                
                return week_start.strftime('%Y-%m-%d')
        except:
            pass
        
        # 默认返回当前日期
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_title_and_link_list(self) -> List[Dict[str, str]]:
        """
        获取产品标题和链接列表（主方法）
        
        Returns:
            List[Dict[str, str]]: 产品列表
        """
        try:
            # 优先使用 Playwright 方法
            return self.get_title_and_link_list_with_playwright()
        except Exception as e:
            print(f"❌ Playwright 方法失败: {e}")
            return []
    
    def get_news_content(self, url: str) -> str:
        """
        获取单个产品的详细内容（进入产品页面获取真实标题和描述）
        
        Args:
            url: 产品页面URL
            
        Returns:
            str: 产品描述内容
        """
        print(f"📖 获取产品详细信息: {url}")
        
        # 实现重试机制，类似排行榜页面
        max_attempts = 5
        
        for attempt in range(max_attempts):
            print(f"🔄 产品页面尝试 {attempt + 1}/{max_attempts}")
            
            try:
                result = self._get_product_content_single_attempt(url)
                
                # 检查是否成功获取到真实内容（不是Cloudflare页面）
                if (result and 
                    "Verifying you are human" not in result and 
                    "Just a moment" not in result and
                    "www.producthunt.com" not in result):
                    return result
                else:
                    print(f"⚠️ 第{attempt + 1}次尝试获取到的可能是Cloudflare页面")
                    if attempt < max_attempts - 1:
                        print("⏳ 等待3秒后重试...")
                        time.sleep(3)
                        
            except Exception as e:
                print(f"❌ 第{attempt + 1}次尝试失败: {e}")
                if attempt < max_attempts - 1:
                    print("⏳ 等待3秒后重试...")
                    time.sleep(3)
        
        # 如果所有尝试都失败，返回从URL提取的产品名
        product_slug = url.split('/')[-1].replace('-', ' ').title()
        print(f"⚠️ 所有尝试都失败，使用URL中的产品名: {product_slug}")
        return f"{product_slug} - Product Hunt 产品"
    
    def _get_product_content_single_attempt(self, url: str) -> str:
        """
        单次尝试获取产品内容
        
        Args:
            url: 产品页面URL
            
        Returns:
            str: 产品描述内容
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = context.new_page()
                
                # 反检测脚本
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    delete window.chrome.loadTimes;
                    delete window.chrome.csi;
                    delete window.chrome.app;
                """)
                
                print("🌐 访问产品页面...")
                
                # 访问产品页面
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(random.randint(3000, 6000))
                
                print("✅ 访问产品页面")
                
                # 滚动页面以确保内容加载（添加安全检查）
                for i in range(5):
                    try:
                        page.evaluate(f"""
                            if (document.body && document.body.scrollHeight) {{
                                window.scrollTo(0, document.body.scrollHeight/2 * {i + 1});
                            }} else {{
                                window.scrollTo(0, window.innerHeight * {i + 1});
                            }}
                        """)
                        page.wait_for_timeout(random.randint(1000, 2000))
                    except Exception as scroll_error:
                        print(f"⚠️ 滚动失败，跳过: {scroll_error}")
                        break
                
                page.wait_for_timeout(3000)
                
                # 获取页面内容，处理导航问题
                max_content_attempts = 3
                content = None
                
                for content_attempt in range(max_content_attempts):
                    try:
                        content = page.content()
                        break
                    except Exception as content_error:
                        if "navigating" in str(content_error).lower():
                            print(f"⚠️ 产品页面正在导航中，坚持当前URL，等待后重试 ({content_attempt + 1}/{max_content_attempts})")
                            page.wait_for_timeout(random.randint(3000, 5000))
                            continue
                        else:
                            raise content_error
                
                browser.close()
                
                if not content:
                    print("❌ 无法获取产品页面内容，页面可能在持续导航")
                    return "无法获取产品详情"
                
                # 解析产品页面内容
                soup = BeautifulSoup(content, 'lxml')
                
                # 提取产品名称
                product_name = ""
                
                # 尝试多种方式提取产品名称
                name_selectors = [
                    'h1',  # 主标题
                    '[data-test*="product-name"]',
                    '[data-test*="title"]',
                    '.product-title',
                    '.product-name',
                    'meta[property="og:title"]',
                    'title'
                ]
                
                for selector in name_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        if selector.startswith('meta'):
                            text = element.get('content', '')
                        else:
                            text = element.get_text().strip()
                        
                        if text and len(text) > 2 and len(text) < 100:
                            # 清理标题
                            text = ' '.join(text.split())
                            # 移除 Product Hunt 相关后缀
                            suffixes_to_remove = [
                                " - Product Hunt", " | Product Hunt", " on Product Hunt",
                                " - PH", " | PH", " (PH)"
                            ]
                            for suffix in suffixes_to_remove:
                                if text.endswith(suffix):
                                    text = text[:-len(suffix)]
                            
                            product_name = text
                            break
                    
                    if product_name:
                        break
                
                # 提取产品描述
                product_description = ""
                
                # 尝试多种方式提取产品描述
                description_selectors = [
                    'meta[property="og:description"]',
                    'meta[name="description"]',
                    '[data-test*="product-description"]',
                    '[data-test*="description"]',
                    '.product-description',
                    '.description',
                    '.tagline',
                    'p'  # 最后尝试第一个段落
                ]
                
                for selector in description_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        if selector.startswith('meta'):
                            text = element.get('content', '')
                        else:
                            text = element.get_text().strip()
                        
                        # 选择合适长度的描述
                        if text and len(text) > 20 and len(text) < 1000:
                            # 清理描述
                            text = ' '.join(text.split())
                            
                            # 移除 Product Hunt 相关后缀
                            suffixes_to_remove = [
                                " - Product Hunt", " | Product Hunt", " on Product Hunt"
                            ]
                            for suffix in suffixes_to_remove:
                                if text.endswith(suffix):
                                    text = text[:-len(suffix)]
                            
                            product_description = text
                            break
                    
                    if product_description:
                        break
                
                # 组合产品名称和描述
                if product_name and product_description:
                    # 确保描述不重复产品名称
                    if not product_description.lower().startswith(product_name.lower()):
                        final_content = f"{product_name} - {product_description}"
                    else:
                        final_content = product_description
                    
                    print(f"✅ 提取到: {product_name}")
                    print(f"📝 描述: {product_description[:100]}...")
                    return final_content
                    
                elif product_name:
                    print(f"✅ 仅提取到产品名称: {product_name}")
                    return product_name
                    
                elif product_description:
                    print(f"✅ 仅提取到产品描述: {product_description[:100]}...")
                    return product_description
                
                # 如果都没找到，返回 URL 中的产品名
                product_slug = url.split('/')[-1].replace('-', ' ').title()
                print(f"⚠️ 使用URL中的产品名: {product_slug}")
                return f"{product_slug} - Product Hunt 产品"
                
        except Exception as e:
            print(f"❌ 获取产品详细信息失败: {e}")
            # 返回从URL提取的产品名作为备选
            product_slug = url.split('/')[-1].replace('-', ' ').title()
            return f"{product_slug} - Product Hunt 产品"
    
    def get_news_list(self) -> List[Dict[str, str]]:
        """
        获取完整的新闻列表（包含内容）
        
        Returns:
            List[Dict[str, str]]: 包含完整信息的产品列表
        """
        print("📰 获取完整的 Product Hunt 产品列表...")
        
        # 先获取标题和链接列表
        products = self.get_title_and_link_list()
        
        if not products:
            print("❌ 没有获取到任何产品")
            return []
        
        print(f"📝 为 {len(products)} 个产品获取详细内容...")
        
        # 为每个产品获取详细内容，添加 tqdm 进度条
        complete_products = []
        for i, product in enumerate(tqdm(products, desc="🏆 Getting Product Hunt content")):
            try:
                print(f"📖 ({i+1}/{len(products)}) 获取: {product['title']}")
                
                # 获取内容
                content = self.get_news_content(product['link'])
                product['content'] = content
                
                complete_products.append(product)
                
                # 添加随机延迟，避免请求过快
                if i < len(products) - 1:  # 最后一个不需要延迟
                    delay = random.randint(1, 3)
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ 获取产品 {product['title']} 的内容失败: {e}")
                # 即使获取内容失败，也保留基本信息
                product['content'] = "无法获取产品描述"
                complete_products.append(product)
        
        print(f"✅ 成功获取 {len(complete_products)} 个完整产品信息")
        return complete_products


    def get_top_products_of_week(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        获取本周排名前N的产品
        
        Args:
            limit: 返回的产品数量限制
            
        Returns:
            List[Dict[str, str]]: 本周排名前N的产品列表
        """
        print(f"🏆 获取本周排名前 {limit} 的产品...")
        
        products = self.get_title_and_link_list()
        
        if not products:
            print("❌ 未获取到任何产品")
            return []
        
        # 限制返回数量
        top_products = products[:limit]
        
        print(f"✅ 成功获取本周排名前 {len(top_products)} 的产品")
        return top_products


if __name__ == "__main__":
    # 测试代码 - 获取本周排名前5的产品
    scraper = ProductHuntScraper()
    top_products = scraper.get_top_products_of_week(5)
    
    if top_products:
        print(f"\n🏆 本周Product Hunt排名前 {len(top_products)} 的产品:")
        print("=" * 60)
        
        for i, product in enumerate(top_products):
            print(f"第 {i+1} 名: {product['title']}")
            print(f"   🔗 链接: {product['link']}")
            print(f"   📅 日期: {product['date']}")
            print(f"   🏷️ 来源: {product['tag']}")
            print()
    else:
        print("❌ 没有获取到任何产品")
