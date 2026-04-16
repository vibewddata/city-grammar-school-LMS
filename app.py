import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="School LMS",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DB_PATH = 'school_lms.db'

@st.cache_resource
def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Admin login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 School LMS Login")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")
        if st.button("Login 🚀", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Login successful! 🎉")
                st.rerun()
            else:
                st.error("Invalid credentials! ❌")
                st.info("Demo: admin / admin123")
    
    with col2:
        st.markdown("""
        ## 📚 School Management System
        **Features:**
        - 👨‍🎓 Student Management
        - 👨‍🏫 Teacher Management  
        - 💰 Fee Management
        - 💼 Salary Management
        - 📊 Analytics Dashboard
        """)

if not st.session_state.logged_in:
    login()
    st.stop()

# Initialize DB
init_db()

# Sidebar
st.sidebar.title("🏫 School LMS")
st.sidebar.markdown("---")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center; }
    .stButton > button { width: 100%; height: 2.5rem; border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Main App
def dashboard():
    st.markdown('<h1 class="main-header">📊 School Dashboard</h1>', unsafe_allow_html=True)
    
    conn = get_db_connection()
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_teachers = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]
    total_fees = conn.execute("SELECT SUM(amount) FROM fees WHERE status = 'paid'").fetchone()[0] or 0
    pending_fees = conn.execute("SELECT SUM(amount) FROM fees WHERE status = 'unpaid'").fetchone()[0] or 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='font-size: 2.5rem; margin: 0;'>{total_students}</h2>
            <p style='margin: 0;'>👨‍🎓 Students</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='font-size: 2.5rem; margin: 0;'>{total_teachers}</h2>
            <p style='margin: 0;'>👨‍🏫 Teachers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='font-size: 2.5rem; margin: 0;'>₹{total_fees:,.0f}</h2>
            <p style='margin: 0;'>💰 Collected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='font-size: 2.5rem; margin: 0;'>₹{pending_fees:,.0f}</h2>
            <p style='margin: 0;'>⏳ Pending</p>
        </div>
        """, unsafe_allow_html=True)
    
    conn.close()

def students_page():
    st.header("👨‍🎓 Student Management")
    
    # Add Student
    with st.expander("➕ Add New Student", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            class_name = st.text_input("Class", placeholder="10A")
        with col2:
            section = st.text_input("Section")
            parent_name = st.text_input("Parent Name")
        
        if st.button("Add Student", use_container_width=True):
            if name and class_name:
                conn = get_db_connection()
                conn.execute('INSERT INTO students (name, class_name, section, parent_name) VALUES (?, ?, ?, ?)',
                           (name, class_name, section or "N/A", parent_name or "N/A"))
                conn.commit()
                conn.close()
                st.success("Student added! 🎉")
                st.rerun()
    
    # Students Table
    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT * FROM students ORDER BY created_at DESC", conn)
    conn.close()
    
    if not students_df.empty:
        st.subheader(f"📋 {len(students_df)} Students")
        st.dataframe(students_df, use_container_width=True)
        
        # Delete functionality
        st.warning("⚠️ Select students to delete:")
        selected = st.multiselect("Select Student IDs to delete:", students_df['id'].tolist())
        if st.button("🗑️ Delete Selected", type="primary", use_container_width=True) and selected:
            conn = get_db_connection()
            for student_id in selected:
                conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
            conn.commit()
            conn.close()
            st.success(f"Deleted {len(selected)} students!")
            st.rerun()
    else:
        st.info("No students found. Add some! 👆")

def teachers_page():
    st.header("👨‍🏫 Teacher Management")
    
    # Add Teacher
    with st.expander("➕ Add New Teacher", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            subject = st.text_input("Subject")
        with col2:
            phone = st.text_input("Phone")
        
        if st.button("Add Teacher", use_container_width=True):
            if name and subject:
                conn = get_db_connection()
                conn.execute('INSERT INTO teachers (name, subject, phone) VALUES (?, ?, ?)',
                           (name, subject, phone or None))
                conn.commit()
                conn.close()
                st.success("Teacher added! 🎉")
                st.rerun()
    
    # Teachers Table
    conn = get_db_connection()
    teachers_df = pd.read_sql_query("SELECT * FROM teachers ORDER BY created_at DESC", conn)
    conn.close()
    
    if not teachers_df.empty:
        st.subheader(f"📋 {len(teachers_df)} Teachers")
        st.dataframe(teachers_df, use_container_width=True)
        
        selected = st.multiselect("Select Teacher IDs to delete:", teachers_df['id'].tolist())
        if st.button("🗑️ Delete Selected", type="primary", use_container_width=True) and selected:
            conn = get_db_connection()
            for teacher_id in selected:
                conn.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
            conn.commit()
            conn.close()
            st.success(f"Deleted {len(selected)} teachers!")
            st.rerun()
    else:
        st.info("No teachers found. Add some! 👆")

def fees_page():
    st.header("💰 Fee Management")
    
    conn = get_db_connection()
    students = conn.execute('SELECT id, name FROM students').fetchall()
    conn.close()
    
    # Add Fee
    with st.expander("➕ Generate Fee Record", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            student_id = st.selectbox("Student", [""] + [(s['id'], s['name']) for s in students])
            student_id = student_id[0] if isinstance(student_id, tuple) else student_id
        with col2:
            month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June",
                                         "July", "August", "September", "October", "November", "December"])
            year = st.number_input("Year", value=datetime.now().year, min_value=2020)
        with col3:
            amount = st.number_input("Amount (₹)", min_value=0.0, value=5000.0, step=100.0)
        
        col4, col5 = st.columns(2)
        with col4:
            if st.button("💾 Generate Fee", use_container_width=True):
                if student_id:
                    conn = get_db_connection()
                    conn.execute('INSERT INTO fees (student_id, month, year, amount) VALUES (?, ?, ?, ?)',
                               (student_id, month, year, amount))
                    conn.commit()
                    conn.close()
                    st.success("Fee record created! 🎉")
                    st.rerun()
    
    # Fees Table
    conn = get_db_connection()
    fees_df = pd.read_sql_query("""
        SELECT f.*, s.name as student_name 
        FROM fees f 
        JOIN students s ON f.student_id = s.id 
        ORDER BY f.created_at DESC
    """, conn)
    conn.close()
    
    if not fees_df.empty:
        st.subheader(f"📋 {len(fees_df)} Fee Records")
        
        # Fee Status Update
        status_col = st.columns([3,1,1])
        with status_col[1]:
            if st.button("✅ Mark Paid", use_container_width=True):
                pass  # Add logic here
        with status_col[2]:
            if st.button("❌ Mark Unpaid", use_container_width=True):
                pass  # Add logic here
        
        st.dataframe(fees_df, use_container_width=True)
    else:
        st.info("No fee records. Generate some! 👆")

def salary_page():
    st.header("💼 Salary Management")
    
    conn = get_db_connection()
    teachers = conn.execute('SELECT id, name FROM teachers').fetchall()
    conn.close()
    
    # Add Salary
    with st.expander("➕ Add Salary Record", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            teacher_id = st.selectbox("Teacher", [""] + [(t['id'], t['name']) for t in teachers])
            teacher_id = teacher_id[0] if isinstance(teacher_id, tuple) else teacher_id
        with col2:
            month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June",
                                         "July", "August", "September", "October", "November", "December"])
            year = st.number_input("Year", value=datetime.now().year, min_value=2020)
        with col3:
            amount = st.number_input("Salary (₹)", min_value=0.0, value=25000.0, step=1000.0)
        
        if st.button("💾 Add Salary", use_container_width=True):
            if teacher_id:
                conn = get_db_connection()
                conn.execute('INSERT INTO salary (teacher_id, month, year, amount) VALUES (?, ?, ?, ?)',
                           (teacher_id, month, year, amount))
                conn.commit()
                conn.close()
                st.success("Salary record added! 🎉")
                st.rerun()
    
    # Salary Table
    conn = get_db_connection()
    salary_df = pd.read_sql_query("""
        SELECT s.*, t.name as teacher_name 
        FROM salary s 
        JOIN teachers t ON s.teacher_id = t.id 
        ORDER BY s.created_at DESC
    """, conn)
    conn.close()
    
    if not salary_df.empty:
        st.subheader(f"📋 {len(salary_df)} Salary Records")
        st.dataframe(salary_df, use_container_width=True)
    else:
        st.info("No salary records. Add some! 👆")

# Navigation
page = st.sidebar.selectbox(
    "Choose Page",
    ["📊 Dashboard", "👨‍🎓 Students", "👨‍🏫 Teachers", "💰 Fees", "💼 Salary"]
)

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Render pages
if page == "📊 Dashboard":
    dashboard()
elif page == "👨‍🎓 Students":
    students_page()
elif page == "👨‍🏫 Teachers":
    teachers_page()
elif page == "💰 Fees":
    fees_page()
elif page == "💼 Salary":
    salary_page()

# Footer
st.markdown("---")
st.markdown("🏫 **School LMS** - Built with Streamlit | Data persists in SQLite")
