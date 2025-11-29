import os
import json
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. PARSER ENGINE 
# ==========================================

@dataclass
class ArticleDTO:
    """Данные полученной статьи."""
    source_name: str
    source_url: str
    title: str
    authors: list[str]
    article_url: str
    article_direction: str
    certain_directions: list[str]

class ArxivorgArticleParser:
    """Класс парсера статей для arxiv.org."""
    BASE_URL = 'https://arxiv.org/'
    SEARCH_URL = 'https://arxiv.org/search/?searchtype=all&source=header&query='
    SOURCE_NAME = 'arxiv.org'
    
    DIRECTIONS_KEYWORDS = {
        "Информатика и компьютерные науки": [
            "информатика", "компьютер", "программирование", "алгоритм", "база данных",
            "вычислительная техника", "кибернетика", "искусственный интеллект",
            "машинное обучение", "нейронные сети", "компьютерное зрение", "анализ данных",
            "большие данные", "веб-разработка", "мобильные приложения", "облачные вычисления",
            "кибербезопасность", "криптография", "блокчейн", "виртуальная реальность",
            "интернет вещей", "робототехника", "автоматизация", "цифровизация",
            "программное обеспечение", "аппаратное обеспечение", "сети", "сервер",
            "фронтенд", "бэкенд", "фуллстек", "devops", "agile", "scrum",
            "computer science", "informatics", "programming", "algorithm", "database",
            "software", "hardware", "computing", "artificial intelligence", "ai",
            "machine learning", "neural networks", "deep learning", "computer vision",
            "data science", "big data", "web development", "mobile apps", "cloud computing",
            "cybersecurity", "cryptography", "blockchain", "virtual reality", "vr",
            "internet of things", "iot", "robotics", "automation", "digitalization",
            "frontend", "backend", "fullstack", "devops", "agile", "scrum"
        ],
        "Математика": [
            "математика", "алгебра", "геометрия", "анализ", "исчисление",
            "дифференциальные уравнения", "теория вероятностей", "статистика",
            "численные методы", "оптимизация", "топология", "теория чисел",
            "комбинаторика", "теория графов", "математическая логика", "теория множеств",
            "математическое моделирование", "вычислительная математика", "линейная алгебра",
            "дискретная математика", "функциональный анализ", "теория вероятностей",
            "математическая статистика", "теория игр", "финансовая математика",
            "mathematics", "algebra", "geometry", "calculus", "analysis",
            "differential equations", "probability theory", "statistics",
            "numerical methods", "optimization", "topology", "number theory",
            "combinatorics", "graph theory", "mathematical logic", "set theory",
            "mathematical modeling", "computational mathematics", "linear algebra",
            "discrete mathematics", "functional analysis", "probability",
            "mathematical statistics", "game theory", "financial mathematics"
        ],
        "Физика": [
            "физика", "механика", "термодинамика", "оптика", "электричество",
            "магнетизм", "квантовая физика", "ядерная физика", "астрофизика",
            "теория относительности", "электродинамика", "статистическая физика",
            "физика твердого тела", "физика плазмы", "акустика", "гидродинамика",
            "молекулярная физика", "атомная физика", "физика элементарных частиц",
            "космология", "гравитация", "физика конденсированного состояния",
            "нанофизика", "биофизика", "геофизика",
            "physics", "mechanics", "thermodynamics", "optics", "electricity",
            "magnetism", "quantum physics", "nuclear physics", "astrophysics",
            "relativity", "electrodynamics", "statistical physics",
            "solid state physics", "plasma physics", "acoustics", "hydrodynamics",
            "molecular physics", "atomic physics", "particle physics",
            "cosmology", "gravity", "condensed matter physics",
            "nanophysics", "biophysics", "geophysics"
        ],
        "Химия": [
            "химия", "органическая химия", "неорганическая химия", "аналитическая химия",
            "физическая химия", "биохимия", "химические реакции", "периодическая система",
            "молекулы", "атомы", "соединения", "катализ", "полимеры", "нанохимия",
            "электрохимия", "фотохимия", "радиохимия", "квантовая химия", "стереохимия",
            "химическая кинетика", "химическое равновесие", "химическая термодинамика",
            "материаловедение", "кристаллография", "спектроскопия",
            "chemistry", "organic chemistry", "inorganic chemistry", "analytical chemistry",
            "physical chemistry", "biochemistry", "chemical reactions", "periodic table",
            "molecules", "atoms", "compounds", "catalysis", "polymers", "nanochemistry",
            "electrochemistry", "photochemistry", "radiochemistry", "quantum chemistry",
            "stereochemistry", "chemical kinetics", "chemical equilibrium", "chemical thermodynamics",
            "materials science", "crystallography", "spectroscopy"
        ],
        "Биология": [
            "биология", "генетика", "эволюция", "ботаника", "зоология",
            "микробиология", "молекулярная биология", "клеточная биология",
            "экология", "физиология", "анатомия", "биотехнология", "биоинформатика",
            "генная инженерия", "иммунология", "вирусология", "биохимия",
            "нейробиология", "биофизика", "палеонтология", "эмбриология",
            "цитология", "гистология", "систематика", "биогеография",
            "biology", "genetics", "evolution", "botany", "zoology",
            "microbiology", "molecular biology", "cell biology",
            "ecology", "physiology", "anatomy", "biotechnology", "bioinformatics",
            "genetic engineering", "immunology", "virology", "biochemistry",
            "neuroscience", "biophysics", "paleontology", "embryology",
            "cytology", "histology", "taxonomy", "biogeography"
        ],
        "Русский язык и литература": [
            "русский язык", "литература", "грамматика", "синтаксис", "морфология",
            "поэзия", "проза", "фольклор", "лингвистика", "филология",
            "пушкин", "толстой", "достоевский", "чехов", "русская классика",
            "словообразование", "орфография", "пунктуация", "стилистика",
            "риторика", "литературоведение", "поэтика", "текстология",
            "диалектология", "палеография", "семантика", "прагматика",
            "russian language", "literature", "grammar", "syntax", "morphology",
            "poetry", "prose", "folklore", "linguistics", "philology",
            "pushkin", "tolstoy", "dostoevsky", "chekhov", "russian classics",
            "word formation", "spelling", "punctuation", "stylistics",
            "rhetoric", "literary criticism", "poetics", "textual criticism",
            "dialectology", "paleography", "semantics", "pragmatics"
        ],
        "История": [
            "история", "археология", "древний мир", "средневековье", "новое время",
            "исторические события", "цивилизация", "культура", "историография",
            "всемирная история", "отечественная история", "история россии",
            "античность", "ренессанс", "просвещение", "революция", "война",
            "исторические источники", "архивы", "музееведение", "палеография",
            "нумизматика", "геральдика", "историческая география",
            "history", "archaeology", "ancient world", "middle ages", "modern era",
            "historical events", "civilization", "culture", "historiography",
            "world history", "national history", "russian history",
            "antiquity", "renaissance", "enlightenment", "revolution", "war",
            "historical sources", "archives", "museology", "paleography",
            "numismatics", "heraldry", "historical geography"
        ],
        "Экономика": [
            "экономика", "макроэкономика", "микроэкономика", "финансы", "банки",
            "рынок", "инвестиции", "бизнес", "менеджмент", "маркетинг",
            "бухгалтерия", "аудит", "налоги", "бюджет", "инфляция",
            "безработица", "валютный курс", "фондовый рынок", "криптовалюты",
            "предпринимательство", "логистика", "снабжение", "продажи",
            "экономический рост", "международная торговля", "государственные финансы",
            "economics", "macroeconomics", "microeconomics", "finance", "banks",
            "market", "investment", "business", "management", "marketing",
            "accounting", "audit", "taxes", "budget", "inflation",
            "unemployment", "exchange rate", "stock market", "cryptocurrency",
            "entrepreneurship", "logistics", "supply chain", "sales",
            "economic growth", "international trade", "public finance"
        ],
        # ... (Можно добавить остальные категории, но для MVP этого достаточно)
    }

    def parse(self, target_name: str) -> list[ArticleDTO]:
        """Запуск парсера."""
        print(f"[PARSER] Starting parser for: {target_name}")
        articles = self.parse_news_page(target_name)
        return articles

    def parse_news_page(self, target_name: str) -> list[ArticleDTO]:
        """Основной парсер статей."""
        result: list[ArticleDTO] = []
        try:
            search_query = target_name.replace(' ', '+')
            url = f"{self.SEARCH_URL}{search_query}"
            print(f"[PARSER] URL: {url}")

            html_content = self.get_data(url)
            if not html_content: return result

            soup = BeautifulSoup(html_content, 'html.parser')
            search_results = soup.find_all('li', class_='arxiv-result')

            # Ограничим первыми 10 результатами для скорости
            for i, item in enumerate(search_results[:10]):
                try:
                    article_dto = self.parse_article_item(item)
                    if article_dto:
                        result.append(article_dto)
                except Exception as e:
                    print(f"[PARSER] Error parsing result {i + 1}: {e}")
                    continue
        except Exception as e:
            print(f"[PARSER] Error in parse_news_page: {e}")

        print(f"[PARSER] Total parsed: {len(result)}")
        return result

    def parse_article_item(self, item) -> ArticleDTO | None:
        try:
            title_elem = item.find('p', class_='title')
            title = title_elem.get_text().strip() if title_elem else "No title"

            link_elems = item.find('p', class_='list-title is-inline-block').find_all('a')
            article_url = ''
            for el in link_elems:
                if el.get_text() == 'pdf': # Приоритет на PDF
                    article_url = el['href']
                    break
            if not article_url and link_elems: article_url = link_elems[0]['href']

            authors = self.parse_authors(item)
            direction = self.parse_direction(item)
            source_url = self.BASE_URL

            directions = []
            # Проверка по ключевым словам
            text_to_check = (title + " " + direction).lower()
            for category, keywords in self.DIRECTIONS_KEYWORDS.items():
                for k in keywords:
                    if k in text_to_check:
                        if category not in directions:
                            directions.append(category)
                        break # Достаточно одного совпадения для категории

            return ArticleDTO(
                source_name=self.SOURCE_NAME,
                source_url=source_url,
                title=title,
                authors=authors,
                article_url=article_url,
                article_direction=direction,
                certain_directions=directions
            )
        except Exception as e:
            print(f"[PARSER] Item error: {e}")
            return None

    def parse_authors(self, item) -> list[str]:
        authors = []
        try:
            authors_elems = item.find('p', class_='authors').find_all('a')
            for elem in authors_elems: authors.append(elem.get_text().strip())
        except: pass
        return authors

    def parse_direction(self, item) -> str:
        direction = ""
        try:
            span_elem = item.find('span', class_='abstract-full')
            if span_elem: direction = span_elem.get_text().strip()
        except: pass
        return direction

    def get_data(self, url: str) -> str | None:
        try:
            headers = {'User-Agent': UserAgent().random}
            resp = requests.get(url, headers=headers, timeout=15)
            return resp.text if resp.status_code == 200 else None
        except Exception as e:
            print(f"[PARSER] HTTP Error: {e}")
            return None

