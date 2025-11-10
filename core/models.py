"""Modèles de base de données pour OpenDirecte"""
from datetime import datetime
from core.extensions import db


# Table d'association pour la relation many-to-many User-Group
user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)


class User(db.Model):
    """Modèle Utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # eleve, prof, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    groups = db.relationship('Group', secondary=user_groups, backref='members')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', secondary='message_recipients', backref='recipients')
    homeworks = db.relationship('Homework', backref='author', cascade='all, delete-orphan')
    notes_given = db.relationship('Note', foreign_keys='Note.teacher_id', backref='teacher', cascade='all, delete-orphan')
    notes_received = db.relationship('Note', foreign_keys='Note.student_id', backref='student', cascade='all, delete-orphan')
    
    def to_dict(self, include_groups=True):
        """Sérialisation en dictionnaire"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_groups:
            data['groups'] = [g.to_dict(include_members=False) for g in self.groups]
        return data


class Group(db.Model):
    """Modèle Groupe (classe ou club)"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # classe, club
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    homeworks = db.relationship('Homework', backref='group', cascade='all, delete-orphan')
    events = db.relationship('CalendarEvent', backref='group', cascade='all, delete-orphan')
    
    def to_dict(self, include_members=True):
        """Sérialisation en dictionnaire"""
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_members:
            data['members'] = [{'id': m.id, 'username': m.username, 'role': m.role} for m in self.members]
        return data


class Announcement(db.Model):
    """Modèle Annonce (Feed)"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship('User', backref='announcements')
    
    def to_dict(self):
        """Sérialisation en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author': self.author.username if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Table d'association pour le suivi des devoirs complétés
homework_completions = db.Table('homework_completions',
    db.Column('homework_id', db.Integer, db.ForeignKey('homeworks.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('completed_at', db.DateTime, default=datetime.utcnow)
)


class Homework(db.Model):
    """Modèle Devoir"""
    __tablename__ = 'homeworks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachments.id'), nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    attachment = db.relationship('Attachment', foreign_keys=[attachment_id])
    completed_by = db.relationship('User', secondary=homework_completions, backref='completed_homeworks')
    
    def to_dict(self, user_id=None):
        """Sérialisation en dictionnaire"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'author_id': self.author_id,
            'author': self.author.username if self.author else None,
            'attachment_id': self.attachment_id,
            'subject': self.subject,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if user_id:
            data['is_completed'] = any(u.id == user_id for u in self.completed_by)
        
        return data


# Table d'association pour Message recipients
message_recipients = db.Table('message_recipients',
    db.Column('message_id', db.Integer, db.ForeignKey('messages.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)


class Message(db.Model):
    """Modèle Message"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    attachment = db.relationship('Attachment', foreign_keys=[attachment_id])
    
    def to_dict(self):
        """Sérialisation en dictionnaire"""
        return {
            'id': self.id,
            'subject': self.subject,
            'content': self.content,
            'sender_id': self.sender_id,
            'sender': self.sender.username if self.sender else None,
            'recipients': [{'id': r.id, 'username': r.username} for r in self.recipients],
            'attachment_id': self.attachment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read
        }


class CalendarEvent(db.Model):
    """Modèle Événement calendrier"""
    __tablename__ = 'calendar_events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Champs de récurrence
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20), nullable=True)  # weekly, biweekly, monthly
    recurrence_end = db.Column(db.DateTime, nullable=True)
    parent_event_id = db.Column(db.Integer, db.ForeignKey('calendar_events.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_events')
    parent_event = db.relationship('CalendarEvent', remote_side=[id], backref='recurring_instances')
    
    def to_dict(self):
        """Sérialisation en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'is_recurring': self.is_recurring,
            'recurrence_type': self.recurrence_type,
            'recurrence_end': self.recurrence_end.isoformat() if self.recurrence_end else None,
            'parent_event_id': self.parent_event_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Note(db.Model):
    """Modèle Note"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    max_value = db.Column(db.Float, default=20.0)
    comment = db.Column(db.Text, nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Sérialisation en dictionnaire"""
        return {
            'id': self.id,
            'subject': self.subject,
            'value': self.value,
            'max_value': self.max_value,
            'comment': self.comment,
            'student_id': self.student_id,
            'student': self.student.username if self.student else None,
            'teacher_id': self.teacher_id,
            'teacher': self.teacher.username if self.teacher else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Attachment(db.Model):
    """Modèle Pièce jointe"""
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    uploader = db.relationship('User', backref='attachments')
    
    def to_dict(self):
        """Sérialisation en dictionnaire"""
        return {
            'id': self.id,
            'filename': self.filename,
            'mimetype': self.mimetype,
            'size': self.size,
            'uploader_id': self.uploader_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
