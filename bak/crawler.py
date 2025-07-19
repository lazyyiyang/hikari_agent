#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trafilatura最佳实践代码
支持批量处理、错误处理、多种输出格式和配置优化
"""

import trafilatura
import requests
from urllib.parse import urljoin, urlparse
import json
import time
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trafilatura.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ExtractResult:
    """提取结果数据类"""
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    error: Optional[str] = None
    success: bool = False

class ContentExtractor:
    """内容提取器类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化内容提取器
        
        Args:
            config: 配置字典，包含各种提取参数
        """
        self.config = config or {}
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
        })
        
        # 设置超时
        self.timeout = self.config.get('timeout', 30)
        
        # 配置trafilatura设置
        self.trafilatura_config = trafilatura.settings.use_config()
        self.trafilatura_config.set('DEFAULT', 'EXTRACTION_TIMEOUT', str(self.config.get('extraction_timeout', 30)))
        
    def fetch_url(self, url: str) -> Optional[str]:
        """
        获取URL内容
        
        Args:
            url: 目标URL
            
        Returns:
            HTML内容或None
        """
        try:
            # 使用trafilatura内置的fetch_url（推荐）
            downloaded = trafilatura.fetch_url(url, config=self.trafilatura_config)
            if downloaded:
                return downloaded
                
            # 备用方案：使用requests
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取URL失败 {url}: {e}")
            return None
    
    def extract_content(self, url: str, html: Optional[str] = None) -> ExtractResult:
        """
        提取单个URL的内容
        
        Args:
            url: 目标URL
            html: 可选的HTML内容，如果提供则不会重新下载
            
        Returns:
            ExtractResult对象
        """
        result = ExtractResult(url=url)
        
        try:
            # 获取HTML内容
            if html is None:
                html = self.fetch_url(url)
                
            if not html:
                result.error = "无法获取HTML内容"
                return result
            
            # 基本内容提取
            content = trafilatura.extract(
                html,
                config=self.trafilatura_config,
                include_comments=self.config.get('include_comments', False),
                include_tables=self.config.get('include_tables', True),
                include_images=self.config.get('include_images', False),
                include_links=self.config.get('include_links', False),
                deduplicate=self.config.get('deduplicate', True),
                favor_precision=self.config.get('favor_precision', False),
                favor_recall=self.config.get('favor_recall', True),
                url=url
            )
            
            if not content:
                result.error = "无法提取内容"
                return result
            
            result.content = content
            
            # 提取元数据
            metadata = trafilatura.extract_metadata(html, default_url=url)
            if metadata:
                result.title = metadata.title
                result.author = metadata.author
                result.date = metadata.date
                result.description = metadata.description
                result.language = metadata.language
                if hasattr(metadata, 'tags') and metadata.tags:
                    result.tags = metadata.tags
            
            result.success = True
            logger.info(f"成功提取内容: {url}")
            
        except Exception as e:
            result.error = f"提取失败: {str(e)}"
            logger.error(f"提取内容失败 {url}: {e}")
        
        return result
    
    def extract_multiple(self, urls: List[str], max_workers: int = 5) -> List[ExtractResult]:
        """
        并发提取多个URL的内容
        
        Args:
            urls: URL列表
            max_workers: 最大并发数
            
        Returns:
            ExtractResult列表
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.extract_content, url): url 
                for url in urls
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_result = ExtractResult(url=url, error=f"并发执行错误: {str(e)}")
                    results.append(error_result)
                    logger.error(f"并发提取失败 {url}: {e}")
        
        return results
    
    def save_results(self, results: List[ExtractResult], output_file: str, format: str = 'json'):
        """
        保存提取结果
        
        Args:
            results: 提取结果列表
            output_file: 输出文件路径
            format: 输出格式 ('json', 'csv', 'txt')
        """
        try:
            if format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json_data = []
                    for result in results:
                        json_data.append({
                            'url': result.url,
                            'title': result.title,
                            'content': result.content,
                            'author': result.author,
                            'date': result.date,
                            'language': result.language,
                            'description': result.description,
                            'tags': result.tags,
                            'error': result.error,
                            'success': result.success
                        })
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
            elif format == 'csv':
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL', 'Title', 'Content', 'Author', 'Date', 'Language', 'Error', 'Success'])
                    for result in results:
                        writer.writerow([
                            result.url, result.title, result.content, result.author, 
                            result.date, result.language, result.error, result.success
                        ])
                        
            elif format == 'txt':
                with open(output_file, 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(f"URL: {result.url}\n")
                        f.write(f"Title: {result.title}\n")
                        f.write(f"Author: {result.author}\n")
                        f.write(f"Date: {result.date}\n")
                        f.write(f"Success: {result.success}\n")
                        if result.error:
                            f.write(f"Error: {result.error}\n")
                        f.write(f"Content:\n{result.content}\n")
                        f.write("-" * 80 + "\n")
                        
            logger.info(f"结果已保存到: {output_file}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")

def main():
    """主函数示例"""
    # 配置参数
    config = {
        'timeout': 30,
        'extraction_timeout': 30,
        'include_tables': True,
        'include_links': False,
        'include_images': False,
        'deduplicate': True,
        'favor_recall': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    extractor = ContentExtractor(config)
    single_result = extractor.extract_content("https://finance.sina.com.cn/roll/2025-07-14/doc-inffkshv6323997.shtml")
    if single_result.success:
        print(f"标题: {single_result.title}")
        print(f"内容长度: {len(single_result.content or '')}")
        print(f"作者: {single_result.author}")
        print(f"日期: {single_result.date}")
    else:
        print(f"提取失败: {single_result.error}")
    

if __name__ == "__main__":
    main()