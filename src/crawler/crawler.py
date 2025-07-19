#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trafilatura最佳实践代码
支持批量处理、错误处理、多种输出格式和配置优化
"""
from markdownify import markdownify as md
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

    
class Crawler:
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

    def crawl(self, url: str):
        """
        爬取单个URL并提取内容
        
        Args:
            url: 目标URL
            
        Returns:
            ExtractResult对象
        """
        result = self.extract_content(url)
        content = f"# {result.title}\n\n{result.content}"
        content = md(content)
        if len(content) > 1000:
            content = content[:1000] + "..."
        return content