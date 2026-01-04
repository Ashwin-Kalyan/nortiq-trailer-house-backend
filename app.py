"""
Flask Backend for Trailer House Inquiry Form Submission
Form fields match your screenshot
CREDENTIALS PATH: /etc/secrets/credentials.json
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import time

# Try to import Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("Note: gspread not installed - Google Sheets disabled")

app = Flask(__name__)
CORS(app)

# Environment variables - GET FROM ENV VARS
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY", "")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

# CORRECT credentials file path for Render Secret Files
CREDENTIALS_FILE_PATH = "/etc/secrets/credentials.json"

# Your Vercel frontend
FRONTEND_DOMAIN = "https://nortiq-trailer-house-vercel-9afi.vercel.app"

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'service': 'Trailer House Inquiry Form Backend',
        'frontend': FRONTEND_DOMAIN,
        'form_fields': {
            'consultation_method': 'オンライン（Team / Zoom）, 電話',
            'consultation_type': 'トレーテールウスについて聞きたい, 新築戸建施設について聞きたい, お見積りについて聞きたい, その他',
            'name': '名前',
            'furigana': 'ふりがな',
            'email': 'メールアドレス',
            'phone': '電話番号',
            'content': 'ご相談内容'
        },
        'config': {
            'google_sheets': bool(GOOGLE_SHEET_KEY),
            'credentials_path': CREDENTIALS_FILE_PATH,
            'file_exists': os.path.exists(CREDENTIALS_FILE_PATH) if SHEETS_AVAILABLE else 'N/A',
            'sheets_library': 'AVAILABLE' if SHEETS_AVAILABLE else 'NOT AVAILABLE'
        },
        'endpoints': {
            'submit': '/submit (POST)',
            'health': '/health (GET)',
            'test': '/test (GET)',
            'debug': '/debug (GET)',
            'check_creds': '/check-creds (GET)'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test():
    """Check configuration"""
    creds_file_exists = os.path.exists(CREDENTIALS_FILE_PATH) if SHEETS_AVAILABLE else False
    
    return jsonify({
        'google_sheet_key': 'SET' if GOOGLE_SHEET_KEY else 'NOT SET',
        'credentials_path': CREDENTIALS_FILE_PATH,
        'file_exists': creds_file_exists,
        'file_exists_detail': 'YES' if creds_file_exists else 'NO - Check Render Secret Files',
        'sheets_library': 'AVAILABLE' if SHEETS_AVAILABLE else 'NOT AVAILABLE',
        'frontend': FRONTEND_DOMAIN,
        'server_time': datetime.now().isoformat()
    })

@app.route('/debug')
def debug():
    """Debug credentials file"""
    debug_info = {
        'credentials_path': CREDENTIALS_FILE_PATH,
        'file_exists': os.path.exists(CREDENTIALS_FILE_PATH),
        'sheets_available': SHEETS_AVAILABLE,
        'frontend': FRONTEND_DOMAIN,
        'server_time': time.time(),
        'render_environment': bool(os.getenv('RENDER')),
        'environment': {
            'GOOGLE_SHEET_KEY_set': bool(GOOGLE_SHEET_KEY),
            'GOOGLE_CREDENTIALS_PATH_set': bool(GOOGLE_CREDENTIALS_PATH)
        }
    }
    
    if os.path.exists(CREDENTIALS_FILE_PATH):
        try:
            with open(CREDENTIALS_FILE_PATH, 'r') as f:
                content = f.read()
                debug_info['file_size'] = len(content)
                debug_info['file_readable'] = True
                
                # Try to parse as JSON
                try:
                    creds = json.loads(content)
                    debug_info['json_valid'] = True
                    debug_info['service_account'] = creds.get('client_email', 'Not found')
                    debug_info['project_id'] = creds.get('project_id', 'Not found')
                    debug_info['private_key_id'] = creds.get('private_key_id', 'Not found')
                except json.JSONDecodeError as e:
                    debug_info['json_valid'] = False
                    debug_info['json_error'] = str(e)
                    
        except Exception as e:
            debug_info['file_readable'] = False
            debug_info['file_error'] = str(e)
    else:
        debug_info['file_exists'] = False
        debug_info['note'] = 'Upload credentials.json to Render → Environment → Secret Files'
        debug_info['secret_files_guide'] = 'Mount path should be: /etc/secrets'
    
    return jsonify(debug_info)

@app.route('/check-creds', methods=['GET'])
def check_credentials():
    """Verify credentials file"""
    try:
        print(f"🔍 Checking credentials at: {CREDENTIALS_FILE_PATH}")
        
        if not os.path.exists(CREDENTIALS_FILE_PATH):
            return jsonify({
                'status': 'error',
                'message': 'File not found at exact path',
                'exact_path': CREDENTIALS_FILE_PATH,
                'instruction': '1. Go to Render → Your Service → Environment\n2. Scroll to "Secret Files"\n3. Add file with mount path: /etc/secrets\n4. Filename: credentials.json\n5. Paste your service account JSON'
            }), 404
        
        with open(CREDENTIALS_FILE_PATH, 'r') as f:
            content = f.read()
            print(f"📄 File size: {len(content)} bytes")
            creds = json.loads(content)
        
        # Extract key details
        client_email = creds.get('client_email', '')
        
        return jsonify({
            'status': 'success',
            'message': 'Credentials file is valid',
            'file_path': CREDENTIALS_FILE_PATH,
            'file_size': len(content),
            'service_account': client_email,
            'share_sheet_with': client_email,  # EMAIL TO SHARE GOOGLE SHEET WITH
            'project_id': creds.get('project_id'),
            'private_key_id': creds.get('private_key_id'),
            'action_required': 'Share your Google Sheet with the service account email above'
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid JSON format',
            'error': str(e),
            'file_path': CREDENTIALS_FILE_PATH
        }), 500
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__,
            'file_path': CREDENTIALS_FILE_PATH
        }), 500

def load_credentials():
    """Load credentials from EXACT path"""
    print(f"📂 Loading from: {CREDENTIALS_FILE_PATH}")
    
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        print(f"❌ File not found: {CREDENTIALS_FILE_PATH}")
        print("💡 Upload to Render → Environment → Secret Files")
        print("💡 Mount Path: /etc/secrets")
        print("💡 Filename: credentials.json")
        return None
    
    try:
        with open(CREDENTIALS_FILE_PATH, 'r') as f:
            credentials = json.load(f)
        
        # Verify required fields
        required = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing = [field for field in required if field not in credentials]
        
        if missing:
            print(f"❌ Missing fields: {missing}")
            return None
        
        print(f"✅ Loaded credentials for: {credentials.get('client_email', 'Unknown')}")
        return credentials
        
    except Exception as e:
        print(f"❌ Error reading {CREDENTIALS_FILE_PATH}: {e}")
        return None

def save_to_google_sheets(data):
    """Save form data to Google Sheets"""
    if not SHEETS_AVAILABLE:
        print("❌ Google Sheets library not available")
        return False
    
    if not GOOGLE_SHEET_KEY:
        print("❌ GOOGLE_SHEET_KEY not set")
        return False
    
    try:
        print("="*50)
        print("📊 GOOGLE SHEETS SAVE ATTEMPT")
        print("="*50)
        print(f"📁 Credentials: {CREDENTIALS_FILE_PATH}")
        print(f"🔑 Sheet ID: {GOOGLE_SHEET_KEY}")
        print(f"⏰ Time: {datetime.now().isoformat()}")
        
        # Load credentials from EXACT path
        credentials_dict = load_credentials()
        if not credentials_dict:
            print("❌ FAILED: Could not load credentials")
            return False
        
        service_email = credentials_dict.get('client_email', 'Unknown')
        print(f"✅ Service Account: {service_email}")
        print(f"✅ Project: {credentials_dict.get('project_id', 'Unknown')}")
        
        # Setup Google Sheets
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        
        creds = Credentials.from_service_account_info(
            credentials_dict, 
            scopes=scope
        )
        
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        print(f"🔓 Opening Google Sheet...")
        spreadsheet = client.open_by_key(GOOGLE_SHEET_KEY)
        worksheet = spreadsheet.sheet1
        print(f"✅ Opened sheet: {worksheet.title}")
        
        # Check if headers exist, if not add them
        existing_headers = worksheet.row_values(1)
        if not existing_headers:
            print("📝 Adding headers to sheet...")
            headers = [
                "Timestamp",
                "相談方法",
                "相談種類",
                "名前",
                "ふりがな",
                "メールアドレス",
                "電話番号",
                "ご相談内容"
            ]
            worksheet.append_row(headers)
            print("✅ Headers added")
        
        # Prepare data row
        consultation_type = data.get('consultation_type', '')
        if isinstance(consultation_type, list):
            consultation_type = ', '.join(consultation_type)
        
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data.get('consultation_method', ''),
            consultation_type,
            data.get('name', ''),
            data.get('furigana', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('content', '')
        ]
        
        print(f"📝 Data: {row}")
        
        # Append row
        worksheet.append_row(row)
        print(f"✅ SUCCESS: Saved to Google Sheets!")
        print(f"👤 User: {data.get('name', 'Unknown')}")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"❌ GOOGLE SHEETS ERROR: {type(e).__name__}")
        print(f"❌ Details: {str(e)}")
        
        # Specific error handling
        if 'invalid_grant' in str(e):
            print("🔑 ERROR: Invalid JWT Signature")
            print("💡 Solution: Regenerate credentials or check time sync")
        elif 'PERMISSION_DENIED' in str(e):
            print("🔑 ERROR: Permission denied")
            print(f"💡 Solution: Share sheet with: {credentials_dict.get('client_email', 'service account')}")
        elif 'not found' in str(e).lower():
            print("🔑 ERROR: Sheet not found")
            print("💡 Solution: Check GOOGLE_SHEET_KEY environment variable")
        elif 'sheet1' in str(e).lower():
            print("🔑 ERROR: sheet1 not found")
            print("💡 Solution: Make sure your Google Sheet has at least one worksheet")
        
        import traceback
        traceback.print_exc()
        return False

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_form():
    """Handle form submission - Trailer House Inquiry Form"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    print("\n" + "="*60)
    print("📝 FORM SUBMISSION - Trailer House Inquiry")
    print("="*60)
    
    try:
        # Get data - support both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        print(f"📧 Email: {data.get('email', 'No email')}")
        print(f"📞 Phone: {data.get('phone', 'No phone')}")
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'content']
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return jsonify({
                'success': False,
                'error': '必須項目が入力されていません',
                'missing_fields': missing_fields
            }), 400
        
        # Save to Google Sheets
        sheets_success = False
        if GOOGLE_SHEET_KEY and SHEETS_AVAILABLE:
            sheets_success = save_to_google_sheets(data)
        else:
            print("⚠️ Google Sheets: Not configured")
        
        # Prepare response
        response = {
            'success': True,
            'message': 'お問い合わせが正常に送信されました。確認後、担当者よりご連絡いたします。',
            'sheets_saved': sheets_success,
            'timestamp': datetime.now().isoformat(),
            'form_data': {
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', '')
            }
        }
        
        print(f"✅ Response: {response}")
        print("="*60)
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print("\n" + "="*60)
    print("🚀 TRAILER HOUSE FORM BACKEND")
    print("="*60)
    print(f"📍 Port: {port}")
    print(f"🌐 Frontend: {FRONTEND_DOMAIN}")
    print(f"📊 Sheets Key: {'✅ SET' if GOOGLE_SHEET_KEY else '❌ NOT SET'}")
    print(f"📁 Credentials Path: {CREDENTIALS_FILE_PATH}")
    print(f"📁 File Exists: {'✅ YES' if os.path.exists(CREDENTIALS_FILE_PATH) else '❌ NO'}")
    print(f"📚 Sheets Lib: {'✅ AVAILABLE' if SHEETS_AVAILABLE else '❌ MISSING'}")
    print("="*60)
    print("💡 Upload credentials to Render → Environment → Secret Files")
    print("💡 Mount Path: /etc/secrets")
    print("💡 Filename: credentials.json")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)