from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Import all modules
try:
    from uid_manager import UIDManager
    from trust_system import TrustSystem
    from community_matching import CommunityMatching
    from analytics_engine import AnalyticsEngine
    from vendor_profile_manager import VendorProfileManager
    from ai_business_assistant import AIBusinessAssistant
    from content_automation import ContentAutomation
    from advertising_manager import AdvertisingManager
    from fundraising_manager import FundraisingManager
    from collaboration_engine import CollaborationEngine
    from resource_optimizer import ResourceOptimizer
    from automation_controller import AutomationController
    
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all Python files are in the backend folder")
    exit(1)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Initialize all managers
print("Initializing managers...")
uid_manager = UIDManager()
trust_system = TrustSystem()
community_matching = CommunityMatching()
analytics_engine = AnalyticsEngine()
vendor_manager = VendorProfileManager()

# Initialize AI Assistant with OpenAI API key
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    ai_assistant = AIBusinessAssistant(api_key=openai_key)
    print("✅ AI Business Assistant initialized with OpenAI key")
else:
    ai_assistant = AIBusinessAssistant(api_key="dummy-key-for-testing")
    print("⚠️  OpenAI API key not found. Using dummy key for testing.")

content_automation = ContentAutomation()
advertising_manager = AdvertisingManager()
fundraising_manager = FundraisingManager()
collaboration_engine = CollaborationEngine()
resource_optimizer = ResourceOptimizer()
automation_controller = AutomationController()

print("✅ All managers initialized successfully!")

# Start content scheduler in background
print("Starting content scheduler...")
content_automation.start_scheduler()
print("✅ Content scheduler started!")

# ===== HELPER FUNCTIONS =====

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect('platform.db')
    conn.row_factory = sqlite3.Row
    return conn

def validate_session():
    """Validate user session from request"""
    session_id = request.headers.get('Authorization')
    if not session_id:
        return None
    return uid_manager.validate_session(session_id)

def success_response(data=None, message="Success"):
    """Standard success response"""
    response = {'success': True, 'message': message}
    if data:
        response['data'] = data
    return jsonify(response)

def error_response(message="Error", status_code=400):
    """Standard error response"""
    return jsonify({'success': False, 'message': message}), status_code

# ===== AUTHENTICATION ENDPOINTS =====

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type', 'vendor')
        
        if not all([username, email, password]):
            return error_response('Missing required fields')
        
        user_id = uid_manager.create_user(username, email, password, user_type)
        
        if user_id:
            return success_response(
                {'user_id': user_id, 'username': username, 'user_type': user_type},
                'User registered successfully'
            )
        else:
            return error_response('Username or email already exists')
            
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return error_response('Registration failed')

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return error_response('Missing email or password')
        
        auth_result = uid_manager.authenticate_user(email, password)
        
        if auth_result:
            return success_response(
                {
                    'user_id': auth_result['user_id'],
                    'username': auth_result['username'],
                    'user_type': auth_result['user_type'],
                    'session_id': auth_result['session_id']
                },
                'Login successful'
            )
        else:
            return error_response('Invalid credentials', 401)
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return error_response('Login failed')

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        session_id = request.headers.get('Authorization')
        if session_id:
            # In production, invalidate session in database
            pass
        return success_response(message='Logged out successfully')
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return error_response('Logout failed')

@app.route('/api/auth/validate', methods=['GET'])
def validate():
    """Validate user session"""
    try:
        user = validate_session()
        if user:
            return success_response(
                {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'user_type': user['user_type']
                },
                'Session valid'
            )
        else:
            return error_response('Invalid session', 401)
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return error_response('Validation failed')

# ===== VENDOR PROFILE ENDPOINTS =====

