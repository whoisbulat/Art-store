import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'  # измените на случайный текст
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Конфигурация загрузки файлов
UPLOAD_FOLDER = os.path.join('static', 'images', 'works')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


# ---------- МОДЕЛИ БАЗЫ ДАННЫХ ----------
class Artwork(db.Model):
    """Одна работа (картина, керамика, вышивка)"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # oil, mixed, embroidery
    technique = db.Column(db.String(100), nullable=True)  # техника изготовления (для керамики)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Artwork {self.title}>'


class About(db.Model):
    """Информация обо мне (био, фото, контакты)"""
    id = db.Column(db.Integer, primary_key=True)
    bio = db.Column(db.Text, nullable=False, default='')
    photo_filename = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    instagram = db.Column(db.String(200), nullable=True)
    telegram = db.Column(db.String(200), nullable=True)


class User(db.Model):
    """Для простой авторизации (один пользователь)"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Пожалуйста, авторизуйтесь', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


def init_admin_user():
    """Создаёт администратора, если его нет"""
    if not User.query.first():
        # пароль 'admin123' хешируем простым способом (для простоты)
        # в реальном проекте используйте Werkzeug generate_password_hash
        admin = User(username='admin', password_hash=hashlib.md5('admin123'.encode()).hexdigest())
        db.session.add(admin)
        db.session.commit()


def init_about():
    """Создаёт пустую запись About, если её нет"""
    if not About.query.first():
        about = About(
            bio='Welcome to my cabinet of curiosities! I\'m an artist...',
            email='anastasia@artmail.com',
            instagram='https://instagram.com/anastasia.art',
            telegram='https://t.me/anastasia'
        )
        db.session.add(about)
        db.session.commit()


# ---------- ПУБЛИЧНЫЕ МАРШРУТЫ ----------
@app.route('/')
def index():
    about = About.query.first()
    # Для статистики в разделе About (количества работ)
    paintings_count = Artwork.query.filter_by(category='oil').count()
    ceramics_count = Artwork.query.filter_by(category='mixed').count()
    embroidery_count = Artwork.query.filter_by(category='embroidery').count()
    return render_template('index.html', about=about,
                           paintings_count=paintings_count,
                           ceramics_count=ceramics_count,
                           embroidery_count=embroidery_count)


@app.route('/paintings')
def paintings():
    artworks = Artwork.query.filter_by(category='oil').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Oil Paintings', category='oil')


@app.route('/ceramics')
def ceramics():
    artworks = Artwork.query.filter_by(category='mixed').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Mixed Media & Ceramics', category='mixed')


@app.route('/embroidery')
def embroidery():
    artworks = Artwork.query.filter_by(category='embroidery').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Embroidery', category='embroidery')


@app.route('/about')
def about_page():
    about = About.query.first()
    return render_template('about.html', about=about)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Здесь можно настроить реальную отправку почты
        flash(f'Спасибо, {name}! Ваше сообщение отправлено.', 'success')
        return redirect(url_for('contact'))
    about = About.query.first()
    return render_template('contact.html', about=about)


# ---------- АДМИН-ПАНЕЛЬ ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == hashlib.md5(password.encode()).hexdigest():
            session['admin_logged_in'] = True
            flash('Добро пожаловать в админ-панель', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_dashboard():
    artworks = Artwork.query.order_by(Artwork.created_at.desc()).all()
    return render_template('admin/dashboard.html', artworks=artworks)


@app.route('/admin/artwork/add', methods=['GET', 'POST'])
@login_required
def add_artwork():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        year = request.form.get('year')
        category = request.form.get('category')
        technique = request.form.get('technique')

        if 'image' not in request.files:
            flash('Файл изображения не выбран', 'danger')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('Файл изображения не выбран', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Добавляем временную метку, чтобы избежать дублирования
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            artwork = Artwork(
                title=title,
                description=description,
                image_filename=filename,
                year=year if year else None,
                category=category,
                technique=technique if technique else None
            )
            db.session.add(artwork)
            db.session.commit()
            flash('Работа успешно добавлена', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('admin/artwork_form.html')


@app.route('/admin/artwork/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_artwork(id):
    artwork = Artwork.query.get_or_404(id)
    if request.method == 'POST':
        artwork.title = request.form.get('title')
        artwork.description = request.form.get('description')
        artwork.year = request.form.get('year') or None
        artwork.category = request.form.get('category')
        artwork.technique = request.form.get('technique') or None

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Удаляем старый файл
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], artwork.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                artwork.image_filename = filename

        db.session.commit()
        flash('Работа обновлена', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/artwork_form.html', artwork=artwork)


@app.route('/admin/artwork/delete/<int:id>')
@login_required
def delete_artwork(id):
    artwork = Artwork.query.get_or_404(id)
    # Удаляем файл изображения
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], artwork.image_filename)
    if os.path.exists(image_path):
        os.remove(image_path)
    db.session.delete(artwork)
    db.session.commit()
    flash('Работа удалена', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/about/edit', methods=['GET', 'POST'])
@login_required
def edit_about():
    about = About.query.first()
    if not about:
        about = About()
        db.session.add(about)
        db.session.commit()

    if request.method == 'POST':
        about.bio = request.form.get('bio')
        about.email = request.form.get('email')
        about.instagram = request.form.get('instagram')
        about.telegram = request.form.get('telegram')

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                about.photo_filename = filename

        db.session.commit()
        flash('Информация обновлена', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/about_edit.html', about=about)

@app.route('/api/artworks')
def api_artworks():
    artworks = Artwork.query.order_by(Artwork.created_at.desc()).all()
    return [{'id': a.id, 'title': a.title, 'description': a.description, 'image_filename': a.image_filename, 'year': a.year, 'category': a.category, 'technique': a.technique} for a in artworks]


# Запуск и инициализация БД
with app.app_context():
    db.create_all()
    init_admin_user()
    init_about()

if __name__ == '__main__':
    app.run(debug=True)