import os
import json
import uuid
import secrets
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

import resend
import firebase_admin
from firebase_admin import credentials, auth as fb_auth

# Use an explicit absolute path for serving files
_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=_ROOT, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024

DATABASE_URL = os.environ.get('DATABASE_URL', '')
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '').strip()
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '').strip()
SQUARE_ENVIRONMENT = os.environ.get('SQUARE_ENVIRONMENT', 'production').strip()

if not firebase_admin._apps:
    sa_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', '').lstrip('\ufeff').strip()
    if sa_key:
        cred = credentials.Certificate(json.loads(sa_key))
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

resend.api_key = os.environ.get('RESEND_API_KEY', '')
RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'CannaGrudge <onboarding@resend.dev>')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def query_db(sql, params=None, one=False):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    try:
        rows = cur.fetchall()
        result = rows[0] if one and rows else rows if not one else None
    except psycopg2.ProgrammingError:
        result = None
    cur.close()
    conn.close()
    return result

def execute_db(sql, params=None):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    try:
        result = cur.fetchone()
    except psycopg2.ProgrammingError:
        result = None
    cur.close()
    conn.close()
    return result

def verify_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth_header.split('Bearer ')[1]
        try:
            decoded = fb_auth.verify_id_token(token)
            uid = decoded['uid']
            email = decoded.get('email', '')
            user = query_db('SELECT * FROM users WHERE firebase_uid = %s', (uid,), one=True)
            if not user:
                user = execute_db(
                    'INSERT INTO users (firebase_uid, email, name) VALUES (%s, %s, %s) RETURNING *',
                    (uid, email, decoded.get('name', ''))
                )
            if not user or not user.get('is_admin'):
                return jsonify({'error': 'Admin access required'}), 403
            request.admin_user = user
        except Exception as e:
            return jsonify({'error': 'Invalid token', 'detail': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

def seed_email_templates():
    from email_templates import DEFAULT_TEMPLATES
    for tmpl in DEFAULT_TEMPLATES:
        existing = query_db('SELECT id FROM email_templates WHERE slug = %s', (tmpl['slug'],), one=True)
        if not existing:
            execute_db(
                'INSERT INTO email_templates (slug, name, subject, html_body, description) VALUES (%s, %s, %s, %s, %s)',
                (tmpl['slug'], tmpl['name'], tmpl['subject'], tmpl['html_body'], tmpl['description'])
            )

try:
    pass  # email templates seeded lazily on first request
except Exception as e:
    print(f"[EMAIL SEED] {e}")

def seed_ticket_tiers():
    """Seed default ticket tiers if they don't exist"""
    try:
        existing = query_db('SELECT COUNT(*) as cnt FROM ticket_tiers', one=True)
        if existing and existing['cnt'] > 0:
            return
        
        tiers = [
            {
                'name': 'Regular Entry',
                'price_cents': 4000,
                'description': 'General admission ticket with full event access',
                'features': 'Standing room access|Vendor marketplace|Games & activities area|Food & drink available|Live fight card + halftime entertainment',
                'capacity': 500,
                'sort_order': 1,
                'active': True
            },
            {
                'name': 'Early Entry Add-On',
                'price_cents': 2000,
                'description': 'Upgrade to enter one hour before general admission',
                'features': 'Enter one hour early|Skip early lines|First access to vendors & merch|Get premium viewing spots|Requires Regular Entry ticket',
                'capacity': 200,
                'sort_order': 2,
                'active': True
            }
        ]
        
        for tier in tiers:
            execute_db(
                '''INSERT INTO ticket_tiers (name, price_cents, description, features, capacity, sort_order, active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (tier['name'], tier['price_cents'], tier['description'], tier['features'], 
                 tier['capacity'], tier['sort_order'], tier['active'])
            )
        print(f"[TICKET SEED] Created {len(tiers)} default ticket tiers")
    except Exception as e:
        print(f"[TICKET SEED ERROR] {e}")

try:
    pass  # ticket tiers seeded lazily on first request
except Exception as e:
    print(f"[TICKET SEED] {e}")

def run_migrations():
    """Add any missing columns to existing tables."""
    migrations = [
        # --- orders: ensure every column the app writes to exists ---
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_number TEXT DEFAULT 'LEGACY'",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS email TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS name TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_amount INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_cents INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount_cents INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_code TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS square_payment_id TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_url TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS billing_address TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS checked_in BOOLEAN DEFAULT FALSE",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS checked_in_at TIMESTAMPTZ",
        # --- order_items: ensure every column the app writes to exists ---
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_id INTEGER",
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS quantity INTEGER",
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS unit_price INTEGER",
    ]
    for sql in migrations:
        try:
            execute_db(sql)
        except Exception as e:
            print(f"[MIGRATION] {sql[:60]}... => {e}")

_seeded = False
def _lazy_seed():
    global _seeded
    if _seeded:
        return
    _seeded = True
    try:
        if DATABASE_URL:
            run_migrations()
    except Exception as e:
        print(f"[MIGRATION] {e}")
    try:
        seed_email_templates()
    except Exception as e:
        print(f"[EMAIL SEED] {e}")
    try:
        if DATABASE_URL:
            seed_ticket_tiers()
    except Exception as e:
        print(f"[TICKET SEED] {e}")

@app.before_request
def before_req():
    _lazy_seed()

def send_email(to_email, template_slug, variables=None):
    variables = variables or {}
    tmpl = query_db('SELECT * FROM email_templates WHERE slug = %s', (template_slug,), one=True)
    if not tmpl:
        print(f"[EMAIL] Template '{template_slug}' not found")
        return None
    subject = tmpl['subject']
    html = tmpl['html_body']
    for key, val in variables.items():
        subject = subject.replace('{{' + key + '}}', str(val))
        html = html.replace('{{' + key + '}}', str(val))
    try:
        r = resend.Emails.send({
            'from': RESEND_FROM_EMAIL,
            'to': [to_email],
            'subject': subject,
            'html': html,
        })
        print(f"[EMAIL] Sent '{template_slug}' to {to_email}")
        return r
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return None

def _as_cents(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def build_order_items_html(order_items):
    rows = ''
    for li in (order_items or []):
        tier_name = li.get('tier_name') or 'Ticket'
        qty = _as_cents(li.get('qty') if li.get('qty') is not None else li.get('quantity'), 0)
        unit_price = _as_cents(li.get('unit_price_cents') if li.get('unit_price_cents') is not None else li.get('unit_price'), 0)
        rows += (
            f'<tr><td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#ffffff;">{tier_name}</td>'
            f'<td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#ffffff;text-align:center;">{qty}</td>'
            f'<td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#d4a843;text-align:right;">${unit_price * qty / 100:.2f}</td></tr>'
        )
    return rows

def send_purchase_confirmation_email(order, order_items, subtotal_cents=None, discount_cents=None, total_cents=None):
    email = (order.get('email') or '').strip().lower()
    if not email:
        return False

    subtotal = _as_cents(subtotal_cents, _as_cents(order.get('subtotal'), _as_cents(order.get('total_cents'))))
    discount = _as_cents(discount_cents, _as_cents(order.get('discount_cents')))
    total = _as_cents(total_cents, _as_cents(order.get('total_cents'), subtotal - discount))

    result = send_email(email, 'purchase_confirmation', {
        'buyer_name': (order.get('name') or 'Guest').strip() or 'Guest',
        'order_id': str(order.get('id') or ''),
        'order_items': build_order_items_html(order_items),
        'subtotal': f'${subtotal / 100:.2f}',
        'discount': f'${discount / 100:.2f}',
        'total': f'${total / 100:.2f}',
        'receipt_url': order.get('receipt_url') or '#',
        'payment_id': order.get('square_payment_id') or '',
    })
    return bool(result)

@app.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'service': 'cannagrudge'}), 200

@app.route('/')
def index():
    return send_from_directory(_ROOT, 'index.html')

# Clean URL routing — serve /deck → deck.html, /tickets → tickets.html, etc.
# These explicit routes take priority over Flask's static file handler.
_HTML_PAGES = set()
for _f in os.listdir(_ROOT):
    if _f.endswith('.html') and _f != 'index.html':
        _HTML_PAGES.add(_f[:-5])  # e.g. 'deck', 'tickets', 'sponsors'

@app.route('/<page>')
def serve_page(page):
    if page in _HTML_PAGES:
        return send_from_directory(_ROOT, page + '.html')
    # Let Flask's static handler try, or fall through to 404
    try:
        return send_from_directory(_ROOT, page)
    except Exception:
        return send_from_directory(_ROOT, 'error.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory(_ROOT, 'error.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return send_from_directory(_ROOT, 'error.html'), 500

@app.route('/api/square-config', methods=['GET'])
def square_config():
    app_id = os.environ.get('SQUARE_APPLICATION_ID', '').strip()
    loc_id = os.environ.get('SQUARE_LOCATION_ID', '').strip()
    return jsonify({'applicationId': app_id, 'locationId': loc_id})

@app.route('/api/payment-status', methods=['GET'])
def payment_status():
    app_id = os.environ.get('SQUARE_APPLICATION_ID', '').strip()
    loc_id = os.environ.get('SQUARE_LOCATION_ID', '').strip()
    token = os.environ.get('SQUARE_ACCESS_TOKEN', '').strip()
    return jsonify({
        'square_app_id_set': bool(app_id),
        'square_app_id_prefix': app_id[:12] + '...' if app_id else 'NOT SET',
        'square_location_id_set': bool(loc_id),
        'square_location_id': loc_id if loc_id else 'NOT SET',
        'square_token_set': bool(token),
        'square_token_prefix': token[:12] + '...' if token else 'NOT SET',
        'square_environment': SQUARE_ENVIRONMENT,
        'all_configured': bool(app_id and loc_id and token)
    })

@app.route('/api/init-db', methods=['POST'])
def init_db():
    secret = os.environ.get('BOOTSTRAP_SECRET', '')
    if not secret:
        return jsonify({'error': 'Not available'}), 404
    data = request.get_json() or {}
    if data.get('secret') != secret:
        return jsonify({'error': 'Forbidden'}), 403
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        sql = f.read()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Database initialized'})

@app.route('/api/bootstrap-admin', methods=['POST'])
def bootstrap_admin():
    secret = os.environ.get('BOOTSTRAP_SECRET', '')
    if not secret:
        return jsonify({'error': 'Not available'}), 404
    data = request.get_json() or {}
    if data.get('secret') != secret:
        return jsonify({'error': 'Forbidden'}), 403
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'email required'}), 400
    result = execute_db('UPDATE users SET is_admin = TRUE WHERE LOWER(email) = %s RETURNING id, email', (email,))
    if not result:
        return jsonify({'error': f'No user found with email {email}'}), 404
    return jsonify({'success': True, 'admin_set_for': result['email']})

@app.route('/api/tickets', methods=['GET'])
def get_public_tickets():
    tiers = query_db('SELECT id, name, price_cents, description, features, capacity, sold, active FROM ticket_tiers WHERE active = TRUE ORDER BY sort_order')
    result = []
    for t in tiers:
        t['features'] = t['features'].split('|') if t['features'] else []
        result.append(t)
    return jsonify(result)

@app.route('/api/promos/validate', methods=['POST'])
def validate_promo():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    now = datetime.now(timezone.utc)
    promo = query_db(
        'SELECT * FROM promo_codes WHERE UPPER(code) = %s AND active = TRUE',
        (code,), one=True
    )
    if not promo:
        return jsonify({'error': 'Invalid promo code'}), 404
    if promo['max_uses'] > 0 and promo['uses'] >= promo['max_uses']:
        return jsonify({'error': 'Promo code has been fully redeemed'}), 400
    if promo['starts_at'] and now < promo['starts_at']:
        return jsonify({'error': 'Promo code is not yet active'}), 400
    if promo['ends_at'] and now > promo['ends_at']:
        return jsonify({'error': 'Promo code has expired'}), 400
    return jsonify({
        'valid': True,
        'code': promo['code'],
        'discount_type': promo['discount_type'],
        'discount_amount': promo['discount_amount']
    })

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    from square.client import Client
    data = request.get_json()
    if not data or 'sourceId' not in data:
        return jsonify({'error': 'Missing payment source'}), 400

    cart_items = data.get('items', [])
    email = (data.get('email') or '').strip().lower()
    buyer_name = data.get('name', '')
    promo_code = (data.get('promoCode') or '').strip().upper()

    # Map frontend item IDs to database names for tier lookup
    item_id_to_tier_name = {
        'regular-entry': 'Regular Entry',
        'early-entry-addon': 'Early Entry Add-On',
    }

    fallback_catalog = {
        'regular-entry': {'name': 'Regular Entry', 'price_cents': 4000},
        'early-entry-addon': {'name': 'Early Entry Add-On', 'price_cents': 2000},
    }

    total = 0
    regular_qty = 0
    early_addon_qty = 0
    order_line_items = []
    for item in cart_items:
        tier_id = item.get('tierId')
        item_id = item.get('id', '')
        tier = None
        
        # First try by tier_id if provided
        if tier_id:
            tier = query_db('SELECT * FROM ticket_tiers WHERE id = %s AND active = TRUE', (tier_id,), one=True)
        
        # Then try by item_id as database ID (only if it looks like an integer)
        if not tier and item_id and str(item_id).isdigit():
            tier = query_db('SELECT * FROM ticket_tiers WHERE id = %s AND active = TRUE', (item_id,), one=True)
        
        # Finally try by matching tier name from item_id
        if not tier and item_id in item_id_to_tier_name:
            tier_name_lookup = item_id_to_tier_name[item_id]
            tier = query_db('SELECT * FROM ticket_tiers WHERE name = %s AND active = TRUE', (tier_name_lookup,), one=True)
        
        fallback = fallback_catalog.get(item_id)
        if not tier and not fallback:
            return jsonify({'error': f'Invalid ticket tier'}), 400

        if tier:
            price = tier['price_cents']
            tier_name = tier['name']
            tier_pk = tier['id']
        else:
            price = fallback['price_cents']
            tier_name = fallback['name']
            tier_pk = None

        qty = max(1, min(int(item.get('qty', 1)), 50))
        if tier and tier['capacity'] > 0 and tier['sold'] + qty > tier['capacity']:
            return jsonify({'error': f'{tier["name"]} is sold out or insufficient capacity'}), 400

        if item_id == 'regular-entry':
            regular_qty += qty
        elif item_id == 'early-entry-addon':
            early_addon_qty += qty

        line_total = price * qty
        total += line_total
        order_line_items.append({
            'tier_id': tier_pk,
            'product_id': int(item_id) if str(item_id).isdigit() else None,
            'tier_name': tier_name,
            'qty': qty,
            'unit_price': price
        })

    if early_addon_qty > regular_qty:
        return jsonify({'error': 'Early Entry add-ons must match the number of Regular Entry tickets.'}), 400

    discount = 0
    if promo_code:
        promo = query_db('SELECT * FROM promo_codes WHERE UPPER(code) = %s AND active = TRUE', (promo_code,), one=True)
        if promo:
            if promo['discount_type'] == 'percent':
                discount = int(total * promo['discount_amount'] / 100)
            else:
                discount = promo['discount_amount']
            if discount > total:
                discount = total
            execute_db('UPDATE promo_codes SET uses = uses + 1 WHERE id = %s', (promo['id'],))

    charge_amount = total - discount
    if charge_amount < 0:
        charge_amount = 0

    # Write order to DB FIRST (pending) — so a DB failure never charges the card
    order_number = 'CG-' + str(uuid.uuid4())[:8].upper()
    order = execute_db(
        '''INSERT INTO orders (order_number, email, name, subtotal, total_amount, total_cents, discount_cents, promo_code, status, square_payment_id, receipt_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (order_number, email, buyer_name, total, charge_amount, total, discount, promo_code or None, 'pending', '', '')
    )
    for li in order_line_items:
        execute_db(
            'INSERT INTO order_items (order_id, ticket_tier_id, product_id, tier_name, qty, quantity, unit_price, unit_price_cents) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (order['id'], li['tier_id'], li['product_id'], li['tier_name'], li['qty'], li['qty'], li['unit_price'], li['unit_price'])
        )
        if li['tier_id']:
            execute_db('UPDATE ticket_tiers SET sold = sold + %s WHERE id = %s', (li['qty'], li['tier_id']))

    # Now charge Square
    if charge_amount > 0:
        client = Client(access_token=SQUARE_ACCESS_TOKEN, environment=SQUARE_ENVIRONMENT)
        body = {
            'source_id': data['sourceId'],
            'idempotency_key': str(uuid.uuid4()),
            'amount_money': {'amount': charge_amount, 'currency': 'USD'},
            'location_id': SQUARE_LOCATION_ID,
            'note': f'CannaGrudge Tickets - {buyer_name}',
        }
        if email:
            body['buyer_email_address'] = email
        result = client.payments.create_payment(body=body)
        if not result.is_success():
            print(f'[SQUARE ERROR] {result.errors}')
            execute_db("UPDATE orders SET status='failed' WHERE id=%s", (order['id'],))
            _log_activity('payment_failed', 'purchase', '/checkout',
                          f'Payment failed for {buyer_name} ({email}) — ${charge_amount/100:.2f}',
                          {'order_id': order['id'], 'errors': str(result.errors)})
            return jsonify({'success': False, 'errors': result.errors}), 400
        payment = result.body.get('payment', {})
        payment_id = payment.get('id', '')
        receipt_url = payment.get('receipt_url', '')
    else:
        payment_id = 'FREE-' + str(uuid.uuid4())[:8]
        receipt_url = ''

    # Mark order completed now that payment succeeded
    execute_db(
        "UPDATE orders SET status='completed', square_payment_id=%s, receipt_url=%s WHERE id=%s",
        (payment_id, receipt_url, order['id'])
    )
    order['square_payment_id'] = payment_id
    order['receipt_url'] = receipt_url

    items_summary = ', '.join(f"{li['qty']}x {li['tier_name']}" for li in order_line_items)
    _log_activity('purchase_completed', 'purchase', '/checkout',
                  f'{buyer_name} ({email}) purchased {items_summary} — ${charge_amount/100:.2f}',
                  {'order_id': order['id'], 'payment_id': payment_id, 'total_cents': charge_amount},
                  user_email=email)

    if email:
        send_purchase_confirmation_email(
            order,
            order_line_items,
            subtotal_cents=total,
            discount_cents=discount,
            total_cents=charge_amount,
        )

    return jsonify({
        'success': True,
        'payment': {
            'id': payment_id,
            'status': 'COMPLETED',
            'amount': charge_amount,
            'receipt_url': receipt_url
        },
        'order_id': order['id'],
        'discount': discount
    })


# ──────── User Order Lookup (authenticated) ────────

@app.route('/api/my/orders', methods=['GET'])
def my_orders():
    """Return orders for the currently authenticated user (by email)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split('Bearer ')[1]
    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401
    email = (decoded.get('email') or '').strip().lower()
    if not email:
        return jsonify([])
    orders = query_db(
        '''SELECT id, order_number, email, name, total_cents, discount_cents, promo_code,
                  status, square_payment_id, receipt_url, created_at
           FROM orders WHERE LOWER(email) = %s ORDER BY created_at DESC''',
        (email,)
    )
    for o in orders:
        o['items'] = query_db(
            '''SELECT tier_name, qty, unit_price_cents FROM order_items
               WHERE order_id = %s ORDER BY id''',
            (o['id'],)
        )
        if o.get('created_at'):
            o['created_at'] = o['created_at'].isoformat()
    return jsonify(orders)


@app.route('/api/auth/sync', methods=['POST'])
def auth_sync():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split('Bearer ')[1]
    try:
        decoded = fb_auth.verify_id_token(token)
        uid = decoded['uid']
        email = decoded.get('email', '')
        name = decoded.get('name', '') or ''
        user = query_db('SELECT * FROM users WHERE firebase_uid = %s', (uid,), one=True)
        if user:
            updates = []
            params = []
            if email and email != user.get('email'):
                updates.append('email = %s')
                params.append(email)
            if name and name != user.get('name'):
                updates.append('name = %s')
                params.append(name)
            if updates:
                params.append(user['id'])
                execute_db(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
        else:
            user = execute_db(
                'INSERT INTO users (firebase_uid, email, name) VALUES (%s, %s, %s) RETURNING *',
                (uid, email, name)
            )
            if email:
                try:
                    send_email(email, 'welcome_email', {
                        'user_name': name or email.split('@')[0],
                        'user_email': email,
                    })
                except Exception:
                    pass
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@app.route('/api/admin/import-firebase-users', methods=['POST'])
@verify_admin
def import_firebase_users():
    imported = 0
    updated = 0
    skipped = 0
    page = fb_auth.list_users()
    while page:
        for fb_user in page.users:
            uid = fb_user.uid
            email = fb_user.email or ''
            name = fb_user.display_name or ''
            existing = query_db('SELECT id, email, name FROM users WHERE firebase_uid = %s', (uid,), one=True)
            if existing:
                updates = []
                params = []
                if email and email != existing.get('email'):
                    updates.append('email = %s')
                    params.append(email)
                if name and name != existing.get('name'):
                    updates.append('name = %s')
                    params.append(name)
                if updates:
                    params.append(existing['id'])
                    execute_db(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
                    updated += 1
                else:
                    skipped += 1
            else:
                execute_db(
                    'INSERT INTO users (firebase_uid, email, name) VALUES (%s, %s, %s)',
                    (uid, email, name)
                )
                imported += 1
        page = page.get_next_page()
    return jsonify({'imported': imported, 'updated': updated, 'skipped': skipped, 'total': imported + updated + skipped})


@app.route('/api/admin/verify', methods=['POST'])
def admin_verify():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split('Bearer ')[1]
    try:
        decoded = fb_auth.verify_id_token(token)
        uid = decoded['uid']
        email = decoded.get('email', '')
        user = query_db('SELECT * FROM users WHERE firebase_uid = %s', (uid,), one=True)
        if not user:
            admin_count = query_db('SELECT COUNT(*) as cnt FROM users WHERE is_admin = TRUE', one=True)
            is_first = admin_count['cnt'] == 0
            user = execute_db(
                'INSERT INTO users (firebase_uid, email, name, is_admin) VALUES (%s, %s, %s, %s) RETURNING *',
                (uid, email, decoded.get('name', ''), is_first)
            )
            if email:
                send_email(email, 'welcome_email', {
                    'user_name': decoded.get('name', '') or email.split('@')[0],
                    'user_email': email,
                })
        invite = query_db(
            'SELECT * FROM admin_invites WHERE LOWER(email) = LOWER(%s) AND used_at IS NULL AND expires_at > NOW()',
            (email,), one=True
        )
        if invite and not user.get('is_admin'):
            execute_db('UPDATE users SET is_admin = TRUE WHERE id = %s', (user['id'],))
            execute_db('UPDATE admin_invites SET used_at = NOW() WHERE id = %s', (invite['id'],))
            user['is_admin'] = True
        return jsonify({
            'is_admin': user.get('is_admin', False),
            'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}
        })
    except Exception as e:
        print(f"[ADMIN VERIFY ERROR] {type(e).__name__}: {e}")
        return jsonify({'error': str(e)}), 401


@app.route('/api/admin/tickets', methods=['GET'])
@verify_admin
def admin_get_tickets():
    tiers = query_db('SELECT * FROM ticket_tiers ORDER BY sort_order')
    for t in tiers:
        t['features'] = t['features'].split('|') if t['features'] else []
        if t.get('created_at'):
            t['created_at'] = t['created_at'].isoformat()
        if t.get('sale_start'):
            t['sale_start'] = t['sale_start'].isoformat()
        if t.get('sale_end'):
            t['sale_end'] = t['sale_end'].isoformat()
    return jsonify(tiers)

@app.route('/api/admin/tickets', methods=['POST'])
@verify_admin
def admin_create_ticket():
    d = request.get_json()
    features = '|'.join(d.get('features', [])) if isinstance(d.get('features'), list) else d.get('features', '')
    tier = execute_db(
        '''INSERT INTO ticket_tiers (name, price_cents, description, features, capacity, sort_order, active, sale_start, sale_end)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (d['name'], d['price_cents'], d.get('description', ''), features,
         d.get('capacity', 0), d.get('sort_order', 0), d.get('active', True),
         d.get('sale_start'), d.get('sale_end'))
    )
    return jsonify(tier), 201

@app.route('/api/admin/tickets/<int:tid>', methods=['PUT'])
@verify_admin
def admin_update_ticket(tid):
    d = request.get_json()
    features = '|'.join(d.get('features', [])) if isinstance(d.get('features'), list) else d.get('features', '')
    tier = execute_db(
        '''UPDATE ticket_tiers SET name=%s, price_cents=%s, description=%s, features=%s,
           capacity=%s, sort_order=%s, active=%s, sale_start=%s, sale_end=%s WHERE id=%s RETURNING *''',
        (d['name'], d['price_cents'], d.get('description', ''), features,
         d.get('capacity', 0), d.get('sort_order', 0), d.get('active', True),
         d.get('sale_start'), d.get('sale_end'), tid)
    )
    return jsonify(tier)

@app.route('/api/admin/tickets/<int:tid>', methods=['DELETE'])
@verify_admin
def admin_delete_ticket(tid):
    execute_db('DELETE FROM ticket_tiers WHERE id = %s', (tid,))
    return jsonify({'deleted': True})


@app.route('/api/admin/orders', methods=['GET'])
@verify_admin
def admin_get_orders():
    orders = query_db('''
        SELECT o.*, json_agg(json_build_object('tier_name', oi.tier_name, 'qty', oi.qty, 'unit_price_cents', oi.unit_price_cents)) as items
        FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id ORDER BY o.created_at DESC
    ''')
    for o in orders:
        if o.get('created_at'):
            o['created_at'] = o['created_at'].isoformat()
        if o.get('items') and len(o['items']) == 1 and o['items'][0].get('tier_name') is None:
            o['items'] = []
    return jsonify(orders)

@app.route('/api/admin/orders/<int:oid>', methods=['PUT'])
@verify_admin
def admin_update_order(oid):
    d = request.get_json()
    order = execute_db('UPDATE orders SET status=%s, notes=%s WHERE id=%s RETURNING *',
                       (d.get('status', 'completed'), d.get('notes', ''), oid))
    return jsonify(order)

@app.route('/api/admin/orders/<int:oid>', methods=['GET'])
@verify_admin
def admin_get_order_detail(oid):
    order = query_db('SELECT * FROM orders WHERE id = %s', (oid,), one=True)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    items = query_db(
        '''SELECT tier_name, qty, quantity, unit_price, unit_price_cents
           FROM order_items WHERE order_id = %s ORDER BY id''',
        (oid,)
    )
    if order.get('created_at'):
        order['created_at'] = order['created_at'].isoformat()
    if order.get('updated_at') and hasattr(order['updated_at'], 'isoformat'):
        order['updated_at'] = order['updated_at'].isoformat()
    order['items'] = items or []
    return jsonify(order)

@app.route('/api/admin/orders/<int:oid>/resend-confirmation', methods=['POST'])
@verify_admin
def admin_resend_order_confirmation(oid):
    order = query_db('SELECT * FROM orders WHERE id = %s', (oid,), one=True)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    items = query_db(
        '''SELECT tier_name, qty, quantity, unit_price, unit_price_cents
           FROM order_items WHERE order_id = %s ORDER BY id''',
        (oid,)
    )

    if not (order.get('email') or '').strip():
        return jsonify({'error': 'Order has no customer email address'}), 400

    sent = send_purchase_confirmation_email(order, items or [])
    if not sent:
        return jsonify({'error': 'Failed to send confirmation email'}), 500
    return jsonify({'success': True, 'message': f'Confirmation email resent to {order.get("email")}'})


# ──────── Check-In / Scanner ────────

@app.route('/api/admin/checkin/lookup', methods=['GET'])
@verify_admin
def admin_checkin_lookup():
    """Look up an order by order_number, email, or name for check-in."""
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'error': 'Search query required'}), 400
    orders = query_db(
        '''SELECT o.id, o.order_number, o.email, o.name, o.total_cents, o.status,
                  o.checked_in, o.checked_in_at, o.created_at
           FROM orders o
           WHERE o.status = 'completed'
             AND (UPPER(o.order_number) = UPPER(%s)
                  OR LOWER(o.email) = LOWER(%s)
                  OR LOWER(o.name) LIKE LOWER(%s))
           ORDER BY o.created_at DESC''',
        (q, q, f'%{q}%')
    )
    for o in orders:
        o['items'] = query_db(
            'SELECT tier_name, qty FROM order_items WHERE order_id = %s ORDER BY id',
            (o['id'],)
        )
        for k in ['created_at', 'checked_in_at']:
            if o.get(k):
                o[k] = o[k].isoformat()
    return jsonify(orders)


@app.route('/api/admin/checkin/<int:oid>', methods=['POST'])
@verify_admin
def admin_checkin(oid):
    """Mark an order as checked in."""
    order = query_db('SELECT * FROM orders WHERE id = %s', (oid,), one=True)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'completed':
        return jsonify({'error': 'Only completed orders can be checked in'}), 400
    if order.get('checked_in'):
        ts = order['checked_in_at'].isoformat() if order.get('checked_in_at') else 'unknown time'
        return jsonify({'error': f'Already checked in at {ts}'}), 409
    execute_db(
        'UPDATE orders SET checked_in = TRUE, checked_in_at = NOW() WHERE id = %s',
        (oid,)
    )
    _log_activity('checkin', 'event', '/scanner',
                  f'{order.get("name", "Guest")} ({order.get("email", "")}) checked in — Order #{oid}',
                  {'order_id': oid}, user_email=order.get('email', ''))
    return jsonify({'success': True, 'message': f'{order.get("name", "Guest")} checked in!'})


@app.route('/api/admin/checkin/<int:oid>/undo', methods=['POST'])
@verify_admin
def admin_checkin_undo(oid):
    """Undo a check-in."""
    execute_db(
        'UPDATE orders SET checked_in = FALSE, checked_in_at = NULL WHERE id = %s',
        (oid,)
    )
    return jsonify({'success': True, 'message': 'Check-in undone'})


@app.route('/api/admin/promos', methods=['GET'])
@verify_admin
def admin_get_promos():
    promos = query_db('SELECT * FROM promo_codes ORDER BY created_at DESC')
    for p in promos:
        for k in ['created_at', 'starts_at', 'ends_at']:
            if p.get(k):
                p[k] = p[k].isoformat()
    return jsonify(promos)

@app.route('/api/admin/promos', methods=['POST'])
@verify_admin
def admin_create_promo():
    d = request.get_json()
    code = (d.get('code') or '').strip().upper()
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    promo = execute_db(
        '''INSERT INTO promo_codes (code, discount_type, discount_amount, max_uses, starts_at, ends_at, active)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (code, d.get('discount_type', 'percent'), d.get('discount_amount', 0),
         d.get('max_uses', 0), d.get('starts_at'), d.get('ends_at'), d.get('active', True))
    )
    return jsonify(promo), 201

@app.route('/api/admin/promos/<int:pid>', methods=['PUT'])
@verify_admin
def admin_update_promo(pid):
    d = request.get_json()
    promo = execute_db(
        '''UPDATE promo_codes SET code=%s, discount_type=%s, discount_amount=%s,
           max_uses=%s, starts_at=%s, ends_at=%s, active=%s WHERE id=%s RETURNING *''',
        ((d.get('code') or '').upper(), d.get('discount_type', 'percent'), d.get('discount_amount', 0),
         d.get('max_uses', 0), d.get('starts_at'), d.get('ends_at'), d.get('active', True), pid)
    )
    return jsonify(promo)

@app.route('/api/admin/promos/<int:pid>', methods=['DELETE'])
@verify_admin
def admin_delete_promo(pid):
    execute_db('DELETE FROM promo_codes WHERE id = %s', (pid,))
    return jsonify({'deleted': True})


@app.route('/api/admin/sponsors', methods=['GET'])
@verify_admin
def admin_get_sponsors():
    sponsors = query_db('SELECT * FROM sponsor_requests ORDER BY created_at DESC')
    for s in sponsors:
        for k in ['created_at', 'deck_token_expires']:
            if s.get(k):
                s[k] = s[k].isoformat()
    return jsonify(sponsors)

@app.route('/api/admin/sponsors/<int:sid>/approve', methods=['POST'])
@verify_admin
def admin_approve_sponsor(sid):
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    sponsor = execute_db(
        'UPDATE sponsor_requests SET status=%s, deck_token=%s, deck_token_expires=%s WHERE id=%s RETURNING *',
        ('approved', token, expires, sid)
    )
    return jsonify({'sponsor': sponsor, 'deck_url': f'/deck?token={token}'})

@app.route('/api/admin/sponsors/<int:sid>/deny', methods=['POST'])
@verify_admin
def admin_deny_sponsor(sid):
    sponsor = execute_db('UPDATE sponsor_requests SET status=%s WHERE id=%s RETURNING *', ('denied', sid))
    return jsonify(sponsor)

@app.route('/api/sponsors/request', methods=['POST'])
def sponsor_request():
    d = request.get_json()
    if not d.get('company') or not d.get('email') or not d.get('contact_name'):
        return jsonify({'error': 'Company, contact name, and email are required'}), 400
    sr = execute_db(
        'INSERT INTO sponsor_requests (company, contact_name, email, phone, message) VALUES (%s, %s, %s, %s, %s) RETURNING *',
        (d['company'], d['contact_name'], d['email'], d.get('phone', ''), d.get('message', ''))
    )
    return jsonify({'success': True, 'id': sr['id']}), 201

@app.route('/api/sponsors/deck-access', methods=['GET'])
def check_deck_access():
    token = request.args.get('token', '')
    if not token:
        return jsonify({'error': 'Token required'}), 400
    sr = query_db(
        'SELECT * FROM sponsor_requests WHERE deck_token = %s AND status = %s',
        (token, 'approved'), one=True
    )
    if not sr:
        return jsonify({'error': 'Invalid or expired token'}), 403
    if sr['deck_token_expires'] and datetime.now(timezone.utc) > sr['deck_token_expires']:
        return jsonify({'error': 'Token has expired'}), 403
    return jsonify({'access': True, 'company': sr['company']})


@app.route('/api/admin/invoices', methods=['GET'])
@verify_admin
def admin_get_invoices():
    invoices = query_db('SELECT * FROM invoices ORDER BY created_at DESC')
    for inv in invoices:
        for k in ['created_at', 'due_date']:
            if inv.get(k):
                inv[k] = inv[k].isoformat() if hasattr(inv[k], 'isoformat') else str(inv[k])
    return jsonify(invoices)

@app.route('/api/admin/invoices', methods=['POST'])
@verify_admin
def admin_create_invoice():
    d = request.get_json()
    view_token = secrets.token_urlsafe(24)
    inv = execute_db(
        '''INSERT INTO invoices (sponsor_request_id, recipient_name, recipient_email, company, amount_cents, description, status, due_date, view_token, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (d.get('sponsor_request_id'), d['recipient_name'], d['recipient_email'],
         d.get('company', ''), d['amount_cents'], d.get('description', ''),
         d.get('status', 'draft'), d.get('due_date'), view_token, d.get('notes', ''))
    )
    return jsonify(inv), 201

@app.route('/api/admin/invoices/<int:iid>', methods=['PUT'])
@verify_admin
def admin_update_invoice(iid):
    d = request.get_json()
    inv = execute_db(
        '''UPDATE invoices SET recipient_name=%s, recipient_email=%s, company=%s,
           amount_cents=%s, description=%s, status=%s, due_date=%s, notes=%s WHERE id=%s RETURNING *''',
        (d['recipient_name'], d['recipient_email'], d.get('company', ''),
         d['amount_cents'], d.get('description', ''), d.get('status', 'draft'),
         d.get('due_date'), d.get('notes', ''), iid)
    )
    return jsonify(inv)

@app.route('/api/admin/invoices/<int:iid>/send', methods=['POST'])
@verify_admin
def admin_send_invoice(iid):
    inv = execute_db('UPDATE invoices SET status=%s WHERE id=%s RETURNING *', ('sent', iid))
    if inv and inv.get('recipient_email'):
        base_url = request.host_url.rstrip('/')
        send_email(inv['recipient_email'], 'invoice_notification', {
            'recipient_name': inv.get('recipient_name', ''),
            'amount': f'${inv["amount_cents"] / 100:.2f}',
            'description': inv.get('description', ''),
            'due_date': inv['due_date'].strftime('%B %d, %Y') if hasattr(inv.get('due_date'), 'strftime') else str(inv.get('due_date', '')),
            'invoice_url': f'{base_url}/invoice?token={inv["view_token"]}',
        })
    return jsonify(inv)

@app.route('/api/admin/invoices/<int:iid>/upload', methods=['POST'])
@verify_admin
def admin_upload_invoice_attachment(iid):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'File type .{ext} not allowed. Use PDF, DOC, DOCX, PNG, JPG.'}), 400
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum 10MB.'}), 400
    safe_name = secure_filename(f.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(UPLOAD_FOLDER, stored_name)
    f.save(filepath)
    inv = execute_db(
        'UPDATE invoices SET attachment_filename=%s, attachment_path=%s WHERE id=%s RETURNING *',
        (safe_name, stored_name, iid)
    )
    if inv:
        for k in ['created_at', 'due_date']:
            if inv.get(k):
                inv[k] = inv[k].isoformat() if hasattr(inv[k], 'isoformat') else str(inv[k])
    return jsonify(inv)

@app.route('/api/admin/invoices/<int:iid>/attachment', methods=['DELETE'])
@verify_admin
def admin_delete_invoice_attachment(iid):
    inv = query_db('SELECT attachment_path FROM invoices WHERE id = %s', (iid,), one=True)
    if inv and inv.get('attachment_path'):
        fpath = os.path.join(UPLOAD_FOLDER, inv['attachment_path'])
        if os.path.exists(fpath):
            os.remove(fpath)
    updated = execute_db(
        'UPDATE invoices SET attachment_filename=NULL, attachment_path=NULL WHERE id=%s RETURNING *',
        (iid,)
    )
    if updated:
        for k in ['created_at', 'due_date']:
            if updated.get(k):
                updated[k] = updated[k].isoformat() if hasattr(updated[k], 'isoformat') else str(updated[k])
    return jsonify(updated)

@app.route('/api/invoices/<token>/attachment', methods=['GET'])
def download_invoice_attachment(token):
    inv = query_db('SELECT attachment_filename, attachment_path FROM invoices WHERE view_token = %s', (token,), one=True)
    if not inv or not inv.get('attachment_path'):
        return jsonify({'error': 'No attachment found'}), 404
    return send_from_directory(UPLOAD_FOLDER, inv['attachment_path'],
                               download_name=inv['attachment_filename'],
                               as_attachment=True)

@app.route('/api/admin/invoices/<int:iid>/download', methods=['GET'])
@verify_admin
def admin_download_attachment(iid):
    inv = query_db('SELECT attachment_filename, attachment_path FROM invoices WHERE id = %s', (iid,), one=True)
    if not inv or not inv.get('attachment_path'):
        return jsonify({'error': 'No attachment found'}), 404
    return send_from_directory(UPLOAD_FOLDER, inv['attachment_path'],
                               download_name=inv['attachment_filename'],
                               as_attachment=True)

@app.route('/api/invoices/<token>', methods=['GET'])
def view_invoice(token):
    inv = query_db('SELECT * FROM invoices WHERE view_token = %s', (token,), one=True)
    if not inv:
        return jsonify({'error': 'Invoice not found'}), 404
    for k in ['created_at', 'due_date']:
        if inv.get(k):
            inv[k] = inv[k].isoformat() if hasattr(inv[k], 'isoformat') else str(inv[k])
    inv.pop('attachment_path', None)
    return jsonify(inv)


@app.route('/api/admin/users', methods=['GET'])
@verify_admin
def admin_get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    q = request.args.get('q', '').strip()
    per_page = min(per_page, 200)
    where = ''
    params = []
    if q:
        where = "WHERE LOWER(name) LIKE %s OR LOWER(email) LIKE %s OR firebase_uid ILIKE %s"
        like = f'%{q.lower()}%'
        params = [like, like, like]
    total = query_db(f'SELECT COUNT(*) AS cnt FROM users {where}', params, one=True)
    total = total['cnt'] if total else 0
    offset = (page - 1) * per_page
    rows = query_db(
        f'SELECT id, firebase_uid, email, name, is_admin, created_at FROM users {where} ORDER BY created_at DESC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    for r in rows:
        if r.get('created_at'):
            r['created_at'] = r['created_at'].isoformat()
        oc = query_db('SELECT COUNT(*) as cnt FROM orders WHERE LOWER(email) = LOWER(%s)', (r['email'],), one=True) if r.get('email') else None
        r['order_count'] = oc['cnt'] if oc else 0
    # Also find unique order emails not in users table
    guest_q = ''
    guest_params = []
    if q:
        guest_q = "AND (LOWER(o.name) LIKE %s OR LOWER(o.email) LIKE %s)"
        guest_params = [like, like]
    guests = query_db(
        f"""SELECT o.email, o.name, COUNT(*) as order_count, MIN(o.created_at) as first_order, MAX(o.created_at) as last_order
            FROM orders o
            WHERE o.email IS NOT NULL AND o.email != ''
              AND NOT EXISTS (SELECT 1 FROM users u WHERE LOWER(u.email) = LOWER(o.email))
              {guest_q}
            GROUP BY LOWER(o.email), o.email, o.name
            ORDER BY MAX(o.created_at) DESC""",
        guest_params
    )
    for g in guests:
        for k in ['first_order', 'last_order']:
            if g.get(k):
                g[k] = g[k].isoformat()
    return jsonify({'users': rows, 'total': total, 'page': page, 'per_page': per_page, 'guests': guests or []})


@app.route('/api/admin/admins', methods=['GET'])
@verify_admin
def admin_get_admins():
    admins = query_db('SELECT id, email, name, is_admin, created_at FROM users WHERE is_admin = TRUE ORDER BY created_at')
    for a in admins:
        if a.get('created_at'):
            a['created_at'] = a['created_at'].isoformat()
    invites = query_db('SELECT * FROM admin_invites WHERE used_at IS NULL ORDER BY created_at DESC')
    for i in invites:
        for k in ['created_at', 'expires_at']:
            if i.get(k):
                i[k] = i[k].isoformat()
    return jsonify({'admins': admins, 'invites': invites})

@app.route('/api/admin/admins/invite', methods=['POST'])
@verify_admin
def admin_invite_admin():
    d = request.get_json()
    email = (d.get('email') or '').strip().lower()
    if not email:
        return jsonify({'error': 'Email required'}), 400
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    invite = execute_db(
        'INSERT INTO admin_invites (email, token, expires_at, created_by) VALUES (%s, %s, %s, %s) RETURNING *',
        (email, token, expires, request.admin_user['id'])
    )
    return jsonify(invite), 201

@app.route('/api/admin/admins/<int:uid>/remove', methods=['POST'])
@verify_admin
def admin_remove_admin(uid):
    if uid == request.admin_user['id']:
        return jsonify({'error': 'Cannot remove yourself'}), 400
    execute_db('UPDATE users SET is_admin = FALSE WHERE id = %s', (uid,))
    return jsonify({'removed': True})


@app.route('/api/admin/purchase-links', methods=['GET'])
@verify_admin
def admin_get_purchase_links():
    links = query_db('''
        SELECT pl.*, tt.name as tier_name
        FROM purchase_links pl LEFT JOIN ticket_tiers tt ON pl.tier_id = tt.id
        ORDER BY pl.created_at DESC
    ''')
    for l in links:
        for k in ['created_at', 'expires_at', 'used_at']:
            if l.get(k):
                l[k] = l[k].isoformat()
    return jsonify(links)

@app.route('/api/admin/purchase-links', methods=['POST'])
@verify_admin
def admin_create_purchase_link():
    d = request.get_json()
    token = secrets.token_urlsafe(24)
    expires = datetime.now(timezone.utc) + timedelta(days=int(d.get('expires_days', 7)))
    link = execute_db(
        'INSERT INTO purchase_links (token, email, tier_id, qty, promo_code, expires_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *',
        (token, d.get('email', ''), d.get('tier_id'), d.get('qty', 1), d.get('promo_code'), expires)
    )
    return jsonify({'link': link, 'url': f'/tickets.html?invite={token}'}), 201

@app.route('/api/purchase-links/<token>', methods=['GET'])
def get_purchase_link(token):
    link = query_db('SELECT pl.*, tt.name as tier_name, tt.price_cents FROM purchase_links pl LEFT JOIN ticket_tiers tt ON pl.tier_id = tt.id WHERE pl.token = %s', (token,), one=True)
    if not link:
        return jsonify({'error': 'Invalid link'}), 404
    if link.get('used_at'):
        return jsonify({'error': 'This link has already been used'}), 400
    if link.get('expires_at') and datetime.now(timezone.utc) > link['expires_at']:
        return jsonify({'error': 'This link has expired'}), 400
    return jsonify({
        'email': link['email'],
        'tier_name': link['tier_name'],
        'tier_id': link['tier_id'],
        'price_cents': link['price_cents'],
        'qty': link['qty'],
        'promo_code': link.get('promo_code')
    })


@app.route('/api/admin/stats', methods=['GET'])
@verify_admin
def admin_stats():
    total_orders = query_db('SELECT COUNT(*) as cnt, COALESCE(SUM(total_cents), 0) as revenue FROM orders', one=True)
    total_tickets = query_db('SELECT COALESCE(SUM(qty), 0) as cnt FROM order_items', one=True)
    tier_stats = query_db('SELECT name, sold, capacity FROM ticket_tiers WHERE active = TRUE ORDER BY sort_order')
    pending_sponsors = query_db("SELECT COUNT(*) as cnt FROM sponsor_requests WHERE status = 'pending'", one=True)
    pending_invoices = query_db("SELECT COUNT(*) as cnt, COALESCE(SUM(amount_cents), 0) as total FROM invoices WHERE status IN ('draft', 'sent')", one=True)

    # Analytics summary (last 7 days)
    an = query_db('''
        SELECT COUNT(*) AS views,
               COUNT(DISTINCT session_id) AS sessions,
               AVG(duration_ms) AS avg_dur
        FROM page_views
        WHERE created_at >= NOW() - INTERVAL '7 days'
    ''', one=True) or {}
    views_7d = an.get('views') or 0
    sessions_7d = an.get('sessions') or 0
    avg_dur_7d = an.get('avg_dur') or 0

    # Bounce rate
    bounce = query_db('''
        SELECT COUNT(*) FILTER (WHERE cnt = 1) AS bounces, COUNT(*) AS total
        FROM (SELECT session_id, COUNT(*) AS cnt FROM page_views
              WHERE created_at >= NOW() - INTERVAL '7 days'
                AND session_id IS NOT NULL AND session_id != ''
              GROUP BY session_id) s
    ''', one=True) or {}
    bounce_rate = round(bounce['bounces'] / bounce['total'] * 100, 1) if bounce.get('total') else 0

    # Top 5 pages
    top_pages = query_db('''
        SELECT page, COUNT(*) AS views
        FROM page_views
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY page ORDER BY views DESC LIMIT 5
    ''')

    # Today vs yesterday
    today_views = query_db("SELECT COUNT(*) AS c FROM page_views WHERE created_at::date = CURRENT_DATE", one=True)
    yesterday_views = query_db("SELECT COUNT(*) AS c FROM page_views WHERE created_at::date = CURRENT_DATE - 1", one=True)

    # Live count
    live = query_db("""
        SELECT COUNT(DISTINCT session_id) AS c FROM page_views
        WHERE created_at >= NOW() - INTERVAL '5 minutes'
    """, one=True)

    return jsonify({
        'orders': total_orders['cnt'],
        'revenue': total_orders['revenue'],
        'tickets_sold': total_tickets['cnt'],
        'tiers': tier_stats,
        'pending_sponsors': pending_sponsors['cnt'],
        'pending_invoices': pending_invoices['cnt'],
        'outstanding_invoice_total': pending_invoices['total'],
        'analytics': {
            'views_7d': views_7d,
            'sessions_7d': sessions_7d,
            'bounce_rate': bounce_rate,
            'avg_duration_ms': float(avg_dur_7d) if avg_dur_7d else 0,
            'top_pages': top_pages,
            'today_views': today_views['c'] if today_views else 0,
            'yesterday_views': yesterday_views['c'] if yesterday_views else 0,
            'live_now': live['c'] if live else 0,
        }
    })


@app.route('/api/admin/email-templates', methods=['GET'])
@verify_admin
def admin_get_email_templates():
    templates = query_db('SELECT * FROM email_templates ORDER BY id')
    for t in templates:
        if t.get('updated_at') and hasattr(t['updated_at'], 'isoformat'):
            t['updated_at'] = t['updated_at'].isoformat()
        if t.get('created_at') and hasattr(t['created_at'], 'isoformat'):
            t['created_at'] = t['created_at'].isoformat()
    return jsonify(templates)

@app.route('/api/admin/email-templates/<int:tid>', methods=['PUT'])
@verify_admin
def admin_update_email_template(tid):
    data = request.get_json()
    tmpl = execute_db(
        'UPDATE email_templates SET subject=%s, html_body=%s, updated_at=NOW() WHERE id=%s RETURNING *',
        (data.get('subject', ''), data.get('html_body', ''), tid)
    )
    if not tmpl:
        return jsonify({'error': 'Template not found'}), 404
    return jsonify(tmpl)

@app.route('/api/admin/email-templates/<int:tid>/reset', methods=['POST'])
@verify_admin
def admin_reset_email_template(tid):
    from email_templates import DEFAULT_TEMPLATES
    tmpl = query_db('SELECT slug FROM email_templates WHERE id = %s', (tid,), one=True)
    if not tmpl:
        return jsonify({'error': 'Template not found'}), 404
    default = next((t for t in DEFAULT_TEMPLATES if t['slug'] == tmpl['slug']), None)
    if not default:
        return jsonify({'error': 'No default template available'}), 404
    updated = execute_db(
        'UPDATE email_templates SET subject=%s, html_body=%s, updated_at=NOW() WHERE id=%s RETURNING *',
        (default['subject'], default['html_body'], tid)
    )
    return jsonify(updated)

@app.route('/api/admin/email-templates/<int:tid>/test', methods=['POST'])
@verify_admin
def admin_test_email_template(tid):
    data = request.get_json()
    test_email = data.get('email', request.admin_user.get('email', ''))
    if not test_email:
        return jsonify({'error': 'No email provided'}), 400
    tmpl = query_db('SELECT * FROM email_templates WHERE id = %s', (tid,), one=True)
    if not tmpl:
        return jsonify({'error': 'Template not found'}), 404
    sample_vars = {
        'buyer_name': 'John Doe', 'order_id': '12345',
        'order_items': '<tr><td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#ffffff;">VIP Ringside</td><td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#ffffff;text-align:center;">2</td><td style="padding:10px 12px;border-bottom:1px solid #2a2a2a;color:#d4a843;text-align:right;">$240.00</td></tr>',
        'subtotal': '$240.00', 'discount': '$0.00', 'total': '$240.00',
        'receipt_url': '#', 'payment_id': 'TEST-abc123',
        'user_name': 'John Doe', 'user_email': test_email,
        'status': 'confirmed',
        'recipient_name': 'Jane Smith', 'amount': '$500.00',
        'description': 'Sponsorship Package', 'due_date': 'March 15, 2026',
        'invoice_url': '#',
    }
    subject = tmpl['subject']
    html = tmpl['html_body']
    for key, val in sample_vars.items():
        subject = subject.replace('{{' + key + '}}', str(val))
        html = html.replace('{{' + key + '}}', str(val))
    try:
        resend.Emails.send({
            'from': RESEND_FROM_EMAIL,
            'to': [test_email],
            'subject': '[TEST] ' + subject,
            'html': html,
        })
        return jsonify({'success': True, 'message': f'Test email sent to {test_email}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


# ─── Analytics & Activity Log ────────────────────────────────

def _log_activity(event_type, category='general', page='', detail='', meta=None,
                  user_email='', user_name='', session_id='', ip_addr='', device_type='', browser='', os_name=''):
    """Insert a row into the activity_log table."""
    import json as _json
    try:
        execute_db(
            '''INSERT INTO activity_log
               (session_id, event_type, category, page, detail, meta, user_email, user_name, ip_addr, device_type, browser, os)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (session_id[:64], event_type[:50], category[:30], page[:200], detail[:1000],
             _json.dumps(meta or {}), user_email[:200], user_name[:100], ip_addr[:45], device_type[:20], browser[:50], os_name[:50])
        )
    except Exception as e:
        print(f"[ACTIVITY LOG] {e}")


@app.route('/api/track', methods=['POST'])
def track_pageview():
    """Lightweight, public endpoint for recording page views + events."""
    d = request.get_json(silent=True) or {}
    session_id = (d.get('sid') or '')[:64]
    page = (d.get('page') or '')[:200]
    event = (d.get('event') or '')[:50]  # optional event type

    # Detect IP for logging (never stored in page_views)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()

    device_type = (d.get('dt') or '')[:20]
    browser = (d.get('br') or '')[:50]
    os_name = (d.get('os') or '')[:50]
    user_name = (d.get('un') or '')[:100]
    user_email = (d.get('ue') or '')[:200]

    # ── Activity log events (clicks, errors, conversions) ──
    if event:
        _log_activity(
            event_type=event,
            category=(d.get('cat') or 'interaction')[:30],
            page=page,
            detail=(d.get('detail') or '')[:1000],
            meta=d.get('meta') if isinstance(d.get('meta'), dict) else {},
            session_id=session_id,
            user_email=user_email,
            user_name=user_name,
            ip_addr=ip,
            device_type=device_type,
            browser=browser,
            os_name=os_name,
        )
        return jsonify({'ok': True})

    # ── Page view tracking ──
    if not session_id or not page:
        return jsonify({'ok': True})

    referrer = (d.get('ref') or '')[:500]
    utm_source = (d.get('us') or '')[:100]
    utm_medium = (d.get('um') or '')[:100]
    utm_campaign = (d.get('uc') or '')[:100]
    screen_w = min(int(d.get('sw') or 0), 9999)
    duration = min(int(d.get('dur') or 0), 3600000)
    is_update = d.get('update')  # if True, UPDATE existing row instead of INSERT

    try:
        if is_update:
            # Update duration on an existing row for this session+page
            execute_db(
                '''UPDATE page_views SET duration_ms = %s, user_name = COALESCE(NULLIF(%s, ''), user_name), user_email = COALESCE(NULLIF(%s, ''), user_email)
                   WHERE id = (SELECT id FROM page_views WHERE session_id = %s AND page = %s ORDER BY created_at DESC LIMIT 1)''',
                (duration, user_name, user_email, session_id, page)
            )
        else:
            execute_db(
                '''INSERT INTO page_views (session_id, page, referrer, utm_source, utm_medium, utm_campaign,
                   device_type, browser, os, screen_width, duration_ms, user_name, user_email)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (session_id, page, referrer, utm_source, utm_medium, utm_campaign,
                 device_type, browser, os_name, screen_w, duration, user_name, user_email)
            )
            # Also log as activity
            _log_activity('pageview', 'navigation', page, f'Viewed {page}',
                          {'referrer': referrer, 'utm_source': utm_source, 'screen_width': screen_w},
                          user_email=user_email, user_name=user_name,
                          session_id=session_id, ip_addr=ip, device_type=device_type, browser=browser, os_name=os_name)
    except Exception as e:
        print(f"[TRACK] {e}")
    return jsonify({'ok': True})


@app.route('/api/admin/analytics', methods=['GET'])
@verify_admin
def admin_analytics():
    """Return comprehensive analytics data for the admin dashboard."""
    days = min(int(request.args.get('days', 30)), 365)
    since = f"NOW() - INTERVAL '{days} days'"

    # Total views & unique sessions
    totals = query_db(f'''
        SELECT COUNT(*) as total_views, COUNT(DISTINCT session_id) as unique_sessions
        FROM page_views WHERE created_at >= {since}
    ''', one=True) or {}

    # Views per day
    daily = query_db(f'''
        SELECT DATE(created_at) as date, COUNT(*) as views, COUNT(DISTINCT session_id) as sessions
        FROM page_views WHERE created_at >= {since}
        GROUP BY DATE(created_at) ORDER BY date
    ''')
    for r in daily:
        r['date'] = r['date'].isoformat() if hasattr(r['date'], 'isoformat') else str(r['date'])

    # Top pages
    pages = query_db(f'''
        SELECT page, COUNT(*) as views, COUNT(DISTINCT session_id) as sessions
        FROM page_views WHERE created_at >= {since}
        GROUP BY page ORDER BY views DESC LIMIT 20
    ''')

    # Top referrers (exclude empty and self)
    referrers = query_db(f'''
        SELECT referrer, COUNT(*) as views, COUNT(DISTINCT session_id) as sessions
        FROM page_views WHERE created_at >= {since} AND referrer != '' AND referrer NOT LIKE '%%cannagrudge%%'
        GROUP BY referrer ORDER BY views DESC LIMIT 20
    ''')

    # UTM sources
    utm = query_db(f'''
        SELECT utm_source as source, utm_medium as medium, utm_campaign as campaign,
               COUNT(*) as views, COUNT(DISTINCT session_id) as sessions
        FROM page_views WHERE created_at >= {since} AND utm_source != ''
        GROUP BY utm_source, utm_medium, utm_campaign ORDER BY views DESC LIMIT 20
    ''')

    # Device types
    devices = query_db(f'''
        SELECT device_type, COUNT(*) as count
        FROM page_views WHERE created_at >= {since} AND device_type != ''
        GROUP BY device_type ORDER BY count DESC
    ''')

    # Browsers
    browsers = query_db(f'''
        SELECT browser, COUNT(*) as count
        FROM page_views WHERE created_at >= {since} AND browser != ''
        GROUP BY browser ORDER BY count DESC LIMIT 10
    ''')

    # OS
    os_list = query_db(f'''
        SELECT os, COUNT(*) as count
        FROM page_views WHERE created_at >= {since} AND os != ''
        GROUP BY os ORDER BY count DESC LIMIT 10
    ''')

    # Screen widths (bucketed)
    screens = query_db(f'''
        SELECT
          CASE
            WHEN screen_width < 576 THEN 'XS (<576)'
            WHEN screen_width < 768 THEN 'SM (576-767)'
            WHEN screen_width < 992 THEN 'MD (768-991)'
            WHEN screen_width < 1200 THEN 'LG (992-1199)'
            ELSE 'XL (1200+)'
          END as bucket,
          COUNT(*) as count
        FROM page_views WHERE created_at >= {since} AND screen_width > 0
        GROUP BY bucket ORDER BY count DESC
    ''')

    # Hourly heatmap (hour of day)
    hourly = query_db(f'''
        SELECT EXTRACT(HOUR FROM created_at)::int as hour, COUNT(*) as views
        FROM page_views WHERE created_at >= {since}
        GROUP BY hour ORDER BY hour
    ''')
    # Fill missing hours
    hour_map = {r['hour']: r['views'] for r in hourly}
    hourly_full = [{'hour': h, 'views': hour_map.get(h, 0)} for h in range(24)]

    # Avg session duration
    avg_dur = query_db(f'''
        SELECT ROUND(AVG(duration_ms)) as avg_ms
        FROM page_views WHERE created_at >= {since} AND duration_ms > 0
    ''', one=True)

    # Bounce rate (sessions with only 1 page view)
    bounce = query_db(f'''
        SELECT
            COUNT(*) FILTER (WHERE pv_count = 1) as bounced,
            COUNT(*) as total
        FROM (
            SELECT session_id, COUNT(*) as pv_count
            FROM page_views WHERE created_at >= {since}
            GROUP BY session_id
        ) sub
    ''', one=True) or {}

    # Pages per session (avg)
    pps = query_db(f'''
        SELECT ROUND(AVG(pv_count)::numeric, 1) as avg_pps FROM (
            SELECT session_id, COUNT(*) as pv_count
            FROM page_views WHERE created_at >= {since}
            GROUP BY session_id
        ) sub
    ''', one=True) or {}

    # New vs returning sessions (sessions seen before the time range)
    new_ret = query_db(f'''
        SELECT
            COUNT(*) FILTER (WHERE first_seen >= {since}) as new_sessions,
            COUNT(*) FILTER (WHERE first_seen < {since}) as returning_sessions
        FROM (
            SELECT session_id, MIN(created_at) as first_seen
            FROM page_views GROUP BY session_id
        ) sub
        WHERE session_id IN (SELECT DISTINCT session_id FROM page_views WHERE created_at >= {since})
    ''', one=True) or {}

    # Top entry pages (first page of each session)
    entry_pages = query_db(f'''
        SELECT page, COUNT(*) as count FROM (
            SELECT DISTINCT ON (session_id) session_id, page
            FROM page_views WHERE created_at >= {since}
            ORDER BY session_id, created_at ASC
        ) sub GROUP BY page ORDER BY count DESC LIMIT 10
    ''')

    # Top exit pages (last page of each session with duration > 0)
    exit_pages = query_db(f'''
        SELECT page, COUNT(*) as count FROM (
            SELECT DISTINCT ON (session_id) session_id, page
            FROM page_views WHERE created_at >= {since}
            ORDER BY session_id, created_at DESC
        ) sub GROUP BY page ORDER BY count DESC LIMIT 10
    ''')

    return jsonify({
        'total_views': totals.get('total_views', 0),
        'unique_sessions': totals.get('unique_sessions', 0),
        'bounce_rate': round(bounce['bounced'] / bounce['total'] * 100, 1) if bounce.get('total') else 0,
        'avg_duration_ms': int(avg_dur['avg_ms'] or 0) if avg_dur and avg_dur.get('avg_ms') else 0,
        'pages_per_session': float(pps.get('avg_pps') or 0),
        'new_sessions': new_ret.get('new_sessions', 0),
        'returning_sessions': new_ret.get('returning_sessions', 0),
        'daily': daily,
        'pages': pages,
        'referrers': referrers,
        'utm_sources': utm,
        'devices': devices,
        'browsers': browsers,
        'os_list': os_list,
        'screens': screens,
        'hourly': hourly_full,
        'entry_pages': entry_pages,
        'exit_pages': exit_pages,
    })


@app.route('/api/admin/activity-log', methods=['GET'])
@verify_admin
def admin_activity_log():
    """Return paginated activity log with filters."""
    page_num = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page_num - 1) * per_page
    category = (request.args.get('category') or '').strip()
    event_type = (request.args.get('event_type') or '').strip()
    search = (request.args.get('q') or '').strip()

    where_clauses = []
    params = []
    if category:
        where_clauses.append('category = %s')
        params.append(category)
    if event_type:
        where_clauses.append('event_type = %s')
        params.append(event_type)
    if search:
        where_clauses.append("(detail ILIKE %s OR page ILIKE %s OR user_email ILIKE %s OR user_name ILIKE %s OR event_type ILIKE %s)")
        params.extend([f'%{search}%'] * 5)

    where = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    total = query_db(
        f'SELECT COUNT(*) as cnt FROM activity_log {where}', params, one=True
    )

    rows = query_db(
        f'''SELECT id, session_id, event_type, category, page, detail, meta,
                   user_email, user_name, ip_addr, device_type, browser, os, created_at
            FROM activity_log {where}
            ORDER BY created_at DESC LIMIT %s OFFSET %s''',
        params + [per_page, offset]
    )
    for r in rows:
        if r.get('created_at'):
            r['created_at'] = r['created_at'].isoformat()
        if isinstance(r.get('meta'), str):
            import json as _json
            try:
                r['meta'] = _json.loads(r['meta'])
            except Exception:
                pass

    # Get distinct categories and event types for filter dropdowns
    categories = query_db('SELECT DISTINCT category FROM activity_log ORDER BY category')
    event_types = query_db('SELECT DISTINCT event_type FROM activity_log ORDER BY event_type')

    return jsonify({
        'rows': rows,
        'total': total['cnt'] if total else 0,
        'page': page_num,
        'per_page': per_page,
        'categories': [c['category'] for c in categories],
        'event_types': [e['event_type'] for e in event_types],
    })


@app.route('/api/admin/error-report', methods=['GET'])
@verify_admin
def admin_error_report():
    """Return recent errors grouped by type, plus individual error rows."""
    days = min(int(request.args.get('days', 7)), 90)

    # Summary: count of errors by event_type
    summary = query_db('''
        SELECT event_type, COUNT(*) AS cnt,
               MAX(created_at) AS last_seen
        FROM activity_log
        WHERE category = 'error' AND created_at >= NOW() - INTERVAL '%s days'
        GROUP BY event_type ORDER BY cnt DESC
    ''' % days)
    for s in summary:
        if s.get('last_seen') and hasattr(s['last_seen'], 'isoformat'):
            s['last_seen'] = s['last_seen'].isoformat()

    total_errors = sum(s['cnt'] for s in summary) if summary else 0

    # Recent error rows (most recent 100)
    rows = query_db('''
        SELECT id, session_id, event_type, page, detail, meta,
               user_email, user_name, device_type, browser, os, created_at
        FROM activity_log
        WHERE category = 'error' AND created_at >= NOW() - INTERVAL '%s days'
        ORDER BY created_at DESC LIMIT 100
    ''' % days)
    for r in rows:
        if r.get('created_at') and hasattr(r['created_at'], 'isoformat'):
            r['created_at'] = r['created_at'].isoformat()
        if isinstance(r.get('meta'), str):
            import json as _json
            try:
                r['meta'] = _json.loads(r['meta'])
            except Exception:
                pass

    return jsonify({
        'total_errors': total_errors,
        'summary': summary,
        'rows': rows,
        'days': days,
    })


@app.route('/api/admin/live-visitors', methods=['GET'])
@verify_admin
def admin_live_visitors():
    """Return sessions active in the last 5 minutes with current page + time on page."""
    rows = query_db('''
        SELECT DISTINCT ON (session_id)
            session_id, page, device_type, browser, os, referrer,
            duration_ms, created_at, user_name, user_email,
            EXTRACT(EPOCH FROM (NOW() - created_at))::int AS seconds_ago
        FROM page_views
        WHERE created_at >= NOW() - INTERVAL '5 minutes'
        ORDER BY session_id, created_at DESC
    ''')
    visitors = []
    for r in rows:
        if r.get('created_at') and hasattr(r['created_at'], 'isoformat'):
            r['created_at'] = r['created_at'].isoformat()
        visitors.append(r)
    return jsonify({'count': len(visitors), 'visitors': visitors})


@app.route('/api/admin/active-sessions', methods=['GET'])
@verify_admin
def admin_active_sessions():
    """Return recent sessions with all their page visits and durations (last 24h)."""
    limit = min(int(request.args.get('limit', 30)), 100)
    sessions = query_db('''
        WITH recent_sessions AS (
            SELECT session_id, MAX(created_at) AS last_seen,
                   MIN(created_at) AS first_seen,
                   COUNT(*) AS page_count,
                   SUM(COALESCE(duration_ms, 0)) AS total_duration_ms
            FROM page_views
            WHERE created_at >= NOW() - INTERVAL '24 hours'
              AND session_id IS NOT NULL AND session_id != ''
            GROUP BY session_id
            ORDER BY last_seen DESC
            LIMIT %s
        )
        SELECT rs.session_id, rs.last_seen, rs.first_seen,
               rs.page_count, rs.total_duration_ms,
               pv.page, pv.duration_ms, pv.device_type, pv.browser, pv.os,
               pv.referrer, pv.user_name, pv.user_email, pv.created_at AS page_at
        FROM recent_sessions rs
        JOIN page_views pv ON pv.session_id = rs.session_id
             AND pv.created_at >= NOW() - INTERVAL '24 hours'
        ORDER BY rs.last_seen DESC, pv.created_at ASC
    ''', (limit,))

    # Group into session objects
    session_map = {}
    for r in sessions:
        sid = r['session_id']
        if sid not in session_map:
            session_map[sid] = {
                'session_id': sid,
                'first_seen': r['first_seen'].isoformat() if hasattr(r.get('first_seen', ''), 'isoformat') else r.get('first_seen', ''),
                'last_seen': r['last_seen'].isoformat() if hasattr(r.get('last_seen', ''), 'isoformat') else r.get('last_seen', ''),
                'page_count': r['page_count'],
                'total_duration_ms': r['total_duration_ms'] or 0,
                'device_type': r.get('device_type', ''),
                'browser': r.get('browser', ''),
                'os': r.get('os', ''),
                'referrer': r.get('referrer', ''),
                'user_name': '',
                'user_email': '',
                'pages': []
            }
        # Keep the most recent non-empty user_name/email
        if r.get('user_name') and not session_map[sid]['user_name']:
            session_map[sid]['user_name'] = r['user_name']
        if r.get('user_email') and not session_map[sid]['user_email']:
            session_map[sid]['user_email'] = r['user_email']
        page_at = r.get('page_at', '')
        if hasattr(page_at, 'isoformat'):
            page_at = page_at.isoformat()
        session_map[sid]['pages'].append({
            'page': r.get('page', ''),
            'duration_ms': r.get('duration_ms') or 0,
            'at': page_at
        })

    return jsonify(list(session_map.values()))