@app.route('/api/vendor/profile/create', methods=['POST'])
def create_vendor_profile():
    """Create a new vendor profile"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        profile_data = data.get('profile_data', {})
        
        if not profile_data.get('business_name'):
            return error_response('Business name is required')
        
        vendor_id = vendor_manager.create_vendor_profile(user['user_id'], profile_data)
        
        # Create initial trust score
        trust_system.calculate_trust_score(vendor_id)
        
        return success_response(
            {'vendor_id': vendor_id},
            'Vendor profile created successfully'
        )
        
    except Exception as e:
        print(f"Create profile error: {str(e)}")
        traceback.print_exc()
        return error_response('Failed to create vendor profile')

@app.route('/api/vendor/profile/<int:vendor_id>', methods=['GET'])
def get_vendor_profile(vendor_id):
    """Get vendor profile"""
    try:
        profile = vendor_manager.get_vendor_profile(vendor_id)
        
        if profile:
            return success_response({'profile': profile})
        else:
            return error_response('Profile not found', 404)
            
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        return error_response('Failed to get vendor profile')

@app.route('/api/vendor/profile/<int:vendor_id>', methods=['PUT'])
def update_vendor_profile(vendor_id):
    """Update vendor profile"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        updates = data.get('updates', {})
        
        success = vendor_manager.update_vendor_profile(vendor_id, updates)
        
        if success:
            return success_response(message='Profile updated successfully')
        else:
            return error_response('Failed to update profile')
            
    except Exception as e:
        print(f"Update profile error: {str(e)}")
        return error_response('Failed to update vendor profile')

@app.route('/api/vendor/profile/<int:vendor_id>/needs', methods=['GET'])
def analyze_vendor_needs(vendor_id):
    """Analyze vendor needs"""
    try:
        needs = vendor_manager.analyze_vendor_needs(vendor_id)
        return success_response({'needs': needs})
    except Exception as e:
        print(f"Analyze needs error: {str(e)}")
        return error_response('Failed to analyze needs')

# ===== ADVERTISING ENDPOINTS =====

