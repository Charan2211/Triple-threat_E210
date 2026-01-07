import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

class FundraisingManager:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def create_pitch(self, vendor_id: int, pitch_data: Dict) -> int:
        """Create a fundraising pitch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fundraising_pitches 
            (vendor_id, title, problem_statement, solution, market_size,
             business_model, traction, funding_amount, equity_offered,
             timeline, pitch_deck_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vendor_id,
            pitch_data['title'],
            pitch_data['problem_statement'],
            pitch_data['solution'],
            pitch_data['market_size'],
            pitch_data['business_model'],
            pitch_data.get('traction', ''),
            pitch_data['funding_amount'],
            pitch_data.get('equity_offered', 0),
            pitch_data.get('timeline', '6-12 months'),
            pitch_data.get('pitch_deck_url', ''),
            'draft'
        ))
        
        pitch_id = cursor.lastrowid
        conn.commit()
        
        # Generate pitch score
        score = self.calculate_pitch_score(pitch_id)
        
        cursor.execute('''
            UPDATE fundraising_pitches 
            SET investor_interest = ?
            WHERE pitch_id = ?
        ''', (score, pitch_id))
        
        conn.commit()
        conn.close()
        
        return pitch_id
    
    def calculate_pitch_score(self, pitch_id: int) -> int:
        """Calculate pitch quality score (1-100)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fundraising_pitches WHERE pitch_id = ?', (pitch_id,))
        pitch = cursor.fetchone()
        
        if not pitch:
            return 0
        
        pitch_dict = dict(pitch)
        
        score = 0
        
        # Problem statement (20 points)
        if len(pitch_dict['problem_statement']) > 100:
            score += 15
        if 'pain' in pitch_dict['problem_statement'].lower():
            score += 5
        
        # Solution clarity (20 points)
        if len(pitch_dict['solution']) > 50:
            score += 20
        
        # Market size (20 points)
        market_size = pitch_dict['market_size']
        if 'billion' in market_size.lower():
            score += 20
        elif 'million' in market_size.lower():
            score += 15
        else:
            score += 10
        
        # Traction (20 points)
        if pitch_dict['traction']:
            traction = pitch_dict['traction'].lower()
            if 'revenue' in traction:
                score += 15
            if 'users' in traction:
                score += 5
        
        # Funding amount appropriateness (20 points)
        try:
            funding_amount = float(pitch_dict['funding_amount'])
            if 50000 <= funding_amount <= 500000:
                score += 20  # Appropriate for seed round
            elif 500000 < funding_amount <= 2000000:
                score += 15  # Series A range
            else:
                score += 10
        except:
            score += 10
        
        conn.close()
        return min(score, 100)
    
    def find_investor_matches(self, pitch_id: int) -> List[Dict]:
        """Find matching investors for a pitch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pitch details
        cursor.execute('''
            SELECT p.*, v.industry, v.location 
            FROM fundraising_pitches p
            JOIN vendor_profiles v ON p.vendor_id = v.vendor_id
            WHERE p.pitch_id = ?
        ''', (pitch_id,))
        pitch = cursor.fetchone()
        
        if not pitch:
            return []
        
        pitch_dict = dict(pitch)
        
        # Find matching investors
        cursor.execute('SELECT * FROM investors')
        investors = cursor.fetchall()
        
        matches = []
        
        for investor in investors:
            investor_dict = dict(investor)
            match_score = 0
            
            # Industry match (40 points)
            investor_industries = json.loads(investor_dict['industries'])
            if pitch_dict['industry'] in investor_industries:
                match_score += 40
            
            # Location match (30 points)
            if investor_dict['location_preference']:
                if pitch_dict['location'] in investor_dict['location_preference']:
                    match_score += 30
            
            # Funding amount match (30 points)
            try:
                funding_needed = float(pitch_dict['funding_amount'])
                check_min = float(investor_dict['check_size_min'])
                check_max = float(investor_dict['check_size_max'])
                
                if check_min <= funding_needed <= check_max:
                    match_score += 30
                elif funding_needed < check_min:
                    match_score += 15
                else:
                    match_score += 10
            except:
                match_score += 10
            
            if match_score >= 50:  # Threshold for showing match
                matches.append({
                    'investor': investor_dict['name'],
                    'firm': investor_dict['firm'],
                    'match_score': match_score,
                    'investment_stage': investor_dict['investment_stage'],
                    'contact_info': investor_dict['contact_info']
                })
        
        conn.close()
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def generate_pitch_template(self, industry: str) -> Dict:
        """Generate a pitch deck template"""
        templates = {
            'technology': {
                'slides': [
                    {'title': 'Problem', 'content': 'What problem are you solving?'},
                    {'title': 'Solution', 'content': 'Your innovative solution'},
                    {'title': 'Market Size', 'content': 'TAM, SAM, SOM analysis'},
                    {'title': 'Business Model', 'content': 'How you make money'},
                    {'title': 'Traction', 'content': 'Current achievements'},
                    {'title': 'Team', 'content': 'Founder backgrounds'},
                    {'title': 'Competition', 'content': 'Competitive landscape'},
                    {'title': 'Funding Ask', 'content': 'How much and for what'}
                ],
                'tips': [
                    'Focus on scalability',
                    'Highlight tech differentiation',
                    'Show user growth metrics'
                ]
            },
            'restaurant': {
                'slides': [
                    {'title': 'Concept', 'content': 'Restaurant vision and theme'},
                    {'title': 'Market Need', 'content': 'Local dining gap'},
                    {'title': 'Menu & Pricing', 'content': 'Signature dishes and pricing'},
                    {'title': 'Location Analysis', 'content': 'Site selection rationale'},
                    {'title': 'Operations Plan', 'content': 'Daily operations'},
                    {'title': 'Marketing Strategy', 'content': 'Customer acquisition'},
                    {'title': 'Financial Projections', 'content': '3-year projections'},
                    {'title': 'Funding Use', 'content': 'Equipment, build-out, working capital'}
                ],
                'tips': [
                    'Emphasize unique dining experience',
                    'Show local market research',
                    'Include chef credentials'
                ]
            }
        }
        
        return templates.get(industry, templates['technology'])
