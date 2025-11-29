import os
import json
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, text, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from collections import defaultdict
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. PARSER ENGINE (ТВОЙ КОД)
# ==========================================

@dataclass
class ArticleDTO:
    source_name: str
    source_url: str
    title: str
    authors: list[str]
    article_url: str
    article_direction: str
    certain_directions: list[str]

class ArxivorgArticleParser:
    BASE_URL = 'https://arxiv.org/'
    SEARCH_URL = 'https://arxiv.org/search/?searchtype=all&source=header&query='
    SOURCE_NAME = 'arxiv.org'
    
    # (Словарь DIRECTIONS_KEYWORDS сокращен для краткости кода, но логика та же)
    DIRECTIONS_KEYWORDS = {
        "IT": ["computer", "informatics", "neural", "learning", "data", "code", "algorithm"],
        "Physics": ["physics", "quantum", "mechanics", "gravity", "spin"],
        "Biology": ["biology", "gene", "dna", "cell", "evolution"],
        "Math": ["math", "algebra", "geometry", "equation", "logic"],
        "Chemistry": ["chemistry", "molecule", "reaction", "atom"]
    }

    def parse(self, target_name: str) -> list[ArticleDTO]:
        print(f"[PARSER] Ищу статьи для: {target_name}...")
        return self.parse_news_page(target_name)

    def parse_news_page(self, target_name: str) -> list[ArticleDTO]:
        result = []
        try:
            search_query = target_name.replace(' ', '+')
            url = f"{self.SEARCH_URL}{search_query}"
            html_content = self.get_data(url)
            if not html_content: return result

            soup = BeautifulSoup(html_content, 'html.parser')
            search_results = soup.find_all('li', class_='arxiv-result')

            for item in search_results[:5]: # Берем топ-5 для скорости
                dto = self.parse_article_item(item)
                if dto: result.append(dto)
        except Exception as e:
            print(f"[PARSER ERROR] {e}")
        return result

    def parse_article_item(self, item) -> ArticleDTO | None:
        try:
            title_elem = item.find('p', class_='title')
            title = title_elem.get_text().strip() if title_elem else "No title"
            
            link_elems = item.find('p', class_='list-title is-inline-block').find_all('a')
            article_url = ''
            for el in link_elems:
                if el.get_text() == 'pdf': # Берем ссылку на PDF если есть
                    article_url = el['href']
                    break
            if not article_url: article_url = link_elems[0]['href']

            authors = self.parse_authors(item)
            direction = self.parse_direction(item)

            # Определяем категорию
            found_directions = []
            text_for_search = (title + " " + direction).lower()
            for key, keywords in self.DIRECTIONS_KEYWORDS.items():
                if any(k in text_for_search for k in keywords):
                    found_directions.append(key)
            
            # Если категорию не нашли, ставим General
            if not found_directions: found_directions = ["General Science"]

            return ArticleDTO(
                source_name=self.SOURCE_NAME,
                source_url=self.BASE_URL,
                title=title,
                authors=authors,
                article_url=article_url,
                article_direction=direction,
                certain_directions=found_directions
            )
        except:
            return None

    def parse_authors(self, item) -> list[str]:
        authors = []
        try:
            authors_elems = item.find('p', class_='authors').find_all('a')
            for elem in authors_elems: authors.append(elem.get_text().strip())
        except: pass
        return authors

    def parse_direction(self, item) -> str:
        try:
            span = item.find('span', class_='abstract-full')
            return span.get_text().strip()[:100] if span else ""
        except: return ""

    def get_data(self, url: str) -> str | None:
        try:
            headers = {'User-Agent': UserAgent().random}
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.text if resp.status_code == 200 else None
        except: return None

# ==========================================
# 2. НАСТРОЙКА FLASK И БД
# ==========================================

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'science_articles.db')
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
    url = Column(String) # Ссылка на оригинал
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
        print("[ML] Переобучение модели на новых данных...")
        session = Session()
        users = session.query(User).all()
        corpus = []
        current_idx = 0
        self.name_to_idx = {}
        self.idx_to_name = {}
        
        for user in users:
            # Собираем текст из заголовков его статей
            text_content = " ".join([a.title for a in user.articles])
            if not text_content: text_content = user.area or "General" # Если статей нет, берем сферу
            
            corpus.append(text_content)
            full_name = f"{user.last_name} {user.first_name}"
            self.name_to_idx[full_name] = current_idx
            self.idx_to_name[current_idx] = full_name
            self.authors_metadata[full_name] = {'area': user.area}
            current_idx += 1
            
        session.close()
        if corpus:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            self.cosine_sim_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

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
            if score < 0.05: continue
            
            recs.append({
                'name': cand_name,
                'score': int(score * 100),
                'area': self.authors_metadata[cand_name]['area'],
                'reason': 'Схожие публикации'
            })
        return recs[:3]

recommender = ScienceRecommender(engine)
arxiv_parser = ArxivorgArticleParser()

# ==========================================
# 4. API Routes
# ==========================================

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
    return jsonify({'error': 'Auth failed'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    session = Session()
    
    if session.query(User).filter_by(email=data['email']).first():
        return jsonify({'error': 'Email busy'}), 400

    last_name = data.get('lastName', '')
    
    # === МАГИЯ: ЗАПУСКАЕМ ПАРСЕР ===
    parsed_articles = arxiv_parser.parse(last_name)
    
    # Определяем основную сферу ученого по его статьям
    user_area = data.get('area', 'General')
    if parsed_articles:
        user_area = parsed_articles[0].certain_directions[0]

    new_user = User(
        email=data['email'], password=data['password'], first_name=data['firstName'],
        last_name=last_name, role=data['role'], academic_status=data['academicStatus'],
        city=data['city'], age=data.get('age'), area=user_area
    )
    
    # Сохраняем найденные статьи в БД
    count_new = 0
    for dto in parsed_articles:
        # Проверяем, есть ли такая статья уже
        existing = session.query(Article).filter_by(url=dto.article_url).first()
        
        if existing:
            new_user.articles.append(existing)
        else:
            new_art = Article(
                title=dto.title,
                url=dto.article_url,
                area=dto.certain_directions[0],
                authors_text=", ".join(dto.authors),
                citations=0 # Arxiv не дает цитирования, ставим 0
            )
            session.add(new_art)
            new_user.articles.append(new_art)
            count_new += 1
            
    session.add(new_user)
    session.commit()
    
    # Сразу дообучаем ML
    recommender.load_and_train()
    
    print(f"[REGISTER] User created. Parsed {len(parsed_articles)} articles. New in DB: {count_new}")

    res_user = {
        'id': new_user.id, 'email': new_user.email, 'firstName': new_user.first_name,
        'lastName': new_user.last_name, 'role': new_user.role, 'area': new_user.area,
        'articles': [a.id for a in new_user.articles], 'likedArticles': [],
        'recommendations': []
    }
    session.close()
    return jsonify(res_user)

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
    # Seed (первоначальное заполнение) для теста
    s = Session()
    if not s.query(User).filter_by(email='admin@sirius.ru').first():
        s.add(User(email='admin@sirius.ru', password='admin', first_name='System', last_name='Admin', role='admin', area='Admin'))
        s.commit()
    s.close()
    
    recommender.load_and_train()
    app.run(debug=True, port=5000)