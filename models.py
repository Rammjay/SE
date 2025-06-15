from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.class_name,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'room': self.room
        } 