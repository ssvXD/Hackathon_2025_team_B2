from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import List, Optional


@dataclass
class ParsedArticleDTO:
    """DTO для спарсенных статей."""
    source_name: str
    source_url: str
    title: str
    authors: List[str]
    article_url: str
    article_direction: str
    certain_directions: List[str]


class ArxivorgArticleParser:
    """Класс парсера статей для arxiv.org."""

    BASE_URL = 'https://arxiv.org/'
    SEARCH_URL = 'https://arxiv.org/search/?searchtype=all&source=header&size=200&query='
    SOURCE_NAME = 'arxiv.org'

    DIRECTIONS_KEYWORDS = {
        "Информатика и компьютерные науки": [
            "информатика", "компьютер", "программирование", "алгоритм", "база данных",
            "computer science", "informatics", "programming", "algorithm", "database",
            "software", "hardware", "computing", "artificial intelligence", "ai",
            "machine learning", "neural networks", "deep learning", "computer vision",
        ],
        "Математика": [
            "математика", "алгебра", "геометрия", "анализ", "исчисление",
            "mathematics", "algebra", "geometry", "calculus", "analysis",
        ],
        "Физика": [
            "физика", "механика", "термодинамика", "оптика", "электричество",
            "physics", "mechanics", "thermodynamics", "optics", "electricity",
        ],
        # ... остальные направления (можно добавить позже)
    }

    def parse(self, target_name: str) -> List[ParsedArticleDTO]:
        """Основной метод парсинга."""
        print(f"Starting arXiv parser for: {target_name}")
        articles = self.parse_news_page(target_name)
        return articles

    def parse_news_page(self, target_name: str) -> List[ParsedArticleDTO]:
        """Парсит страницу с результатами поиска."""
        result: List[ParsedArticleDTO] = []

        try:
            search_query = target_name.replace(' ', '+')
            url = f"{self.SEARCH_URL}{search_query}"

            print(f"Searching for: {target_name}")
            print(f"URL: {url}")

            html_content = self.get_data(url)
            if not html_content:
                return result

            soup = BeautifulSoup(html_content, 'html.parser')
            search_results = soup.find_all('li', class_='arxiv-result')

            for i, item in enumerate(search_results[:min(10, len(search_results))]):
                try:
                    article_dto = self.parse_article_item(item)
                    if article_dto:
                        result.append(article_dto)
                        print(f"Successfully parsed: {article_dto.title[:50]}...")
                except Exception as e:
                    print(f"Error parsing result {i + 1}: {e}")
                    continue

        except Exception as e:
            print(f"Error in parse_news_page: {e}")

        print(f"Total articles parsed: {len(result)}")
        return result

    def parse_article_item(self, item) -> Optional[ParsedArticleDTO]:
        """Парсит отдельный элемент статьи."""
        try:
            # Извлекаем заголовок
            title_elem = item.find('p', class_='title')
            title = title_elem.get_text().strip() if title_elem else "No title"

            # Извлекаем URL статьи
            link_elems = item.find('p', class_='list-title is-inline-block').find_all('a')
            article_url = ''

            for el in link_elems:
                if el.get_text() == 'other':
                    article_url = el['href']
                    break

            # Извлекаем авторов
            authors = self.parse_authors(item)

            # Извлекаем направление/журнал
            direction = self.parse_direction(item)

            # Определяем направления по ключевым словам
            directions = self.detect_directions(title, direction)

            # Используем первое найденное направление как основное
            main_direction = directions[0] if directions else "Other"

            return ParsedArticleDTO(
                source_name=self.SOURCE_NAME,
                source_url=self.BASE_URL,
                title=title,
                authors=authors,
                article_url=article_url,
                article_direction=main_direction,
                certain_directions=directions
            )

        except Exception as e:
            print(f"Error in parse_article_item: {e}")
            return None

    def detect_directions(self, title: str, description: str) -> List[str]:
        """Определяет научные направления по ключевым словам."""
        directions = []
        text_to_analyze = f"{title} {description}".lower()

        for direction, keywords in self.DIRECTIONS_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    directions.append(direction)
                    break
        return directions

    def parse_authors(self, item) -> List[str]:
        """Парсит список авторов."""
        authors = []
        try:
            authors_elems = item.find('p', class_='authors').find_all('a')
            for elem in authors_elems:
                authors.append(elem.get_text().strip())
        except Exception as e:
            print(f"Error parsing authors: {e}")
        return authors

    def parse_direction(self, item) -> str:
        """Парсит направление/журнал статьи."""
        direction = ""
        try:
            span_elem = item.find('span', class_='abstract-full has-text-grey-dark mathjax')
            if span_elem:
                direction += span_elem.get_text()
        except Exception as e:
            print(f"Error parsing direction: {e}")
        return direction.strip()

    def get_data(self, url: str, request_params: dict | None = None) -> Optional[str]:
        """Получение html строки."""
        try:
            user = UserAgent().random
            request_params = request_params or {}
            headers = {
                'User-Agent': user,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers, timeout=30, **request_params)

            if response.status_code == 200:
                print("Successfully fetched page")
                return response.text
            else:
                print(f"HTTP Error: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_data: {e}")
            return None