from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from operator import attrgetter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.secret_key = "cueichsdlc sdcsdc sdcisuh"
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')    
    
with app.app_context():
    db.create_all()    
    
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 
  
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('index'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            return redirect(url_for('index'))

    return render_template("sign_up.html", user=current_user) 

@app.route('/')
@login_required
def index():
    notes = Note.query.order_by(Note.date.desc()).all()
    return render_template('home.html', notes=notes, user=current_user)

@app.route('/note_list')
@login_required
def note_list():
    # Filter notes based on the current user's ID
    notes = Note.query.filter_by(user_id=current_user.id).all()
    notes.sort(key=attrgetter('date'), reverse=True)
    if not notes:
        return redirect(url_for('index'))
    return render_template('note_list.html', notes=notes, user=current_user)

@app.route('/note/<int:id>')
@login_required
def view_note(id):
    note = Note.query.filter_by(id=id, user_id=current_user.id).first()

    if note:
        return render_template('notes.html', note=note, user=current_user)
    else:
        flash('Note not found.', category='error')
        return redirect(url_for('note_list'))

@app.route('/add', methods=['POST'])
@login_required
def add_note():
    title = request.form.get('title')
    body = request.form.get('body')
    
    date = datetime.now().strftime('%m-%d-%Y')
    
    if title and body:
        new_note = Note(title=title, body=body, date=date, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
    return redirect(url_for('note_list'))

@app.route('/delete/<int:id>')
@login_required
def delete_note(id):
    note_to_delete = Note.query.get(id)

    if note_to_delete and note_to_delete.user_id == current_user.id:
        db.session.delete(note_to_delete)
        db.session.commit()

        # Check if there are any notes left for the current user
        remaining_notes = Note.query.filter_by(user_id=current_user.id).all()

        if not remaining_notes:
            # Redirect to home.html if there are no more notes for the current user
            return redirect(url_for('index'))

    return redirect(url_for('note_list'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    note_to_edit = Note.query.get(id)

    if request.method == 'POST':
        note_to_edit.title = request.form.get('title')
        note_to_edit.body = request.form.get('body')
        note_to_edit.date = datetime.now().strftime('%m-%d-%Y') 
        db.session.commit()
        return redirect(url_for('note_list', id=id))

    return render_template('edits_note.html', note=note_to_edit, user=current_user)


if __name__ == '__main__':
    app.run(debug=True)
