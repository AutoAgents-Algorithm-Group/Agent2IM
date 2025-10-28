import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.service.feishu.news import run_news_and_publish

def main():
    """测试新闻采集和推送"""
    run_news_and_publish()

if __name__ == '__main__':
    main()

