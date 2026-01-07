import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ResourceOptimizer:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def optimize_budget_allocation(self, vendor_id: int) -> Dict:
        """Optimize budget allocation across marketing channels"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            return {}
        
        vendor_dict = dict(vendor)
        total_budget = vendor_dict['budget']
        
        # Get historical performance data
        cursor.execute('''
            SELECT platform, SUM(budget) as spent, 
                   AVG(json_extract(performance_metrics, '$.estimated_roi')) as avg_roi
            FROM ad_campaigns 
            WHERE vendor_id = ? AND status = 'completed'
            GROUP BY platform
        ''', (vendor_id,))
        
        historical_data = cursor.fetchall()
        
        conn.close()
        
        # Default allocation (if no historical data)
        if not historical_data:
            return self.get_default_allocation(vendor_dict, total_budget)
        
        # Calculate optimal allocation based on ROI
        platform_performance = {}
        total_weight = 0
        
        for platform, spent, roi in historical_data:
            if roi and roi > 0:
                weight = roi * (spent or 100)  # Weight by ROI and historical spend
                platform_performance[platform] = {
                    'roi': roi,
                    'spent': spent,
                    'weight': weight
                }
                total_weight += weight
        
        # Allocate budget proportionally to weights
        allocation = {}
        if total_weight > 0:
            for platform, data in platform_performance.items():
                percentage = data['weight'] / total_weight
                allocation[platform] = {
                    'budget': total_budget * percentage,
                    'percentage': percentage * 100,
                    'roi': data['roi']
                }
        else:
            allocation = self.get_default_allocation(vendor_dict, total_budget)
        
        # Add recommendations
        recommendations = self.generate_budget_recommendations(allocation, vendor_dict)
        
        return {
            'total_budget': total_budget,
            'allocation': allocation,
            'recommendations': recommendations
        }
    
    def get_default_allocation(self, vendor: Dict, total_budget: float) -> Dict:
        """Get default budget allocation based on business type"""
        industry = vendor['industry']
        
        if industry in ['restaurant', 'retail']:
            return {
                'facebook': {'budget': total_budget * 0.4, 'percentage': 40, 'roi': 2.5},
                'instagram': {'budget': total_budget * 0.3, 'percentage': 30, 'roi': 2.2},
                'google': {'budget': total_budget * 0.2, 'percentage': 20, 'roi': 3.0},
                'local_ads': {'budget': total_budget * 0.1, 'percentage': 10, 'roi': 2.0}
            }
        elif industry in ['technology', 'software']:
            return {
                'linkedin': {'budget': total_budget * 0.4, 'percentage': 40, 'roi': 3.5},
                'google': {'budget': total_budget * 0.3, 'percentage': 30, 'roi': 3.0},
                'content_marketing': {'budget': total_budget * 0.2, 'percentage': 20, 'roi': 2.8},
                'twitter': {'budget': total_budget * 0.1, 'percentage': 10, 'roi': 2.0}
            }
        else:
            return {
                'facebook': {'budget': total_budget * 0.5, 'percentage': 50, 'roi': 2.0},
                'google': {'budget': total_budget * 0.3, 'percentage': 30, 'roi': 2.5},
                'email_marketing': {'budget': total_budget * 0.2, 'percentage': 20, 'roi': 3.0}
            }
    
    def generate_budget_recommendations(self, allocation: Dict, vendor: Dict) -> List[str]:
        """Generate budget optimization recommendations"""
        recommendations = []
        total_budget = sum(item['budget'] for item in allocation.values())
        
        # Check if budget is too low
        if total_budget < 500:
            recommendations.append(
                f"Consider increasing total marketing budget from ${total_budget:.0f} to at least $500/month for meaningful impact"
            )
        
        # Identify underperforming channels
        for platform, data in allocation.items():
            if data.get('roi', 0) < 1.5 and data['budget'] > 100:
                recommendations.append(
                    f"Reduce {platform} spending (ROI: {data['roi']:.1f}x). Consider reallocating ${data['budget']:.0f} to better performing channels."
                )
        
        # Check for missing channels
        vendor_industry = vendor['industry']
        if vendor_industry in ['restaurant', 'retail'] and 'instagram' not in allocation:
            recommendations.append("Add Instagram marketing for visual product showcasing")
        
        if vendor_industry in ['technology', 'consulting'] and 'linkedin' not in allocation:
            recommendations.append("Consider LinkedIn for B2B lead generation")
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if current_month in [11, 12]: 