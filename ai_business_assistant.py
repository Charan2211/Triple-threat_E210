import openai
import json
from typing import List, Dict, Any
import sqlite3
from datetime import datetime, timedelta

class AIBusinessAssistant:
    def __init__(self, api_key, db_path='platform.db'):
        openai.api_key = api_key
        self.db_path = db_path
        self.model = "gpt-4"
        
    def generate_recommendations(self, vendor_id: int) -> List[Dict]:
        """Generate AI-powered business recommendations"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get vendor profile
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            return []
        
        # Get vendor's recent campaigns
        cursor.execute('''
            SELECT * FROM ad_campaigns 
            WHERE vendor_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (vendor_id,))
        campaigns = cursor.fetchall()
        
        # Get vendor's content
        cursor.execute('''
            SELECT * FROM content_calendar 
            WHERE vendor_id = ? 
            ORDER BY scheduled_time DESC 
            LIMIT 10
        ''', (vendor_id,))
        content = cursor.fetchall()
        
        conn.close()
        
        # Prepare context for AI
        context = {
            "business": dict(vendor),
            "recent_campaigns": [dict(c) for c in campaigns],
            "recent_content": [dict(c) for c in content]
        }
        
        # Generate recommendations using OpenAI
        prompt = f"""
        As a business AI advisor, analyze this business profile and suggest actionable recommendations:
        
        Business: {context['business']['business_name']}
        Industry: {context['business']['industry']}
        Budget: ${context['business']['budget']}
        Goals: {context['business']['goals']}
        
        Recent Campaigns: {len(context['recent_campaigns'])}
        Recent Content: {len(context['recent_content'])}
        
        Please provide:
        1. Top 3 advertising opportunities
        2. Content strategy suggestions
        3. Funding/financing options
        4. Potential partnerships
        5. Quick wins (low cost, high impact)
        
        Format as JSON with keys: advertising, content, funding, partnerships, quick_wins.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a business growth advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            recommendations = json.loads(response.choices[0].message.content)
            
            # Save recommendations to database
            self.save_recommendations(vendor_id, recommendations)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self.get_fallback_recommendations(vendor)
    
    def save_recommendations(self, vendor_id: int, recommendations: Dict):
        """Save AI recommendations to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for category, items in recommendations.items():
            if isinstance(items, list):
                for item in items:
                    cursor.execute('''
                        INSERT INTO ai_recommendations 
                        (vendor_id, recommendation_type, content, priority, action_items)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        vendor_id,
                        category,
                        item.get('description', str(item)),
                        item.get('priority', 1),
                        json.dumps(item.get('actions', []))
                    ))
        
        conn.commit()
        conn.close()
    
    def get_fallback_recommendations(self, vendor):
        """Fallback recommendations if AI fails"""
        recommendations = {
            "advertising": [
                {
                    "description": "Set up Google Ads with $10/day budget targeting local customers",
                    "priority": 1,
                    "actions": ["create_google_account", "setup_keywords", "create_ad_copy"]
                }
            ],
            "content": [
                {
                    "description": "Post 3 times per week on Instagram showcasing products",
                    "priority": 2,
                    "actions": ["create_content_calendar", "take_product_photos", "schedule_posts"]
                }
            ]
        }
        return recommendations
    
    def generate_ad_copy(self, product_description: str, target_audience: str, platform: str) -> Dict:
        """Generate ad copy using AI"""
        prompt = f"""
        Generate compelling ad copy for:
        Product: {product_description}
        Target Audience: {target_audience}
        Platform: {platform}
        
        Please provide:
        1. A catchy headline (max 60 characters)
        2. Primary ad text (max 125 characters)
        3. Call-to-action button text
        4. 3 relevant hashtags
        5. Emotional appeal angle
        
        Format as JSON.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generating ad copy: {e}")
            return {
                "headline": f"Amazing {product_description[:20]}...",
                "text": f"Discover our {product_description}. Perfect for {target_audience}!",
                "cta": "Learn More",
                "hashtags": ["#business", "#product", "#sale"],
                "angle": "Value and convenience"
            }