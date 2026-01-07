import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import schedule
import time
from threading import Thread

class AutomationController:
    def __init__(self, db_path='platform.db'):
        self.db_path = db_path
        self.automation_thread = None
        
    def analyze_automation_potential(self, vendor_id: int) -> Dict:
        """Analyze what can be automated for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vendor_profiles WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            return {}
        
        vendor_dict = dict(vendor)
        
        # Get current activities
        cursor.execute('''
            SELECT COUNT(*) as ad_count FROM ad_campaigns 
            WHERE vendor_id = ? AND status IN ('active', 'pending')
        ''', (vendor_id,))
        ad_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) as content_count FROM content_calendar 
            WHERE vendor_id = ? AND status = 'scheduled'
        ''', (vendor_id,))
        content_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate automation potential
        automation_opportunities = []
        time_savings = 0
        cost_savings = 0
        
        # Social media posting
        if content_count > 0:
            automation_opportunities.append({
                'task': 'social_media_posting',
                'current_time': content_count * 15,  # 15 minutes per post
                'automated_time': content_count * 2,  # 2 minutes automated
                'automation_level': 85,
                'tools': ['content_calendar', 'auto_scheduler']
            })
            time_savings += content_count * 13
        
        # Ad campaign monitoring
        if ad_count > 0:
            automation_opportunities.append({
                'task': 'ad_monitoring',
                'current_time': ad_count * 30,  # 30 minutes per campaign
                'automated_time': ad_count * 5,  # 5 minutes automated
                'automation_level': 80,
                'tools': ['performance_alerts', 'auto_optimization']
            })
            time_savings += ad_count * 25
        
        # Reporting
        if ad_count > 0 or content_count > 0:
            automation_opportunities.append({
                'task': 'reporting',
                'current_time': 120,  # 2 hours per week
                'automated_time': 15,  # 15 minutes automated
                'automation_level': 90,
                'tools': ['auto_reports', 'dashboard']
            })
            time_savings += 105
        
        # Calculate ROI
        hourly_rate = 50  # Assumed hourly rate
        cost_savings = time_savings / 60 * hourly_rate
        
        return {
            'vendor': vendor_dict['business_name'],
            'automation_opportunities': automation_opportunities,
            'total_time_savings_hours': round(time_savings / 60, 1),
            'estimated_cost_savings': round(cost_savings, 2),
            'recommended_automations': self.get_recommended_automations(vendor_dict)
        }
    
    def get_recommended_automations(self, vendor: Dict) -> List[Dict]:
        """Get recommended automations based on business profile"""
        recommendations = []
        industry = vendor['industry']
        budget = vendor['budget']
        
        # Always recommend these
        recommendations.append({
            'automation': 'content_scheduling',
            'priority': 'high',
            'description': 'Schedule social media posts in advance',
            'time_saving': '5-10 hours/week',
            'tools_needed': ['content_calendar', 'social_media_api'],
            'setup_time': '1-2 hours'
        })
        
        recommendations.append({
            'automation': 'performance_reporting',
            'priority': 'medium',
            'description': 'Automated weekly performance reports',
            'time_saving': '2-3 hours/week',
            'tools_needed': ['analytics_dashboard', 'auto_email'],
            'setup_time': '30 minutes'
        })
        
        # Industry-specific recommendations
        if industry in ['restaurant', 'retail']:
            recommendations.append({
                'automation': 'inventory_posting',
                'priority': 'high',
                'description': 'Automatically post new products/items',
                'time_saving': '3-5 hours/week',
                'tools_needed': ['inventory_system', 'content_generator'],
                'setup_time': '2-3 hours'
            })
        
        if industry in ['technology', 'consulting']:
            recommendations.append({
                'automation': 'lead_nurturing',
                'priority': 'medium',
                'description': 'Automated email sequences for leads',
                'time_saving': '4-6 hours/week',
                'tools_needed': ['crm_integration', 'email_automation'],
                'setup_time': '1-2 hours'
            })
        
        # Budget-based recommendations
        if budget > 1000:
            recommendations.append({
                'automation': 'ad_optimization',
                'priority': 'high',
                'description': 'Automatically optimize ad budgets and targeting',
                'time_saving': '5-8 hours/week',
                'tools_needed': ['ad_api', 'ml_optimizer'],
                'setup_time': '2-3 hours'
            })
        
        return recommendations
    
    def setup_automation(self, vendor_id: int, automation_type: str) -> bool:
        """Set up a specific automation"""
        automations = {
            'content_scheduling': self.setup_content_scheduling,
            'performance_reporting': self.setup_performance_reporting,
            'ad_optimization': self.setup_ad_optimization,
            'lead_nurturing': self.setup_lead_nurturing,
            'inventory_posting': self.setup_inventory_posting
        }
        
        if automation_type in automations:
            return automations[automation_type](vendor_id)
        
        return False
    
    def setup_content_scheduling(self, vendor_id: int) -> bool:
        """Set up content scheduling automation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create default content schedule
        schedule_times = [
            '09:00',  # Morning
            '12:00',  # Lunch
            '17:00',  # Evening
            '20:00'   # Night
        ]
        
        cursor.execute('''
            INSERT INTO vendor_settings 
            (vendor_id, setting_type, setting_value)
            VALUES (?, 'content_schedule', ?)
        ''', (vendor_id, json.dumps(schedule_times)))
        
        conn.commit()
        conn.close()
        
        # Start scheduler in background
        self.start_content_scheduler(vendor_id)
        
        return True
    
    def start_content_scheduler(self, vendor_id: int):
        """Start content scheduler for vendor"""
        def run_scheduler():
            schedule.every().day.at("09:00").do(self.post_scheduled_content, vendor_id)
            schedule.every().day.at("12:00").do(self.post_scheduled_content, vendor_id)
            schedule.every().day.at("17:00").do(self.post_scheduled_content, vendor_id)
            schedule.every().day.at("20:00").do(self.post_scheduled_content, vendor_id)
            
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        self.automation_thread = Thread(target=run_scheduler, daemon=True)
        self.automation_thread.start()
    
    def post_scheduled_content(self, vendor_id: int):
        """Post scheduled content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get next scheduled content
        cursor.execute('''
            SELECT * FROM content_calendar 
            WHERE vendor_id = ? AND status = 'scheduled'
            ORDER BY scheduled_time ASC 
            LIMIT 1
        ''', (vendor_id,))
        
        content = cursor.fetchone()
        
        if content:
            content_dict = dict(content)
            # In production, integrate with social media APIs
            print(f"Posting content: {content_dict['title']}")
            
            # Update status
            cursor.execute('''
                UPDATE content_calendar 
                SET status = 'posted', 
                    performance_metrics = ?
                WHERE content_id = ?
            ''', (json.dumps({'posted_at': datetime.now().isoformat()}), content_dict['content_id']))
            
            conn.commit()
        
        conn.close()
    
    def setup_performance_reporting(self, vendor_id: int) -> bool:
        """Set up automated performance reporting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Schedule weekly report
        cursor.execute('''
            INSERT INTO vendor_settings 
            (vendor_id, setting_type, setting_value)
            VALUES (?, 'report_schedule', ?)
        ''', (vendor_id, json.dumps({
            'frequency': 'weekly',
            'day': 'monday',
            'time': '08:00',
            'recipients': []
        })))
        
        conn.commit()
        conn.close()
        
        # Schedule report generation
        schedule.every().monday.at("08:00").do(self.generate_weekly_report, vendor_id)
        
        return True
    
    def generate_weekly_report(self, vendor_id: int):
        """Generate weekly performance report"""
        # This would generate and email a report
        print(f"Generating weekly report for vendor {vendor_id}")
        # Implementation would include data aggregation and email sending
