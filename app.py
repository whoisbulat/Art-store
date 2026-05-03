from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Данные портфолио (полностью по вашему описанию)
portfolio_data = {
    'name': 'Anastasia Zaitseva',
    'title': 'Contemporary Impressionist & Mixed Media Artist',
    'location': 'Moscow, Russia',
    'bio': '''Welcome to my cabinet of curiosities! I'm an artist, self-inspired by exploring new techniques and materials.
            I love experimenting with mixed media. All my works are unique and made in a single copy.''',
    'greeting': 'Welcome to my cabinet of curiosities & professional Being contemporary impressionist!',

    # Контакты (иконки из вашего рисунка)
    'contact': {
        'eye': 'https://www.behance.net/anastasia_zaitseva',   # замените на свою ссылку
        'camera': 'https://www.instagram.com/anastasia.art',   # замените
        'video': 'https://www.youtube.com/@anastasiaart',      # замените
        'email': 'anastasia@artmail.com'
    },

    # Техники (вместо навыков программиста)
    'techniques': [
        {'name': 'Oil painting', 'level': 95, 'description': 'Still life, landscape'},
        {'name': 'Mixed media & ceramics', 'level': 90, 'description': 'Stoneware, glazes, textures'},
        {'name': 'Embroidery', 'level': 85, 'description': 'Art embroidery, beads, silk threads'}
    ],

    # Работы по категориям
    'artworks': {
        'oil_paintings': [
            {'title': 'Morning Still Life', 'description': 'Oil on canvas, 50x60 cm', 'image': 'still_life_1.jpg', 'year': 2024, 'category': 'Still life'},
            {'title': 'Crimson Valley', 'description': 'Oil on linen, 70x90 cm', 'image': 'landscape_1.jpg', 'year': 2023, 'category': 'Landscape'}
        ],
        'mixed_media': [
            {'title': 'Earth Vessels', 'description': 'Ceramics, stoneware, glazes', 'image': 'ceramic_1.jpg', 'year': 2024, 'technique': 'Hand building'},
            {'title': 'Memory Fragments', 'description': 'Mixed media: acrylic, sand, fabric', 'image': 'mixed_1.jpg', 'year': 2023}
        ],
        'embroidery': [
            {'title': 'Botanical Garden', 'description': 'Hand embroidery, silk threads', 'image': 'embroidery_1.jpg', 'year': 2024}
        ]
    }
}

# Собираем все работы в один список с меткой категории для удобной фильтрации
all_artworks = []
for cat_key, cat_name in [('oil_paintings', 'oil'), ('mixed_media', 'mixed'), ('embroidery', 'embroidery')]:
    for work in portfolio_data['artworks'][cat_key]:
        work_copy = work.copy()
        work_copy['category_type'] = cat_name
        all_artworks.append(work_copy)
portfolio_data['all_artworks'] = all_artworks


@app.route('/')
def index():
    return render_template('index.html', portfolio=portfolio_data)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Здесь можно настроить реальную отправку почты, но для примера просто flash
        flash(f'Спасибо, {name}! Ваше сообщение отправлено.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', portfolio=portfolio_data)


if __name__ == '__main__':
    app.run(debug=True)