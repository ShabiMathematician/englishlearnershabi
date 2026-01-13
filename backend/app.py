"""
Flask API服务
"""
import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import requests

from backend.models import init_db, User, Article, ReadingHistory, VocabularyItem, ArticleAnalysis, StandardVocabulary
from backend.recommender import ArticleRecommender

app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///english_learning.db')

# 初始化数据库
engine = init_db(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 初始化推荐器
recommender = ArticleRecommender()

def translate_text(text: str, target_lang: str = 'zh-CN') -> str:
    """Translate text using a free translation API (MyMemory)."""
    if not text:
        return ''
    try:
        response = requests.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': f'en|{target_lang}'},
            timeout=8
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get('responseData', {}).get('translatedText', '')
        return translated if translated and translated.lower() != 'null' else ''
    except Exception:
        return ''

def fetch_example_sentence(word: str) -> str:
    """Fetch an example sentence from a free dictionary API."""
    try:
        response = requests.get(
            f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}',
            timeout=8
        )
        if response.status_code != 200:
            return ''
        entries = response.json()
        for entry in entries:
            for meaning in entry.get('meanings', []):
                for definition in meaning.get('definitions', []):
                    example = definition.get('example')
                    if example:
                        return example
    except Exception:
        return ''
    return ''

def resolve_definition(word: str, fallback: str, session) -> str:
    """Resolve a definition using local vocab data when possible."""
    if fallback:
        return fallback
    standard_def = session.query(StandardVocabulary.definition).filter(
        StandardVocabulary.word == word
    ).scalar()
    return standard_def or ''

def init_recommender():
    """初始化推荐系统"""
    session = Session()
    try:
        # 只查询必要的元数据，不查询 content 以提升性能
        articles = session.query(
            Article.id, Article.title, Article.category, 
            Article.difficulty_level, Article.difficulty_score, 
            Article.embedding, Article.views, Article.avg_completion_rate
        ).all()
        
        article_dicts = []
        for article in articles:
            article_dicts.append({
                'id': article.id,
                'title': article.title,
                'category': article.category,
                'difficulty_level': article.difficulty_level,
                'difficulty_score': article.difficulty_score,
                'embedding': article.embedding,
                'views': article.views,
                'avg_completion_rate': article.avg_completion_rate
            })
        recommender.build_index(article_dicts)
    finally:
        session.close()

# ========== 用户相关API ==========

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    
    username = data.get('username')
    email = data.get('email')
    english_level = data.get('english_level', 'B1')
    interests = data.get('interests', {})
    learning_goal = data.get('learning_goal', 'general')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    session = Session()
    try:
        # 检查用户名是否存在
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            english_level=english_level,
            learning_goal=learning_goal,
            interests=interests
        )
        
        session.add(new_user)
        session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'english_level': new_user.english_level,
                'learning_goal': new_user.learning_goal,
                'interests': new_user.interests,
                'estimated_vocabulary': new_user.estimated_vocabulary
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'english_level': user.english_level,
                'learning_goal': user.learning_goal,
                'interests': user.interests,
                'estimated_vocabulary': user.estimated_vocabulary
            }
        }), 200
        
    finally:
        session.close()

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户（通过用户名查询）"""
    username = request.args.get('username')
    
    if not username:
        return jsonify({'error': 'Username parameter is required'}), 400
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'english_level': user.english_level,
                'learning_goal': user.learning_goal,
                'interests': user.interests,
                'estimated_vocabulary': user.estimated_vocabulary
            }
        })
    finally:
        session.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'english_level': user.english_level,
            'learning_goal': user.learning_goal,
            'interests': user.interests,
            'estimated_vocabulary': user.estimated_vocabulary
        })
    finally:
        session.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    data = request.json
    
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 更新字段
        if 'english_level' in data:
            user.english_level = data['english_level']
        if 'interests' in data:
            user.interests = data['interests']
        if 'learning_goal' in data:
            user.learning_goal = data['learning_goal']
        
        user.last_active = datetime.utcnow()
        
        session.commit()
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ========== 文章相关API ==========

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """获取文章列表"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    limit = int(request.args.get('limit', 20))
    
    session = Session()
    try:
        query = session.query(Article)
        
        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty_level=difficulty)
        
        articles = query.order_by(Article.created_at.desc()).limit(limit).all()
        
        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.title,
                'summary': article.content[:200] + ('...' if len(article.content) > 200 else ''),
                'category': article.category,
                'source': article.source,
                'source_name': article.source_name,
                'difficulty_level': article.difficulty_level,
                'word_count': article.word_count,
                'views': article.views
            })
        
        return jsonify({'articles': result})
        
    finally:
        session.close()

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """获取文章详情"""
    session = Session()
    try:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # 更新浏览量
        article.views += 1
        session.commit()
        
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'source': article.source,
            'source_name': article.source_name,
            'url': article.url,
            'category': article.category,
            'difficulty_level': article.difficulty_level,
            'difficulty_score': article.difficulty_score,
            'word_count': article.word_count,
            'sentence_count': article.sentence_count,
            'key_words': article.key_words,
            'views': article.views
        })
        
    finally:
        session.close()

