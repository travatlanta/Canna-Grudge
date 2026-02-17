import os
import json
import uuid
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder='.', static_url_path='')

SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '')

@app.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/square-config', methods=['GET'])
def square_config():
    app_id = os.environ.get('SQUARE_APPLICATION_ID', '')
    loc_id = os.environ.get('SQUARE_LOCATION_ID', '')
    return jsonify({'applicationId': app_id, 'locationId': loc_id})

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    from square.client import Client
    data = request.get_json()
    if not data or 'sourceId' not in data:
        return jsonify({'error': 'Missing payment source'}), 400

    client = Client(
        access_token=SQUARE_ACCESS_TOKEN,
        environment='production'
    )

    amount = data.get('amount', 0)
    currency = data.get('currency', 'USD')
    email = data.get('email', '')
    note = data.get('note', 'CannaGrudge Ticket Purchase')

    body = {
        'source_id': data['sourceId'],
        'idempotency_key': str(uuid.uuid4()),
        'amount_money': {
            'amount': int(amount),
            'currency': currency
        },
        'location_id': SQUARE_LOCATION_ID,
        'note': note,
    }

    if email:
        body['buyer_email_address'] = email

    result = client.payments.create_payment(body=body)

    if result.is_success():
        payment = result.body.get('payment', {})
        return jsonify({
            'success': True,
            'payment': {
                'id': payment.get('id'),
                'status': payment.get('status'),
                'amount': payment.get('amount_money', {}).get('amount'),
                'receipt_url': payment.get('receipt_url', '')
            }
        })
    else:
        errors = result.errors
        return jsonify({'success': False, 'errors': errors}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
