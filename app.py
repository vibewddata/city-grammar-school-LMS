from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'school-lms-secret-key-2024'

# Database initialization
DB_PATH = 'school_lms.db'

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            section TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'unpaid',
            paid_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    # Salary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'unpaid',
            paid_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Hardcoded admin credentials (for demo)
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

# CSS Styles
CSS_STYLES = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .navbar { background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 1rem 0; margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .nav-links { display: flex; gap: 2rem; list-style: none; justify-content: center; }
    .nav-links a { text-decoration: none; color: #333; font-weight: 500; padding: 0.5rem 1rem; border-radius: 25px; transition: all 0.3s; }
    .nav-links a:hover { background: #667eea; color: white; transform: translateY(-2px); }
    .card { background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem; }
    .form-group { margin-bottom: 1.5rem; }
    label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #333; }
    input, select { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
    input:focus, select:focus { outline: none; border-color: #667eea; }
    .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: transform 0.3s; }
    .btn:hover { transform: translateY(-2px); }
    .btn-danger { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); }
    .btn-success { background: linear-gradient(135deg, #51cf66 0%, #40c057 100%); }
    .table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #e1e5e9; }
    .table th { background: #f8f9fa; font-weight: 600; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .stat-card { background: white; padding: 2rem; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .stat-number { font-size: 2.5rem; font-weight: bold; color: #667eea; }
    .stat-label { color: #666; font-size: 1.1rem; margin-top: 0.5rem; }
    .alert { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .logout { position: absolute; top: 1rem; right: 2rem; }
</style>
"""

# Navigation HTML
NAVBAR = """
<nav class="navbar">
    <div class="container">
        <ul class="nav-links">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('students') }}">👨‍🎓 Students</a></li>
            <li><a href="{{ url_for('teachers') }}">👨‍🏫 Teachers</a></li>
            <li><a href="{{ url_for('fees') }}">💰 Fees</a></li>
            <li><a href="{{ url_for('salary') }}">💼 Salary</a></li>
        </ul>
        {% if session.get('logged_in') %}
        <a href="{{ url_for('logout') }}" class="logout btn btn-danger">Logout</a>
        {% endif %}
    </div>
</nav>
"""

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to check if user is logged in"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template_string(f"""
    {CSS_STYLES}
    <div class="container" style="max-width: 400px; margin-top: 100px;">
        <div class="card">
            <h2 style="text-align: center; margin-bottom: 2rem; color: #333;">🔐 School LMS Login</h2>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required value="admin">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required value="admin123">
                </div>
                <button type="submit" class="btn" style="width: 100%;">Login</button>
            </form>
            <p style="text-align: center; margin-top: 1rem; color: #666;">
                Demo: admin / admin123
            </p>
        </div>
    </div>
    """)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Stats
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_teachers = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]
    total_fees_collected = conn.execute(
        "SELECT SUM(amount) FROM fees WHERE status = 'paid'"
    ).fetchone()[0] or 0
    pending_fees = conn.execute(
        "SELECT SUM(amount) FROM fees WHERE status = 'unpaid'"
    ).fetchone()[0] or 0
    
    conn.close()
    
    return render_template_string(f"""
    {CSS_STYLES}
    {NAVBAR}
    <div class="container">
        <div class="card">
            <h1 style="color: #333; margin-bottom: 2rem;">📊 School Management Dashboard</h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_students}</div>
                    <div class="stat-label">Total Students</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_teachers}</div>
                    <div class="stat-label">Total Teachers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">₹{total_fees_collected:,.2f}</div>
                    <div class="stat-label">Fees Collected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">₹{pending_fees:,.2f}</div>
                    <div class="stat-label">Pending Fees</div>
                </div>
            </div>
        </div>
    </div>
    """, total_students=total_students, total_teachers=total_teachers, 
         total_fees_collected=total_fees_collected, pending_fees=pending_fees)

@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    conn = get_db_connection()
    
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO students (name, class_name, section, parent_name)
            VALUES (?, ?, ?, ?)
        ''', (request.form['name'], request.form['class_name'], 
              request.form['section'], request.form['parent_name']))
        conn.commit()
        flash('Student added successfully!', 'success')
    
    if request.args.get('delete'):
        conn.execute('DELETE FROM students WHERE id = ?', (request.args['delete'],))
        conn.commit()
        flash('Student deleted successfully!', 'success')
    
    students = conn.execute('''
        SELECT * FROM students ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template_string(f"""
    {CSS_STYLES}
    {NAVBAR}
    <div class="container">
        <div class="card">
            <h2>👨‍🎓 Student Management</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <!-- Add Student Form -->
            <form method="POST" style="margin-bottom: 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Class</label>
                    <input type="text" name="class_name" required placeholder="e.g., 10A">
                </div>
                <div class="form-group">
                    <label>Section</label>
                    <input type="text" name="section" required>
                </div>
                <div class="form-group">
                    <label>Parent Name</label>
                    <input type="text" name="parent_name" required>
                </div>
                <button type="submit" class="btn">➕ Add Student</button>
            </form>
            
            <!-- Students Table -->
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Class</th>
                        <th>Section</th>
                        <th>Parent</th>
                        <th>Date Added</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>{{ student['id'] }}</td>
                        <td>{{ student['name'] }}</td>
                        <td>{{ student['class_name'] }}</td>
                        <td>{{ student['section'] }}</td>
                        <td>{{ student['parent_name'] }}</td>
                        <td>{{ student['created_at'][:10] }}</td>
                        <td>
                            <a href="?delete={{ student['id'] }}" 
                               class="btn btn-danger" 
                               style="padding: 6px 12px; font-size: 14px;"
                               onclick="return confirm('Delete {{ student['name'] }}?')">🗑️ Delete</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """, students=students)

@app.route('/teachers', methods=['GET', 'POST'])
@login_required
def teachers():
    conn = get_db_connection()
    
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO teachers (name, subject, phone)
            VALUES (?, ?, ?)
        ''', (request.form['name'], request.form['subject'], request.form['phone']))
        conn.commit()
        flash('Teacher added successfully!', 'success')
    
    if request.args.get('delete'):
        conn.execute('DELETE FROM teachers WHERE id = ?', (request.args['delete'],))
        conn.commit()
        flash('Teacher deleted successfully!', 'success')
    
    teachers_list = conn.execute('''
        SELECT * FROM teachers ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template_string(f"""
    {CSS_STYLES}
    {NAVBAR}
    <div class="container">
        <div class="card">
            <h2>👨‍🏫 Teacher Management</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <!-- Add Teacher Form -->
            <form method="POST" style="margin-bottom: 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Subject</label>
                    <input type="text" name="subject" required>
                </div>
                <div class="form-group">
                    <label>Phone</label>
                    <input type="text" name="phone">
                </div>
                <button type="submit" class="btn">➕ Add Teacher</button>
            </form>
            
            <!-- Teachers Table -->
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Subject</th>
                        <th>Phone</th>
                        <th>Date Added</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for teacher in teachers_list %}
                    <tr>
                        <td>{{ teacher['id'] }}</td>
                        <td>{{ teacher['name'] }}</td>
                        <td>{{ teacher['subject'] }}</td>
                        <td>{{ teacher['phone'] or 'N/A' }}</td>
                        <td>{{ teacher['created_at'][:10] }}</td>
                        <td>
                            <a href="?delete={{ teacher['id'] }}" 
                               class="btn btn-danger" 
                               style="padding: 6px 12px; font-size: 14px;"
                               onclick="return confirm('Delete {{ teacher['name'] }}?')">🗑️ Delete</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """, teachers_list
