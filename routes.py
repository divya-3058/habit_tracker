from flask import request, jsonify
from flask_login import login_required, current_user
from app import db
from app.habit import habit_bp
from app.models import Habit
from datetime import date, timedelta


def _reset_all(habits):
    changed = False
    today   = date.today()
    yest    = today - timedelta(days=1)
    for h in habits:
        if h.completed_today and h.last_completed and h.last_completed < today:
            if h.last_completed < yest:
                h.streak = 0
            h.completed_today = False
            changed = True
    if changed:
        db.session.commit()


# ─── LIST ──────────────────────────────────────────────────────
@habit_bp.route('/list')
@login_required
def list_habits():
    habits = Habit.query.filter_by(user_id=current_user.id)\
                        .order_by(Habit.created_at).all()
    _reset_all(habits)
    return jsonify({
        'habits': [h.to_dict() for h in habits],
        'user':   current_user.to_dict(),
    })


# ─── ADD ───────────────────────────────────────────────────────
@habit_bp.route('/add', methods=['POST'])
@login_required
def add_habit():
    d     = request.get_json(silent=True) or {}
    name  = d.get('name', '').strip()
    time_ = d.get('time', '').strip()
    emoji = d.get('emoji', '')

    if not name:
        return jsonify({'ok': False, 'msg': 'Habit name is required.'}), 400
    if not time_:
        return jsonify({'ok': False, 'msg': 'Alarm time is required.'}), 400

    kw = dict(name=name, habit_time=time_, user_id=current_user.id)
    if emoji:
        kw['emoji'] = emoji
    h = Habit(**kw)
    db.session.add(h)
    db.session.commit()

    return jsonify({'ok': True, 'habit': h.to_dict(), 'user': current_user.to_dict()})


# ─── COMPLETE ──────────────────────────────────────────────────
@habit_bp.route('/complete/<int:hid>', methods=['POST'])
@login_required
def complete_habit(hid):
    h = Habit.query.filter_by(id=hid, user_id=current_user.id).first_or_404()

    # auto-reset if new day
    today = date.today()
    yest  = today - timedelta(days=1)
    if h.completed_today and h.last_completed and h.last_completed < today:
        if h.last_completed < yest:
            h.streak = 0
        h.completed_today = False

    if not h.mark_complete():
        return jsonify({
            'ok':      False,
            'already': True,
            'msg':     'Already completed today! Come back tomorrow 🌙',
            'habit':   h.to_dict(),
            'user':    current_user.to_dict(),
        })

    leveled = current_user.add_xp(10)
    current_user.total_completions += 1
    db.session.commit()

    return jsonify({
        'ok':        True,
        'leveled':   leveled,
        'habit':     h.to_dict(),
        'user':      current_user.to_dict(),
        'msg':       f'🎉 +10 XP! Streak: {h.streak} day{"s" if h.streak != 1 else ""}!',
    })


# ─── DELETE ────────────────────────────────────────────────────
@habit_bp.route('/delete/<int:hid>', methods=['DELETE'])
@login_required
def delete_habit(hid):
    h = Habit.query.filter_by(id=hid, user_id=current_user.id).first_or_404()
    db.session.delete(h)
    db.session.commit()
    return jsonify({'ok': True})


# ─── USER STATS ────────────────────────────────────────────────
@habit_bp.route('/stats')
@login_required
def stats():
    return jsonify({'user': current_user.to_dict()})
