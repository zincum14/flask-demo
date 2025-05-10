from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.comment import Comment
from ..models.post import Post
from .. import db, redis_client
import json

bp = Blueprint('comments', __name__)

@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    # 尝试从Redis缓存获取
    cache_key = f'post:{post_id}:comments'
    cached_comments = redis_client.get(cache_key)
    
    if cached_comments:
        return jsonify(json.loads(cached_comments))
    
    comments = Comment.query.filter_by(
        post_id=post_id,
        parent_id=None,
        is_approved=True
    ).order_by(Comment.created_at.desc()).all()
    
    result = [comment.to_dict() for comment in comments]
    
    # 缓存结果
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return jsonify(result)

@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    post = Post.query.get_or_404(post_id)
    
    comment = Comment(
        content=data['content'],
        author_id=user_id,
        post_id=post_id,
        parent_id=data.get('parent_id'),
        is_approved=True  # 可以根据需要设置为False，等待管理员审核
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete(f'post:{post_id}:comments')
    
    return jsonify(comment.to_dict()), 201

@bp.route('/comments/<int:id>', methods=['PUT'])
@jwt_required()
def update_comment(id):
    comment = Comment.query.get_or_404(id)
    user_id = get_jwt_identity()
    
    if comment.author_id != user_id:
        return jsonify({'error': '没有权限修改此评论'}), 403
    
    data = request.get_json()
    comment.content = data.get('content', comment.content)
    
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete(f'post:{comment.post_id}:comments')
    
    return jsonify(comment.to_dict())

@bp.route('/comments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    user_id = get_jwt_identity()
    
    if comment.author_id != user_id:
        return jsonify({'error': '没有权限删除此评论'}), 403
    
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    
    # 清除相关缓存
    redis_client.delete(f'post:{post_id}:comments')
    
    return '', 204 