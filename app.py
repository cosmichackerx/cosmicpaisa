from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import base64

app = Flask(__name__)

# Configure Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/spin', methods=['POST'])
def spin_wheel():
    try:
        phone_number = request.form['phone_number']
        
        # Validate phone number
        if not phone_number.isdigit() or len(phone_number) != 11:
            return jsonify({'error': 'Invalid phone number. Use 11 digits (e.g., 03367307471).'}), 400

        # Step 1: Initialize session
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://my.ptcl.net.pk/SpinTheWheel/Default.aspx"
        }

        # Step 2: Load form page
        url_form = "https://my.ptcl.net.pk/SpinTheWheel/Default.aspx"
        response = session.get(url_form, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        viewstate = soup.find("input", {"id": "__VIEWSTATE"})["value"]
        event_validation = soup.find("input", {"id": "__EVENTVALIDATION"})["value"]
        viewstate_generator = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})["value"]

        # Step 3: Download CAPTCHA
        captcha_url = "https://my.ptcl.net.pk/SpinTheWheel/Captcha.aspx"
        captcha_response = session.get(captcha_url, headers=headers)
        captcha_img = Image.open(BytesIO(captcha_response.content))
        
        # Convert CAPTCHA to base64 for frontend display
        buffered = BytesIO()
        captcha_img.save(buffered, format="PNG")
        captcha_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({
            'status': 'captcha_required',
            'captcha_image': captcha_base64,
            'viewstate': viewstate,
            'event_validation': event_validation,
            'viewstate_generator': viewstate_generator,
            'session_cookies': dict(session.cookies)
        })

    except Exception as e:
        return jsonify({'error': f'Initialization failed: {str(e)}'}), 500

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json
        phone_number = data['phone_number']
        captcha_text = data['captcha_text']
        viewstate = data['viewstate']
        event_validation = data['event_validation']
        viewstate_generator = data['viewstate_generator']
        session_cookies = data['session_cookies']

        # Recreate session
        session = requests.Session()
        session.cookies.update(session_cookies)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://my.ptcl.net.pk/SpinTheWheel/Default.aspx"
        }

        # Submit form
        url_form = "https://my.ptcl.net.pk/SpinTheWheel/Default.aspx"
        form_data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_generator,
            "__EVENTVALIDATION": event_validation,
            "txtMobile": phone_number,
            "txtCaptcha": captcha_text,
            "chkTerms": "on",
            "btnNext": "Start Game"
        }

        response_form = session.post(url_form, data=form_data, headers=headers)
        if "SpinWheel.aspx" not in response_form.url:
            return jsonify({'error': 'Form submission failed. Check CAPTCHA or phone number.'}), 400

        # Spin the wheel
        spin_url = "https://my.ptcl.net.pk/SpinTheWheel/SpinWheel.aspx/SpinWheels"
        spin_headers = {
            **headers,
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }

        spin_response = session.post(spin_url, json={}, headers=spin_headers)
        if spin_response.status_code != 200:
            return jsonify({'error': 'Spin request failed.'}), 400

        reward = spin_response.json()
        return jsonify({'reward': reward})

    except Exception as e:
        return jsonify({'error': f'Submission failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
