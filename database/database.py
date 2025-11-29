# database.py
import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. НАСТРОЙКА БАЗЫ ДАННЫХ
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'science_articles.db')

# Создаем движок SQLite
engine = create_engine(f'sqlite:///{db_path}', echo=False)
Base = declarative_base()


class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    source_name = Column(String)
    source_url = Column(String)
    title = Column(String)
    article_url = Column(String)
    article_direction = Column(String)  # Например: 'IT', 'Biology', 'Physics'

    authors = relationship("Author", back_populates="article", cascade="all, delete-orphan")


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String)  # ФИО автора
    article_id = Column(Integer, ForeignKey('articles.id'))

    article = relationship("Article", back_populates="authors")


# Создаем таблицы
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# ==========================================
# 2. DTO И ФУНКЦИИ РАБОТЫ С ДАННЫМИ
# ==========================================

class ArticleDTO:
    def __init__(self, source_name, source_url, title, authors, article_url, article_direction):
        self.source_name = source_name
        self.source_url = source_url
        self.title = title
        self.authors = authors  # Список имен ['Иванов', 'Петров']
        self.article_url = article_url
        self.article_direction = article_direction


def save_list_of_articles(articles_list):
    session = Session()
    try:
        count = 0
        for dto in articles_list:
            # Проверка дублей по URL
            exists = session.query(Article).filter_by(article_url=dto.article_url).first()
            if exists:
                continue

            new_article = Article(
                source_name=dto.source_name,
                source_url=dto.source_url,
                title=dto.title,
                article_url=dto.article_url,
                article_direction=dto.article_direction
            )

            for author_name in dto.authors:
                new_article.authors.append(Author(name=author_name))

            session.add(new_article)
            count += 1

        session.commit()
        print(f"[DB] Сохранено новых статей: {count}")
    except Exception as e:
        print(f"[DB] Ошибка: {e}")
        session.rollback()
    finally:
        session.close()


def get_all_articles():
    """Получить все статьи из базы данных"""
    session = Session()
    try:
        articles = session.query(Article).all()
        return articles
    except Exception as e:
        print(f"[DB] Ошибка при получении статей: {e}")
        return []
    finally:
        session.close()


def get_articles_by_author(author_name):
    """Найти статьи по имени автора"""
    session = Session()
    try:
        articles = session.query(Article).join(Author).filter(Author.name.ilike(f"%{author_name}%")).all()
        return articles
    except Exception as e:
        print(f"[DB] Ошибка при поиске статей автора: {e}")
        return []
    finally:
        session.close()


def get_all_authors():
    """Получить всех уникальных авторов"""
    session = Session()
    try:
        authors = session.query(Author.name).distinct().all()
        return [author[0] for author in authors]
    except Exception as e:
        print(f"[DB] Ошибка при получении авторов: {e}")
        return []
    finally:
        session.close()


def clear_database():
    """Очистить базу данных"""
    session = Session()
    try:
        session.query(Author).delete()
        session.query(Article).delete()
        session.commit()
        print("[DB] База данных очищена")
    except Exception as e:
        print(f"[DB] Ошибка при очистке базы: {e}")
        session.rollback()
    finally:
        session.close()


# ==========================================
# 3. АЛГОРИТМ РЕКОМЕНДАЦИЙ (ML ENGINE)
# ==========================================