# ==========================================
# 2. FLASK & DATABASE SETUP
# ==========================================

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database/science_articles.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

likes_table = Table('likes', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('article_id', Integer, ForeignKey('articles.id'))
)

authors_articles = Table('authors_articles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('article_id', Integer, ForeignKey('articles.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String, default="user")
    academic_status = Column(String)
    city = Column(String)
    age = Column(Integer)
    area = Column(String)
    
    articles = relationship("Article", secondary=authors_articles, back_populates="authors_users")
    liked_articles = relationship("Article", secondary=likes_table)

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    area = Column(String) 
    citations = Column(Integer, default=0)
    authors_text = Column(String) # Сохраняем список авторов строкой
    
    authors_users = relationship("User", secondary=authors_articles, back_populates="articles")

Base.metadata.create_all(engine)

# ==========================================
# 3. ML ENGINE
# ==========================================

class ScienceRecommender:
    def __init__(self, db_engine):
        self.engine = db_engine
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000)
        self.tfidf_matrix = None
        self.name_to_idx = {}
        self.idx_to_name = {}
        self.authors_metadata = {}

    def load_and_train(self):
        print("[ML] Retraining model...")
        session = Session()
        users = session.query(User).all()
        corpus = []
        current_idx = 0
        self.name_to_idx = {}
        self.idx_to_name = {}
        
        for user in users:
            # Текст для ML: заголовки статей + область
            text_content = " ".join([a.title for a in user.articles]) + " " + (user.area or "")
            
            corpus.append(text_content)
            full_name = f"{user.last_name} {user.first_name}"
            self.name_to_idx[full_name] = current_idx
            self.idx_to_name[current_idx] = full_name
            self.authors_metadata[full_name] = {'area': user.area}
            current_idx += 1
            
        session.close()
        if corpus:
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
                self.cosine_sim_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
            except ValueError:
                print("[ML] Not enough data to train yet.")

    def get_recommendations(self, last_name, first_name):
        full_name = f"{last_name} {first_name}"
        if self.tfidf_matrix is None or full_name not in self.name_to_idx: return []
        
        idx = self.name_to_idx[full_name]
        scores = list(enumerate(self.cosine_sim_matrix[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        recs = []
        for cand_idx, score in scores:
            cand_name = self.idx_to_name[cand_idx]
            if cand_name == full_name: continue
            if score < 0.05: continue # Отсекаем мусор
            
            recs.append({
                'name': cand_name,
                'score': int(score * 100),
                'area': self.authors_metadata[cand_name]['area'],
                'reason': 'Схожие научные интересы'
            })
        return recs[:3]

# Инициализация
recommender = ScienceRecommender(engine)
arxiv_parser = ArxivorgArticleParser()

# ==========================================
# 4. API ROUTES
# ==========================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    session = Session()
    
    if session.query(User).filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    last_name = data.get('lastName', '')
    
    # 1. ЗАПУСК ПАРСЕРА
    parsed_articles = arxiv_parser.parse(last_name)
    
    # 2. Определение сферы (берем самую частую из найденных или "General")
    user_area = "General Science"
    if parsed_articles:
        # Собираем все определенные направления
        all_dirs = []
        for dto in parsed_articles:
            all_dirs.extend(dto.certain_directions)
        
        if all_dirs:
            # Находим самое частое
            from collections import Counter
            user_area = Counter(all_dirs).most_common(1)[0][0]
    
    # Если парсер ничего не нашел, оставляем то, что выбрал пользователь в форме (если было)
    if user_area == "General Science" and data.get('area'):
        user_area = data.get('area')

    new_user = User(
        email=data['email'], password=data['password'], first_name=data['firstName'],
        last_name=last_name, role=data['role'], academic_status=data['academicStatus'],
        city=data['city'], age=data.get('age'), area=user_area
    )
    
    # 3. Сохранение статей
    for dto in parsed_articles:
        # Проверяем дубликаты по URL
        existing_art = session.query(Article).filter_by(url=dto.article_url).first()
        
        if existing_art:
            new_user.articles.append(existing_art)
        else:
            # Берем первое определенное направление для статьи или General
            art_area = dto.certain_directions[0] if dto.certain_directions else "Scientific Article"
            
            new_art = Article(
                title=dto.title,
                url=dto.article_url,
                area=art_area,
                authors_text=", ".join(dto.authors),
                citations=0
            )
            session.add(new_art)
            new_user.articles.append(new_art)
            
    session.add(new_user)
    session.commit()
    
    # 4. Переобучение ML
    recommender.load_and_train()

    res_user = {
        'id': new_user.id, 'email': new_user.email, 'firstName': new_user.first_name,
        'lastName': new_user.last_name, 'role': new_user.role, 'area': new_user.area,
        'articles': [a.id for a in new_user.articles], 'likedArticles': []
    }
    session.close()
    return jsonify(res_user)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    session = Session()
    user = session.query(User).filter_by(email=data['email'], password=data['password']).first()
    if user:
        recs = recommender.get_recommendations(user.last_name, user.first_name)
        res = {
            'id': user.id, 'email': user.email, 'firstName': user.first_name, 'lastName': user.last_name,
            'role': user.role, 'area': user.area, 
            'articles': [a.id for a in user.articles],
            'likedArticles': [a.id for a in user.liked_articles],
            'recommendations': recs
        }
        session.close()
        return jsonify(res)
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/articles', methods=['GET'])
def get_articles():
    session = Session()
    articles = session.query(Article).all()
    res = []
    for a in articles:
        likes = session.query(likes_table).filter_by(article_id=a.id).count()
        res.append({
            'id': a.id, 'title': a.title, 'area': a.area, 
            'citations': a.citations, 'likes': likes, 'url': a.url,
            'authors': a.authors_text.split(', ') if a.authors_text else []
        })
    session.close()
    return jsonify(res)

@app.route('/api/users', methods=['GET'])
def get_users():
    session = Session()
    users = session.query(User).all()
    res = []
    for u in users:
        res.append({
            'id': u.id, 'email': u.email, 'firstName': u.first_name, 'lastName': u.last_name,
            'role': u.role, 'academicStatus': u.academic_status, 'city': u.city, 'age': u.age, 'area': u.area,
            'articles': [a.id for a in u.articles],
            'likedArticles': [a.id for a in u.liked_articles]
        })
    session.close()
    return jsonify(res)

@app.route('/api/like', methods=['POST'])
def like():
    data = request.json
    session = Session()
    u = session.query(User).get(data['userId'])
    a = session.query(Article).get(data['articleId'])
    if a in u.liked_articles: u.liked_articles.remove(a)
    else: u.liked_articles.append(a)
    session.commit()
    session.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Создаем админа при первом запуске
    s = Session()
    if not s.query(User).filter_by(email='admin@sirius.ru').first():
        s.add(User(email='admin@sirius.ru', password='admin', first_name='System', last_name='Admin', role='admin', area='Admin'))
        s.commit()
    s.close()
    
    recommender.load_and_train()
    app.run(debug=True, port=5000)
