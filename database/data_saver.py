import os
import sys
from typing import List

# Добавляем путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import ArticleDTO, save_list_of_articles
    from arxiv_parser import ParsedArticleDTO, ArxivorgArticleParser
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure database.py and arxiv_parser.py are in the same directory")
    exit(1)


class DataSaver:
    """Класс для сохранения спарсенных данных в базу данных."""

    def __init__(self):
        self.parser = ArxivorgArticleParser()

    def convert_to_db_dto(self, parsed_article: ParsedArticleDTO) -> ArticleDTO:
        """Конвертирует ParsedArticleDTO в ArticleDTO для базы данных."""
        return ArticleDTO(
            source_name=parsed_article.source_name,
            source_url=parsed_article.source_url,
            title=parsed_article.title,
            authors=parsed_article.authors,
            article_url=parsed_article.article_url,
            article_direction=parsed_article.article_direction
        )

    def save_parsed_data(self, target_name: str) -> dict:
        """Парсит данные и сохраняет их в базу данных."""
        print(f"Starting parsing and saving for: {target_name}")

        # Парсим данные
        parsed_articles = self.parser.parse(target_name)

        if not parsed_articles:
            return {
                "status": "error",
                "message": "No articles found",
                "articles_count": 0
            }

        # Конвертируем в DTO для базы данных
        db_articles = [self.convert_to_db_dto(article) for article in parsed_articles]

        # Сохраняем в базу данных
        save_list_of_articles(db_articles)

        return {
            "status": "success",
            "message": f"Successfully saved {len(db_articles)} articles",
            "articles_count": len(db_articles),
            "articles": [
                {
                    "title": article.title[:50] + "..." if len(article.title) > 50 else article.title,
                    "authors": article.authors,
                    "direction": article.article_direction
                }
                for article in parsed_articles[:3]  # Показываем только первые 3
            ]
        }

    def parse_multiple_targets(self, target_names: List[str]) -> dict:
        """Парсит и сохраняет данные для нескольких целей."""
        results = {}

        for target in target_names:
            print(f"\n{'=' * 50}")
            print(f"Processing: {target}")
            print(f"{'=' * 50}")

            result = self.save_parsed_data(target)
            results[target] = result

            if result["status"] == "success":
                print(f"✓ Successfully processed {target}: {result['articles_count']} articles")
            else:
                print(f"✗ Failed to process {target}: {result['message']}")

        return results


# Пример использования
if __name__ == "__main__":
    saver = DataSaver()

    # Пример 1: Одиночный запрос
    result = saver.save_parsed_data("machine learning")
    print(f"Result: {result}")

    # Пример 2: Множественные запросы
    targets = ["quantum physics", "neural networks", "bioinformatics"]
    results = saver.parse_multiple_targets(targets)

    print("\nSummary:")
    for target, result in results.items():
        status_icon = "✓" if result["status"] == "success" else "✗"
        print(f"{status_icon} {target}: {result['message']}")