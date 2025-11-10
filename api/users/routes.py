"""Module de gestion des utilisateurs"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from core.extensions import db, bcrypt
from core.models import User, Group
from core.permissions import get_current_user, admin_required, is_owner_or_admin

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


@users_bp.route('/list', methods=['GET'])
@jwt_required()
def list_users_for_messaging():
    """Lister tous les utilisateurs pour la messagerie (accessible à tous)"""
    users = User.query.all()
    
    return jsonify({
        'users': [{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users]
    }), 200


@users_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    """Lister tous les utilisateurs (admin uniquement)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'page': page,
        'per_page': per_page,
        'pages': users.pages
    }), 200


@users_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """Créer un utilisateur (admin uniquement)"""
    data = request.get_json()
    
    # Validation
    required_fields = ['username', 'email', 'password', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['role'] not in ['eleve', 'prof', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Vérifier si l'utilisateur existe déjà
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Créer l'utilisateur
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data['role']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Obtenir les détails d'un utilisateur (admin ou soi-même)"""
    current_user = get_current_user()
    
    if not is_owner_or_admin(current_user, user_id):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Modifier un utilisateur (admin ou soi-même)"""
    current_user = get_current_user()
    
    if not is_owner_or_admin(current_user, user_id):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Seul admin peut modifier le rôle
    if 'role' in data and current_user.role != 'admin':
        return jsonify({'error': 'Only admin can change role'}), 403
    
    # Mise à jour des champs
    if 'email' in data:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'error': 'Email already exists'}), 409
        user.email = data['email']
    
    if 'username' in data:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'error': 'Username already exists'}), 409
        user.username = data['username']
    
    if 'password' in data:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    if 'role' in data and current_user.role == 'admin':
        if data['role'] not in ['eleve', 'prof', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur (admin uniquement)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200


@users_bp.route('/<int:user_id>/groups', methods=['PUT'])
@jwt_required()
@admin_required
def manage_user_groups(user_id):
    """Ajouter ou retirer des groupes d'un utilisateur (admin uniquement)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'add_groups' in data:
        for group_id in data['add_groups']:
            group = Group.query.get(group_id)
            if group and group not in user.groups:
                user.groups.append(group)
    
    if 'remove_groups' in data:
        for group_id in data['remove_groups']:
            group = Group.query.get(group_id)
            if group and group in user.groups:
                user.groups.remove(group)
    
    db.session.commit()
    
    return jsonify({
        'message': 'User groups updated successfully',
        'user': user.to_dict()
    }), 200
