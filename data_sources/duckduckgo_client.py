from langchain_community.tools import DuckDuckGoSearchResults


class SearchClient:
    def __init__(self) -> None:
        self.search = DuckDuckGoSearchResults()

    def search(self, query: str) -> str:
        return self.search.invoke(query)


if __name__ == "__main__":
    search_client = SearchClient()
    query = "商汤科技 公司简介 发展历程 核心技术"
    print(search_client.search(query))
