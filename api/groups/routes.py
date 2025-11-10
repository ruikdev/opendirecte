"""Module de gestion des groupes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from core.extensions import db
from core.models import Group
from core.permissions import get_current_user, admin_required

groups_bp = Blueprint('groups', __name__, url_prefix='/api/v1/groups')


@groups_bp.route('', methods=['GET'])
@jwt_required()
def list_groups():
    """Lister les groupes (admin: tous, autres: leurs groupes)"""
    current_user = get_current_user()
    
    if current_user.role == 'admin':
        groups = Group.query.all()
    else:
        groups = current_user.groups
    
    return jsonify({
        'groups': [g.to_dict(include_members=True) for g in groups]
    }), 200


@groups_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_group():
    """Créer un groupe (admin uniquement)"""
    data = request.get_json()
    
    # Validation
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['type'] not in ['classe', 'club']:
        return jsonify({'error': 'Invalid group type'}), 400
    
    # Vérifier si le groupe existe déjà
    if Group.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Group already exists'}), 409
    
    # Créer le groupe
    group = Group(
        name=data['name'],
        type=data['type']
    )
    
    db.session.add(group)
    db.session.commit()
    
    return jsonify({
        'message': 'Group created successfully',
        'group': group.to_dict()
    }), 201


@groups_bp.route('/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group(group_id):
    """Obtenir les détails d'un groupe"""
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    return jsonify(group.to_dict()), 200


@groups_bp.route('/<int:group_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_group(group_id):
    """Modifier un groupe (admin uniquement)"""
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        existing_group = Group.query.filter_by(name=data['name']).first()
        if existing_group and existing_group.id != group_id:
            return jsonify({'error': 'Group name already exists'}), 409
        group.name = data['name']
    
    if 'type' in data:
        if data['type'] not in ['classe', 'club']:
            return jsonify({'error': 'Invalid group type'}), 400
        group.type = data['type']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Group updated successfully',
        'group': group.to_dict()
    }), 200


@groups_bp.route('/<int:group_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_group(group_id):
    """Supprimer un groupe (admin uniquement)"""
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    db.session.delete(group)
    db.session.commit()
    
    return jsonify({'message': 'Group deleted successfully'}), 200
