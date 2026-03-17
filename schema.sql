-- CannaGrudge Database Schema

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    firebase_uid TEXT UNIQUE NOT NULL,
    email TEXT,
    name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT,
    subject TEXT,
    html_body TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ticket_tiers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    features TEXT DEFAULT '',
    capacity INTEGER DEFAULT 0,
    sold INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    sale_start TIMESTAMPTZ,
    sale_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS promo_codes (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    discount_type TEXT DEFAULT 'percent',
    discount_amount INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 0,
    uses INTEGER DEFAULT 0,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number TEXT DEFAULT 'LEGACY',
    email TEXT,
    name TEXT,
    subtotal INTEGER DEFAULT 0,
    total_amount INTEGER DEFAULT 0,
    total_cents INTEGER DEFAULT 0,
    discount_cents INTEGER DEFAULT 0,
    promo_code TEXT,
    status TEXT DEFAULT 'pending',
    square_payment_id TEXT,
    receipt_url TEXT,
    billing_address TEXT,
    notes TEXT DEFAULT '',
    checked_in BOOLEAN DEFAULT FALSE,
    checked_in_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    ticket_tier_id INTEGER,
    product_id INTEGER,
    tier_name TEXT,
    qty INTEGER DEFAULT 1,
    quantity INTEGER DEFAULT 1,
    unit_price INTEGER DEFAULT 0,
    unit_price_cents INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sponsor_requests (
    id SERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT DEFAULT '',
    message TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    deck_token TEXT,
    deck_token_expires TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_invites (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    used_at TIMESTAMPTZ,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchase_links (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    email TEXT DEFAULT '',
    tier_id INTEGER REFERENCES ticket_tiers(id),
    qty INTEGER DEFAULT 1,
    promo_code TEXT,
    expires_at TIMESTAMPTZ,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    sponsor_request_id INTEGER REFERENCES sponsor_requests(id),
    recipient_name TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    company TEXT DEFAULT '',
    amount_cents INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    due_date DATE,
    view_token TEXT UNIQUE NOT NULL,
    notes TEXT DEFAULT '',
    attachment_filename TEXT,
    attachment_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS page_views (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    page TEXT NOT NULL,
    referrer TEXT DEFAULT '',
    utm_source TEXT DEFAULT '',
    utm_medium TEXT DEFAULT '',
    utm_campaign TEXT DEFAULT '',
    device_type TEXT DEFAULT '',
    browser TEXT DEFAULT '',
    os TEXT DEFAULT '',
    country TEXT DEFAULT '',
    screen_width INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    user_name TEXT DEFAULT '',
    user_email TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_page_views_created ON page_views(created_at);
CREATE INDEX IF NOT EXISTS idx_page_views_session ON page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_page_views_page ON page_views(page);

CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    session_id TEXT DEFAULT '',
    event_type TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    page TEXT DEFAULT '',
    detail TEXT DEFAULT '',
    meta JSONB DEFAULT '{}',
    user_email TEXT DEFAULT '',
    user_name TEXT DEFAULT '',
    ip_addr TEXT DEFAULT '',
    device_type TEXT DEFAULT '',
    browser TEXT DEFAULT '',
    os TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_event ON activity_log(event_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_category ON activity_log(category);

CREATE TABLE IF NOT EXISTS contact_messages (
    id SERIAL PRIMARY KEY,
    name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    message TEXT NOT NULL,
    status TEXT DEFAULT 'unread',
    admin_reply TEXT DEFAULT '',
    replied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contact_messages_status ON contact_messages(status);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created ON contact_messages(created_at);
