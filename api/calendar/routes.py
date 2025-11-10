"""Module de gestion du calendrier"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from icalendar import Calendar
from datetime import datetime, timedelta
from core.extensions import db
from core.models import CalendarEvent, Group
from core.permissions import get_current_user, admin_required, prof_or_admin_required

calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/v1/calendar')


@calendar_bp.route('', methods=['GET'])
@jwt_required()
def list_events():
    """Lister les événements pour les groupes de l'utilisateur"""
    current_user = get_current_user()
    
    if current_user.role == 'admin':
        events = CalendarEvent.query.all()
    else:
        # Récupérer les événements des groupes de l'utilisateur
        group_ids = [g.id for g in current_user.groups]
        events = CalendarEvent.query.filter(CalendarEvent.group_id.in_(group_ids)).all()
    
    return jsonify({
        'events': [e.to_dict() for e in events]
    }), 200


@calendar_bp.route('/import', methods=['POST'])
@jwt_required()
@admin_required
def import_ics():
    """Importer un fichier .ics pour un groupe (admin uniquement)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    group_id = request.form.get('group_id')
    
    if not group_id:
        return jsonify({'error': 'Missing group_id'}), 400
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    if not file.filename.endswith('.ics'):
        return jsonify({'error': 'File must be .ics format'}), 400
    
    try:
        # Lire et parser le fichier ICS
        ics_content = file.read()
        cal = Calendar.from_ical(ics_content)
        
        events_created = 0
        for component in cal.walk():
            if component.name == "VEVENT":
                event = CalendarEvent(
                    title=str(component.get('summary', 'Sans titre')),
                    description=str(component.get('description', '')),
                    start_time=component.get('dtstart').dt,
                    end_time=component.get('dtend').dt,
                    location=str(component.get('location', '')),
                    group_id=group_id
                )
                db.session.add(event)
                events_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{events_created} events imported successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        # Log the error for debugging but don't expose stack trace
        import logging
        logging.error(f'Failed to import calendar: {str(e)}')
        return jsonify({'error': 'Failed to import calendar'}), 400


@calendar_bp.route('', methods=['POST'])
@jwt_required()
@prof_or_admin_required
def create_event():
    """Créer un événement (prof uniquement, pour ses groupes)"""
    current_user = get_current_user()
    data = request.get_json()
    
    # Validation
    required_fields = ['title', 'start_time', 'end_time', 'group_ids']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    group_ids = data.get('group_ids', [])
    if not isinstance(group_ids, list) or len(group_ids) == 0:
        return jsonify({'error': 'At least one group must be selected'}), 400
    
    # Vérifier que l'utilisateur appartient aux groupes sélectionnés
    user_group_ids = [g.id for g in current_user.groups]
    for group_id in group_ids:
        if group_id not in user_group_ids:
            return jsonify({'error': f'You are not a member of group {group_id}'}), 403
        
        # Vérifier que le groupe existe
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': f'Group {group_id} not found'}), 404
    
    try:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Vérifier que start_time < end_time
        if start_time >= end_time:
            return jsonify({'error': 'Start time must be before end time'}), 400
        
        is_recurring = data.get('is_recurring', False)
        recurrence_type = data.get('recurrence_type')
        recurrence_end = datetime.fromisoformat(data['recurrence_end'].replace('Z', '+00:00')) if data.get('recurrence_end') else None
        
        total_created = 0
        all_created_events = []
        
        # Créer un événement pour chaque groupe sélectionné
        for group_id in group_ids:
            # Créer l'événement principal
            event = CalendarEvent(
                title=data['title'],
                description=data.get('description', ''),
                start_time=start_time,
                end_time=end_time,
                location=data.get('location', ''),
                group_id=group_id,
                created_by=current_user.id,
                is_recurring=is_recurring,
                recurrence_type=recurrence_type,
                recurrence_end=recurrence_end
            )
            db.session.add(event)
            db.session.flush()  # Pour obtenir l'ID
            
            # Créer les événements récurrents si nécessaire
            created_events = [event]
            if event.is_recurring and event.recurrence_type and event.recurrence_end:
                created_events.extend(_create_recurring_instances(event))
            
            total_created += len(created_events)
            all_created_events.append(event)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{total_created} event(s) created successfully for {len(group_ids)} group(s)',
            'events': [e.to_dict() for e in all_created_events]
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        import logging
        logging.error(f'Failed to create event: {str(e)}')
        return jsonify({'error': 'Failed to create event'}), 400


def _create_recurring_instances(parent_event):
    """Créer les instances d'un événement récurrent"""
    instances = []
    current_date = parent_event.start_time
    duration = parent_event.end_time - parent_event.start_time
    
    # Déterminer l'incrément selon le type de récurrence
    if parent_event.recurrence_type == 'weekly':
        delta = timedelta(weeks=1)
    elif parent_event.recurrence_type == 'biweekly':
        delta = timedelta(weeks=2)
    elif parent_event.recurrence_type == 'monthly':
        delta = timedelta(days=30)  # Approximation
    else:
        return instances
    
    # Générer les instances (maximum 52 pour éviter les abus)
    max_instances = 52
    count = 0
    
    while count < max_instances:
        current_date += delta
        if current_date > parent_event.recurrence_end:
            break
        
        instance = CalendarEvent(
            title=parent_event.title,
            description=parent_event.description,
            start_time=current_date,
            end_time=current_date + duration,
            location=parent_event.location,
            group_id=parent_event.group_id,
            created_by=parent_event.created_by,
            is_recurring=False,
            parent_event_id=parent_event.id
        )
        db.session.add(instance)
        instances.append(instance)
        count += 1
    
    return instances