@app.route('/api/advertising/campaign/create', methods=['POST'])
def create_ad_campaign():
    """Create a new advertising campaign"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        vendor_id = data.get('vendor_id')
        campaign_data = data.get('campaign_data', {})
        
        # Verify user owns this vendor (in production, add proper authorization)
        if not vendor_id:
            return error_response('Vendor ID required')
        
        campaign_id = advertising_manager.create_campaign(vendor_id, campaign_data)
        
        # Add trust event for campaign creation
        trust_system.add_trust_event(
            vendor_id, 
            'campaign_created', 
            5, 
            f"Created new campaign: {campaign_data.get('campaign_name', 'Unnamed')}"
        )
        
        return success_response(
            {'campaign_id': campaign_id},
            'Campaign created successfully'
        )
        
    except Exception as e:
        print(f"Create campaign error: {str(e)}")
        traceback.print_exc()
        return error_response('Failed to create campaign')

@app.route('/api/advertising/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get campaign details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,))
        campaign = cursor.fetchone()
        conn.close()
        
        if campaign:
            campaign_dict = dict(campaign)
            # Parse JSON fields
            for field in ['target_audience', 'keywords', 'visuals', 'performance_metrics']:
                if campaign_dict[field]:
                    campaign_dict[field] = json.loads(campaign_dict[field])
            return success_response({'campaign': campaign_dict})
        else:
            return error_response('Campaign not found', 404)
            
    except Exception as e:
        print(f"Get campaign error: {str(e)}")
        return error_response('Failed to get campaign')

@app.route('/api/advertising/campaign/<int:campaign_id>/optimize', methods=['GET'])
def optimize_campaign(campaign_id):
    """Get optimization suggestions for a campaign"""
    try:
        optimizations = advertising_manager.optimize_campaign(campaign_id)
        return success_response({'optimizations': optimizations})
    except Exception as e:
        print(f"Optimize campaign error: {str(e)}")
        return error_response('Failed to optimize campaign')

@app.route('/api/advertising/platform-recommendations/<int:vendor_id>', methods=['GET'])
def get_platform_recommendations(vendor_id):
    """Get platform recommendations for a vendor"""
    try:
        recommendations = advertising_manager.get_platform_recommendations(vendor_id)
        return success_response({'recommendations': recommendations})
    except Exception as e:
        print(f"Platform recommendations error: {str(e)}")
        return error_response('Failed to get platform recommendations')

@app.route('/api/advertising/campaigns/vendor/<int:vendor_id>', methods=['GET'])
def get_vendor_campaigns(vendor_id):
    """Get all campaigns for a vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ad_campaigns 
            WHERE vendor_id = ? 
            ORDER BY created_at DESC
        ''', (vendor_id,))
        
        campaigns = cursor.fetchall()
        conn.close()
        
        campaigns_list = []
        for campaign in campaigns:
            campaign_dict = dict(campaign)
            # Parse JSON fields
            for field in ['target_audience', 'keywords', 'visuals', 'performance_metrics']:
                if campaign_dict[field]:
                    campaign_dict[field] = json.loads(campaign_dict[field])
            campaigns_list.append(campaign_dict)
        
        return success_response({'campaigns': campaigns_list})
        
    except Exception as e:
        print(f"Get vendor campaigns error: {str(e)}")
        return error_response('Failed to get campaigns')

# ===== CONTENT AUTOMATION ENDPOINTS =====

@app.route('/api/content/generate-ideas/<int:vendor_id>', methods=['GET'])
def generate_content_ideas(vendor_id):
    """Generate content ideas for a vendor"""
    try:
        count = request.args.get('count', default=10, type=int)
        ideas = content_automation.generate_content_ideas(vendor_id, count)
        return success_response({'ideas': ideas})
    except Exception as e:
        print(f"Generate ideas error: {str(e)}")
        return error_response('Failed to generate content ideas')

@app.route('/api/content/schedule', methods=['POST'])
def schedule_content():
    """Schedule content for posting"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        vendor_id = data.get('vendor_id')
        content_data = data.get('content_data', {})
        
        if not vendor_id:
            return error_response('Vendor ID required')
        
        content_id = content_automation.schedule_content(vendor_id, content_data)
        
        return success_response(
            {'content_id': content_id},
            'Content scheduled successfully'
        )
        
    except Exception as e:
        print(f"Schedule content error: {str(e)}")
        return error_response('Failed to schedule content')

@app.route('/api/content/hashtags', methods=['POST'])
def generate_hashtags():
    """Generate hashtags for content"""
    try:
        data = request.json
        industry = data.get('industry')
        content = data.get('content', '')
        
        hashtags = content_automation.generate_hashtags(industry, content)
        return success_response({'hashtags': hashtags})
        
    except Exception as e:
        print(f"Generate hashtags error: {str(e)}")
        return error_response('Failed to generate hashtags')

@app.route('/api/content/calendar/<int:vendor_id>', methods=['GET'])
def get_content_calendar(vendor_id):
    """Get content calendar for a vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM content_calendar 
            WHERE vendor_id = ? 
            ORDER BY scheduled_time ASC
        ''', (vendor_id,))
        
        content_items = cursor.fetchall()
        conn.close()
        
        content_list = []
        for item in content_items:
            item_dict = dict(item)
            # Parse JSON fields
            for field in ['platform', 'hashtags', 'performance_metrics']:
                if item_dict[field]:
                    item_dict[field] = json.loads(item_dict[field])
            content_list.append(item_dict)
        
        return success_response({'content': content_list})
        
    except Exception as e:
        print(f"Get content calendar error: {str(e)}")
        return error_response('Failed to get content calendar')

# ===== AI ASSISTANT ENDPOINTS =====

@app.route('/api/ai/recommendations/<int:vendor_id>', methods=['GET'])
def get_ai_recommendations(vendor_id):
    """Get AI-powered business recommendations"""
    try:
        recommendations = ai_assistant.generate_recommendations(vendor_id)
        return success_response({'recommendations': recommendations})
    except Exception as e:
        print(f"AI recommendations error: {str(e)}")
        # Return fallback recommendations
        try:
            profile = vendor_manager.get_vendor_profile(vendor_id)
            if profile:
                fallback = ai_assistant.get_fallback_recommendations(profile)
                return success_response({'recommendations': fallback})
        except:
            pass
        return error_response('Failed to generate recommendations')

