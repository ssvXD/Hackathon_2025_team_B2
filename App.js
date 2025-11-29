import React, { useState, useEffect } from 'react';

// ==================================================================================
// 1. КОНФИГУРАЦИЯ API (СВЯЗЬ С PYTHON)
// ==================================================================================
const API_URL = 'http://127.0.0.1:5000/api';

// ==================================================================================
// 2. СЛОВАРЬ (i18n)
// ==================================================================================
const DICT = {
  ru: {
    nav_search: 'Поиск', nav_login: 'Войти', nav_logout: 'Выйти',
    hero_title: 'Sirius Scholar', 
    hero_desc: 'Единая цифровая платформа: Рейтинги ученых, Гранты и AI-Поиск коллег.',
    btn_find: '🔍 Найти исследователя', btn_join: 'Создать профиль',
    home_feed: '🔥 Лента публикаций', home_stats: 'Статистика платформы',
    stat_users: 'Ученых в базе', stat_indexed: 'Индексировано статей', stat_monitor: 'Мониторинг 24/7',
    trend_title: 'В тренде', trend_sub: 'Самое популярное за неделю',

    login_title: 'Вход в личный кабинет', login_err: 'Ошибка! Неверный email или пароль', login_hint: 'Demo: admin@sirius.ru / admin',
    reg_title: 'Регистрация', reg_desc: 'Введите фамилию. Система (Python) найдет ваши статьи.',
    reg_btn: 'Зарегистрироваться', reg_wait: 'Анализ базы данных...',
    
    search_title: 'База знаний', search_ph: 'Введите фамилию или научную область...',
    
    profile_edit: '✏️ Редактировать', profile_save: 'Сохранить', profile_cancel: 'Отмена',
    profile_contact: '✉️ Связаться', profile_hide_contact: '🔼 Скрыть контакты',
    profile_add_btn: '➕ Добавить статью', profile_del_btn: 'Удалить',
    
    lbl_rating: 'Научный Рейтинг', lbl_hindex: 'Индекс Хирша', lbl_pubs: 'Статей', lbl_cits: 'Цитирований',
    
    rec_title: '💡 AI Рекомендации коллег', rec_why: 'Алгоритм ML подобрал для вас:',
    art_title: 'Список публикаций', art_none: 'Публикации не найдены',
    
    lbl_email: 'Email', lbl_pass: 'Пароль', lbl_name: 'Имя', lbl_lname: 'Фамилия',
    lbl_city: 'Город', lbl_age: 'Возраст', lbl_status: 'Статус / Роль', lbl_is_admin: 'Зарегистрировать как Администратора (Demo)',
    lbl_art_title: 'Название статьи', lbl_art_url: 'Ссылка', lbl_art_cit: 'Цитат',
    
    st_student: 'Студент', st_phd: 'Аспирант', st_researcher: 'Научный сотрудник', st_prof: 'Профессор',
    
    back: '← Назад', like_err: 'Войдите в систему, чтобы ставить лайки',
    lbl_cit_short: 'Цит.', lbl_auth: 'Авторы:',
    contact_phone: 'Телефон:', contact_email: 'Почта:'
  },
  en: {
    nav_search: 'Search', nav_login: 'Login', nav_logout: 'Logout',
    hero_title: 'Sirius Scholar', hero_desc: 'Digital Ecosystem: Scientific Ratings, Grants, and Collaboration.',
    btn_find: '🔍 Find Researcher', btn_join: 'Join Now',
    home_feed: '🔥 Live Feed', home_stats: 'Platform Stats',
    stat_users: 'Researchers', stat_indexed: 'Indexed Articles', stat_monitor: '24/7 Monitoring',
    trend_title: 'Trending Now', trend_sub: 'Most popular this week',

    login_title: 'System Login', login_err: 'Invalid credentials', login_hint: 'Demo: admin@sirius.ru / admin',
    reg_title: 'Registration', reg_desc: 'Enter last name. System will auto-detect papers.',
    reg_btn: 'Sign Up', reg_wait: 'Searching databases...',
    
    search_title: 'Knowledge Base', search_ph: 'Search by author or research area...',
    
    profile_edit: '✏️ Edit', profile_save: 'Save', profile_cancel: 'Cancel',
    profile_contact: '✉️ Contact', profile_hide_contact: '🔼 Hide Contacts',
    profile_add_btn: '➕ Add Article', profile_del_btn: 'Delete',
    
    lbl_rating: 'Sci-Score', lbl_hindex: 'H-Index', lbl_pubs: 'Papers', lbl_cits: 'Citations',
    
    rec_title: '💡 AI Recommendations', rec_why: 'Based on your interests:',
    art_title: 'Publications List', art_none: 'No publications found',
    
    lbl_email: 'Email', lbl_pass: 'Password',
    lbl_name: 'First Name', lbl_lname: 'Last Name',
    lbl_city: 'City', lbl_age: 'Age', lbl_status: 'Academic Status', lbl_is_admin: 'Register as Administrator (Demo)',
    lbl_art_title: 'Article Title', lbl_art_url: 'Link', lbl_art_cit: 'Citations',
    
    st_student: 'Student', st_phd: 'PhD Student', st_researcher: 'Researcher', st_prof: 'Professor',
    
    back: '← Back', like_err: 'Please login to like', lbl_cit_short: 'Cit.', lbl_auth: 'Authors:',
    contact_phone: 'Phone:', contact_email: 'Email:'
  }
};