@app.route('/api/articles/<int:article_id>/analysis', methods=['GET'])
def get_article_analysis(article_id):
    """从ArticleAnalysis表读取LLM分析结果,构建高亮数据"""
    session = Session()
    try:
        analysis = session.query(ArticleAnalysis).filter_by(
            article_id=article_id
        ).first()

        if not analysis:
            return jsonify({'error': 'Article analysis not found'}), 404

        highlights = []
        data = analysis.analysis_data

        # 1. 词汇高亮 (Vocabulary)
        for idx, vocab in enumerate(data.get('vocabulary', [])):
            highlights.append({
                'id': f'vocab-{idx}',
                'text': vocab.get('word', ''),
                'type': 'vocabulary',
                'explanation': f"{vocab.get('pronunciation', '')} - {vocab.get('definition', '')}",
                'anchors': [vocab.get('word', '')]
            })

        # 2. 搭配高亮 (Collocations)
        for idx, coll in enumerate(data.get('collocations', [])):
            highlights.append({
                'id': f'coll-{idx}',
                'text': coll.get('phrase', ''),
                'type': 'collocation',
                'explanation': coll.get('meaning', ''),
                'anchors': [coll.get('phrase', '')]
            })

        # 3. 语法高亮 (Sentence Patterns)
        for idx, pattern in enumerate(data.get('sentence_patterns', [])):
            source_sentence = pattern.get('source_sentence', '')
            if source_sentence:
                highlights.append({
                    'id': f'pattern-{idx}',
                    'text': source_sentence,
                    'type': 'grammar',
                    'explanation': pattern.get('explanation', ''),
                    'anchors': pattern.get('anchors', []) # 如果有锚点则返回，没有则为空
                })

        return jsonify({'articleId': article_id, 'highlights': highlights})
    finally:
        session.close()

# ========== 推荐相关API ==========