@calendar_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
@prof_or_admin_required
def update_event(event_id):
    """Mettre à jour un événement (prof uniquement pour ses propres cours)"""
    current_user = get_current_user()
    event = CalendarEvent.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Vérifier que c'est le créateur du cours
    if event.created_by != current_user.id:
        return jsonify({'error': 'You can only modify your own courses'}), 403
    
    data = request.get_json()
    
    try:
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'start_time' in data:
            event.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        if 'end_time' in data:
            event.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        if 'location' in data:
            event.location = data['location']
        if 'group_id' in data:
            group = Group.query.get(data['group_id'])
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            event.group_id = data['group_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        import logging
        logging.error(f'Failed to update event: {str(e)}')
        return jsonify({'error': 'Failed to update event'}), 400


@calendar_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
@prof_or_admin_required
def delete_event(event_id):
    """Supprimer un événement (prof uniquement pour ses propres cours)"""
    current_user = get_current_user()
    data = request.get_json() or {}
    delete_series = data.get('delete_series', False)
    
    event = CalendarEvent.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Vérifier que c'est le créateur du cours
    if event.created_by != current_user.id:
        return jsonify({'error': 'You can only delete your own courses'}), 403
    
    deleted_count = 1
    
    # Si c'est un événement parent récurrent et qu'on veut supprimer toute la série
    if delete_series and event.is_recurring:
        # Supprimer toutes les instances
        CalendarEvent.query.filter_by(parent_event_id=event.id).delete()
        deleted_count += CalendarEvent.query.filter_by(parent_event_id=event.id).count()
    
    # Si c'est une instance et qu'on veut supprimer toute la série
    if delete_series and event.parent_event_id:
        parent = CalendarEvent.query.get(event.parent_event_id)
        if parent:
            # Supprimer le parent et toutes ses instances
            CalendarEvent.query.filter_by(parent_event_id=parent.id).delete()
            deleted_count = CalendarEvent.query.filter_by(parent_event_id=parent.id).count() + 1
            db.session.delete(parent)
        db.session.delete(event)
    else:
        # Supprimer uniquement cet événement
        db.session.delete(event)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{deleted_count} event(s) deleted successfully'
    }), 200