@app.route('/api/ai/ad-copy', methods=['POST'])
def generate_ad_copy():
    """Generate ad copy using AI"""
    try:
        data = request.json
        product_description = data.get('product_description', '')
        target_audience = data.get('target_audience', '')
        platform = data.get('platform', 'facebook')
        
        if not product_description:
            return error_response('Product description required')
        
        ad_copy = ai_assistant.generate_ad_copy(product_description, target_audience, platform)
        return success_response({'ad_copy': ad_copy})
        
    except Exception as e:
        print(f"Generate ad copy error: {str(e)}")
        return error_response('Failed to generate ad copy')

@app.route('/api/ai/analyze-pitch/<int:pitch_id>', methods=['GET'])
def analyze_pitch(pitch_id):
    """Analyze a pitch using AI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fundraising_pitches WHERE pitch_id = ?', (pitch_id,))
        pitch = cursor.fetchone()
        conn.close()
        
        if not pitch:
            return error_response('Pitch not found', 404)
        
        # In production, use AI to analyze pitch
        # For now, return mock analysis
        analysis = {
            'score': 78,
            'strengths': ['Clear problem statement', 'Innovative solution'],
            'weaknesses': ['Missing financial projections', 'Limited traction data'],
            'suggestions': [
                'Add 3-year financial projections',
                'Include customer testimonials',
                'Expand on market validation'
            ]
        }
        
        return success_response({'analysis': analysis})
        
    except Exception as e:
        print(f"Analyze pitch error: {str(e)}")
        return error_response('Failed to analyze pitch')

# ===== FUNDRAISING ENDPOINTS =====

@app.route('/api/fundraising/pitch/create', methods=['POST'])
def create_pitch():
    """Create a fundraising pitch"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        vendor_id = data.get('vendor_id')
        pitch_data = data.get('pitch_data', {})
        
        if not vendor_id:
            return error_response('Vendor ID required')
        
        pitch_id = fundraising_manager.create_pitch(vendor_id, pitch_data)
        
        # Add trust event for pitch creation
        trust_system.add_trust_event(
            vendor_id,
            'pitch_created',
            10,
            f"Created fundraising pitch: {pitch_data.get('title', 'Untitled')}"
        )
        
        return success_response(
            {'pitch_id': pitch_id},
            'Pitch created successfully'
        )
        
    except Exception as e:
        print(f"Create pitch error: {str(e)}")
        return error_response('Failed to create pitch')

@app.route('/api/fundraising/pitch/<int:pitch_id>/investor-matches', methods=['GET'])
def get_investor_matches(pitch_id):
    """Find investor matches for a pitch"""
    try:
        matches = fundraising_manager.find_investor_matches(pitch_id)
        return success_response({'matches': matches})
    except Exception as e:
        print(f"Investor matches error: {str(e)}")
        return error_response('Failed to find investor matches')

@app.route('/api/fundraising/pitch-template/<industry>', methods=['GET'])
def get_pitch_template(industry):
    """Get pitch deck template for an industry"""
    try:
        template = fundraising_manager.generate_pitch_template(industry)
        return success_response({'template': template})
    except Exception as e:
        print(f"Pitch template error: {str(e)}")
        return error_response('Failed to get pitch template')

