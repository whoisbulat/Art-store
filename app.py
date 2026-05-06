import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'images', 'works')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


# ---------- МОДЕЛИ ----------
class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # основное изображение денормализовано для быстрых запросов, синхронизируется с WorkImage
    image_filename = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    technique = db.Column(db.String(100), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship('WorkImage', backref='artwork', lazy=True,
                             cascade='all, delete-orphan')

    def get_primary_image(self):
        for img in self.images:
            if img.is_primary:
                return img
        return None

    def get_secondary_images(self):
        return [img for img in self.images if not img.is_primary]


class WorkImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)


class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bio = db.Column(db.Text, nullable=False, default='')
    photo_filename = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    instagram = db.Column(db.String(200), nullable=True)
    telegram = db.Column(db.String(200), nullable=True)


class User(db.Model):
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
    if not User.query.first():
        admin = User(username='admin', password_hash=hashlib.md5('admin123'.encode()).hexdigest())
        db.session.add(admin)
        db.session.commit()


def init_about():
    if not About.query.first():
        about = About(
            bio='Welcome to my cabinet of curiosities! I\'m an artist...',
            email='anastasia@artmail.com',
            instagram='https://instagram.com/anastasia.art',
            telegram='https://t.me/anastasia'
        )
        db.session.add(about)
        db.session.commit()


def migrate_categories():
    mixed_works = Artwork.query.filter_by(category='mixed').all()
    for work in mixed_works:
        work.category = 'mixed_media'
    if mixed_works:
        db.session.commit()
        print(f"Миграция: {len(mixed_works)} работ переведены из 'mixed' в 'mixed_media'")


def migrate_work_images():
    """Перенос существующих работ в новую таблицу WorkImage, если она пуста."""
    if WorkImage.query.first() is None:
        artworks = Artwork.query.all()
        for art in artworks:
            if art.image_filename:
                img = WorkImage(
                    artwork_id=art.id,
                    filename=art.image_filename,
                    is_primary=True
                )
                db.session.add(img)
        db.session.commit()
        print("Миграция изображений завершена.")


# ---------- ПУБЛИЧНЫЕ МАРШРУТЫ ----------
@app.route('/')
def index():
    about = About.query.first()
    paintings_count = Artwork.query.filter_by(category='oil').count()
    mixed_media_count = Artwork.query.filter_by(category='mixed_media').count()
    ceramics_count = Artwork.query.filter_by(category='ceramics').count()
    embroidery_count = Artwork.query.filter_by(category='embroidery').count()
    return render_template('index.html', about=about,
                           paintings_count=paintings_count,
                           mixed_media_count=mixed_media_count,
                           ceramics_count=ceramics_count,
                           embroidery_count=embroidery_count)


@app.route('/paintings')
def paintings():
    artworks = Artwork.query.filter_by(category='oil').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Oil Paintings', category='oil')


@app.route('/mixed-media')
def mixed_media():
    artworks = Artwork.query.filter_by(category='mixed_media').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Mixed Media', category='mixed_media')


@app.route('/ceramics')
def ceramics():
    artworks = Artwork.query.filter_by(category='ceramics').order_by(Artwork.year.desc()).all()
    return render_template('gallery.html', artworks=artworks, title='Ceramics', category='ceramics')


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
        flash(f'Спасибо, {name}! Ваше сообщение отправлено.', 'success')
        return redirect(url_for('contact'))
    about = About.query.first()
    return render_template('contact.html', about=about)