@app.route('/api/recommend', methods=['GET'])
def recommend():
    """获取推荐文章"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=10, type=int)
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    session = Session()
    try:
        recommendations = recommender.recommend_hybrid(session, user_id, limit)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ========== 阅读历史API ==========

@app.route('/api/reading_history', methods=['POST'])
def add_reading_history():
    """添加阅读记录"""
    data = request.json
    
    user_id = data.get('user_id')
    article_id = data.get('article_id')
    
    if not user_id or not article_id:
        return jsonify({'error': 'user_id and article_id are required'}), 400
    
    session = Session()
    try:
        # 检查是否已有记录
        existing = session.query(ReadingHistory).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if existing:
            # 更新现有记录
            if 'completion_rate' in data:
                existing.completion_rate = data['completion_rate']
            if 'time_spent' in data:
                existing.time_spent = data['time_spent']
            if 'liked' in data:
                existing.liked = data['liked']
            if 'bookmarked' in data:
                existing.bookmarked = data['bookmarked']
            if 'words_looked_up' in data:
                existing.words_looked_up = data['words_looked_up']
            
            existing.finished_at = datetime.utcnow()
        else:
            # 创建新记录
            history = ReadingHistory(
                user_id=user_id,
                article_id=article_id,
                completion_rate=data.get('completion_rate', 0.0),
                time_spent=data.get('time_spent', 0),
                liked=data.get('liked', 0),
                bookmarked=data.get('bookmarked', 0),
                words_looked_up=data.get('words_looked_up', [])
            )
            session.add(history)
        
        # 更新文章统计
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            # 重新计算平均完成率
            all_history = session.query(ReadingHistory).filter_by(article_id=article_id).all()
            completion_rates = [h.completion_rate for h in all_history if h.completion_rate]
            if completion_rates:
                article.avg_completion_rate = sum(completion_rates) / len(completion_rates)
        
        session.commit()
        
        return jsonify({'message': 'Reading history saved successfully'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reading_history/<int:user_id>', methods=['GET'])
def get_reading_history(user_id):
    """获取用户阅读历史"""
    limit = request.args.get('limit', default=20, type=int)
    
    session = Session()
    try:
        history = session.query(ReadingHistory).filter_by(user_id=user_id)\
            .order_by(ReadingHistory.created_at.desc()).limit(limit).all()
        
        result = []
        for record in history:
            article = record.article
            if article:
                result.append({
                    'article_id': article.id,
                    'title': article.title,
                    'category': article.category,
                    'completion_rate': record.completion_rate,
                    'time_spent': record.time_spent,
                    'liked': record.liked,
                    'bookmarked': record.bookmarked,
                    'created_at': record.created_at.isoformat()
                })
        
        return jsonify({'history': result})
        
    finally:
        session.close()

# ========== 生词本API ==========

@app.route('/api/vocabulary', methods=['POST'])
def add_vocabulary():
    """添加生词"""
    data = request.json
    
    user_id = data.get('user_id')
    word = data.get('word')
    
    if not user_id or not word:
        return jsonify({'error': 'user_id and word are required'}), 400
    
    session = Session()
    try:
        # 检查是否已存在
        existing = session.query(VocabularyItem).filter_by(
            user_id=user_id,
            word=word.lower()
        ).first()
        
        if existing:
            return jsonify({'message': 'Word already in vocabulary'}), 200
        
        vocab = VocabularyItem(
            user_id=user_id,
            word=word.lower(),
            definition=data.get('definition', ''),
            example_sentence=data.get('example_sentence', ''),
            source_article_id=data.get('source_article_id')
        )
        
        session.add(vocab)
        session.commit()
        
        return jsonify({'message': 'Word added to vocabulary'}), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/vocabulary/<int:user_id>', methods=['GET'])
def get_vocabulary(user_id):
    """获取用户生词本"""
    session = Session()
    try:
        vocab_items = session.query(VocabularyItem).filter_by(user_id=user_id)\
            .order_by(VocabularyItem.created_at.desc()).all()
        
        result = []
        for item in vocab_items:
            result.append({
                'id': item.id,
                'word': item.word,
                'definition': item.definition,
                'example_sentence': item.example_sentence,
                'mastery_level': item.mastery_level,
                'times_reviewed': item.times_reviewed,
                'created_at': item.created_at.isoformat()
            })
        
        return jsonify({'vocabulary': result})
        
    finally:
        session.close()

@app.route('/api/vocabulary/learning', methods=['GET'])
def get_learning_vocabulary():
    """获取标准词汇列表并提供翻译与例句"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=6, type=int)
    list_name = request.args.get('list_name', type=str)

    session = Session()
    try:
        query = session.query(StandardVocabulary)
        if list_name:
            query = query.filter(StandardVocabulary.list_name == list_name)
        if user_id:
            existing_words = session.query(VocabularyItem.word).filter(
                VocabularyItem.user_id == user_id
            ).subquery()
            query = query.filter(~StandardVocabulary.word.in_(existing_words))

        vocab_items = query.order_by(func.random()).limit(limit).all()
        result = []
        for item in vocab_items:
            example_sentence = fetch_example_sentence(item.word)
            if not example_sentence:
                example_sentence = f'I am learning the word "{item.word}" today.'
            result.append({
                'id': item.id,
                'word': item.word,
                'definition': item.definition,
                'translation': translate_text(item.word),
                'example_sentence': example_sentence,
                'example_translation': translate_text(example_sentence)
            })

        return jsonify({'vocabulary': result})
    finally:
        session.close()

