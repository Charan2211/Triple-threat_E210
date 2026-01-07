-- Existing tables remain, adding new ones:

-- Vendor Profiles
CREATE TABLE IF NOT EXISTS vendor_profiles (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    business_name VARCHAR(255),
    business_type VARCHAR(100),
    industry VARCHAR(100),
    location VARCHAR(255),
    website VARCHAR(255),
    description TEXT,
    target_audience TEXT,
    budget DECIMAL(10,2),
    goals TEXT,
    constraints TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Advertising Campaigns
CREATE TABLE IF NOT EXISTS ad_campaigns (
    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    campaign_name VARCHAR(255),
    platform VARCHAR(50),
    ad_type VARCHAR(50),
    budget DECIMAL(10,2),
    daily_budget DECIMAL(10,2),
    target_audience TEXT,
    keywords TEXT,
    ad_copy TEXT,
    visuals TEXT,
    landing_page VARCHAR(255),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    performance_metrics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
);

-- Content Calendar
CREATE TABLE IF NOT EXISTS content_calendar (
    content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    title VARCHAR(255),
    content_type VARCHAR(50),
    platform VARCHAR(50),
    content_text TEXT,
    media_url VARCHAR(255),
    hashtags TEXT,
    scheduled_time DATETIME,
    status VARCHAR(50),
    performance_metrics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
);

-- Fundraising Pitches
CREATE TABLE IF NOT EXISTS fundraising_pitches (
    pitch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    title VARCHAR(255),
    problem_statement TEXT,
    solution TEXT,
    market_size TEXT,
    business_model TEXT,
    traction TEXT,
    funding_amount DECIMAL(10,2),
    equity_offered DECIMAL(5,2),
    timeline TEXT,
    pitch_deck_url VARCHAR(255),
    status VARCHAR(50),
    investor_interest INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
);

-- Investor Profiles
CREATE TABLE IF NOT EXISTS investors (
    investor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    firm VARCHAR(255),
    investment_stage VARCHAR(100),
    industries TEXT,
    check_size_min DECIMAL(10,2),
    check_size_max DECIMAL(10,2),
    location_preference TEXT,
    contact_info TEXT,
    previous_investments TEXT
);

-- Collaborations
CREATE TABLE IF NOT EXISTS collaborations (
    collab_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor1_id INTEGER,
    vendor2_id INTEGER,
    collaboration_type VARCHAR(100),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor1_id) REFERENCES vendor_profiles(vendor_id),
    FOREIGN KEY (vendor2_id) REFERENCES vendor_profiles(vendor_id)
);

-- AI Recommendations
CREATE TABLE IF NOT EXISTS ai_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    recommendation_type VARCHAR(100),
    content TEXT,
    priority INTEGER,
    action_items TEXT,
    estimated_impact DECIMAL(5,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor_profiles(vendor_id)
);

-- Resources & Templates
CREATE TABLE IF NOT EXISTS resources (
    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type VARCHAR(100),
    title VARCHAR(255),
    content TEXT,
    category VARCHAR(100),
    difficulty_level VARCHAR(50),
    estimated_time INTEGER,
    tags TEXT
);
