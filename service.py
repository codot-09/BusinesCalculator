# services.py
from entity import User, Yuk, Chiqim, db
from datetime import datetime, timedelta
import jwt
from flask import current_app

SECRET_KEY = "your-secret-key"  # Bu maxfiy kalitni xavfsiz saqlang

class AuthService:
    def login(self, username, password):
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            token = jwt.encode(
                {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=24)},
                SECRET_KEY,
                algorithm='HS256'
            )
            return {'user': user, 'token': token}
        return None

    def register(self, username, password):
        if User.query.filter_by(username=username).count() > 0:
            return None
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        token = jwt.encode(
            {'user_id': new_user.id, 'exp': datetime.utcnow() + timedelta(hours=24)},
            SECRET_KEY,
            algorithm='HS256'
        )
        return {'user': new_user, 'token': token}

    def verify_token(self, token):
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return User.query.get(data['user_id'])
        except jwt.InvalidTokenError:
            return None

class UserService:
    def get_profile(self, user_id):
        return User.query.get_or_404(user_id)

class YukService:
    def add_yuk(self, user_id, amount):
        yuk = Yuk(user_id=user_id, amount=amount)
        db.session.add(yuk)
        db.session.commit()
        return yuk

    def get_yuklar(self, user_id, start_date=None, end_date=None):
        query = Yuk.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Yuk.date >= start_date)
        if end_date:
            query = query.filter(Yuk.date <= end_date)
        return query.all()

class ChiqimService:
    def add_chiqim(self, user_id, amount):
        chiqim = Chiqim(user_id=user_id, amount=amount)
        db.session.add(chiqim)
        db.session.commit()
        return chiqim

    def get_chiqimlar(self, user_id, start_date=None, end_date=None):
        query = Chiqim.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Chiqim.date >= start_date)
        if end_date:
            query = query.filter(Chiqim.date <= end_date)
        return query.all()

class StatisticsService:
    def get_statistics(self, user_id):
        yuklar = Yuk.query.filter_by(user_id=user_id).all()
        chiqimlar = Chiqim.query.filter_by(user_id=user_id).all()
        yuk_summasi = sum(yuk.amount for yuk in yuklar) if yuklar else 0
        chiqim_summasi = sum(chiqim.amount for chiqim in chiqimlar) if chiqimlar else 0
        return {
            'yuk_summasi': yuk_summasi,
            'chiqim_summasi': chiqim_summasi,
            'farq': yuk_summasi - chiqim_summasi
        }