"""
HAC Platform - Backend Server
Complete with AI Recommendations System
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import random
import sqlite3
from datetime import datetime, timedelta
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Configuration
DATABASE = 'hac_database.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Sample data for initialization
SAMPLE_DATA = {
    "vendors": [
        {"id": 1, "name": "TechCorp Inc.", "category": "Technology", "revenue": 150000, "growth": 12.5},
        {"id": 2, "name": "HealthPlus", "category": "Healthcare", "revenue": 89000, "growth": 8.3},
        {"id": 3, "name": "EcoGoods", "category": "Retail", "revenue": 120000, "growth": 15.2},
        {"id": 4, "name": "FoodExpress", "category": "Food & Beverage", "revenue": 75000, "growth": 6.7}
    ],
    "campaigns": [
        {"id": 1, "name": "Summer Sale", "vendor_id": 1, "budget": 5000, "status": "active", "roi": 3.2},
        {"id": 2, "name": "Health Awareness", "vendor_id": 2, "budget": 3000, "status": "completed", "roi": 2.8},
        {"id": 3, "name": "Eco Launch", "vendor_id": 3, "budget": 7000, "status": "active", "roi": 4.1},
        {"id": 4, "name": "Food Festival", "vendor_id": 4, "budget": 2500, "status": "planning", "roi": 0}
    ],
    "metrics": [
        {"id": 1, "date": "2024-01-15", "visitors": 1250, "conversions": 87, "revenue": 12500},
        {"id": 2, "date": "2024-01-16", "visitors": 1420, "conversions": 92, "revenue": 13800},
        {"id": 3, "date": "2024-01-17", "visitors": 1580, "conversions": 105, "revenue": 15200},
        {"id": 4, "date": "2024-01-18", "visitors": 1320, "conversions": 88, "revenue": 12900}
    ]
}

# AI Recommendations Database
AI_RECOMMENDATIONS = {
    "general": [
        "Optimize ad targeting for users aged 25-34 to improve ROI by 23%",
        "Increase video content production by 40% for higher engagement rates",
        "Run A/B tests on landing page designs to improve conversion rates",
        "Allocate 70% of budget to top-performing channels, 30% to testing new opportunities",
        "Use customer testimonials in ads to increase trust and conversion by 60%",
        "Schedule social media posts during peak hours (8-10 AM & 6-8 PM local time)",
        "Implement retargeting campaigns for users who abandoned carts or browsed products",
        "Collaborate with micro-influencers in your niche for authentic promotion"
    ],
    "advertising": [
        "Increase Google Ads budget by 20% for high-intent keywords with low competition",
        "Test different Facebook ad formats: carousel vs single image vs video",
        "Use lookalike audiences to reach new potential customers similar to your best clients",
        "Optimize ad copy with emotional triggers and clear calls-to-action",
        "Implement dayparting to show ads only during optimal business hours",
        "Use UTM parameters consistently to track campaign performance accurately",
        "Test value-based bidding strategies to maximize conversion value",
        "Create urgency with limited-time offers and countdown timers"
    ],
    "content": [
        "Create how-to video tutorials demonstrating your products in action",
        "Start a weekly newsletter sharing industry insights and company updates",
        "Repurpose top-performing blog content into videos, infographics, and podcasts",
        "Use storytelling techniques in case studies to make them more engaging",
        "Implement a content calendar for consistent posting across all channels",
        "Create interactive content like polls, quizzes, and ROI calculators",
        "Optimize blog posts for featured snippets by answering questions directly",
        "Use data visualization to explain complex topics simply"
    ],
    "fundraising": [
        "Create a compelling origin story around your mission and vision",
        "Offer tiered reward systems with different benefits at each donation level",
        "Use social proof by showcasing testimonials from previous donors",
        "Host virtual fundraising events with engaging speakers and activities",
        "Create a monthly subscription model for recurring donations",
        "Partner with corporate sponsors for matching gift campaigns",
        "Use crowdfunding platforms to reach a wider audience",
        "Create urgency with time-limited matching gift opportunities"
    ],
    "collaboration": [
        "Set up weekly check-in meetings with all team members",
        "Use project management tools to track tasks and deadlines",
        "Create shared documents for real-time collaboration",
        "Establish clear communication protocols and response time expectations",
        "Schedule quarterly strategy review sessions",
        "Implement peer feedback sessions for continuous improvement",
        "Use video calls for complex discussions instead of email",
        "Create knowledge base for frequently asked questions and processes"
    ]
}

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Create vendors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                revenue REAL,
                growth REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vendor_id INTEGER,
                budget REAL,
                status TEXT,
                roi REAL,
                start_date DATE,
                end_date DATE,
                FOREIGN KEY (vendor_id) REFERENCES vendors (id)
            )
        ''')
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                visitors INTEGER,
                conversions INTEGER,
                revenue REAL,
                campaign_id INTEGER,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        ''')
        
        # Create users table (for authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create AI recommendations log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_recommendations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                recommendation TEXT,
                user_id INTEGER,
                viewed BOOLEAN DEFAULT 0,
                implemented BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
        # Insert sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM vendors")
        if cursor.fetchone()[0] == 0:
            logger.info("Inserting sample data...")
            
            # Insert vendors
            for vendor in SAMPLE_DATA["vendors"]:
                cursor.execute('''
                    INSERT INTO vendors (name, category, revenue, growth)
                    VALUES (?, ?, ?, ?)
                ''', (vendor["name"], vendor["category"], vendor["revenue"], vendor["growth"]))
            
            # Insert campaigns
            for campaign in SAMPLE_DATA["campaigns"]:
                cursor.execute('''
                    INSERT INTO campaigns (name, vendor_id, budget, status, roi)
                    VALUES (?, ?, ?, ?, ?)
                ''', (campaign["name"], campaign["vendor_id"], campaign["budget"], 
                      campaign["status"], campaign["roi"]))
            
            # Insert metrics
            for metric in SAMPLE_DATA["metrics"]:
                cursor.execute('''
                    INSERT INTO metrics (date, visitors, conversions, revenue)
                    VALUES (?, ?, ?, ?)
                ''', (metric["date"], metric["visitors"], metric["conversions"], metric["revenue"]))
            
            conn.commit()
            logger.info("Sample data inserted successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

# ==================== BASIC API ENDPOINTS ====================

@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_from_directory(app.static_folder, 'vendor-dashboard.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "hac-backend",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/init', methods=['GET', 'POST'])
def initialize_system():
    """Initialize system with sample data"""
    try:
        success = init_db()
        if success:
            return jsonify({
                "success": True,
                "message": "System initialized successfully with sample data",
                "database": DATABASE,
                "tables": ["vendors", "campaigns", "metrics", "users", "ai_recommendations_log"]
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to initialize database"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

# ==================== VENDOR ENDPOINTS ====================

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vendors ORDER BY created_at DESC")
        vendors = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "count": len(vendors),
            "vendors": vendors
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get a specific vendor"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        vendor = cursor.fetchone()
        
        if vendor:
            cursor.execute("SELECT * FROM campaigns WHERE vendor_id = ?", (vendor_id,))
            campaigns = [dict(row) for row in cursor.fetchall()]
            
            result = dict(vendor)
            result["campaigns"] = campaigns
            
            conn.close()
            return jsonify({
                "success": True,
                "vendor": result
            })
        else:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Vendor not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== CAMPAIGN ENDPOINTS ====================

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, v.name as vendor_name 
            FROM campaigns c 
            LEFT JOIN vendors v ON c.vendor_id = v.id 
            ORDER BY c.id DESC
        ''')
        campaigns = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "count": len(campaigns),
            "campaigns": campaigns
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.json
        required_fields = ['name', 'vendor_id', 'budget']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (name, vendor_id, budget, status, roi, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['vendor_id'],
            data['budget'],
            data.get('status', 'planning'),
            data.get('roi', 0),
            data.get('start_date'),
            data.get('end_date')
        ))
        
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Campaign created successfully",
            "campaign_id": campaign_id
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== METRICS & ANALYTICS ====================

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get metrics data"""
    try:
        period = request.args.get('period', '7days')  # 7days, 30days, 90days
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate date range
        end_date = datetime.now().date()
        if period == '7days':
            start_date = end_date - timedelta(days=7)
        elif period == '30days':
            start_date = end_date - timedelta(days=30)
        elif period == '90days':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        cursor.execute('''
            SELECT date, 
                   SUM(visitors) as visitors,
                   SUM(conversions) as conversions,
                   SUM(revenue) as revenue,
                   ROUND(CAST(SUM(conversions) AS FLOAT) / NULLIF(SUM(visitors), 0) * 100, 2) as conversion_rate
            FROM metrics
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        
        # Calculate totals
        total_visitors = sum(m['visitors'] or 0 for m in metrics)
        total_conversions = sum(m['conversions'] or 0 for m in metrics)
        total_revenue = sum(m['revenue'] or 0 for m in metrics)
        avg_conversion_rate = round((total_conversions / total_visitors * 100) if total_visitors > 0 else 0, 2)
        
        conn.close()
        
        return jsonify({
            "success": True,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "summary": {
                "total_visitors": total_visitors,
                "total_conversions": total_conversions,
                "total_revenue": total_revenue,
                "avg_conversion_rate": avg_conversion_rate
            },
            "metrics": metrics
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analytics/summary', methods=['GET'])
def analytics_summary():
    """Get analytics summary"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get vendor count
        cursor.execute("SELECT COUNT(*) as count FROM vendors")
        vendor_count = cursor.fetchone()['count']
        
        # Get campaign statistics
        cursor.execute("SELECT COUNT(*) as total, SUM(budget) as total_budget FROM campaigns")
        campaign_stats = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as active FROM campaigns WHERE status = 'active'")
        active_campaigns = cursor.fetchone()['active']
        
        # Get revenue metrics
        cursor.execute("SELECT SUM(revenue) as total_revenue, AVG(revenue) as avg_revenue FROM metrics")
        revenue_stats = cursor.fetchone()
        
        # Get recent activity
        cursor.execute('''
            SELECT m.date, m.visitors, m.conversions, m.revenue
            FROM metrics m
            ORDER BY m.date DESC
            LIMIT 5
        ''')
        recent_activity = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "summary": {
                "vendors": vendor_count,
                "total_campaigns": campaign_stats['total'] or 0,
                "active_campaigns": active_campaigns,
                "total_budget": campaign_stats['total_budget'] or 0,
                "total_revenue": revenue_stats['total_revenue'] or 0,
                "avg_revenue": round(revenue_stats['avg_revenue'] or 0, 2)
            },
            "recent_activity": recent_activity,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== AI RECOMMENDATIONS ENDPOINTS ====================

@app.route('/api/ai/health', methods=['GET'])
def ai_health():
    """AI service health check"""
    return jsonify({
        "status": "healthy",
        "service": "ai_recommendations",
        "version": "1.0.0",
        "categories_available": list(AI_RECOMMENDATIONS.keys()),
        "total_recommendations": sum(len(recs) for recs in AI_RECOMMENDATIONS.values()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/ai/recommend', methods=['GET'])
def get_ai_recommendations():
    """Get AI-powered recommendations"""
    try:
        category = request.args.get('category', 'general')
        count = int(request.args.get('count', 3))
        
        # Get recommendations for requested category
        if category in AI_RECOMMENDATIONS:
            recommendations = AI_RECOMMENDATIONS[category]
        else:
            recommendations = AI_RECOMMENDATIONS['general']
            category = 'general'
        
        # Ensure count is valid
        count = min(max(1, count), len(recommendations))
        
        # Select random recommendations
        selected_recommendations = random.sample(recommendations, count)
        
        # Simulate AI processing (optional delay)
        # time.sleep(0.3)  # Uncomment for realistic delay
        
        # Log the recommendation (optional)
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            for rec in selected_recommendations:
                cursor.execute('''
                    INSERT INTO ai_recommendations_log (category, recommendation)
                    VALUES (?, ?)
                ''', (category, rec))
            conn.commit()
            conn.close()
        except:
            pass  # Silently fail if logging doesn't work
        
        return jsonify({
            "success": True,
            "category": category,
            "count": count,
            "recommendations": selected_recommendations,
            "confidence": round(random.uniform(0.85, 0.95), 2),  # Simulated confidence score
            "model": "hac_ai_v1.0",
            "generated_at": datetime.now().isoformat(),
            "next_refresh": (datetime.now() + timedelta(hours=1)).isoformat()
        })
        
    except Exception as e:
        # Fallback recommendations
        fallback_recs = [
            "Start by analyzing your current campaign performance data",
            "Focus on optimizing your top 3 performing channels first",
            "Set clear, measurable goals for each marketing initiative"
        ]
        
        return jsonify({
            "success": True,
            "category": "general",
            "count": len(fallback_recs),
            "recommendations": fallback_recs,
            "confidence": 0.8,
            "model": "fallback_v1",
            "generated_at": datetime.now().isoformat(),
            "note": "Using fallback recommendations due to error",
            "error": str(e)
        })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint for interactive recommendations"""
    try:
        data = request.json
        message = data.get('message', '').lower()
        context = data.get('context', {})
        
        # Simple response logic based on keywords
        responses = {
            "budget": "Allocate 60% of budget to proven channels, 30% to testing new opportunities, and 10% as emergency reserve. Review allocations weekly.",
            "targeting": "Focus on demographics with highest lifetime value: Typically age 25-34, urban areas, and interest-based targeting. Use lookalike audiences.",
            "content": "Video content performs 3x better than static images. Incorporate storytelling and customer testimonials for authenticity.",
            "roi": "Track key metrics: Customer Acquisition Cost (CAC), Lifetime Value (LTV), Click-Through Rate (CTR). Aim for at least 4:1 ROI on ad spend.",
            "engagement": "Post during peak hours (8-10 AM and 7-9 PM local time). Use questions in captions to encourage comments and shares.",
            "growth": "Test one new marketing channel each quarter. Optimize top performers monthly. Diversify to reduce risk.",
            "social media": "Focus on 2-3 platforms where your audience is most active. Quality over quantity - better to excel on fewer platforms.",
            "email": "Segment your email list by behavior and demographics. Personalize subject lines for 26% higher open rates.",
            "seo": "Create comprehensive content targeting long-tail keywords. Optimize page speed and mobile experience.",
            "analytics": "Set up conversion tracking on all platforms. Create weekly performance dashboards. Focus on actionable insights."
        }
        
        # Find the best matching response
        response_text = "I recommend analyzing your historical data to identify patterns and opportunities for optimization. Start with your top-performing campaigns and replicate what works."
        matched_keyword = "general"
        
        for keyword in responses:
            if keyword in message:
                response_text = responses[keyword]
                matched_keyword = keyword
                break
        
        # Generate suggested actions
        suggested_actions = [
            "Review last month's performance data for insights",
            "Set up an A/B test for your hypothesis",
            "Schedule a performance review meeting with your team"
        ]
        
        # Add context-specific actions
        if "budget" in matched_keyword:
            suggested_actions.append("Create a budget allocation spreadsheet")
        if "content" in matched_keyword:
            suggested_actions.append("Audit your existing content performance")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "matched_keyword": matched_keyword,
            "suggested_actions": suggested_actions,
            "confidence": round(random.uniform(0.75, 0.92), 2),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "I'm experiencing technical difficulties. Please try again in a moment.",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """Analyze provided data with AI insights"""
    try:
        data = request.json.get('data', {})
        analysis_type = request.json.get('type', 'general')
        
        # Generate insights based on analysis type
        insights = [
            f"Identified {random.randint(2, 8)} key performance indicators in your data",
            f"Top performing channel appears to be {random.choice(['Social Media', 'Search Ads', 'Email Marketing', 'Direct Traffic'])}",
            f"Suggested optimization: Increase investment by {random.randint(10, 30)}% in top performers",
            f"Potential ROI improvement: {random.randint(15, 45)}% with recommended changes",
            f"Found {random.randint(1, 5)} underutilized opportunities for growth"
        ]
        
        # Add type-specific insights
        if analysis_type == 'campaign':
            insights.append("Campaign performance shows strong initial engagement but needs better conversion optimization")
        elif analysis_type == 'audience':
            insights.append("Audience segmentation reveals 3 distinct customer personas with different engagement patterns")
        elif analysis_type == 'content':
            insights.append("Content analysis shows video performs 3x better than images for your audience")
        
        return jsonify({
            "success": True,
            "analysis_type": analysis_type,
            "insights": insights,
            "confidence": round(random.uniform(0.7, 0.9), 2),
            "next_steps": [
                "Implement A/B testing for the top recommendation",
                "Review results in 7-14 days",
                "Adjust strategy based on performance data"
            ],
            "risk_assessment": "Low to moderate risk. Recommendations based on industry best practices.",
            "estimated_impact": f"{random.randint(10, 40)}% improvement potential",
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/categories', methods=['GET'])
def ai_categories():
    """Get available AI recommendation categories"""
    return jsonify({
        "success": True,
        "categories": [
            {"id": "general", "name": "General Marketing", "description": "Overall marketing strategy recommendations"},
            {"id": "advertising", "name": "Advertising", "description": "Paid media and advertising optimizations"},
            {"id": "content", "name": "Content Strategy", "description": "Content creation and distribution advice"},
            {"id": "fundraising", "name": "Fundraising", "description": "Fundraising and donor engagement strategies"},
            {"id": "collaboration", "name": "Team Collaboration", "description": "Teamwork and project management tips"}
        ],
        "timestamp": datetime.now().isoformat()
    })

# ==================== CONTENT STUDIO ENDPOINTS ====================

@app.route('/api/content', methods=['GET'])
def get_content():
    """Get content items"""
    try:
        # This would normally fetch from database
        sample_content = [
            {"id": 1, "title": "Summer Campaign Video", "type": "video", "status": "published", "views": 1250},
            {"id": 2, "title": "Product Launch Blog", "type": "blog", "status": "draft", "views": 0},
            {"id": 3, "title": "Social Media Graphics", "type": "image", "status": "published", "views": 3200},
            {"id": 4, "title": "Email Newsletter", "type": "email", "status": "scheduled", "views": 0}
        ]
        
        return jsonify({
            "success": True,
            "content": sample_content
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== FUNDRAISING ENDPOINTS ====================

@app.route('/api/fundraising', methods=['GET'])
def get_fundraising():
    """Get fundraising data"""
    try:
        # Sample fundraising data
        fundraising_data = {
            "total_raised": 125000,
            "goal": 200000,
            "progress": 62.5,
            "donors": 342,
            "active_campaigns": 3,
            "recent_donations": [
                {"donor": "John D.", "amount": 500, "date": "2024-01-15"},
                {"donor": "Acme Corp", "amount": 2500, "date": "2024-01-14"},
                {"donor": "Sarah M.", "amount": 100, "date": "2024-01-13"}
            ]
        }
        
        return jsonify({
            "success": True,
            "data": fundraising_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== SYSTEM UTILITIES ====================

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information"""
    return jsonify({
        "success": True,
        "system": {
            "name": "HAC Platform",
            "version": "1.0.0",
            "environment": "development",
            "backend_url": "http://127.0.0.1:5000",
            "frontend_url": "http://localhost:8080",
            "database": DATABASE,
            "status": "running"
        },
        "resources": {
            "ai_recommendations": len(AI_RECOMMENDATIONS['general']),
            "sample_vendors": len(SAMPLE_DATA['vendors']),
            "sample_campaigns": len(SAMPLE_DATA['campaigns'])
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/system/reset', methods=['POST'])
def reset_system():
    """Reset system to initial state (development only)"""
    try:
        # Remove database file
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
        
        # Reinitialize
        init_db()
        
        return jsonify({
            "success": True,
            "message": "System reset successfully",
            "database": "recreated",
            "sample_data": "reloaded"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested URL was not found on the server"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# ==================== MAIN EXECUTION ====================

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Print startup message
    print("=" * 60)
    print("🚀 SYSTEM STARTED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("🌐 BACKEND API:")
    print("  URL:      http://127.0.0.1:5000")
    print("  Health:   http://127.0.0.1:5000/api/health")
    print("  Init DB:  http://127.0.0.1:5000/api/init")
    print()
    print("🤖 AI RECOMMENDATIONS:")
    print("  Status:   http://127.0.0.1:5000/api/ai/health")
    print("  General:  http://127.0.0.1:5000/api/ai/recommend")
    print("  Categories: http://127.0.0.1:5000/api/ai/categories")
    print()
    print("💻 FRONTEND PAGES:")
    print("  Dashboard:     http://localhost:8080/vendor-dashboard.html")
    print("  Advertising:   http://localhost:8080/advertising.html")
    print("  Fundraising:   http://localhost:8080/fundraising-hub.html")
    print("  Content:       http://localhost:8080/content-studio.html")
    print("  AI Assistant:  http://localhost:8080/ai-assistant.html")
    print("  Collaboration: http://localhost:8080/collaboration-board.html")
    print()
    print("⚡ QUICK START:")
    print("  1. Open dashboard in browser")
    print("  2. Click 'Initialize Sample Data' or visit: http://127.0.0.1:5000/api/init")
    print("  3. Test AI: http://127.0.0.1:5000/api/ai/recommend?count=5")
    print("  4. Start using the system!")
    print()
    print("🛑 TO STOP: Press Ctrl+C in this window")
    print("=" * 60)
    print()
    
    # Try to open browser automatically
    try:
        import webbrowser
        webbrowser.open("http://localhost:8080/vendor-dashboard.html")
        print("📱 Opening dashboard in your browser...")
    except:
        print("⚠️  Could not open browser automatically. Please open manually.")
    
    print()
    
    # Run the Flask app
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )