import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests

class AdvertisingManager:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
        # In production, use actual API keys from environment variables
        self.platform_apis = {
            'google_ads': None,
            'facebook': None,
            'instagram': None,
            'linkedin': None,
            'twitter': None
        }
    
    def create_campaign(self, vendor_id: int, campaign_data: Dict) -> int:
        """Create a new advertising campaign"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ad_campaigns 
            (vendor_id, campaign_name, platform, ad_type, budget, daily_budget,
             target_audience, keywords, ad_copy, visuals, landing_page,
             start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vendor_id,
            campaign_data['campaign_name'],
            campaign_data['platform'],
            campaign_data['ad_type'],
            campaign_data['budget'],
            campaign_data.get('daily_budget', campaign_data['budget']/30),
            json.dumps(campaign_data['target_audience']),
            json.dumps(campaign_data.get('keywords', [])),
            campaign_data['ad_copy'],
            json.dumps(campaign_data.get('visuals', [])),
            campaign_data.get('landing_page', ''),
            campaign_data['start_date'],
            campaign_data['end_date'],
            'pending'
        ))
        
        campaign_id = cursor.lastrowid
        
        # Generate performance prediction
        prediction = self.predict_campaign_performance(campaign_data)
        
        cursor.execute('''
            UPDATE ad_campaigns 
            SET performance_metrics = ?
            WHERE campaign_id = ?
        ''', (json.dumps(prediction), campaign_id))
        
        conn.commit()
        conn.close()
        
        return campaign_id
    
    def predict_campaign_performance(self, campaign_data: Dict) -> Dict:
        """Predict campaign performance based on historical data"""
        # Simplified prediction algorithm
        # In production, use ML models trained on historical data
        
        platform_multipliers = {
            'google': 1.2,
            'facebook': 1.0,
            'instagram': 0.9,
            'linkedin': 1.5,
            'twitter': 0.8
        }
        
        budget = campaign_data['budget']
        platform = campaign_data['platform']
        duration = (datetime.strptime(campaign_data['end_date'], '%Y-%m-%d') - 
                   datetime.strptime(campaign_data['start_date'], '%Y-%m-%d')).days
        
        if duration == 0:
            duration = 1
        
        daily_budget = budget / duration
        multiplier = platform_multipliers.get(platform, 1.0)
        
        # Estimated metrics
        estimated_impressions = int(daily_budget * 1000 * multiplier)
        estimated_clicks = int(estimated_impressions * 0.02)  # 2% CTR
        estimated_conversions = int(estimated_clicks * 0.05)  # 5% conversion rate
        estimated_cpc = daily_budget / estimated_clicks if estimated_clicks > 0 else 0
        
        return {
            'estimated_impressions': estimated_impressions,
            'estimated_clicks': estimated_clicks,
            'estimated_conversions': estimated_conversions,
            'estimated_cpc': estimated_cpc,
            'estimated_roi': (estimated_conversions * 50) / budget  # Assuming $50 avg order value
        }
    
    def optimize_campaign(self, campaign_id: int) -> Dict:
        """Provide optimization suggestions for a campaign"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            return {}
        
        campaign_dict = dict(campaign)
        campaign_dict['performance_metrics'] = json.loads(campaign_dict['performance_metrics'])
        
        optimizations = []
        
        # Check budget allocation
        if campaign_dict['daily_budget'] < 10:
            optimizations.append({
                'area': 'budget',
                'suggestion': 'Increase daily budget to at least $10 for better reach',
                'expected_impact': '+25% impressions',
                'priority': 'high'
            })
        
        # Check keywords
        keywords = json.loads(campaign_dict['keywords'])
        if len(keywords) < 5:
            optimizations.append({
                'area': 'keywords',
                'suggestion': 'Add more specific keywords (5-15 recommended)',
                'expected_impact': '+15% CTR',
                'priority': 'medium'
            })
        
        # Check ad copy length
        if len(campaign_dict['ad_copy']) < 50:
            optimizations.append({
                'area': 'ad_copy',
                'suggestion': 'Make ad copy more descriptive (50-90 characters optimal)',
                'expected_impact': '+10% engagement',
                'priority': 'medium'
            })
        
        # Check timing
        start_date = datetime.strptime(campaign_dict['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(campaign_dict['end_date'], '%Y-%m-%d')
        
        if (end_date - start_date).days < 7:
            optimizations.append({
                'area': 'duration',
                'suggestion': 'Extend campaign to at least 7 days for better learning',
                'expected_impact': '+30% data quality',
                'priority': 'low'
            })
        
        conn.close()
        
        return {
            'campaign': campaign_dict['campaign_name'],
            'current_status': campaign_dict['status'],
            'optimizations': optimizations
        }
    
    def get_platform_recommendations(self, vendor_id: int) -> List[Dict]:
        """Recommend advertising platforms based on vendor profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            return []
        
        vendor_dict = dict(vendor)
        
        recommendations = []
        
        # B2B businesses
        if vendor_dict['industry'] in ['technology', 'consulting', 'enterprise']:
            recommendations.append({
                'platform': 'linkedin',
                'reason': 'Best for B2B and professional services',
                'budget_suggestion': '$500-2000/month',
                'targeting': 'Job titles, industries, company size'
            })
        
        # Visual products
        if vendor_dict['industry'] in ['fashion', 'food', 'art', 'home_decor']:
            recommendations.append({
                'platform': 'instagram',
                'reason': 'Visual platform perfect for product showcase',
                'budget_suggestion': '$300-1000/month',
                'targeting': 'Interests, demographics, lookalike audiences'
            })
        
        # Local businesses
        if 'local' in vendor_dict.get('location', '').lower():
            recommendations.append({
                'platform': 'google',
                'reason': 'Local search intent and Google Maps integration',
                'budget_suggestion': '$200-800/month',
                'targeting': 'Location, search intent, keywords'
            })
        
        # All businesses should consider Facebook
        recommendations.append({
            'platform': 'facebook',
            'reason': 'Broad reach and sophisticated targeting options',
            'budget_suggestion': '$200-1000/month',
            'targeting': 'Demographics, interests, behaviors'
        })
        
        conn.close()
        return recommendations