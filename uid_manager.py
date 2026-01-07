import sqlite3
import hashlib
import uuid
from datetime import datetime

class UIDManager:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                user_type VARCHAR(20) DEFAULT 'vendor',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, email, password, user_type='vendor'):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, user_type)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, user_type))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Create initial vendor profile
            if user_type == 'vendor':
                cursor.execute('''
                    INSERT INTO vendor_profiles (user_id, business_name)
                    VALUES (?, ?)
                ''', (user_id, f"{username}'s Business"))
                conn.commit()
            
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def authenticate_user(self, email, password):
        """Authenticate user login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT id, username, user_type FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (user[0],))
            conn.commit()
            
            # Create session
            session_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, expires_at)
                VALUES (?, ?, datetime('now', '+7 days'))
            ''', (session_id, user[0]))
            conn.commit()
            
            conn.close()
            return {
                'user_id': user[0],
                'username': user[1],
                'user_type': user[2],
                'session_id': session_id
            }
        
        conn.close()
        return None
    
    def validate_session(self, session_id):
        """Validate user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.user_type 
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'user_type': user[2]
            }
        return None
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, user_type, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'user_type': user[3],
                'created_at': user[4],
                'last_login': user[5]
            }
        return None