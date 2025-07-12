import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from fake_useragent import UserAgent
import json
import re


import re
from readability import Document
from bs4 import BeautifulSoup
import logging


def get_clean_content(url):
    """
    获取网页的干净正文内容
    
    参数:
        url (str): 目标网页URL
        
    返回:
        str: 清理后的正文文本
    """
    try:
        # 设置请求头模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 获取网页内容
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        # 使用readability提取正文
        doc = Document(response.content)
        main_content = doc.summary()
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', main_content)
        
        # 移除多余空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # 移除常见无关元素
        clean_text = re.sub(r'相关阅读|推荐阅读|延伸阅读|责任编辑[：:].*?\.', '', clean_text)
        
        return clean_text
    
    except Exception as e:
        return f"获取内容失败: {str(e)}"





class BingSearchCrawler:
    def __init__(self):
        self.base_url = "https://www.bing.com/search"
        self.ua = UserAgent()
        self.session = requests.Session()
        self.domains = {
            '新浪财经': 'finance.sina.com.cn',
            '华尔街日报': 'cn.wsj.com',
            '巨潮资讯': 'www.cninfo.com.cn',
            '百度百科': 'baike.baidu.com',
            '知乎': 'www.zhihu.com',
            '微博': 'weibo.com',
            '雪球': 'xueqiu.com',
            '东方财富': 'www.eastmoney.com',
            '腾讯财经': 'finance.qq.com',
            '网易财经': 'money.163.com',
            '同花顺': 'www.10jqka.com.cn',
            '证券时报': 'www.stcn.com',
            '财联社': 'www.cls.cn',
            '第一财经': 'www.yicai.com'
        }

    def get_headers(self):
        """获取随机请求头"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def search(self, query, num_results=10, lang='zh-CN'):
        """
        搜索并返回结果

        Args:
            query (str): 搜索关键词
            num_results (int): 返回结果数量
            lang (str): 语言设置
        """
        results = []
        page = 1

        while len(results) < num_results:
            # 构建搜索URL
            params = {
                'q': query,
                'first': (page - 1) * 10 + 1,  # Bing的分页参数
                'FORM': 'PORE',
                'cc': 'CN' if lang == 'zh-CN' else 'US',
                'setlang': lang
            }

            try:
                # 发送请求，加入5秒超时设置
                response = self.session.get(
                    self.base_url,
                    params=params,
                    headers=self.get_headers(),
                    timeout=5
                )
                response.raise_for_status()

                # 方法1：最安全的处理方式（推荐）
                try:
                    # 先尝试用utf-8解码
                    html = response.content.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果失败则用chardet检测编码
                    import chardet
                    encoding = chardet.detect(response.content)['encoding']
                    if encoding:
                        html = response.content.decode(encoding, errors='replace')  # 用replace避免报错
                    else:
                        print("编码检测失败")
                        continue
                # 解析HTML
                soup = BeautifulSoup(html, 'html.parser')
                # 提取搜索结果
                search_results = soup.find_all('li', class_='b_algo')
                if not search_results:
                    print(f"第 {page} 页没有找到结果")
                    break

                for result in search_results:
                    if len(results) >= num_results:
                        break

                    # 提取标题
                    title_elem = result.find('h2')
                    title = title_elem.get_text(strip=True) if title_elem else "无标题"
                    # 提取链接
                    link = result.find("a").get("href")
                    # 提取描述
                    desc_elem = result.find('p') or result.find('div', class_='b_caption')
                    description = desc_elem.get_text(strip=True) if desc_elem else "无描述"

                    results.append({
                        'title': title,
                        'link': link,
                        'description': description,
                        'rank': len(results) + 1
                    })

                page += 1

                # 随机延时，避免被封
                time.sleep(random.uniform(1, 3))

            except requests.RequestException as e:
                print(f"请求错误: {e}")
                break
            except Exception as e:
                print(f"解析错误: {e}")
                break

        return results[:num_results]

    def save_results(self, results, filename='bing_results.json'):
        """保存搜索结果到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到 {filename}")

    def print_results(self, results):
        """打印搜索结果"""
        print(f"\n共找到 {len(results)} 个结果:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   链接: {result['link']}")
            print(f"   描述: {result['description'][:100]}...")
            print("-" * 80)


# 使用示例
def main():
    # 创建爬虫实例
    crawler = BingSearchCrawler()

    # 搜索关键词
    query = "特斯拉"

    print(f"正在搜索: {query}")

    # 执行搜索
    results = crawler.search(query, num_results=20)

    # 显示结果
    crawler.print_results(results)

    # 保存结果
    # crawler.save_results(results)


if __name__ == "__main__":
    # main()


    url = "https://www.autohome.com.cn/price/bc/brandid_133"
    print(get_clean_content(url))