from app import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy_utils import ArrowType
import arrow
import json
from flask import g, current_app
import requests


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(254), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class ApiCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256), index=True, unique=True)
    time = db.Column(ArrowType)
    data = db.Column(db.UnicodeText)


    @staticmethod
    def request(url):
        cache = ApiCache.query.filter_by(url=url).first()
        if cache and cache.time < arrow.utcnow():
            # Giltigt data finns i cache. Returnera.
            current_app.logger.debug('Cache hit!')
            return json.loads(cache.data)

        BASE_URL = app.config['BASE_URL']
        current_app.logger.debug('Requesting {}'.format(url))
        r = requests.get(BASE_URL + url,
                        headers={'Authorization': 'Bearer ' + getattr(g, 'token', '')})

        while r.status_code == 400:
            current_app.logger.info('Invalid credentials or other error ({}).'.format(r.status_code))
            data = {'grant_type': 'client_credentials',
                    'client_id': app.config['CLIENT_ID'],
                    'client_secret': app.config['CLIENT_SECRET']}
            current_app.logger.debug('Requesting token with data:\n{}'.format(data))
            r_token = requests.post(BASE_URL + '/oauth2/token', data=data)
            current_app.logger.debug('Token request return data.\n{}'.format(r_token))

            token = r_token.json()['access_token']
            current_app.logger.debug('Received access token: {}'.format(token))
            setattr(g, 'token', token = token)

            r = requests.get(BASE_URL + url,
                            headers={'Authorization': 'Bearer ' + getattr(g, 'token', '')})

        if 200 <= r.status_code < 400:
            current_app.logger.debug('Successful request to API. Storing in cache.')
            if cache:
                db.session.delete(cache)
                db.session.commit()

            cache = ApiCache(url=url, time=arrow.utcnow().shift(hours=1), data=r.data)
            db.session.add(cache)
            db.session.commit()
            return r.data
