import os
import json
import uuid
import secrets
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, auth as fb_auth

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '')

if not firebase_admin._apps:
    firebase_admin.initialize_app()

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

@app.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/assets/deck/<path:filename>')
def protected_deck_assets(filename):
    referer = request.headers.get('Referer', '')
    if 'deck.html' not in referer or 'token=' not in referer:
        return jsonify({'error': 'Access denied'}), 403
    return send_from_directory('assets/deck', filename)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/square-config', methods=['GET'])
def square_config():
    app_id = os.environ.get('SQUARE_APPLICATION_ID', '')
    loc_id = os.environ.get('SQUARE_LOCATION_ID', '')
    return jsonify({'applicationId': app_id, 'locationId': loc_id})

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
    email = data.get('email', '')
    buyer_name = data.get('name', '')
    promo_code = (data.get('promoCode') or '').strip().upper()

    total = 0
    order_line_items = []
    for item in cart_items:
        tier_id = item.get('tierId')
        tier = None
        if tier_id:
            tier = query_db('SELECT * FROM ticket_tiers WHERE id = %s AND active = TRUE', (tier_id,), one=True)
        if not tier:
            item_id = item.get('id', '')
            if item_id:
                tier = query_db('SELECT * FROM ticket_tiers WHERE id = %s AND active = TRUE', (item_id,), one=True)
        if not tier:
            return jsonify({'error': f'Invalid ticket tier'}), 400
        price = tier['price_cents']
        qty = max(1, min(int(item.get('qty', 1)), 50))
        if tier['capacity'] > 0 and tier['sold'] + qty > tier['capacity']:
            return jsonify({'error': f'{tier["name"]} is sold out or insufficient capacity'}), 400
        line_total = price * qty
        total += line_total
        order_line_items.append({
            'tier_id': tier['id'],
            'tier_name': tier['name'],
            'qty': qty,
            'unit_price': price
        })

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

    if charge_amount > 0:
        client = Client(access_token=SQUARE_ACCESS_TOKEN, environment='production')
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
            return jsonify({'success': False, 'errors': result.errors}), 400
        payment = result.body.get('payment', {})
        payment_id = payment.get('id', '')
        receipt_url = payment.get('receipt_url', '')
    else:
        payment_id = 'FREE-' + str(uuid.uuid4())[:8]
        receipt_url = ''

    order = execute_db(
        '''INSERT INTO orders (email, name, total_cents, discount_cents, promo_code, status, square_payment_id, receipt_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (email, buyer_name, total, discount, promo_code or None, 'completed', payment_id, receipt_url)
    )

    for li in order_line_items:
        execute_db(
            'INSERT INTO order_items (order_id, ticket_tier_id, tier_name, qty, unit_price_cents) VALUES (%s, %s, %s, %s, %s)',
            (order['id'], li['tier_id'], li['tier_name'], li['qty'], li['unit_price'])
        )
        if li['tier_id']:
            execute_db('UPDATE ticket_tiers SET sold = sold + %s WHERE id = %s', (li['qty'], li['tier_id']))

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
    return jsonify({'sponsor': sponsor, 'deck_url': f'/deck.html?token={token}'})

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
    return jsonify(inv)

@app.route('/api/invoices/<token>', methods=['GET'])
def view_invoice(token):
    inv = query_db('SELECT * FROM invoices WHERE view_token = %s', (token,), one=True)
    if not inv:
        return jsonify({'error': 'Invoice not found'}), 404
    for k in ['created_at', 'due_date']:
        if inv.get(k):
            inv[k] = inv[k].isoformat() if hasattr(inv[k], 'isoformat') else str(inv[k])
    return jsonify(inv)


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
    return jsonify({
        'orders': total_orders['cnt'],
        'revenue': total_orders['revenue'],
        'tickets_sold': total_tickets['cnt'],
        'tiers': tier_stats,
        'pending_sponsors': pending_sponsors['cnt'],
        'pending_invoices': pending_invoices['cnt'],
        'outstanding_invoice_total': pending_invoices['total']
    })


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