@app.route('/api/vocabulary/quiz', methods=['GET'])
def get_vocabulary_quiz():
    """获取词汇测验题目"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=5, type=int)

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    session = Session()
    try:
        user_vocab = session.query(VocabularyItem).filter_by(user_id=user_id).all()
        if not user_vocab:
            return jsonify({'questions': []})

        quiz_candidates = []
        for item in user_vocab:
            definition = resolve_definition(item.word, item.definition, session)
            if definition:
                quiz_candidates.append((item.word, definition))

        if not quiz_candidates:
            return jsonify({'questions': []})

        random.shuffle(quiz_candidates)
        selected = quiz_candidates[:min(limit, len(quiz_candidates))]

        distractor_pool = session.query(StandardVocabulary.definition).filter(
            StandardVocabulary.definition.isnot(None)
        ).order_by(func.random()).limit(50).all()
        distractor_defs = [row.definition for row in distractor_pool if row.definition]

        questions = []
        for word, definition in selected:
            options = [definition]
            while len(options) < 4 and distractor_defs:
                candidate = random.choice(distractor_defs)
                if candidate not in options:
                    options.append(candidate)
            while len(options) < 4:
                options.append(f'Definition of {word}')
            random.shuffle(options)
            questions.append({
                'word': word,
                'question': f'What is the meaning of "{word}"?',
                'options': options,
                'answer': definition
            })

        return jsonify({'questions': questions})
    finally:
        session.close()

# ========== 统计信息API ==========

@app.route('/api/stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """获取用户学习统计"""
    session = Session()
    try:
        # 总阅读文章数
        total_articles = session.query(ReadingHistory).filter_by(user_id=user_id).count()
        
        # 总阅读时长
        time_records = session.query(ReadingHistory.time_spent).filter_by(user_id=user_id).all()
        total_time = sum([r[0] for r in time_records if r[0]])
        
        # 平均完成率
        completion_records = session.query(ReadingHistory.completion_rate).filter_by(user_id=user_id).all()
        completion_rates = [r[0] for r in completion_records if r[0]]
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # 生词数量
        vocab_count = session.query(VocabularyItem).filter_by(user_id=user_id).count()
        
        # 各类别阅读分布
        category_stats = {}
        history = session.query(ReadingHistory).filter_by(user_id=user_id).all()
        for record in history:
            if record.article:
                cat = record.article.category or 'general'
                category_stats[cat] = category_stats.get(cat, 0) + 1
        
        return jsonify({
            'total_articles': total_articles,
            'total_time_minutes': round(total_time / 60, 1) if total_time else 0,
            'avg_completion_rate': round(avg_completion, 2),
            'vocabulary_count': vocab_count,
            'category_distribution': category_stats
        })
        
    finally:
        session.close()

# ========== 健康检查 ==========

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/')
def index():
    """首页"""
    return jsonify({
        'message': 'Welcome to English Learning API',
        'version': '1.0.1',
        'endpoints': {
            'register': 'POST /api/register',
            'login': 'POST /api/login',
            'get_users': 'GET /api/users?username=<username>',
            'get_user': 'GET /api/users/<user_id>',
            'get_articles': 'GET /api/articles',
            'get_article': 'GET /api/articles/<article_id>',
            'recommend': 'GET /api/recommend?user_id=<user_id>',
            'add_reading_history': 'POST /api/reading_history',
            'get_vocabulary': 'GET /api/vocabulary/<user_id>',
            'add_vocabulary': 'POST /api/vocabulary',
            'get_learning_vocabulary': 'GET /api/vocabulary/learning?user_id=<user_id>&limit=<limit>',
            'get_vocabulary_quiz': 'GET /api/vocabulary/quiz?user_id=<user_id>&limit=<limit>',
            'get_stats': 'GET /api/stats/<user_id>'
        }
    })

if __name__ == '__main__':
    # 初始化推荐系统
    print("Initializing recommender system...")
    init_recommender()
    print("Recommender system initialized.")
    
    # 启动服务
    app.run(debug=True, host='0.0.0.0', port=5000)