// ==================================================================================
// 3. СТИЛИ
// ==================================================================================
const styles = {
  app: { minHeight: '100vh', backgroundColor: '#0f172a', fontFamily: "'Inter', sans-serif", color: '#e2e8f0' },
  container: { maxWidth: '1100px', margin: '0 auto', padding: '20px' },
  header: { background: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #1e293b', padding: '1rem 0', position: 'sticky', top: 0, zIndex: 100 },
  card: { background: '#1e293b', borderRadius: '16px', padding: '30px', border: '1px solid #334155', marginBottom: '20px', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' },
  input: { width: '100%', padding: '14px', background: '#020617', border: '1px solid #334155', borderRadius: '8px', color: 'white', fontSize: '16px', outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s', marginBottom: 10 },
  select: { width: '100%', padding: '14px', background: '#020617', border: '1px solid #334155', borderRadius: '8px', color: 'white', fontSize: '16px', outline: 'none', boxSizing: 'border-box' },
  btnPrimary: { background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: 'white', border: 'none', borderRadius: '8px', padding: '12px 24px', cursor: 'pointer', fontWeight: '600', transition: 'transform 0.1s' },
  btnOutline: { background: 'transparent', border: '1px solid #3b82f6', color: '#60a5fa', borderRadius: '8px', padding: '10px 20px', cursor: 'pointer' },
  hero: { background: 'linear-gradient(180deg, rgba(37, 99, 235, 0.15) 0%, rgba(15, 23, 42, 0) 100%)', borderRadius: '20px', padding: '80px 20px', textAlign: 'center', marginBottom: '40px' },
  tag: { fontSize: '11px', background: '#334155', padding: '4px 8px', borderRadius: 4, color: '#94a3b8' },
  contactBox: { marginTop: 15, padding: 15, background: 'rgba(59, 130, 246, 0.1)', borderRadius: 8, border: '1px solid #3b82f6' },
  recommendationCard: { background: 'linear-gradient(135deg, #1e293b, #0f172a)', border: '1px solid #60a5fa', borderRadius: 12, padding: 15, marginBottom: 10 }
};

// ==================================================================================
// 4. ДОЧЕРНИЕ КОМПОНЕНТЫ
// ==================================================================================

const ArticleCard = ({ art, currentUser, onLike, t }) => {
  const isLiked = currentUser?.likedArticles?.includes(art.id);
  
  return (
    <div style={{...styles.card, padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10}}>
      <div>
        <a href={art.url} target="_blank" rel="noopener noreferrer" style={{fontWeight: '600', fontSize: '16px', color: '#60a5fa', marginBottom: 5, display:'block', textDecoration: 'none'}}>
          {art.title} ↗
        </a>
        <div style={{display:'flex', gap: 10, alignItems:'center'}}>
          <span style={styles.tag}>{art.area}</span>
          <span style={{color: '#94a3b8', fontSize: '13px'}}>{t('lbl_auth')} {(art.authors || []).join(', ')}</span>
        </div>
      </div>
      <div style={{display:'flex', gap: 15, alignItems:'center'}}>
         <div style={{textAlign: 'center'}}>
            <div style={{fontSize: '16px', fontWeight: 'bold', color: '#e2e8f0'}}>{art.citations}</div>
            <div style={{fontSize: '10px', color: '#94a3b8'}}>{t('lbl_cit_short')}</div>
         </div>
         <div style={{textAlign: 'center', cursor: 'pointer'}} onClick={() => onLike(art.id)}>
            <div style={{fontSize: '20px', color: isLiked ? '#f43f5e' : '#475569'}}>{isLiked ? '❤️' : '🤍'}</div>
            <div style={{fontSize: '12px', color: '#94a3b8'}}>{art.likes || 0}</div>
         </div>
      </div>
    </div>
  );
};

const UserProfile = ({ targetProfile, currentUser, articles, onBack, onLike, onAddArticle, t }) => {
  const [showContacts, setShowContacts] = useState(false);
  const [isAddingArt, setIsAddingArt] = useState(false);
  
  // Фильтруем статьи пользователя
  const userArts = articles.filter(a => targetProfile.articles.includes(a.id));
  const isMe = currentUser?.id === targetProfile.id;
  const isAdmin = currentUser?.role === 'admin';

  // Расчет H-Index
  const calculateHIndex = (arts) => {
    if (!arts || !arts.length) return 0;
    const citations = arts.map(a => a.citations).sort((a, b) => b - a);
    let h = 0;
    for (let i = 0; i < citations.length; i++) {
      if (citations[i] >= i + 1) h = i + 1; else break;
    }
    return h;
  };
  const liveHIndex = calculateHIndex(userArts);

  // Обработка добавления статьи
  const handleAdd = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    onAddArticle(targetProfile.id, {
      title: fd.get('title'),
      url: fd.get('url'),
      citations: Number(fd.get('citations')),
      area: targetProfile.area,
      authors: targetProfile.lastName
    });
    setIsAddingArt(false);
  };

  return (
    <div style={styles.container}>
      <button onClick={onBack} style={{...styles.btnOutline, marginBottom: 20, border: 'none', paddingLeft: 0}}>{t('back')}</button>
      <div style={{display: 'grid', gridTemplateColumns: '300px 1fr', gap: 30}}>
        
        {/* ЛЕВАЯ КОЛОНКА: Инфо */}
        <div style={{...styles.card, textAlign: 'center', height: 'fit-content'}}>
          <div style={{width: 100, height: 100, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, fontWeight: 'bold', color: 'white'}}>
            {targetProfile.firstName?.[0]}{targetProfile.lastName?.[0]}
          </div>
          <h2 style={{color: 'white', margin: '0 0 5px'}}>{targetProfile.firstName} {targetProfile.lastName}</h2>
          <div style={{color: '#60a5fa', marginBottom: 10}}>{targetProfile.academicStatus}</div>
          <div style={{color: '#94a3b8', fontSize: 14, marginBottom: 20}}>{targetProfile.area}</div>
          
          <div style={{textAlign: 'left', background: '#0f172a', padding: 15, borderRadius: 10}}>
             <p style={{margin: '5px 0', color: '#cbd5e1', fontSize: 14}}>📍 {targetProfile.city} ({targetProfile.age})</p>
             {(isMe || showContacts) && <p style={{margin: '5px 0', color: '#cbd5e1', fontSize: 14}}>📧 {targetProfile.email}</p>}
          </div>

          {!isMe && (
            <button style={{...styles.btnPrimary, width: '100%', marginTop: 15}} onClick={() => setShowContacts(!showContacts)}>
              {showContacts ? t('profile_hide_contact') : t('profile_contact')}
            </button>
          )}
        </div>

        {/* ПРАВАЯ КОЛОНКА: Контент */}
        <div>
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 15, marginBottom: 20}}>
            <div style={{...styles.card, padding: 20, textAlign: 'center', marginBottom: 0}}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: '#60a5fa'}}>{liveHIndex}</div>
              <div style={{fontSize: '12px', color: '#94a3b8'}}>{t('lbl_hindex')}</div>
            </div>
            <div style={{...styles.card, padding: 20, textAlign: 'center', marginBottom: 0}}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: 'white'}}>{userArts.length}</div>
              <div style={{fontSize: '12px', color: '#94a3b8'}}>{t('lbl_pubs')}</div>
            </div>
          </div>

          {/* БЛОК ML РЕКОМЕНДАЦИЙ (Только для меня) */}
          {isMe && currentUser.recommendations && currentUser.recommendations.length > 0 && (
            <div style={{marginBottom: 30}}>
              <h3 style={{color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                {t('rec_title')} <span style={{fontSize: 12, color: '#60a5fa'}}>ML Engine v1.0</span>
              </h3>
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 10}}>
                  {currentUser.recommendations.map((rec, idx) => (
                      <div key={idx} style={styles.recommendationCard}>
                          <div style={{fontWeight: 'bold', color: 'white'}}>{rec.name}</div>
                          <div style={{fontSize: 12, color: '#94a3b8', marginBottom: 5}}>{rec.area}</div>
                          <div style={{fontSize: 13, color: '#4ade80'}}>Match: {rec.score}%</div>
                          <div style={{fontSize: 11, color: '#64748b', fontStyle: 'italic'}}>{rec.reason}</div>
                      </div>
                  ))}
              </div>
            </div>
          )}

          {/* КНОПКА АДМИНА */}
          {isAdmin && (
            <div style={{textAlign: 'right', marginBottom: 20}}>
               <button onClick={() => setIsAddingArt(!isAddingArt)} style={styles.btnOutline}>{isAddingArt ? t('profile_cancel') : t('profile_add_btn')}</button>
            </div>
          )}

          {isAddingArt && (
            <form onSubmit={handleAdd} style={{...styles.card, border: '1px dashed #60a5fa'}}>
              <label style={{color:'#94a3b8'}}>Название</label><input name="title" style={styles.input} required />
              <label style={{color:'#94a3b8'}}>URL</label><input name="url" style={styles.input} />
              <label style={{color:'#94a3b8'}}>Цитат</label><input name="citations" type="number" style={styles.input} required />
              <button style={styles.btnPrimary}>OK</button>
            </form>
          )}

          <h3 style={{color: 'white'}}>{t('art_title')}</h3>
          {userArts.map(art => (
            <ArticleCard key={art.id} art={art} currentUser={currentUser} onLike={onLike} t={t} />
          ))}
          {userArts.length === 0 && <div style={{color: '#94a3b8'}}>{t('art_none')}</div>}
        </div>
      </div>
    </div>
  );
};

