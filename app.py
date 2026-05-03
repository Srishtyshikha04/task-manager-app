from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    status = db.Column(db.String(20))
    due_date = db.Column(db.String(20))

# ---------------- ROUTES ---------------- #

@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']

    user = User(name=name, email=email, password=password, role=role)
    db.session.add(user)
    db.session.commit()

    return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        session['user_id'] = user.id
        session['role'] = user.role
        return redirect('/dashboard')
    else:
        return "Invalid credentials"


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    total = Task.query.count()
    completed = Task.query.filter_by(status='completed').count()
    pending = Task.query.filter_by(status='pending').count()

    return render_template(
        'dashboard.html',
        total=total,
        completed=completed,
        pending=pending
    )


# ---------------- PROJECTS ---------------- #

@app.route('/projects')
def projects():
    if 'user_id' not in session:
        return redirect('/')

    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)


@app.route('/create_project', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return redirect('/')

    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['project_name']

    project = Project(name=name, created_by=session['user_id'])
    db.session.add(project)
    db.session.commit()

    return redirect('/projects')


# ---------------- TASKS ---------------- #

@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect('/')

    all_tasks = Task.query.all()
    users = User.query.all()
    projects = Project.query.all()   # ✅ ADD THIS

    today = datetime.today().date()

    for task in all_tasks:
        task.is_overdue = False

        if task.due_date:
            task_date = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            if task_date < today and task.status != 'completed':
                task.is_overdue = True

        # attach project name
        project = Project.query.get(task.project_id)
        task.project_name = project.name if project else "No Project"

    return render_template(
        'tasks.html',
        tasks=all_tasks,
        users=users,
        projects=projects   # ✅ PASS TO HTML
    )


@app.route('/create_task', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return redirect('/')

    if session.get('role') != 'admin':
        return "Access Denied"

    title = request.form['title']
    status = request.form['status']
    due_date = request.form['due_date']
    assigned_to = int(request.form['assigned_to'])
    project_id = int(request.form['project_id'])   # ✅ ADD THIS

    task = Task(
        title=title,
        status=status,
        due_date=due_date,
        assigned_to=assigned_to,
        project_id=project_id
    )

    db.session.add(task)
    db.session.commit()

    return redirect('/tasks')


# ---------------- LOGOUT ---------------- #

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN ---------------- #

import os

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)