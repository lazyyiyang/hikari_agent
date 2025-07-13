import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class WebContentExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_content(self, url):
        """
        从给定URL提取干净的正文内容
        
        Args:
            url (str): 目标网页URL
            
        Returns:
            dict: 包含标题、正文和元数据的字典
        """
        try:
            # 发送请求获取网页内容
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除无关元素
            self._remove_unwanted_elements(soup)
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取正文内容
            content = self._extract_main_content(soup)
            
            # 清理文本
            clean_content = self._clean_text(content)
            
            return {
                'url': url,
                'title': title,
                'content': clean_content,
                'length': len(clean_content)
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'title': None,
                'content': None,
                'length': 0
            }
    
    def _remove_unwanted_elements(self, soup):
        """移除不需要的HTML元素"""
        # 要移除的标签
        unwanted_tags = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'form', 'input', 'button', 'iframe', 'embed', 'object',
            'video', 'audio', 'canvas', 'svg', 'noscript', 'meta',
            'link', 'title', 'head'
        ]
        
        # 移除标签
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # 移除具有特定class或id的元素
        unwanted_classes = [
            'ad', 'ads', 'advertisement', 'banner', 'sidebar', 'menu',
            'navigation', 'nav', 'footer', 'header', 'comment', 'comments',
            'social', 'share', 'related', 'recommended', 'popup', 'modal',
            'breadcrumb', 'tag', 'tags', 'category', 'categories'
        ]
        
        for class_name in unwanted_classes:
            # 移除包含这些关键词的class
            for element in soup.find_all(class_=re.compile(class_name, re.I)):
                element.decompose()
            # 移除包含这些关键词的id
            for element in soup.find_all(id=re.compile(class_name, re.I)):
                element.decompose()
    
    def _extract_title(self, soup):
        """提取页面标题"""
        title = None
        
        # 尝试不同的标题提取方法
        title_selectors = [
            'h1',
            'title',
            '[class*="title"]',
            '[id*="title"]',
            'h2'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                break
        
        return title
    
    def _extract_main_content(self, soup):
        """提取主要内容"""
        content = ""
        
        # 尝试不同的内容提取策略
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post"]',
            '[id*="content"]',
            '[id*="article"]',
            '[id*="post"]',
            'main',
            '.entry-content',
            '.post-content',
            '.article-content'
        ]
        
        # 首先尝试特定的内容选择器
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 100:  # 确保内容足够长
                    break
        
        # 如果没有找到合适的内容，尝试提取所有段落
        if not content or len(content) < 100:
            paragraphs = soup.find_all(['p', 'div', 'span'])
            content_parts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # 过滤掉太短的文本
                    content_parts.append(text)
            
            content = ' '.join(content_parts)
        
        return content
    
    def _clean_text(self, text):
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符和符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff\.,!?;:()"\'-]', '', text)
        
        # 移除重复的标点符号
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # 移除过短的句子（可能是导航文本等）
        sentences = text.split('.')
        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return '. '.join(clean_sentences).strip()

# 使用示例
def main():
    extractor = WebContentExtractor()
    
    # 测试URL
    test_urls = [
        "https://www.havefunwithhistory.com/barack-obama-timeline/"
    ]
    
    for url in test_urls:
        print(f"\n提取 {url} 的内容:")
        print("-" * 50)
        
        result = extractor.extract_content(url)
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        else:
            print(f"标题: {result['title']}")
            print(f"内容长度: {result['length']} 字符")
            print(f"内容预览: {result['content'][:1000]}...")

if __name__ == "__main__":
    main()