// ==================================================================================
// 5. СТРАНИЦЫ (LOGIN / REGISTER / HOME)
// ==================================================================================

const RegistrationPage = ({ onRegister, onBack, loading, t }) => {
  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px 0'}}>
      <form onSubmit={onRegister} style={{...styles.card, width: '450px'}}>
        <h2 style={{textAlign: 'center', color: 'white'}}>{t('reg_title')}</h2>
        <p style={{color: '#94a3b8', textAlign: 'center', fontSize: '13px', marginBottom: 20}}>{t('reg_desc')}</p>
        
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10}}>
          <div><label style={{color:'#94a3b8'}}>{t('lbl_name')}</label><input name="firstName" style={styles.input} required/></div>
          <div><label style={{color:'#94a3b8'}}>{t('lbl_lname')}</label><input name="lastName" style={styles.input} required/></div>
        </div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10}}>
          <div><label style={{color:'#94a3b8'}}>{t('lbl_age')}</label><input name="age" type="number" style={styles.input} required/></div>
          <div><label style={{color:'#94a3b8'}}>{t('lbl_city')}</label><input name="city" style={styles.input} required/></div>
        </div>
        <div>
          <label style={{color:'#94a3b8'}}>{t('lbl_status')}</label>
          <select name="academicStatus" style={styles.select} required>
            <option value="Student">{t('st_student')}</option>
            <option value="PhD Student">{t('st_phd')}</option>
            <option value="Researcher">{t('st_researcher')}</option>
            <option value="Professor">{t('st_prof')}</option>
          </select>
        </div>
        <div style={{marginTop: 10}}><label style={{color:'#94a3b8'}}>{t('lbl_email')}</label><input name="email" style={styles.input} required/></div>
        <div style={{marginTop: 10}}><label style={{color:'#94a3b8'}}>{t('lbl_pass')}</label><input name="password" type="password" style={styles.input} required/></div>
        
        <div style={{marginTop: 15, display:'flex', alignItems:'center', gap: 10}}>
          <input type="checkbox" name="isAdmin" style={{width: 16, height: 16}} />
          <label style={{margin:0, color: '#cbd5e1', cursor:'pointer', fontSize:13}}>{t('lbl_is_admin')}</label>
        </div>

        <button style={{...styles.btnPrimary, width: '100%', marginTop: 25}} disabled={loading}>
          {loading ? t('reg_wait') : t('reg_btn')}
        </button>
        <div style={{textAlign: 'center', marginTop: 15, color: '#94a3b8', cursor: 'pointer'}} onClick={onBack}>{t('back')}</div>
      </form>
    </div>
  );
};