@app.route('/api/fundraising/pitches/vendor/<int:vendor_id>', methods=['GET'])
def get_vendor_pitches(vendor_id):
    """Get all pitches for a vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM fundraising_pitches 
            WHERE vendor_id = ? 
            ORDER BY created_at DESC
        ''', (vendor_id,))
        
        pitches = cursor.fetchall()
        conn.close()
        
        pitches_list = [dict(pitch) for pitch in pitches]
        return success_response({'pitches': pitches_list})
        
    except Exception as e:
        print(f"Get vendor pitches error: {str(e)}")
        return error_response('Failed to get pitches')

# ===== COLLABORATION ENDPOINTS =====

@app.route('/api/collaboration/matches/<int:vendor_id>', methods=['GET'])
def get_collaboration_matches(vendor_id):
    """Find collaboration partners for a vendor"""
    try:
        matches = collaboration_engine.find_collaboration_matches(vendor_id)
        return success_response({'matches': matches})
    except Exception as e:
        print(f"Collaboration matches error: {str(e)}")
        return error_response('Failed to find collaboration matches')

@app.route('/api/collaboration/initiate', methods=['POST'])
def initiate_collaboration():
    """Initiate a collaboration"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        vendor1_id = data.get('vendor1_id')
        vendor2_id = data.get('vendor2_id')
        collaboration_type = data.get('collaboration_type')
        
        if not all([vendor1_id, vendor2_id, collaboration_type]):
            return error_response('Missing required fields')
        
        collab_id = collaboration_engine.initiate_collaboration(
            vendor1_id, vendor2_id, collaboration_type
        )
        
        # Add trust events for both vendors
        trust_system.add_trust_event(
            vendor1_id,
            'collaboration_initiated',
            5,
            f'Initiated collaboration with vendor {vendor2_id}'
        )
        
        trust_system.add_trust_event(
            vendor2_id,
            'collaboration_received',
            5,
            f'Received collaboration request from vendor {vendor1_id}'
        )
        
        return success_response(
            {'collab_id': collab_id},
            'Collaboration initiated successfully'
        )
        
    except Exception as e:
        print(f"Initiate collaboration error: {str(e)}")
        return error_response('Failed to initiate collaboration')

