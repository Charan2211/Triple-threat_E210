import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AnalyticsEngine:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
    
    def get_vendor_analytics(self, vendor_id: int, period_days: int = 30) -> Dict:
        """Get comprehensive analytics for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Campaign analytics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_campaigns,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_campaigns,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_campaigns,
                SUM(budget) as total_spent,
                AVG(json_extract(performance_metrics, '$.estimated_roi')) as avg_roi
            FROM ad_campaigns 
            WHERE vendor_id = ? AND created_at >= ?
        ''', (vendor_id, start_date.strftime('%Y-%m-%d')))
        
        campaign_stats = cursor.fetchone()
        
        # Content analytics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_content,
                SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as posted_content,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_content,
                content_type,
                COUNT(*) as count
            FROM content_calendar 
            WHERE vendor_id = ? AND created_at >= ?
            GROUP BY content_type
        ''', (vendor_id, start_date.strftime('%Y-%m-%d')))
        
        content_stats = cursor.fetchall()
        
        # Collaboration analytics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_collaborations,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_collaborations,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_collaborations
            FROM collaborations 
            WHERE (vendor1_id = ? OR vendor2_id = ?) AND created_at >= ?
        ''', (vendor_id, vendor_id, start_date.strftime('%Y-%m-%d')))
        
        collab_stats = cursor.fetchone()
        
        # Platform performance
        cursor.execute('''
            SELECT 
                platform,
                COUNT(*) as campaign_count,
                AVG(json_extract(performance_metrics, '$.estimated_roi')) as avg_roi,
                SUM(budget) as total_spent
            FROM ad_campaigns 
            WHERE vendor_id = ? AND created_at >= ?
            GROUP BY platform
            ORDER BY total_spent DESC
        ''', (vendor_id, start_date.strftime('%Y-%m-%d')))
        
        platform_performance = cursor.fetchall()
        
        conn.close()
        
        # Calculate metrics
        total_spent = campaign_stats[3] or 0
        total_campaigns = campaign_stats[0] or 0
        active_campaigns = campaign_stats[1] or 0
        avg_roi = campaign_stats[4] or 0
        
        # Calculate engagement rate (simplified)
        engagement_rate = min(avg_roi * 0.1, 0.5) if avg_roi > 0 else 0.1
        
        return {
            'period': f'Last {period_days} days',
            'campaigns': {
                'total': total_campaigns,
                'active': active_campaigns,
                'completed': campaign_stats[2] or 0,
                'total_spent': total_spent,
                'average_roi': avg_roi
            },
            'content': {
                'total': len(content_stats),
                'by_type': [
                    {'type': row[3], 'count': row[4]} for row in content_stats
                ],
                'posted': sum(row[1] for row in content_stats),
                'scheduled': sum(row[2] for row in content_stats)
            },
            'collaborations': {
                'total': collab_stats[0] or 0,
                'completed': collab_stats[1] or 0,
                'active': collab_stats[2] or 0
            },
            'platform_performance': [
                {
                    'platform': row[0],
                    'campaigns': row[1],
                    'avg_roi': row[2] or 0,
                    'total_spent': row[3] or 0
                } for row in platform_performance
            ],
            'summary_metrics': {
                'engagement_rate': engagement_rate,
                'cost_per_campaign': total_spent / total_campaigns if total_campaigns > 0 else 0,
                'content_frequency': len(content_stats) / period_days,
                'collaboration_rate': (collab_stats[1] or 0) / period_days
            }
        }
    
    def generate_insights(self, vendor_id: int) -> List[Dict]:
        """Generate actionable insights from analytics"""
        analytics = self.get_vendor_analytics(vendor_id)
        
        insights = []
        
        # Campaign insights
        if analytics['campaigns']['total'] > 0:
            if analytics['campaigns']['average_roi'] < 1.5:
                insights.append({
                    'type': 'warning',
                    'category': 'advertising',
                    'title': 'Low Campaign ROI',
                    'description': f'Average ROI is {analytics["campaigns"]["average_roi"]:.2f}x',
                    'recommendation': 'Optimize ad targeting and creative',
                    'priority': 'high'
                })
            
            # Platform performance insights
            for platform in analytics['platform_performance']:
                if platform['avg_roi'] > 2.5:
                    insights.append({
                        'type': 'success',
                        'category': 'advertising',
                        'title': f'High Performing Platform',
                        'description': f'{platform["platform"]} has {platform["avg_roi"]:.2f}x ROI',
                        'recommendation': f'Increase budget allocation to {platform["platform"]}',
                        'priority': 'medium'
                    })
        
        # Content insights
        if analytics['content']['total'] > 0:
            content_freq = analytics['summary_metrics']['content_frequency']
            if content_freq < 0.3:  # Less than 2 posts per week
                insights.append({
                    'type': 'info',
                    'category': 'content',
                    'title': 'Low Content Frequency',
                    'description': f'Only {content_freq:.1f} posts per day on average',
                    'recommendation': 'Increase posting frequency to 3-5 times per week',
                    'priority': 'medium'
                })
        
        # Collaboration insights
        collab_rate = analytics['summary_metrics']['collaboration_rate']
        if collab_rate < 0.1:  # Less than 1 collaboration per 10 days
            insights.append({
                'type': 'info',
                'category': 'collaboration',
                'title': 'Limited Collaborations',
                'description': 'Few collaboration activities detected',
                'recommendation': 'Explore partnership opportunities with similar businesses',
                'priority': 'low'
            })
        
        # Budget insights
        total_spent = analytics['campaigns']['total_spent']
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT budget FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor_budget = cursor.fetchone()[0] or 0
        conn.close()
        
        if vendor_budget > 0:
            utilization = (total_spent / vendor_budget) * 100
            if utilization < 30:
                insights.append({
                    'type': 'warning',
                    'category': 'budget',
                    'title': 'Low Budget Utilization',
                    'description': f'Only {utilization:.1f}% of budget used',
                    'recommendation': 'Consider launching new campaigns or increasing existing ones',
                    'priority': 'medium'
                })
        
        return insights
    
    def get_trends(self, vendor_id: int) -> Dict:
        """Get trend data for visualizations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 4 weeks of data
        weeks = []
        for i in range(4):
            week_end = datetime.now() - timedelta(weeks=i)
            week_start = week_end - timedelta(weeks=1)
            
            # Campaigns per week
            cursor.execute('''
                SELECT COUNT(*), SUM(budget)
                FROM ad_campaigns 
                WHERE vendor_id = ? AND created_at BETWEEN ? AND ?
            ''', (vendor_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            campaign_data = cursor.fetchone()
            
            # Content per week
            cursor.execute('''
                SELECT COUNT(*)
                FROM content_calendar 
                WHERE vendor_id = ? AND created_at BETWEEN ? AND ?
            ''', (vendor_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            content_data = cursor.fetchone()
            
            weeks.append({
                'week': f'Week {4-i}',
                'campaigns': campaign_data[0] or 0,
                'spending': campaign_data[1] or 0,
                'content': content_data[0] or 0
            })
        
        conn.close()
        
        # Reverse to chronological order
        weeks.reverse()
        
        return {
            'weekly_data': weeks,
            'current_vs_previous': self.calculate_growth(weeks)
        }
    
    def calculate_growth(self, weekly_data: List[Dict]) -> Dict:
        """Calculate growth rates"""
        if len(weekly_data) < 2:
            return {}
        
        current = weekly_data[-1]
        previous = weekly_data[-2]
        
        def calc_growth(current_val, previous_val):
            if previous_val == 0:
                return 0
            return ((current_val - previous_val) / previous_val) * 100
        
        return {
            'campaigns_growth': calc_growth(current['campaigns'], previous['campaigns']),
            'spending_growth': calc_growth(current['spending'], previous['spending']),
            'content_growth': calc_growth(current['content'], previous['content'])
        }