class ScienceRecommender:
    """
    Система рекомендаций.
    Работает напрямую с SQL базой, выгружает данные в Pandas DataFrame.
    """

    def __init__(self, db_engine):
        self.engine = db_engine
        # TfidfVectorizer превращает текст в числа.
        # max_features=5000 - берем топ 5000 самых важных слов
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')

        self.tfidf_matrix = None
        self.cosine_sim_matrix = None

        # Словари для быстрого поиска: Имя <-> Индекс
        self.name_to_idx = {}
        self.idx_to_name = {}

        # Метаданные авторов
        self.authors_metadata = {}

        # Граф соавторства (чтобы не рекомендовать коллег)
        self.coauthors_graph = defaultdict(set)

    def load_data(self):
        """Сбор данных: Группируем тексты статей по имени автора."""
        print("[ML] Загрузка данных...")

        # SQL запрос: берем имя автора, заголовок статьи и направление
        sql_texts = """
        SELECT 
            auth.name as author_name,
            art.title || ' ' || art.article_direction as text_content,
            art.article_direction
        FROM authors auth
        JOIN articles art ON auth.article_id = art.id
        """

        # Читаем SQL сразу в Pandas (быстро)
        df = pd.read_sql(text(sql_texts), self.engine)

        if df.empty:
            print("[ML] База пуста.")
            return []

        # ГРУППИРОВКА: Так как у нас нет таблицы "UniqueAuthor", мы считаем,
        # что одинаковые имена = один человек. Склеиваем все его статьи в одну строку.
        grouped = df.groupby('author_name').agg({
            'text_content': ' '.join,
            'article_direction': lambda x: x.mode()[0] if not x.mode().empty else "Unknown"
        }).reset_index()

        corpus = []

        # Заполняем внутренние структуры
        for idx, row in grouped.iterrows():
            name = row['author_name']
            corpus.append(row['text_content'])

            self.name_to_idx[name] = idx
            self.idx_to_name[idx] = name

            self.authors_metadata[name] = {
                'direction': row['article_direction']
            }

        return corpus

    def build_coauthors_graph(self):
        """Строим связи: кто с кем работал в одной статье."""
        print("[ML] Построение графа связей...")

        # Находим авторов, у которых одинаковый article_id
        sql_graph = """
        SELECT DISTINCT 
            a1.name as author_a, 
            a2.name as author_b
        FROM authors a1
        JOIN authors a2 ON a1.article_id = a2.article_id
        WHERE a1.name != a2.name
        """

        edges = pd.read_sql(text(sql_graph), self.engine)

        for _, row in edges.iterrows():
            self.coauthors_graph[row['author_a']].add(row['author_b'])
            self.coauthors_graph[row['author_b']].add(row['author_a'])  # Двунаправленный граф

    def train(self):
        """Запуск обучения"""
        corpus = self.load_data()
        if not corpus:
            return

        self.build_coauthors_graph()

        print(f"[ML] Векторизация {len(corpus)} авторов...")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)

        print("[ML] Расчет матрицы сходства...")
        self.cosine_sim_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        print("[ML] Готово.")

    def get_recommendations(self, author_name, top_n=3):
        """Главный метод получения рекомендаций"""
        if self.cosine_sim_matrix is None:
            return ["Модель не обучена"]

        if author_name not in self.name_to_idx:
            return [f"Автор '{author_name}' не найден в базе"]

        idx = self.name_to_idx[author_name]

        # Получаем все оценки похожести для этого автора
        scores = list(enumerate(self.cosine_sim_matrix[idx]))
        # Сортируем: от самых похожих к непохожим
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommendations = []
        known_coauthors = self.coauthors_graph[author_name]
        my_direction = self.authors_metadata[author_name]['direction']

        for cand_idx, score in scores:
            cand_name = self.idx_to_name[cand_idx]

            # 1. Не я сам
            if cand_name == author_name:
                continue
            # 2. Не мой коллега
            if cand_name in known_coauthors:
                continue
            # 3. Не мусор (слишком низкое совпадение)
            if score < 0.05:
                continue

            cand_direction = self.authors_metadata[cand_name]['direction']

            # Формируем ответ
            reason = "Схожие научные интересы"
            if my_direction != cand_direction:
                reason += " (Междисциплинарно!)"
                score *= 1.2  # Бонус за междисциплинарность

            recommendations.append({
                'name': cand_name,
                'score': round(score * 100, 1),
                'direction': cand_direction,
                'reason': reason
            })

            if len(recommendations) >= top_n:
                break

        return recommendations

    def get_author_stats(self):
        """Получить статистику по авторам"""
        return {
            'total_authors': len(self.name_to_idx),
            'authors_list': list(self.name_to_idx.keys())[:10]  # Первые 10 авторов
        }


# ==========================================
# 4. ПРИМЕР ЗАПУСКА (MAIN)
# ==========================================

if __name__ == "__main__":
    # 1. Очистим базу для чистого теста (удалите файл .db если хотите сохранить данные)
    if os.path.exists(db_path):
        os.remove(db_path)
        Base.metadata.create_all(engine)
        print("[INIT] База данных пересоздана.")

    # 2. Подготовим тестовые данные
    # Сценарий:
    # - "Петров" и "Иванов" работают вместе над Python (IT)
    # - "Сидоров" пишет про Python (IT), но отдельно (Идеальный кандидат для Петрова)
    # - "Кузнецов" пишет про Биологию (Biology)
    # - "Менделеев" пишет про Химию, но упоминает Python (Слабая связь)

    dataset = [
        ArticleDTO("Source A", "u1", "Анализ данных на языке Python", ["Петров П.П.", "Иванов И.И."], "l1", "IT"),
        ArticleDTO("Source B", "u2", "Разработка нейросетей на Python", ["Сидоров С.С."], "l2", "IT"),
        ArticleDTO("Source C", "u3", "Генетика и молекулярная биология", ["Кузнецов К.К."], "l3", "Biology"),
        ArticleDTO("Source D", "u4", "Химический анализ с использованием Python скриптов", ["Менделеев Д.И."], "l4",
                   "Chemistry"),
    ]

    save_list_of_articles(dataset)

    # 3. Инициализация ML
    recommender = ScienceRecommender(engine)
    recommender.train()

    # 4. Тестирование рекомендаций
    target = "Петров П.П."
    print(f"\n--- Ищем партнеров для: {target} ---")

    recs = recommender.get_recommendations(target)

    if isinstance(recs, list) and recs and isinstance(recs[0], dict):
        for r in recs:
            print(f"Рекомендуем: {r['name']:<15} | Сфера: {r['direction']:<10} | Совпадение: {r['score']}%")
            print(f"   -> {r['reason']}")
    else:
        print(recs)

    # 5. Покажем статистику
    stats = recommender.get_author_stats()
    print(f"\nСтатистика: {stats['total_authors']} авторов в базе")
    print(f"Примеры авторов: {', '.join(stats['authors_list'])}")