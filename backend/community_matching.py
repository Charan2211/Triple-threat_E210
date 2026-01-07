import sqlite3
import json
from typing import List, Dict, Any

class CommunityMatching:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def find_similar_vendors(self, vendor_id: int, limit: int = 10) -> List[Dict]:
        """Find vendors with similar profiles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get target vendor profile
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        target_vendor = cursor.fetchone()
        
        if not target_vendor:
            return []
        
        target_dict = dict(target_vendor)
        
        # Get all other vendors
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id != ?', (vendor_id,))
        all_vendors = cursor.fetchall()
        
        similarities = []
        
        for vendor in all_vendors:
            vendor_dict = dict(vendor)
            similarity_score = self.calculate_similarity(target_dict, vendor_dict)
            
            if similarity_score > 0.3:  # Threshold
                similarities.append({
                    'vendor_id': vendor_dict['vendor_id'],
                    'business_name': vendor_dict['business_name'],
                    'industry': vendor_dict['industry'],
                    'similarity_score': similarity_score,
                    'common_features': self.get_common_features(target_dict, vendor_dict)
                })
        
        conn.close()
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:limit]
    
    def calculate_similarity(self, vendor1: Dict, vendor2: Dict) -> float:
        """Calculate similarity score between two vendors"""
        score = 0
        factors = 0
        
        # Industry match (40%)
        if vendor1['industry'] == vendor2['industry']:
            score += 0.4
        factors += 0.4
        
        # Location proximity (20%)
        if vendor1['location'] and vendor2['location']:
            # Simple location match
            if vendor1['location'] == vendor2['location']:
                score += 0.2
            elif vendor1['location'].split(',')[0] == vendor2['location'].split(',')[0]:
                score += 0.1
        factors += 0.2
        
        # Business type (15%)
        if vendor1['business_type'] == vendor2['business_type']:
            score += 0.15
        factors += 0.15
        
        # Target audience overlap (15%)
        audience1 = set(json.loads(vendor1['target_audience']))
        audience2 = set(json.loads(vendor2['target_audience']))
        
        if audience1 and audience2:
            overlap = len(audience1.intersection(audience2)) / len(audience1.union(audience2))
            score += overlap * 0.15
        factors += 0.15
        
        # Budget similarity (10%)
        budget1 = vendor1['budget'] or 0
        budget2 = vendor2['budget'] or 0
        
        if budget1 > 0 and budget2 > 0:
            ratio = min(budget1, budget2) / max(budget1, budget2)
            score += ratio * 0.1
        factors += 0.1
        
        return score / factors if factors > 0 else 0
    
    def get_common_features(self, vendor1: Dict, vendor2: Dict) -> List[str]:
        """Get common features between vendors"""
        common = []
        
        if vendor1['industry'] == vendor2['industry']:
            common.append(f"Same industry: {vendor1['industry']}")
        
        if vendor1['location'] == vendor2['location']:
            common.append(f"Same location: {vendor1['location']}")
        
        # Common goals
        goals1 = set(json.loads(vendor1['goals']))
        goals2 = set(json.loads(vendor2['goals']))
        common_goals = goals1.intersection(goals2)
        
        if common_goals:
            common.append(f"Shared goals: {', '.join(list(common_goals)[:3])}")
        
        # Similar budget range
        budget1 = vendor1['budget'] or 0
        budget2 = vendor2['budget'] or 0
        
        if abs(budget1 - budget2) < max(budget1, budget2) * 0.5:  # Within 50%
            common.append("Similar budget range")
        
        return common
    
    def create_community_groups(self):
        """Create community groups based on similarities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all vendors
        cursor.execute('SELECT vendor_id FROM vendor_profiles')
        vendor_ids = [row[0] for row in cursor.fetchall()]
        
        groups = []
        processed = set()
        
        for vendor_id in vendor_ids:
            if vendor_id in processed:
                continue
            
            # Find similar vendors
            similar = self.find_similar_vendors(vendor_id, limit=5)
            similar_ids = [s['vendor_id'] for s in similar if s['similarity_score'] > 0.5]
            
            if similar_ids:
                group = [vendor_id] + similar_ids
                groups.append({
                    'name': f"Community Group {len(groups) + 1}",
                    'members': group,
                    'size': len(group),
                    'common_industry': self.get_common_industry(group)
                })
                
                processed.update(group)
            else:
                processed.add(vendor_id)
        
        conn.close()
        return groups
    
    def get_common_industry(self, vendor_ids: List[int]) -> str:
        """Get the most common industry among vendors"""
        if not vendor_ids:
            return "Mixed"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(vendor_ids))
        cursor.execute(f'''
            SELECT industry, COUNT(*) as count
            FROM vendor_profiles
            WHERE vendor_id IN ({placeholders})
            GROUP BY industry
            ORDER BY count DESC
            LIMIT 1
        ''', vendor_ids)
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else "Mixed"
    
    def recommend_community_actions(self, vendor_id: int) -> List[Dict]:
        """Recommend community actions for a vendor"""
        similar_vendors = self.find_similar_vendors(vendor_id, limit=5)
        
        recommendations = []
        
        if similar_vendors:
            top_match = similar_vendors[0]
            recommendations.append({
                'type': 'connect',
                'title': f'Connect with {top_match["business_name"]}',
                'description': f'Similar business in {top_match["industry"]} industry',
                'reason': f'High similarity score: {top_match["similarity_score"]:.2f}',
                'priority': 'high'
            })
        
        # Check for collaboration opportunities
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.business_name, v.industry, 
                   COUNT(c.collab_id) as collaborations
            FROM vendor_profiles v
            LEFT JOIN collaborations c ON v.vendor_id IN (c.vendor1_id, c.vendor2_id)
            WHERE v.vendor_id != ?
            GROUP BY v.vendor_id
            HAVING collaborations < 3
            ORDER BY collaborations ASC
            LIMIT 3
        ''', (vendor_id,))
        
        potential_partners = cursor.fetchall()
        conn.close()
        
        for partner in potential_partners:
            recommendations.append({
                'type': 'collaborate',
                'title': f'Collaborate with {partner[0]}',
                'description': f'They have few existing collaborations',
                'reason': f'{partner[1]} industry, only {partner[2]} collaborations',
                'priority': 'medium'
            })
        
        return recommendations
