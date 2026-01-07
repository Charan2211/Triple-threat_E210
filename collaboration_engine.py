import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime

class CollaborationEngine:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def find_collaboration_matches(self, vendor_id: int) -> List[Dict]:
        """Find potential collaboration partners"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get requesting vendor profile
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        requester = cursor.fetchone()
        
        if not requester:
            return []
        
        requester_dict = dict(requester)
        
        # Get all other vendors
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id != ?', (vendor_id,))
        all_vendors = cursor.fetchall()
        
        matches = []
        
        for vendor in all_vendors:
            vendor_dict = dict(vendor)
            match_score = 0
            collaboration_types = []
            
            # Industry complementarity (30 points)
            if self.are_industries_complementary(requester_dict['industry'], vendor_dict['industry']):
                match_score += 30
                collaboration_types.append('cross_promotion')
            
            # Location proximity (20 points)
            if requester_dict['location'] == vendor_dict['location']:
                match_score += 20
                collaboration_types.append('local_partnership')
            
            # Goal alignment (25 points)
            requester_goals = json.loads(requester_dict['goals'])
            vendor_goals = json.loads(vendor_dict['goals'])
            
            common_goals = set(requester_goals) & set(vendor_goals)
            if common_goals:
                match_score += len(common_goals) * 5
                collaboration_types.append('shared_objectives')
            
            # Skill complementarity (25 points)
            if self.has_complementary_skills(requester_dict, vendor_dict):
                match_score += 25
                collaboration_types.append('skill_exchange')
            
            if match_score >= 40:  # Minimum threshold
                matches.append({
                    'vendor_id': vendor_dict['vendor_id'],
                    'business_name': vendor_dict['business_name'],
                    'industry': vendor_dict['industry'],
                    'location': vendor_dict['location'],
                    'match_score': match_score,
                    'collaboration_types': collaboration_types,
                    'synergy_areas': self.find_synergy_areas(requester_dict, vendor_dict)
                })
        
        conn.close()
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def are_industries_complementary(self, industry1: str, industry2: str) -> bool:
        """Check if two industries are complementary"""
        complementary_pairs = [
            ('restaurant', 'food_delivery'),
            ('retail', 'logistics'),
            ('software', 'consulting'),
            ('photography', 'real_estate'),
            ('event_planning', 'catering')
        ]
        
        for pair in complementary_pairs:
            if (industry1 == pair[0] and industry2 == pair[1]) or \
               (industry1 == pair[1] and industry2 == pair[0]):
                return True
        
        return False
    
    def has_complementary_skills(self, vendor1: Dict, vendor2: Dict) -> bool:
        """Check if vendors have complementary skills"""
        # Simplified skill detection based on business type
        skill_map = {
            'restaurant': ['culinary', 'customer_service', 'inventory_management'],
            'technology': ['programming', 'product_development', 'technical_support'],
            'retail': ['sales', 'merchandising', 'customer_relations'],
            'consulting': ['strategy', 'analysis', 'client_management'],
            'creative': ['design', 'content_creation', 'branding']
        }
        
        skills1 = skill_map.get(vendor1['industry'], [])
        skills2 = skill_map.get(vendor2['industry'], [])
        
        # Check if they have different primary skills
        return len(set(skills1) & set(skills2)) < 2
    
    def find_synergy_areas(self, vendor1: Dict, vendor2: Dict) -> List[str]:
        """Find specific areas of synergy between vendors"""
        synergies = []
        
        # Customer sharing
        if vendor1['target_audience'] and vendor2['target_audience']:
            audience1 = json.loads(vendor1['target_audience'])
            audience2 = json.loads(vendor2['target_audience'])
            
            if set(audience1) & set(audience2):
                synergies.append('shared_customer_base')
        
        # Resource sharing
        if vendor1['budget'] < 5000 or vendor2['budget'] < 5000:
            synergies.append('resource_pooling')
        
        # Marketing synergy
        if 'increase_sales' in json.loads(vendor1['goals']) and \
           'increase_sales' in json.loads(vendor2['goals']):
            synergies.append('joint_marketing')
        
        # Geographic synergy
        if vendor1['location'] == vendor2['location']:
            synergies.append('local_partnership')
        
        return synergies
    
    def initiate_collaboration(self, vendor1_id: int, vendor2_id: int, collaboration_type: str) -> int:
        """Initiate a collaboration between two vendors"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO collaborations 
            (vendor1_id, vendor2_id, collaboration_type, status)
            VALUES (?, ?, ?, ?)
        ''', (vendor1_id, vendor2_id, collaboration_type, 'proposed'))
        
        collab_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return collab_id
    
    def get_collaboration_ideas(self, vendor1: Dict, vendor2: Dict) -> List[str]:
        """Generate collaboration ideas for two vendors"""
        ideas = []
        
        if vendor1['industry'] == 'restaurant' and vendor2['industry'] == 'food_delivery':
            ideas.extend([
                'Joint promotion: Free delivery with restaurant purchase',
                'Co-branded marketing campaign',
                'Shared customer loyalty program'
            ])
        
        if vendor1['industry'] == 'retail' and vendor2['industry'] == 'retail':
            ideas.extend([
                'Cross-promotion in each other\'s stores',
                'Joint pop-up event',
                'Bundle deals combining products'
            ])
        
        if 'local' in vendor1['location'] and 'local' in vendor2['location']:
            ideas.extend([
                'Co-host local community event',
                'Joint advertisement in local newspaper',
                'Shared booth at local fair'
            ])
        
        # Generic collaboration ideas
        ideas.extend([
            'Social media shoutout exchange',
            'Co-created content (blog post, video)',
            'Referral program with incentives',
            'Shared workshop or webinar'
        ])
        
        return ideas