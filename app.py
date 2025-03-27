from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from
from service import AuthService, UserService, YukService, ChiqimService, StatisticsService
from entity import db
from functools import wraps
import os
from flask_cors import CORS  # CORS qo'shildi

app = Flask(__name__)
CORS(app)  # CORS barcha endpointlarga ruxsat beradi

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SWAGGER'] = {
    'title': 'API Hujjatlashtirish',
    'uiversion': 3,
    'specs_route': '/apidocs/',
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Bearer tokenni kiriting (masalan, "Bearer <token>")'
        }
    }
}
db.init_app(app)
swagger = Swagger(app)

auth_service = AuthService()
user_service = UserService()
yuk_service = YukService()
chiqim_service = ChiqimService()
statistics_service = StatisticsService()

# Token tekshiruvi uchun dekorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token topilmadi'}), 401
        token = token.replace('Bearer ', '', 1) if token.startswith('Bearer ') else token
        user = auth_service.verify_token(token)
        if not user:
            return jsonify({'message': 'Yaroqsiz token'}), 401
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome to BusinesCalculator API'})

# Auth API
@app.route('/api/auth/login', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Muvaffaqiyatli kirish',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'token': {'type': 'string'}
                }
            }
        },
        '401': {'description': 'Noto\'g\'ri login yoki parol'}
    }
})
def login():
    data = request.get_json()
    result = auth_service.login(data['username'], data['password'])
    if result:
        return jsonify({'id': result['user'].id, 'username': result['user'].username, 'token': result['token']})
    return jsonify({'message': 'Noto\'g\'ri login yoki parol'}), 401

@app.route('/api/auth/register', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Muvaffaqiyatli ro\'yxatdan o\'tish',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'token': {'type': 'string'}
                }
            }
        },
        '400': {'description': 'Foydalanuvchi allaqachon mavjud'}
    }
})
def register():
    data = request.get_json()
    result = auth_service.register(data['username'], data['password'])
    if result:
        return jsonify({'id': result['user'].id, 'username': result['user'].username, 'token': result['token']})
    return jsonify({'message': 'Foydalanuvchi allaqachon mavjud'}), 400

# User API
@app.route('/api/user/profile', methods=['GET'])
@token_required
@swag_from({
    'tags': ['User'],
    'security': [{'Bearer': []}],
    'responses': {
        '200': {
            'description': 'Foydalanuvchi profili',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'}
                }
            }
        }
    }
})
def get_user_profile(current_user):
    return jsonify({'id': current_user.id, 'username': current_user.username})

# Yuk API
@app.route('/api/yuk', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Yuk'],
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number'}
                },
                'required': ['amount']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Yuk qo\'shildi',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'date': {'type': 'string'},
                    'amount': {'type': 'number'}
                }
            }
        }
    }
})
def add_yuk(current_user):
    data = request.get_json()
    yuk = yuk_service.add_yuk(current_user.id, data['amount'])
    return jsonify({'id': yuk.id, 'date': yuk.date, 'amount': yuk.amount})

@app.route('/api/yuk', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Yuk'],
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'start_date',
            'in': 'query',
            'type': 'string',
            'description': 'Boshlanish sanasi (ixtiyoriy)'
        },
        {
            'name': 'end_date',
            'in': 'query',
            'type': 'string',
            'description': 'Tugash sanasi (ixtiyoriy)'
        }
    ],
    'responses': {
        '200': {
            'description': 'Yuklar ro\'yxati',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'date': {'type': 'string'},
                        'amount': {'type': 'number'}
                    }
                }
            }
        }
    }
})
def get_yuklar(current_user):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    yuklar = yuk_service.get_yuklar(current_user.id, start_date, end_date)
    return jsonify([{'id': yuk.id, 'date': yuk.date, 'amount': yuk.amount} for yuk in yuklar])

# Chiqim API
@app.route('/api/chiqim', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Chiqim'],
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number'}
                },
                'required': ['amount']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Chiqim qo\'shildi',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'date': {'type': 'string'},
                    'amount': {'type': 'number'}
                }
            }
        }
    }
})
def add_chiqim(current_user):
    data = request.get_json()
    chiqim = chiqim_service.add_chiqim(current_user.id, data['amount'])
    return jsonify({'id': chiqim.id, 'date': chiqim.date, 'amount': chiqim.amount})

@app.route('/api/chiqim', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Chiqim'],
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'start_date',
            'in': 'query',
            'type': 'string',
            'description': 'Boshlanish sanasi (ixtiyoriy)'
        },
        {
            'name': 'end_date',
            'in': 'query',
            'type': 'string',
            'description': 'Tugash sanasi (ixtiyoriy)'
        }
    ],
    'responses': {
        '200': {
            'description': 'Chiqimlar ro\'yxati',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'date': {'type': 'string'},
                        'amount': {'type': 'number'}
                    }
                }
            }
        }
    }
})
def get_chiqimlar(current_user):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    chiqimlar = chiqim_service.get_chiqimlar(current_user.id, start_date, end_date)
    return jsonify([{'id': chiqim.id, 'date': chiqim.date, 'amount': chiqim.amount} for chiqim in chiqimlar])

# Statistics API
@app.route('/api/statistics', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Statistics'],
    'security': [{'Bearer': []}],
    'responses': {
        '200': {
            'description': 'Foydalanuvchi statistikasi',
            'schema': {
                'type': 'object',
                'properties': {
                    'yuk_summasi': {'type': 'number'},
                    'chiqim_summasi': {'type': 'number'},
                    'farq': {'type': 'number'}
                }
            }
        }
    }
})
def get_statistics(current_user):
    statistics = statistics_service.get_statistics(current_user.id)
    return jsonify(statistics)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)