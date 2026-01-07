import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule
import time
from threading import Thread
import requests

class ContentAutomation:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
        self.scheduler_thread = None
        
    def generate_content_ideas(self, vendor_id: int, count: int = 10) -> List[Dict]:
        """Generate content ideas for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            return []
        
        vendor_dict = dict(vendor)
        
        # Content templates based on industry
        industry_templates = {
            'restaurant': [
                "Behind the scenes: How we make our signature dish",
                "Customer spotlight: Our favorite regulars",
                "New menu item announcement",
                "Cooking tips from our chef",
                "Local ingredient showcase"
            ],
            'retail': [
                "Product highlight: {product}",
                "How to style: Fashion tips",
                "Customer reviews showcase",
                "Sale announcement",
                "New arrivals preview"
            ],
            'services': [
                "Case study: How we helped {client_type}",
                "Industry insights: {topic}",
                "Team member spotlight",
                "FAQ: Answering common questions",
                "How-to guide: {task}"
            ]
        }
        
        # Generate content ideas
        content_ideas = []
        templates = industry_templates.get(vendor_dict['industry'], industry_templates['services'])
        
        for i in range(min(count, len(templates))):
            content_ideas.append({
                'title': templates[i],
                'content_type': 'post',
                'platform': ['instagram', 'facebook'],
                'estimated_time': 30,
                'difficulty': 'easy'
            })
        
        # Add promotional content
        content_ideas.append({
            'title': f"Special offer: 20% off for new customers",
            'content_type': 'promotion',
            'platform': ['facebook', 'instagram'],
            'estimated_time': 15,
            'difficulty': 'easy'
        })
        
        # Add educational content
        content_ideas.append({
            'title': f"5 things to know about {vendor_dict['industry']}",
            'content_type': 'educational',
            'platform': ['linkedin', 'blog'],
            'estimated_time': 45,
            'difficulty': 'medium'
        })
        
        conn.close()
        return content_ideas
    
    def schedule_content(self, vendor_id: int, content_data: Dict) -> int:
        """Schedule content for posting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO content_calendar 
            (vendor_id, title, content_type, platform, content_text, 
             media_url, hashtags, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vendor_id,
            content_data['title'],
            content_data['content_type'],
            json.dumps(content_data['platform']),
            content_data.get('content_text', ''),
            content_data.get('media_url', ''),
            json.dumps(content_data.get('hashtags', [])),
            content_data['scheduled_time'],
            'scheduled'
        ))
        
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to scheduler
        self.add_to_scheduler(content_id, content_data['scheduled_time'])
        
        return content_id
    
    def add_to_scheduler(self, content_id: int, scheduled_time: str):
        """Add content to automated scheduler"""
        scheduled_dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
        
        def post_content():
            """Function to execute when scheduled time arrives"""
            self.execute_content_post(content_id)
        
        # Schedule the post
        schedule.every().day.at(scheduled_dt.strftime('%H:%M')).do(post_content)
    
    def execute_content_post(self, content_id: int):
        """Execute content posting to social media"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM content_calendar WHERE content_id = ?', (content_id,))
        content = cursor.fetchone()
        
        if not content:
            return
        
        content_dict = dict(content)
        
        # Update status to posting
        cursor.execute('''
            UPDATE content_calendar 
            SET status = 'posting'
            WHERE content_id = ?
        ''', (content_id,))
        conn.commit()
        
        try:
            # In production, integrate with social media APIs
            platforms = json.loads(content_dict['platform'])
            
            for platform in platforms:
                if platform == 'facebook':
                    # Post to Facebook API
                    pass
                elif platform == 'instagram':
                    # Post to Instagram API
                    pass
                elif platform == 'linkedin':
                    # Post to LinkedIn API
                    pass
                elif platform == 'twitter':
                    # Post to Twitter API
                    pass
            
            # Update status to posted
            cursor.execute('''
                UPDATE content_calendar 
                SET status = 'posted',
                    performance_metrics = ?
                WHERE content_id = ?
            ''', (json.dumps({'posted_at': datetime.now().isoformat()}), content_id))
            
        except Exception as e:
            print(f"Error posting content: {e}")
            cursor.execute('''
                UPDATE content_calendar 
                SET status = 'failed'
                WHERE content_id = ?
            ''', (content_id,))
        
        conn.commit()
        conn.close()
    
    def start_scheduler(self):
        """Start the content scheduler in a separate thread"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def generate_hashtags(self, industry: str, content: str) -> List[str]:
        """Generate relevant hashtags for content"""
        industry_hashtags = {
            'restaurant': ['food', 'foodie', 'restaurant', 'dining', 'chef'],
            'retail': ['shopping', 'fashion', 'style', 'shoplocal', 'retail'],
            'technology': ['tech', 'innovation', 'startup', 'digital', 'ai'],
            'services': ['service', 'professional', 'business', 'expert', 'consulting']
        }
        
        base_tags = industry_hashtags.get(industry, ['business', 'entrepreneur', 'smallbusiness'])
        
        # Add trending tags (simplified)
        trending = ['trending', 'viral', 'popular']
        
        # Add content-specific tags
        content_words = content.lower().split()
        content_tags = [word for word in content_words if len(word) > 4][:3]
        
        all_tags = base_tags + trending + content_tags
        return [f"#{tag}" for tag in all_tags[:10]]
