from server import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.DATABASE.Model):
    id = db.DATABASE.Column(db.DATABASE.Integer, primary_key=True)
    username = db.DATABASE.Column(db.DATABASE.String(64), index=True, unique=True)
    email = db.DATABASE.Column(db.DATABASE.String(120), index=True, unique=True)
    password_hash = db.DATABASE.Column(db.DATABASE.
                                       String(255))

    # posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # def __init__(self, username, password):
    #     self.username = username
    #     self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        print(check_password_hash(self.password_hash, password))
        print("self.password_hash: ", self.password_hash)
        return check_password_hash(self.password_hash, password)
