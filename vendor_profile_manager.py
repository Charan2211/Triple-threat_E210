from flask import jsonify
import sqlite3
import json
from datetime import datetime

class VendorProfileManager:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def create_vendor_profile(self, user_id, profile_data):
        """Create a new vendor profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vendor_profiles 
            (user_id, business_name, business_type, industry, location, 
             website, description, target_audience, budget, goals, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            profile_data.get('business_name'),
            profile_data.get('business_type'),
            profile_data.get('industry'),
            profile_data.get('location'),
            profile_data.get('website'),
            profile_data.get('description'),
            json.dumps(profile_data.get('target_audience', [])),
            profile_data.get('budget', 0),
            json.dumps(profile_data.get('goals', [])),
            json.dumps(profile_data.get('constraints', {}))
        ))
        
        vendor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return vendor_id
    
    def get_vendor_profile(self, vendor_id):
        """Retrieve vendor profile"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        profile = cursor.fetchone()
        
        if profile:
            profile_dict = dict(profile)
            # Parse JSON fields
            profile_dict['target_audience'] = json.loads(profile_dict['target_audience'])
            profile_dict['goals'] = json.loads(profile_dict['goals'])
            profile_dict['constraints'] = json.loads(profile_dict['constraints'])
        
        conn.close()
        return profile_dict if profile else None
    
    def update_vendor_profile(self, vendor_id, updates):
        """Update vendor profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        if 'business_name' in updates:
            update_fields.append('business_name = ?')
            values.append(updates['business_name'])
        
        if 'target_audience' in updates:
            update_fields.append('target_audience = ?')
            values.append(json.dumps(updates['target_audience']))
        
        if 'goals' in updates:
            update_fields.append('goals = ?')
            values.append(json.dumps(updates['goals']))
        
        if 'budget' in updates:
            update_fields.append('budget = ?')
            values.append(updates['budget'])
        
        if update_fields:
            values.append(vendor_id)
            query = f'''
                UPDATE vendor_profiles 
                SET {', '.join(update_fields)}
                WHERE vendor_id = ?
            '''
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        return True
    
    def analyze_vendor_needs(self, vendor_id):
        """Analyze vendor profile to identify needs"""
        profile = self.get_vendor_profile(vendor_id)
        
        if not profile:
            return None
        
        needs = []
        
        # Analyze budget constraints
        if profile['budget'] < 1000:
            needs.append({
                'category': 'funding',
                'priority': 'high',
                'description': 'Low budget detected. Consider fundraising options.',
                'actions': ['explore_grants', 'create_pitch', 'seek_partnerships']
            })
        
        # Analyze target audience
        if len(profile['target_audience']) < 3:
            needs.append({
                'category': 'marketing',
                'priority': 'medium',
                'description': 'Target audience definition is limited.',
                'actions': ['audience_research', 'competitor_analysis', 'create_buyer_personas']
            })
        
        # Analyze goals
        goals = profile['goals']
        if 'increase_sales' in goals:
            needs.append({
                'category': 'advertising',
                'priority': 'high',
                'description': 'Goal: Increase sales. Launch targeted ad campaigns.',
                'actions': ['create_google_ads', 'setup_facebook_ads', 'optimize_landing_pages']
            })
        
        if 'brand_awareness' in goals:
            needs.append({
                'category': 'content',
                'priority': 'medium',
                'description': 'Goal: Brand awareness. Develop content strategy.',
                'actions': ['content_calendar', 'social_media_plan', 'influencer_outreach']
            })
        
        return needs