from flask import Flask
from backend.models import db, User
from datetime import timedelta
from flask_caching import Cache
from backend.celery.celery_code import celery_init_app
from flask import send_file
from flask_mail import Mail


app = None
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='frontend')
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hospitalv2.sqlite3"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CACHE_TYPE'] = "RedisCache"
    app.config['CACHE_DEFAULT_TIMEOUT'] = 30
    app.config['CACHE_REDIS_PORT'] = 6379
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_PORT'] = 1025
    app.config['MAIL_USERNAME'] = None
    app.config['MAIL_PASSWORD'] = None
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    mail.init_app(app)
    db.init_app(app)
    app.app_context().push()
    return app


app = create_app()
app.mail = mail
celery = celery_init_app(app)
cache = Cache(app)
app.cache = cache
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
from backend.api import *
if __name__ == "__main__":
    db.create_all()
    existing_user = User.query.filter_by(email='admin@email.com').first()
    if not existing_user:
        admin = User(username = 'admin123', email = 'admin@email.com', password = 'admin@1234', type='admin')
        db.session.add(admin)
        db.session.commit()
        department1 = Department(Department_name='Cardiology', Description='Department for Heart and Cardiovascular diseases')
        department2 = Department(Department_name='Oncology', Description='Department for Cancer treatment')
        department3 = Department(Department_name='General', Description='Department for General body-checkups')
        db.session.add(department1)
        db.session.add(department2)
        db.session.add(department3)
        db.session.commit()
    app.run()

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)
    

#Use the below commands for running the below app

# redis-server
# celery -A app.celery worker --loglevel=info
# celery -A app.celery beat --loglevel=info
# ./mailhog


