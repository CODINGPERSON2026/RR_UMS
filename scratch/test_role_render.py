import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from flask import render_template

with app.test_request_context():
    for r in ['CO', '2IC', 'ADJUTANT', 'OC', 'JCO']:
        html = render_template('weight_system/home.html', role=r)
        has_header_div = '<div class="ai-fitness-header-action">' in html
        has_href = 'href="/fitness/"' in html
        print(f"Role: {r:10} | Header Action Div: {has_header_div} | Link to /fitness/: {has_href}")