@app.route('/artwork/<int:id>')
def artwork_detail(id):
    artwork = Artwork.query.get_or_404(id)
    primary_img = artwork.get_primary_image()
    secondary_images = artwork.get_secondary_images()
    return render_template('artwork_detail.html', artwork=artwork,
                           primary=primary_img, secondary=secondary_images)


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
        size = request.form.get('size')

        # Основное изображение
        primary_file = request.files.get('primary_image')
        if not primary_file or primary_file.filename == '':
            flash('Основное изображение обязательно', 'danger')
            return redirect(request.url)
        if not allowed_file(primary_file.filename):
            flash('Недопустимый формат основного изображения', 'danger')
            return redirect(request.url)

        # Сохраняем основное изображение
        filename = secure_filename(primary_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        primary_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        primary_image_filename = filename

        # Создаем работу
        artwork = Artwork(
            title=title,
            description=description,
            image_filename=primary_image_filename,  # пока основное
            year=year if year else None,
            category=category,
            technique=technique if technique else None,
            size=size if size else None
        )
        db.session.add(artwork)
        db.session.flush()  # получаем artwork.id

        # Создаем запись основного изображения
        primary_img = WorkImage(artwork_id=artwork.id, filename=primary_image_filename, is_primary=True)
        db.session.add(primary_img)

        # Дополнительные изображения
        additional_files = request.files.getlist('additional_images')
        for file in additional_files:
            if file and file.filename != '' and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
                fname = ts + fname
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                img = WorkImage(artwork_id=artwork.id, filename=fname, is_primary=False)
                db.session.add(img)

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
        artwork.size = request.form.get('size') or None

        # Обработка нового основного изображения (если загружено)
        primary_file = request.files.get('primary_image')
        if primary_file and primary_file.filename != '' and allowed_file(primary_file.filename):
            # удалить старые основные изображения (физически и из базы)
            old_primary = artwork.get_primary_image()
            if old_primary:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_primary.filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                db.session.delete(old_primary)
            # сохранить новое основное
            filename = secure_filename(primary_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            primary_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # добавить запись и обновить artwork.image_filename
            new_primary = WorkImage(artwork_id=artwork.id, filename=filename, is_primary=True)
            db.session.add(new_primary)
            artwork.image_filename = filename

        # Дополнительные изображения
        additional_files = request.files.getlist('additional_images')
        for file in additional_files:
            if file and file.filename != '' and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
                fname = ts + fname
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                img = WorkImage(artwork_id=artwork.id, filename=fname, is_primary=False)
                db.session.add(img)

        db.session.commit()
        flash('Работа обновлена', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/artwork_form.html', artwork=artwork)


@app.route('/admin/artwork/delete/<int:id>')
@login_required
def delete_artwork(id):
    artwork = Artwork.query.get_or_404(id)
    # удаляем все изображения с диска
    for img in artwork.images:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(artwork)
    db.session.commit()
    flash('Работа удалена', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/artwork/<int:artwork_id>/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_work_image(artwork_id, image_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    img = WorkImage.query.get_or_404(image_id)
    if img.artwork_id != artwork.id:
        flash('Изображение не принадлежит этой работе', 'danger')
        return redirect(url_for('edit_artwork', id=artwork_id))
    # Удаляем файл
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
    if os.path.exists(img_path):
        os.remove(img_path)
    db.session.delete(img)
    db.session.commit()
    flash('Изображение удалено', 'success')
    return redirect(url_for('edit_artwork', id=artwork_id))


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
    result = []
    for a in artworks:
        primary = a.get_primary_image()
        result.append({
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'image_filename': primary.filename if primary else a.image_filename,
            'year': a.year,
            'category': a.category,
            'technique': a.technique,
            'size': a.size
        })
    return result

@app.route('/api/artwork/<int:id>')
def api_artwork_detail(id):
    artwork = Artwork.query.get_or_404(id)
    primary = artwork.get_primary_image()
    secondary = artwork.get_secondary_images()
    images = []
    if primary:
        images.append(primary.filename)
    for img in secondary:
        images.append(img.filename)
    return {
        'id': artwork.id,
        'title': artwork.title,
        'description': artwork.description,
        'year': artwork.year,
        'size': artwork.size,
        'technique': artwork.technique,
        'category': artwork.category,
        'images': images
    }


# ---------- ЗАПУСК И ИНИЦИАЛИЗАЦИЯ ----------
with app.app_context():
    db.create_all()
    init_admin_user()
    init_about()
    migrate_categories()
    migrate_work_images()

if __name__ == '__main__':
    app.run(debug=True)