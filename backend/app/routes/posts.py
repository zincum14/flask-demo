from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.post import Post, Tag
from ..models.user import User
from .. import db, redis_client
import json

bp = Blueprint('posts', __name__)

@bp.route('/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 尝试从Redis缓存获取
    cache_key = f'posts:page:{page}:per_page:{per_page}'
    cached_posts = redis_client.get(cache_key)
    
    if cached_posts:
        return jsonify(json.loads(cached_posts))
    
    posts = Post.query.filter_by(published=True)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    result = {
        'items': [post.to_dict() for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': posts.page
    }
    
    # 缓存结果
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return jsonify(result)

@bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    # 尝试从Redis缓存获取
    cache_key = f'post:{id}'
    cached_post = redis_client.get(cache_key)
    
    if cached_post:
        return jsonify(json.loads(cached_post))
    
    post = Post.query.get_or_404(id)
    
    # 增加浏览量
    post.views += 1
    db.session.commit()
    
    # 缓存结果
    redis_client.setex(cache_key, 3600, json.dumps(post.to_dict()))
    
    return jsonify(post.to_dict())

@bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    post = Post(
        title=data['title'],
        content=data['content'],
        summary=data.get('summary'),
        cover_image=data.get('cover_image'),
        author_id=user_id,
        published=data.get('published', False)
    )
    
    # 处理标签
    if 'tags' in data:
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            post.tags.append(tag)
    
    db.session.add(post)
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete('posts:page:1:per_page:10')
    
    return jsonify(post.to_dict()), 201

@bp.route('/posts/<int:id>', methods=['PUT'])
@jwt_required()
def update_post(id):
    post = Post.query.get_or_404(id)
    user_id = get_jwt_identity()
    
    if post.author_id != user_id:
        return jsonify({'error': '没有权限修改此文章'}), 403
    
    data = request.get_json()
    
    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    post.summary = data.get('summary', post.summary)
    post.cover_image = data.get('cover_image', post.cover_image)
    post.published = data.get('published', post.published)
    
    # 更新标签
    if 'tags' in data:
        post.tags = []
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            post.tags.append(tag)
    
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete(f'post:{id}')
    redis_client.delete('posts:page:1:per_page:10')
    
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_post(id):
    post = Post.query.get_or_404(id)
    user_id = get_jwt_identity()
    
    if post.author_id != user_id:
        return jsonify({'error': '没有权限删除此文章'}), 403
    
    db.session.delete(post)
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete(f'post:{id}')
    redis_client.delete('posts:page:1:per_page:10')
    
    return '', 204 