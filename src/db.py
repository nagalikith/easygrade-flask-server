from flask import Flask, render_template, request, flash, click, current_app, g
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50, nullable=False))
    password = db.Column(db.String(50), nullable=False)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    max_submissions = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)

class Submission(db.Model):
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_id = db.Column(db.String(50), primary_key=True)
    submission_time_client = db.Column(db.DateTime, nullable=False)
    submission_time_server = db.Column(db.DateTime, nullable=False)
    summary = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    s3_url = db.Column(db.String(50), nullable=False)

class Submission_Aggregate(db.Model):
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_id = db.Column(db.String(50), db.ForeignKey('submission.submission_id'), nullable=False)
    summary = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

participation = db.Table(
    'participation',
    SQLAlchemy.Column('assignment_id', SQLAlchemy.Integer, SQLAlchemy.ForeignKey('assignment.id'), primary_key=True),
    SQLAlchemy.Column('student_id', SQLAlchemy.Integer, SQLAlchemy.ForeignKey('user.id'), primary_key=True),
    SQLAlchemy.Column('num_of_submissions', SQLAlchemy.Integer, nullable=False))




                         