@app.route('/api/collaboration/similar-vendors/<int:vendor_id>', methods=['GET'])
def get_similar_vendors(vendor_id):
    """Find vendors with similar profiles"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        similar_vendors = community_matching.find_similar_vendors(vendor_id, limit)
        return success_response({'similar_vendors': similar_vendors})
    except Exception as e:
        print(f"Similar vendors error: {str(e)}")
        return error_response('Failed to find similar vendors')

# ===== RESOURCE OPTIMIZATION ENDPOINTS =====

@app.route('/api/resources/budget-optimization/<int:vendor_id>', methods=['GET'])
def optimize_budget(vendor_id):
    """Get optimized budget allocation"""
    try:
        optimization = resource_optimizer.optimize_budget_allocation(vendor_id)
        return success_response({'optimization': optimization})
    except Exception as e:
        print(f"Budget optimization error: {str(e)}")
        return error_response('Failed to optimize budget')

@app.route('/api/resources/templates/<resource_type>', methods=['GET'])
def get_resource_templates(resource_type):
    """Get resource templates"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM resources 
            WHERE resource_type = ? 
            ORDER BY difficulty_level
        ''', (resource_type,))
        
        templates = cursor.fetchall()
        conn.close()
        
        templates_list = [dict(template) for template in templates]
        return success_response({'templates': templates_list})
        
    except Exception as e:
        print(f"Resource templates error: {str(e)}")
        return error_response('Failed to get resource templates')

# ===== AUTOMATION ENDPOINTS =====

@app.route('/api/automation/analyze/<int:vendor_id>', methods=['GET'])
def analyze_automation(vendor_id):
    """Analyze automation potential"""
    try:
        analysis = automation_controller.analyze_automation_potential(vendor_id)
        return success_response({'analysis': analysis})
    except Exception as e:
        print(f"Automation analysis error: {str(e)}")
        return error_response('Failed to analyze automation potential')

@app.route('/api/automation/setup', methods=['POST'])
def setup_automation():
    """Set up automation"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        vendor_id = data.get('vendor_id')
        automation_type = data.get('automation_type')
        
        if not vendor_id or not automation_type:
            return error_response('Missing required fields')
        
        success = automation_controller.setup_automation(vendor_id, automation_type)
        
        if success:
            return success_response(message='Automation setup initiated')
        else:
            return error_response('Setup failed')
            
    except Exception as e:
        print(f"Setup automation error: {str(e)}")
        return error_response('Failed to setup automation')

# ===== ANALYTICS ENDPOINTS =====

@app.route('/api/analytics/dashboard/<int:vendor_id>', methods=['GET'])
def get_vendor_dashboard(vendor_id):
    """Get comprehensive dashboard data for vendor"""
    try:
        # Get basic profile
        profile = vendor_manager.get_vendor_profile(vendor_id)
        if not profile:
            return error_response('Vendor not found', 404)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get active campaigns
        cursor.execute('''
            SELECT * FROM ad_campaigns 
            WHERE vendor_id = ? AND status IN ('active', 'pending')
            ORDER BY created_at DESC
            LIMIT 5
        ''', (vendor_id,))
        campaigns = [dict(c) for c in cursor.fetchall()]
        
        # Parse JSON fields for campaigns
        for campaign in campaigns:
            for field in ['target_audience', 'keywords', 'visuals', 'performance_metrics']:
                if campaign[field]:
                    campaign[field] = json.loads(campaign[field])
        
        # Get scheduled content
        cursor.execute('''
            SELECT * FROM content_calendar 
            WHERE vendor_id = ? AND status = 'scheduled'
            ORDER BY scheduled_time ASC
            LIMIT 10
        ''', (vendor_id,))
        content = [dict(c) for c in cursor.fetchall()]
        
        # Parse JSON fields for content
        for item in content:
            for field in ['platform', 'hashtags', 'performance_metrics']:
                if item[field]:
                    item[field] = json.loads(item[field])
        
        # Get AI recommendations
        cursor.execute('''
            SELECT * FROM ai_recommendations 
            WHERE vendor_id = ? AND status != 'completed'
            ORDER BY priority DESC
            LIMIT 5
        ''', (vendor_id,))
        recommendations = [dict(r) for r in cursor.fetchall()]
        
        # Get trust score
        cursor.execute('SELECT score FROM trust_scores WHERE vendor_id = ?', (vendor_id,))
        trust_result = cursor.fetchone()
        trust_score = trust_result['score'] if trust_result else 50
        
        conn.close()
        
        # Calculate metrics
        total_campaigns = len(campaigns)
        total_content = len(content)
        pending_actions = len([r for r in recommendations if r.get('priority', 0) == 1])
        
        # Calculate budget utilization
        total_budget = profile.get('budget', 0)
        spent_budget = sum(c.get('budget', 0) for c in campaigns if c.get('status') == 'active')
        budget_utilization = (spent_budget / total_budget * 100) if total_budget > 0 else 0
        
        return success_response({
            'dashboard': {
                'profile': profile,
                'campaigns': campaigns,
                'content': content,
                'recommendations': recommendations,
                'metrics': {
                    'total_campaigns': total_campaigns,
                    'total_content': total_content,
                    'pending_actions': pending_actions,
                    'trust_score': trust_score,
                    'budget_utilization': round(budget_utilization, 2),
                    'total_budget': total_budget,
                    'spent_budget': spent_budget
                }
            }
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        traceback.print_exc()
        return error_response('Failed to load dashboard')

@app.route('/api/analytics/insights/<int:vendor_id>', methods=['GET'])
def get_analytics_insights(vendor_id):
    """Get analytics insights for a vendor"""
    try:
        insights = analytics_engine.generate_insights(vendor_id)
        return success_response({'insights': insights})
    except Exception as e:
        print(f"Analytics insights error: {str(e)}")
        return error_response('Failed to generate insights')

@app.route('/api/analytics/trends/<int:vendor_id>', methods=['GET'])
def get_analytics_trends(vendor_id):
    """Get trend data for visualizations"""
    try:
        trends = analytics_engine.get_trends(vendor_id)
        return success_response({'trends': trends})
    except Exception as e:
        print(f"Analytics trends error: {str(e)}")
        return error_response('Failed to get trends')

# ===== TRUST SYSTEM ENDPOINTS =====

@app.route('/api/trust/score/<int:vendor_id>', methods=['GET'])
def get_trust_score(vendor_id):
    """Get trust score for a vendor"""
    try:
        trust_report = trust_system.get_vendor_trust_report(vendor_id)
        return success_response({'trust_report': trust_report})
    except Exception as e:
        print(f"Trust score error: {str(e)}")
        return error_response('Failed to get trust score')

@app.route('/api/trust/review', methods=['POST'])
def add_review():
    """Add a review for a vendor"""
    try:
        user = validate_session()
        if not user:
            return error_response('Authentication required', 401)
        
        data = request.json
        reviewer_id = user['user_id']
        vendor_id = data.get('vendor_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not all([vendor_id, rating]):
            return error_response('Missing required fields')
        
        if not 1 <= rating <= 5:
            return error_response('Rating must be between 1 and 5')
        
        review_id = trust_system.add_review(reviewer_id, vendor_id, rating, comment)
        
        return success_response(
            {'review_id': review_id},
            'Review added successfully'
        )
        
    except Exception as e:
        print(f"Add review error: {str(e)}")
        return error_response('Failed to add review')

# ===== COMMUNITY ENDPOINTS =====

@app.route('/api/community/groups', methods=['GET'])
def get_community_groups():
    """Get community groups"""
    try:
        groups = community_matching.create_community_groups()
        return success_response({'groups': groups})
    except Exception as e:
        print(f"Community groups error: {str(e)}")
        return error_response('Failed to get community groups')

@app.route('/api/community/recommendations/<int:vendor_id>', methods=['GET'])
def get_community_recommendations(vendor_id):
    """Get community action recommendations"""
    try:
        recommendations = community_matching.recommend_community_actions(vendor_id)
        return success_response({'recommendations': recommendations})
    except Exception as e:
        print(f"Community recommendations error: {str(e)}")
        return error_response('Failed to get community recommendations')

# ===== SYSTEM ENDPOINTS =====

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return success_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'online',
                'ai_assistant': 'online' if openai_key else 'limited',
                'content_scheduler': 'online'
            }
        })
        
    except Exception as e:
        return error_response(f'System unhealthy: {str(e)}', 500)

@app.route('/api/init', methods=['GET'])
def initialize_system():
    """Initialize system with sample data"""
    try:
        # Check if database exists and has data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for existing vendors
        cursor.execute('SELECT COUNT(*) as count FROM vendor_profiles')
        vendor_count = cursor.fetchone()['count']
        
        if vendor_count == 0:
            # Create sample vendor
            cursor.execute('''
                INSERT INTO vendor_profiles 
                (user_id, business_name, business_type, industry, location, 
                 website, description, target_audience, budget, goals, constraints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                1,  # Assuming user_id 1 exists
                "Sample Business",
                "LLC",
                "technology",
                "San Francisco, CA",
                "https://samplebusiness.com",
                "A tech startup developing innovative solutions for small businesses",
                '["small_businesses", "entrepreneurs", "startups"]',
                10000.00,
                '["increase_sales", "brand_awareness", "get_funding"]',
                '{"time": "limited", "resources": "moderate"}'
            ))
            
            vendor_id = cursor.lastrowid
            
            # Create sample campaign
            cursor.execute('''
                INSERT INTO ad_campaigns 
                (vendor_id, campaign_name, platform, ad_type, budget, daily_budget,
                 target_audience, keywords, ad_copy, visuals, landing_page,
                 start_date, end_date, status, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor_id,
                "Launch Campaign",
                "facebook",
                "awareness",
                1000.00,
                33.33,
                '["age_25_45", "entrepreneurs", "small_business_owners"]',
                '["business", "startup", "marketing"]',
                "Launch your business with our innovative platform!",
                '["image1.jpg", "image2.jpg"]',
                "https://samplebusiness.com/launch",
                "2024-01-01",
                "2024-01-31",
                "active",
                '{"estimated_impressions": 50000, "estimated_clicks": 1000, "estimated_roi": 2.5}'
            ))
            
            # Create sample content
            cursor.execute('''
                INSERT INTO content_calendar 
                (vendor_id, title, content_type, platform, content_text, 
                 media_url, hashtags, scheduled_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor_id,
                "Welcome Post",
                "post",
                '["facebook", "instagram"]',
                "Excited to launch our new platform for small businesses! 🚀",
                "https://samplebusiness.com/welcome.jpg",
                '["#business", "#startup", "#launch"]',
                "2024-01-15 09:00:00",
                "scheduled"
            ))
            
            # Create sample pitch
            cursor.execute('''
                INSERT INTO fundraising_pitches 
                (vendor_id, title, problem_statement, solution, market_size,
                 business_model, traction, funding_amount, equity_offered,
                 timeline, pitch_deck_url, status, investor_interest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor_id,
                "AI-Powered Business Platform",
                "Small businesses struggle with marketing and fundraising",
                "All-in-one platform with AI assistance",
                "$10B total addressable market",
                "Subscription-based SaaS",
                "100+ beta users, 95% satisfaction",
                500000.00,
                15.0,
                "6-12 months to scale",
                "https://samplebusiness.com/pitch.pdf",
                "active",
                3
            ))
            
            conn.commit()
            conn.close()
            
            return success_response({
                'initialized': True,
                'vendor_id': vendor_id,
                'message': 'System initialized with sample data'
            })
        else:
            conn.close()
            return success_response({
                'initialized': False,
                'message': 'System already has data'
            })
            
    except Exception as e:
        print(f"Initialize error: {str(e)}")
        traceback.print_exc()
        return error_response('Failed to initialize system')

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return error_response('Endpoint not found', 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return error_response('Method not allowed', 405)

@app.errorhandler(500)
def internal_error(error):
    print(f"Internal server error: {error}")
    return error_response('Internal server error', 500)

# ===== MAIN APPLICATION =====

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 AI Advertising and Fundraising Assistant")
    print("="*50)
    
    # Initialize database
    print("\n📊 Initializing database...")
    try:
        conn = sqlite3.connect('platform.db')
        with open('complete_schema.sql', 'r') as f:
            conn.executescript(f.read())
        
        # Add sample resources
        resources = [
            ('ad_template', 'Facebook Ad Template', 'Complete template for Facebook ads including best practices and examples.', 'advertising', 'beginner', 30, 'facebook,ads,template'),
            ('content_calendar', 'Weekly Content Calendar', 'Template for planning weekly content across social media platforms.', 'content', 'beginner', 60, 'content,calendar,planning'),
            ('pitch_deck', 'Investor Pitch Deck Template', '10-slide pitch deck template with placeholders for each section.', 'fundraising', 'intermediate', 120, 'pitch,investor,funding'),
            ('budget_template', 'Marketing Budget Template', 'Monthly marketing budget spreadsheet with ROI calculations.', 'finance', 'beginner', 45, 'budget,marketing,finance'),
            ('collab_agreement', 'Collaboration Agreement', 'Template for business collaboration agreements.', 'legal', 'advanced', 90, 'collaboration,legal,agreement')
        ]
        
        cursor = conn.cursor()
        for resource in resources:
            cursor.execute('''
                INSERT OR IGNORE INTO resources 
                (resource_type, title, content, category, difficulty_level, estimated_time, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', resource)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        traceback.print_exc()
    
    print("\n🌐 Starting backend server...")
    print("📍 Backend URL: http://127.0.0.1:5000")
    print("📍 API Documentation: http://127.0.0.1:5000/api/health")
    print("\n🔗 Frontend should be served at: http://localhost:8080")
    print("📱 Open browser to: http://localhost:8080/vendor-dashboard.html")
    print("\n🔄 To initialize with sample data, visit: http://127.0.0.1:5000/api/init")
    print("="*50 + "\n")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)