const LoginPage = ({ onLogin, onToReg, onHome, t }) => {
  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <form onSubmit={onLogin} style={{...styles.card, width: '350px'}}>
        <h2 style={{textAlign: 'center', color: 'white', marginBottom: 20}}>{t('login_title')}</h2>
        <div style={{marginBottom: 15}}><label style={{color:'#94a3b8'}}>{t('lbl_email')}</label><input name="email" style={styles.input} defaultValue="admin@sirius.ru"/></div>
        <div style={{marginBottom: 25}}><label style={{color:'#94a3b8'}}>{t('lbl_pass')}</label><input name="password" type="password" style={styles.input} defaultValue="admin"/></div>
        <button style={{...styles.btnPrimary, width: '100%'}}>{t('nav_login')}</button>
        <div style={{textAlign:'center', fontSize: 12, color:'#64748b', marginTop:10}}>{t('login_hint')}</div>
        <div style={{textAlign: 'center', marginTop: 15, color: '#60a5fa', cursor: 'pointer'}} onClick={onToReg}>{t('reg_title')}</div>
        <div style={{textAlign: 'center', marginTop: 10, color: '#94a3b8', cursor: 'pointer'}} onClick={onHome}>Home</div>
      </form>
    </div>
  );
};

const SearchPage = ({ users, search, setSearch, onSelectUser, onBack, t }) => {
  const filtered = users.filter(u => (u.lastName + u.area).toLowerCase().includes(search.toLowerCase()));
  return (
    <div style={styles.container}>
      <button onClick={onBack} style={{...styles.btnOutline, marginBottom: 20, border: 'none', paddingLeft: 0}}>{t('back')}</button>
      <h2 style={{color: 'white', marginBottom: 20}}>{t('search_title')}</h2>
      <input style={{...styles.input, fontSize: '18px', padding: '16px', marginBottom: 30}} placeholder={t('search_ph')} value={search} onChange={e => setSearch(e.target.value)} />
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 20}}>
        {filtered.map(u => (
          <div key={u.id} style={{...styles.card, cursor: 'pointer', border: u.role === 'admin' ? '1px solid #f59e0b' : styles.card.border}} onClick={() => onSelectUser(u)}>
            <div style={{display: 'flex', gap: 15, alignItems: 'center'}}>
              <div style={{width: 50, height: 50, borderRadius: '50%', background: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold'}}>
                {u.firstName?.[0]}{u.lastName?.[0]}
              </div>
              <div>
                <div style={{fontWeight: 'bold', color: 'white'}}>{u.lastName} {u.firstName?.[0]}.</div>
                <div style={{fontSize: '12px', color: '#60a5fa'}}>{u.academicStatus || u.area}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const HomePage = ({ onSearch, onRegister, currentUser, articles, users, onLike, t }) => {
  return (
    <div style={styles.container}>
      <div style={styles.hero}>
        <h1 style={{fontSize: '3.5rem', fontWeight: '800', margin: '0 0 20px', background: 'linear-gradient(90deg, #60a5fa, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'}}>{t('hero_title')}</h1>
        <p style={{color: '#94a3b8', fontSize: '1.3rem', maxWidth: '600px', margin: '0 auto 40px'}}>{t('hero_desc')}</p>
        <div style={{display: 'flex', justifyContent: 'center', gap: 20}}>
          <button style={styles.btnPrimary} onClick={onSearch}>{t('btn_find')}</button>
          {!currentUser && <button style={styles.btnOutline} onClick={onRegister}>{t('btn_join')}</button>}
        </div>
      </div>
      <div style={{display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 30}}>
        <div>
          <h3 style={{color: 'white'}}>{t('home_feed')} <span style={{fontSize:12, color:'#94a3b8', marginLeft:10}}>{t('trend_sub')}</span></h3>
          {[...articles].sort((a,b) => (b.likes || 0) - (a.likes || 0)).slice(0, 4).map(art => (
            <ArticleCard key={art.id} art={art} currentUser={currentUser} onLike={onLike} t={t} />
          ))}
        </div>
        <div>
          <h3 style={{color: 'white'}}>{t('home_stats')}</h3>
          <div style={styles.card}>
            <div style={{marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10}}>
              <div style={{fontSize: '28px', fontWeight: 'bold', color: '#60a5fa'}}>{users.length}</div>
              <div style={{fontSize: '13px', color: '#94a3b8'}}>{t('stat_users')}</div>
            </div>
            <div style={{marginBottom: 15}}>
              <div style={{fontSize: '28px', fontWeight: 'bold', color: '#60a5fa'}}>{articles.length}</div>
              <div style={{fontSize: '13px', color: '#94a3b8'}}>{t('stat_indexed')}</div>
            </div>
            <div><div style={{fontSize: '28px', fontWeight: 'bold', color: '#60a5fa'}}>24/7</div><div style={{fontSize: '13px', color: '#94a3b8'}}>{t('stat_monitor')}</div></div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================================================================================
// 6. MAIN APP (СВЯЗЫВАЕМ ВСЕ ВМЕСТЕ)
// ==================================================================================
export default function App() {
  const [lang, setLang] = useState('ru');
  const [view, setView] = useState('home');
  
  const [currentUser, setCurrentUser] = useState(null);
  const [articles, setArticles] = useState([]);
  const [users, setUsers] = useState([]);
  const [targetProfile, setTargetProfile] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const t = (key) => DICT[lang][key] || key;

  // --- ЗАГРУЗКА ДАННЫХ С PYTHON ---
  useEffect(() => {
    const fetchData = async () => {
        try {
            const resA = await fetch(`${API_URL}/articles`);
            const resU = await fetch(`${API_URL}/users`);
            if(resA.ok && resU.ok) {
                setArticles(await resA.json());
                setUsers(await resU.json());
            }
        } catch(e) {
            console.error("Нет связи с Python:", e);
        }
    };
    fetchData();
    
    // Шрифты
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  // --- ВХОД ---
  const handleLogin = async (e) => {
    e.preventDefault();
    const { email, password } = e.target.elements;
    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email: email.value, password: password.value })
        });
        if(res.ok) {
            const user = await res.json();
            setCurrentUser(user);
            if(user.role === 'admin') setView('home');
            else { setTargetProfile(user); setView('profile'); }
        } else {
            alert(t('login_err'));
        }
    } catch(e) { alert('Ошибка соединения с сервером'); }
  };

  // --- РЕГИСТРАЦИЯ ---
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd);
    const payload = { ...data, role: fd.get('isAdmin') === 'on' ? 'admin' : 'user' };
    
    try {
        const res = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        if(res.ok) {
            const newUser = await res.json();
            setUsers([...users, newUser]);
            setCurrentUser(newUser);
            setTargetProfile(newUser);
            setView('profile');
        } else {
            alert('Ошибка регистрации (возможно, email занят)');
        }
    } catch(e) { alert('Ошибка сервера'); }
    setLoading(false);
  };

  // --- ЛАЙКИ ---
  const handleLike = async (artId) => {
    if (!currentUser) return alert(t('like_err'));
    
    // Оптимистичное обновление UI
    const isLiked = currentUser.likedArticles.includes(artId);
    const updatedLiked = isLiked 
        ? currentUser.likedArticles.filter(id => id !== artId)
        : [...currentUser.likedArticles, artId];
        
    setCurrentUser({ ...currentUser, likedArticles: updatedLiked });
    setArticles(prev => prev.map(a => a.id === artId ? { ...a, likes: (a.likes || 0) + (isLiked ? -1 : 1) } : a));

    // Отправка в Python
    await fetch(`${API_URL}/like`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ userId: currentUser.id, articleId: artId })
    });
  };
  
  // --- ДОБАВЛЕНИЕ СТАТЬИ ---
  const handleAddArticle = async (userId, artData) => {
      const res = await fetch(`${API_URL}/articles`, { // Исправлен endpoint
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ...artData, userId })
      });
      const newArt = await res.json();
      setArticles([...articles, newArt]);
      
      // Обновляем текущего юзера чтобы показать статью
      const updatedUser = users.find(u => u.id === userId);
      if(updatedUser) {
          updatedUser.articles.push(newArt.id);
          if(targetProfile.id === userId) setTargetProfile({...updatedUser});
      }
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={{...styles.container, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px'}}>
          <div style={{fontSize: '1.5rem', fontWeight: '800', color: '#60a5fa', cursor: 'pointer'}} onClick={() => setView('home')}>🎓 Scholar</div>
          <div style={{display: 'flex', gap: '15px', alignItems: 'center'}}>
            <select value={lang} onChange={e => setLang(e.target.value)} style={{background:'#334155', color:'white', border:'none', borderRadius:6, padding: '5px 10px', cursor:'pointer', fontFamily:'inherit'}}>
              <option value="ru">🇷🇺 RU</option>
              <option value="en">🇺🇸 EN</option>
            </select>
            <span style={{cursor: 'pointer', color: view === 'search' ? '#60a5fa' : '#94a3b8'}} onClick={() => setView('search')}>{t('nav_search')}</span>
            {currentUser ? (
              <>
                <span style={{cursor: 'pointer', color: 'white', fontWeight: 'bold'}} onClick={() => {setTargetProfile(currentUser); setView('profile')}}>{currentUser.firstName}</span>
                <span style={{cursor: 'pointer', color: '#ef4444', fontSize: '14px'}} onClick={() => {setCurrentUser(null); setView('home')}}>{t('nav_logout')}</span>
              </>
            ) : (
              <button style={styles.btnOutline} onClick={() => setView('login')}>{t('nav_login')}</button>
            )}
          </div>
        </div>
      </header>

      {view === 'home' && <HomePage onSearch={() => setView('search')} onRegister={() => setView('register')} currentUser={currentUser} articles={articles} users={users} onLike={handleLike} t={t} />}
      {view === 'login' && <LoginPage onLogin={handleLogin} onToReg={() => setView('register')} onHome={() => setView('home')} t={t} />}
      {view === 'register' && <RegistrationPage onRegister={handleRegister} onBack={() => setView('login')} loading={loading} t={t} />}
      {view === 'search' && <SearchPage users={users} search={search} setSearch={setSearch} onSelectUser={(u) => { setTargetProfile(u); setView('profile'); }} onBack={() => setView('home')} t={t} />}
      {view === 'profile' && <UserProfile targetProfile={targetProfile} currentUser={currentUser} articles={articles} onBack={() => setView('home')} onLike={handleLike} onAddArticle={handleAddArticle} t={t} />}
    </div>
  );
}