from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import random

STALL_COLORS = [
    '#FF6B6B', '#FFD93D', '#6BCB77', '#4D96FF',
    '#FF922B', '#CC5DE8', '#F06595', '#20C997',
    '#74C0FC', '#FFA94D', '#69DB7C', '#FF8787',
]

STALL_EMOJIS = ['🎠','🎡','🎢','🎪','🎭','🎨','🎯','🎲',
                 '⚡','🏆','🎵','🌟','🔥','💎','🚀','🎀']


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    xp            = db.Column(db.Integer, default=0)
    level         = db.Column(db.Integer, default=1)
    total_completions = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    habits = db.relationship('Habit', backref='user', lazy=True,
                             cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---------- XP / Level ----------
    @property
    def xp_per_level(self):
        return 100   # flat 100 XP per level for simplicity

    @property
    def xp_in_level(self):
        return self.xp % self.xp_per_level

    @property
    def xp_percent(self):
        return self.xp_in_level  # already 0-99

    def add_xp(self, amount=10):
        self.xp += amount
        new_level = (self.xp // self.xp_per_level) + 1
        leveled   = new_level > self.level
        if leveled:
            self.level = new_level
        return leveled

    # ---------- Serialise for API ----------
    def to_dict(self):
        return {
            'xp':       self.xp,
            'level':    self.level,
            'xp_in':    self.xp_in_level,
            'xp_pct':   self.xp_percent,
            'xp_need':  self.xp_per_level,
        }


class Habit(db.Model):
    __tablename__ = 'habits'

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(120), nullable=False)
    habit_time       = db.Column(db.String(10),  nullable=False)   # "HH:MM"
    emoji            = db.Column(db.String(10),  default='🎯')
    color            = db.Column(db.String(20),  nullable=False)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    streak           = db.Column(db.Integer, default=0)
    completed_today  = db.Column(db.Boolean, default=False)
    last_completed   = db.Column(db.Date,    nullable=True)
    total_completions = db.Column(db.Integer, default=0)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kw):
        if 'color' not in kw:
            kw['color'] = random.choice(STALL_COLORS)
        if 'emoji' not in kw:
            kw['emoji'] = random.choice(STALL_EMOJIS)
        super().__init__(**kw)

    def auto_reset(self):
        """Reset completed flag if it's a new day. Return True if reset happened."""
        today     = date.today()
        yesterday = today - timedelta(days=1)
        if self.completed_today and self.last_completed and self.last_completed < today:
            # Break streak if missed a day
            if self.last_completed < yesterday:
                self.streak = 0
            self.completed_today = False
            return True
        return False

    def mark_complete(self):
        today     = date.today()
        yesterday = today - timedelta(days=1)

        if self.completed_today and self.last_completed == today:
            return False   # already done today

        if self.last_completed == yesterday:
            self.streak += 1
        elif self.last_completed != today:
            self.streak = 1

        self.completed_today   = True
        self.last_completed    = today
        self.total_completions += 1
        return True

    def to_dict(self):
        return {
            'id':        self.id,
            'name':      self.name,
            'time':      self.habit_time,
            'emoji':     self.emoji,
            'color':     self.color,
            'streak':    self.streak,
            'completed': self.completed_today,
            'total':     self.total_completions,
        }
