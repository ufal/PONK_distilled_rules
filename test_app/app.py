#!/usr/bin/env python3
"""
Dummy test app for ponk-app3.
Run on port 8000 to verify quest proxy is working.
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ponk-app3 Test</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .success { color: green; font-size: 24px; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🎉 ponk-app3 is working!</h1>
        <p class="success">✓ Flask server running on port 8000</p>
        <p class="success">✓ Quest proxy forwarding correctly</p>
        <hr>
        <h3>Test endpoints:</h3>
        <ul>
            <li><a href="/api/health">/api/health</a> - JSON health check</li>
            <li><a href="/api/echo">/api/echo</a> - Echo test (POST)</li>
        </ul>
    </body>
    </html>
    '''

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'app': 'ponk-app3',
        'port': 8000
    })

@app.route('/api/echo', methods=['GET', 'POST'])
def echo():
    if request.method == 'POST':
        return jsonify({
            'received': request.get_json(force=True, silent=True) or request.data.decode()
        })
    return jsonify({'message': 'Send a POST request to echo data back'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
