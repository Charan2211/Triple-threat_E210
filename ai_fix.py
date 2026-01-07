import os
import sys
import random
import time
from datetime import datetime
from flask import Flask, jsonify, request, Blueprint
import json

# Create a blueprint for AI routes
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Sample recommendations database
RECOMMENDATIONS_DB = {
    "general": [
        "Optimize your ad targeting to focus on users aged 25-34 for better ROI",
        "Increase video content by 40% to boost engagement rates",
        "Run A/B tests on landing page designs to improve conversion",
        "Allocate 70% of budget to top-performing channels, 30% to testing",
        "Use customer testimonials in ads to increase trust by 60%",
        "Schedule posts during peak hours (8-10 AM & 6-8 PM)",
        "Implement retargeting campaigns for abandoned carts",
        "Collaborate with micro-influencers in your niche"
    ],
    "advertising": [
        "Increase Google Ads budget by 20% for high-intent keywords",
        "Test different Facebook ad formats (carousel vs single image)",
        "Use lookalike audiences to reach new potential customers",
        "Optimize ad copy with emotional triggers",
        "Implement dayparting to show ads at optimal times",
        "Use UTM parameters to track campaign performance",
        "Test value-based bidding strategies",
        "Create urgency with limited-time offers"
    ],
    "content": [
        "Create how-to video tutorials for your products",
        "Start a weekly newsletter with industry insights",
        "Repurpose top-performing content into different formats",
        "Use storytelling in your case studies",
        "Implement a content calendar for consistent posting",
        "Create interactive content (polls, quizzes, calculators)",
        "Optimize blog posts for featured snippets",
        "Use data visualization to explain complex topics"
    ],
    "fundraising": [
        "Create a compelling story around your mission",
        "Offer tiered reward systems for different donation levels",
        "Use social proof by showcasing previous donors",
        "Host virtual fundraising events",
        "Create a monthly subscription model",
        "Partner with corporate sponsors",
        "Use crowdfunding platforms for wider reach",
        "Create urgency with matching gift campaigns"
    ]
}

@ai_bp.route('/health', methods=['GET'])
def ai_health():
    """Check AI service health"""
    return jsonify({
        "status": "healthy",
        "service": "ai_recommendations",
        "timestamp": datetime.now().isoformat(),
        "recommendations_available": len(RECOMMENDATIONS_DB["general"])
    })

@ai_bp.route('/recommend', methods=['GET', 'POST'])
def get_recommendations():
    """Get AI-powered recommendations"""
    try:
        # Get parameters
        category = request.args.get('category', 'general')
        count = int(request.args.get('count', 3))
        
        # Get recommendations for category
        if category in RECOMMENDATIONS_DB:
            recommendations = RECOMMENDATIONS_DB[category]
        else:
            recommendations = RECOMMENDATIONS_DB["general"]
        
        # Select random recommendations
        count = min(count, len(recommendations))
        selected = random.sample(recommendations, count)
        
        # Simulate AI processing delay
        time.sleep(0.5)
        
        return jsonify({
            "success": True,
            "category": category,
            "count": count,
            "recommendations": selected,
            "generated_at": datetime.now().isoformat(),
            "model": "local_ai_v1",
            "confidence": round(random.uniform(0.85, 0.95), 2)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Using fallback recommendations",
            "recommendations": [
                "Start by analyzing your current campaign performance",
                "Focus on your top 3 performing channels first",
                "Set clear, measurable goals for each campaign"
            ]
        }), 200

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """Simple AI chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '').lower()
        
        # Simple response logic
        responses = {
            "budget": "Allocate 60% to proven channels, 30% to testing, 10% to emergencies. Review weekly.",
            "targeting": "Focus on demographics with highest LTV: Age 25-34, urban areas, interest-based targeting.",
            "content": "Video content performs 3x better. Use storytelling and customer testimonials.",
            "roi": "Track metrics: CAC, LTV, CTR. Aim for 4:1 ROI on ad spend.",
            "engagement": "Post during peak hours (8-10 AM, 7-9 PM), use questions in captions.",
            "growth": "Test new channels quarterly, optimize top performers monthly."
        }
        
        # Find matching response
        response = "I recommend analyzing your data to identify patterns and opportunities for optimization."
        for key in responses:
            if key in message:
                response = responses[key]
                break
        
        return jsonify({
            "success": True,
            "response": response,
            "suggested_actions": [
                "Review last month's performance data",
                "Set up A/B test for your hypothesis",
                "Schedule a performance review meeting"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "I'm having trouble processing your request. Please try again."
        }), 200

@ai_bp.route('/analyze', methods=['POST'])
def analyze_data():
    """Analyze provided data"""
    try:
        data = request.json.get('data', {})
        
        insights = [
            f"Found {random.randint(2, 8)} key performance indicators",
            f"Top performing channel: {random.choice(['Social Media', 'Search Ads', 'Email', 'Direct'])}",
            f"Suggested optimization: Increase budget by {random.randint(10, 30)}%",
            f"Potential ROI improvement: {random.randint(15, 45)}%"
        ]
        
        return jsonify({
            "success": True,
            "insights": insights,
            "confidence": round(random.uniform(0.7, 0.9), 2),
            "next_steps": [
                "Implement A/B testing",
                "Review in 7 days",
                "Adjust based on results"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })