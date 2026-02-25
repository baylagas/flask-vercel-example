from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
import dotenv

from supabase import create_client, Client

dotenv.load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Database setup - use /tmp directory in production (Vercel)
if os.environ.get('VERCEL'):
    DATABASE = '/tmp/persons.db'
else:
    DATABASE = 'persons.db'

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with the Persons table"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return 'About'

@app.route('/test_supa')
def test_supa():
   
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    """Test route to verify database connection"""
    try:
        response = (
            supabase.table("Products")
            .select("*")
            .execute()
        )
        return f'Database connection successful!{response}'
    except Exception as e:
        return f'Database connection failed: {e}', 500

# CRUD Routes for Persons
@app.route('/persons')
def list_persons():
    """Display all persons"""
    conn = get_db_connection()
    persons = conn.execute('SELECT * FROM persons ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('persons.html', persons=persons)

@app.route('/persons/add', methods=['GET', 'POST'])
def add_person():
    """Add a new person"""
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        
        if name and age:
            try:
                conn = get_db_connection()
                conn.execute('INSERT INTO persons (name, age) VALUES (?, ?)', (name, int(age)))
                conn.commit()
                conn.close()
                flash('Person added successfully!', 'success')
                return redirect(url_for('list_persons'))
            except ValueError:
                flash('Invalid age. Please enter a number.', 'error')
        else:
            flash('Please fill in all fields.', 'error')
    
    return render_template('add_person.html')

@app.route('/persons/edit/<int:person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    """Edit an existing person"""
    conn = get_db_connection()
    person = conn.execute('SELECT * FROM persons WHERE id = ?', (person_id,)).fetchone()
    
    if not person:
        flash('Person not found.', 'error')
        return redirect(url_for('list_persons'))
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        
        if name and age:
            try:
                conn.execute('UPDATE persons SET name = ?, age = ? WHERE id = ?', 
                           (name, int(age), person_id))
                conn.commit()
                conn.close()
                flash('Person updated successfully!', 'success')
                return redirect(url_for('list_persons'))
            except ValueError:
                flash('Invalid age. Please enter a number.', 'error')
        else:
            flash('Please fill in all fields.', 'error')
    
    conn.close()
    return render_template('edit_person.html', person=person)

@app.route('/persons/delete/<int:person_id>', methods=['POST'])
def delete_person(person_id):
    """Delete a person"""
    conn = get_db_connection()
    conn.execute('DELETE FROM persons WHERE id = ?', (person_id,))
    conn.commit()
    conn.close()
    flash('Person deleted successfully!', 'success')
    return redirect(url_for('list_persons'))

# API Routes for JSON responses
@app.route('/api/persons')
def api_list_persons():
    """API endpoint to get all persons as JSON"""
    conn = get_db_connection()
    persons = conn.execute('SELECT * FROM persons ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(person) for person in persons])

@app.route('/api/persons/<int:person_id>')
def api_get_person(person_id):
    """API endpoint to get a specific person as JSON"""
    conn = get_db_connection()
    person = conn.execute('SELECT * FROM persons WHERE id = ?', (person_id,)).fetchone()
    conn.close()
    
    if person:
        return jsonify(dict(person))
    else:
        return jsonify({'error': 'Person not found'}), 404