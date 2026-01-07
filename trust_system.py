import sqlite3
from datetime import datetime, timedelta

class TrustSystem:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize trust system tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trust_scores (
                vendor_id INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 50,
                reliability DECIMAL(3,2) DEFAULT 0.5,
                response_time DECIMAL(5,2),
                completion_rate DECIMAL(5,2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trust_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER,
                event_type VARCHAR(50),
                impact INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reviewer_id INTEGER,
                vendor_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reviewer_id) REFERENCES users(id),
                FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_trust_score(self, vendor_id):
        """Calculate comprehensive trust score for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get collaboration success rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM collaborations 
            WHERE vendor1_id = ? OR vendor2_id = ?
        ''', (vendor_id, vendor_id))
        
        collab_result = cursor.fetchone()
        collab_rate = collab_result[1] / collab_result[0] if collab_result[0] > 0 else 0
        
        # Get average review rating
        cursor.execute('''
            SELECT AVG(rating) FROM reviews WHERE vendor_id = ?
        ''', (vendor_id,))
        
        avg_rating = cursor.fetchone()[0] or 3.0
        
        # Get campaign completion rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM ad_campaigns WHERE vendor_id = ?
        ''', (vendor_id,))
        
        campaign_result = cursor.fetchone()
        campaign_rate = campaign_result[1] / campaign_result[0] if campaign_result[0] > 0 else 0
        
        # Calculate weighted trust score
        score = (
            (collab_rate * 30) +          # 30% collaboration success
            (avg_rating * 10) +           # 10% reviews (avg 3-5 = 30-50)
            (campaign_rate * 20) +        # 20% campaign completion
            40                            # 40% base score
        )
        
        # Normalize to 0-100
        score = min(max(score, 0), 100)
        
        # Update trust score
        cursor.execute('''
            INSERT OR REPLACE INTO trust_scores 
            (vendor_id, score, reliability, completion_rate, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (vendor_id, score, collab_rate, campaign_rate))
        
        conn.commit()
        conn.close()
        
        return score
    
    def add_trust_event(self, vendor_id, event_type, impact, description):
        """Record a trust-affecting event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trust_events (vendor_id, event_type, impact, description)
            VALUES (?, ?, ?, ?)
        ''', (vendor_id, event_type, impact, description))
        
        # Recalculate trust score
        self.calculate_trust_score(vendor_id)
        
        conn.commit()
        conn.close()
    
    def add_review(self, reviewer_id, vendor_id, rating, comment):
        """Add a review for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (reviewer_id, vendor_id, rating, comment)
            VALUES (?, ?, ?, ?)
        ''', (reviewer_id, vendor_id, rating, comment))
        
        # Recalculate trust score
        self.calculate_trust_score(vendor_id)
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_vendor_trust_report(self, vendor_id):
        """Get comprehensive trust report for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trust score
        cursor.execute('SELECT * FROM trust_scores WHERE vendor_id = ?', (vendor_id,))
        trust_data = cursor.fetchone()
        
        # Get recent reviews
        cursor.execute('''
            SELECT r.rating, r.comment, u.username, r.created_at
            FROM reviews r
            JOIN users u ON r.reviewer_id = u.id
            WHERE r.vendor_id = ?
            ORDER BY r.created_at DESC
            LIMIT 5
        ''', (vendor_id,))
        
        reviews = cursor.fetchall()
        
        # Get recent trust events
        cursor.execute('''
            SELECT event_type, impact, description, created_at
            FROM trust_events
            WHERE vendor_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (vendor_id,))
        
        events = cursor.fetchall()
        
        conn.close()
        
        return {
            'trust_score': trust_data[1] if trust_data else 50,
            'reliability': trust_data[2] if trust_data else 0.5,
            'reviews': [
                {
                    'rating': r[0],
                    'comment': r[1],
                    'reviewer': r[2],
                    'date': r[3]
                } for r in reviews
            ],
            'recent_events': [
                {
                    'type': e[0],
                    'impact': e[1],
                    'description': e[2],
                    'date': e[3]
                } for e in events
            ]
        }