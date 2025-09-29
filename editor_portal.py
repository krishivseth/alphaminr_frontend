# editor_portal.py
import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import traceback
import re

# Optional imports with error handling
try:
    from premailer import Premailer
    PREMAILER_AVAILABLE = True
except ImportError:
    PREMAILER_AVAILABLE = False
    print("Warning: Premailer not available")

try:
    import github_helper
    GITHUB_HELPER_AVAILABLE = True
except ImportError:
    GITHUB_HELPER_AVAILABLE = False
    print("Warning: github_helper not available")

try:
    import mailchimp_marketing as MailchimpMarketing
    from mailchimp_marketing.api_client import ApiClientError
    MAILCHIMP_AVAILABLE = True
except ImportError:
    MAILCHIMP_AVAILABLE = False
    print("Warning: Mailchimp not available")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: Anthropic not available")

# Add imports for newsletter generation
import subprocess
import threading
import sys

# --- SETUP ---
load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')
# SECRET_KEY is CRUCIAL for making login sessions secure.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
NEWSLETTER_DIR = "newsletters"
EDITOR_PASSWORD = os.environ.get("EDITOR_PASSWORD")
MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'

# --- API CLIENTS ---
mailchimp = None
if MAILCHIMP_AVAILABLE and not MOCK_MODE and os.environ.get("MAILCHIMP_API_KEY"):
    try:
        mailchimp = MailchimpMarketing.Client()
        mailchimp.set_config({"api_key": os.environ.get("MAILCHIMP_API_KEY"), "server": os.environ.get("MAILCHIMP_SERVER_PREFIX")})
    except Exception as e:
        print(f"Warning: Failed to initialize Mailchimp client: {e}")

client = None
if ANTHROPIC_AVAILABLE and not MOCK_MODE and os.environ.get("ANTHROPIC_API_KEY"):
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    except Exception as e:
        print(f"Warning: Failed to initialize Anthropic client: {e}")

# --- AUTHENTICATION (Improved Logic) ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not EDITOR_PASSWORD:
            # If no password is set, login is disabled.
            return f(*args, **kwargs)
        
        # Check if we have a secret key for sessions
        if not app.config.get('SECRET_KEY'):
            # No secret key, so no session support - allow access
            return f(*args, **kwargs)
        
        # Try to check session, but handle errors gracefully
        try:
            if session.get('logged_in') is not True:
                return redirect(url_for('login', next=request.url))
        except RuntimeError as e:
            # Session not available, allow access without login
            print(f"Warning: Session not available ({e}), allowing access without login")
            return f(*args, **kwargs)
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If login is disabled, redirect to the dashboard.
    if not EDITOR_PASSWORD:
        return redirect(url_for('index'))

    # If user is already logged in, redirect them away from the login page.
    if session.get('logged_in'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        if request.form.get('password') == EDITOR_PASSWORD:
            session['logged_in'] = True
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            error = "Invalid password. Please try again."
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- DATA FUNCTIONS ---
def get_all_newsletters():
    """Get newsletters from Railway backend instead of local directory"""
    try:
        import requests
        
        # Get Railway backend URL from environment
        railway_url = os.environ.get('RAILWAY_BACKEND_URL', 'http://localhost:5000')
        api_url = f"{railway_url}/api/newsletters"
        
        print(f"[DEBUG] Fetching newsletters from Railway: {api_url}")
        
        # Make the API call to Railway backend
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                newsletters = data.get('newsletters', [])
                print(f"[DEBUG] Found {len(newsletters)} newsletters from Railway")
                return newsletters
            else:
                print(f"[DEBUG] Railway API returned success=false: {data.get('error')}")
        else:
            print(f"[DEBUG] Railway API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] Failed to fetch newsletters from Railway: {e}")
    
    # No fallback to local directory - newsletters must come from Railway
    print("[DEBUG] Railway API failed, returning empty list")
    return []

def get_newsletter_content(newsletter_id):
    """Get newsletter content from Railway backend only"""
    print(f"[DEBUG] get_newsletter_content called with ID: {newsletter_id}")
    print(f"[DEBUG] ID type: {type(newsletter_id)}, length: {len(newsletter_id)}")
    
    try:
        import requests
        
        # Get Railway backend URL from environment
        railway_url = os.environ.get('RAILWAY_BACKEND_URL', 'http://localhost:5000')
        api_url = f"{railway_url}/newsletter/{newsletter_id}"
        
        print(f"[DEBUG] Fetching newsletter content from Railway: {api_url}")
        
        # Make the API call to Railway backend
        response = requests.get(api_url, timeout=30)
        
        print(f"[DEBUG] Railway API response: status={response.status_code}, content_length={len(response.text)}")
        
        if response.status_code == 200:
            content = response.text
            print(f"[DEBUG] Successfully fetched newsletter content from Railway ({len(content)} chars)")
            print(f"[DEBUG] Content preview: {content[:100]}...")
            return content
        elif response.status_code == 404:
            print(f"[DEBUG] Newsletter not found in Railway database: {newsletter_id}")
        else:
            print(f"[DEBUG] Railway API call failed: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"[DEBUG] Failed to fetch newsletter content from Railway: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
    
    # No fallback to local files - Railway newsletters must come from Railway
    print(f"[DEBUG] Newsletter not found in Railway backend: {newsletter_id}")
    return None

# --- PROTECTED ROUTES ---
@app.route('/')
@login_required
def index():
    try:
        newsletters = get_all_newsletters()
        return render_template('index.html', newsletters=newsletters)
    except Exception as e:
        # Fallback if template fails
        return f"""
        <html>
        <head><title>Alphaminr Newsletter Generator</title></head>
        <body>
            <h1>Alphaminr Newsletter Generator</h1>
            <p>Status: Working (Template issue resolved)</p>
            <p>Newsletters found: {len(newsletters) if 'newsletters' in locals() else 0}</p>
            <p>Error: {str(e)}</p>
            <a href="/api/test">Test API</a> | 
            <a href="/health">Health Check</a> |
            <a href="/api/env-check">Environment Check</a>
        </body>
        </html>
        """

@app.route('/editor/<newsletter_id>')
@login_required
def editor(newsletter_id):
    content = get_newsletter_content(newsletter_id)
    if content is None: return "Newsletter not found", 404
    return render_template('editor.html', newsletter={'id': newsletter_id, 'html_content': content})

# --- API ROUTES (Session cookie protects these) ---
@app.route('/api/newsletter/<newsletter_id>', methods=['POST'])
@login_required
def save_newsletter(newsletter_id):
    data = request.json
    if not data.get('html_content'): return jsonify({"error": "No content"}), 400
    file_path = f"{NEWSLETTER_DIR}/{newsletter_id}"
    commit_message = f"docs: update {newsletter_id}\n\nNotes: {data.get('editor_notes', 'n/a')}"
    result = github_helper.commit_file(file_path, data['html_content'], commit_message)
    if result.get("success"): return jsonify({"success": True, "message": "Saved to GitHub."})
    return jsonify({"error": f"GitHub Save Failed: {result.get('error')}"}), 500

@app.route('/api/newsletter/<newsletter_id>/review', methods=['POST'])
@login_required
def ai_review_newsletter(newsletter_id):
    html_content = get_newsletter_content(newsletter_id)
    if not html_content: return jsonify({"error": "Not found"}), 404
    if MOCK_MODE or not client: return jsonify({"success": True, "review": "[MOCK] Looks great!"})
    try:
        # Strip HTML tags to focus on content only
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract just the text content, preserving structure
        text_content = soup.get_text(separator='\n\n', strip=True)
        
        # Create a focused prompt for content review
        review_prompt = f"""Please review this financial newsletter content for quality and provide constructive feedback. Focus ONLY on the content, writing quality, and reader value - ignore any formatting or HTML.

Newsletter Content:
{text_content}

Provide feedback on:
- Content accuracy and relevance
- Writing clarity and engagement
- Value to financial newsletter readers
- Suggestions for improvement

Keep your review concise and actionable."""

        response = client.messages.create(
            model="claude-3-haiku-20240307", 
            max_tokens=1024, 
            messages=[{"role": "user", "content": review_prompt}]
        )
        return jsonify({"success": True, "review": response.content[0].text})
    except Exception as e:
        return jsonify({"error": f"AI review failed: {str(e)}"}), 500

@app.route('/api/newsletter/<newsletter_id>/send', methods=['POST'])
@login_required
def send_newsletter(newsletter_id):
    """Send newsletter to Mailchimp list using a manual premailer workflow."""
    print(f"[DEBUG] Send newsletter called with ID: {newsletter_id}")
    
    html_content = get_newsletter_content(newsletter_id)
    if not html_content:
        print(f"[DEBUG] Failed to get newsletter content for ID: {newsletter_id}")
        return jsonify({"error": "Newsletter not found"}), 404
    
    print(f"[DEBUG] Successfully retrieved newsletter content ({len(html_content)} chars)")

    inlined_html = html_content # Default to original html
    try:
        # --- FIXED METHOD ---
        # 1. Read the CSS file
        css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'css', 'newsletter.css')
        css_text = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r') as f:
                css_text = f.read()
            print("Successfully read CSS file.")
        else:
            print("Warning: CSS file not found.")

        # 2. Remove the <link> tag to prevent Premailer from trying to load it
        # This regex will match and remove the CSS link tag
        html_without_link = re.sub(
            r'<link[^>]*href=["\'][^"\']*newsletter\.css["\'][^>]*>',
            '',
            html_content,
            flags=re.IGNORECASE
        )

        # 3. Inject CSS as a style tag in the head
        if css_text:
            # Add the CSS as a style tag in the head
            html_with_style = html_without_link.replace(
                '</head>',
                f'<style type="text/css">{css_text}</style></head>'
            )
            
            # Process with Premailer
            p = Premailer(
                html=html_with_style,
                allow_network=False,
                disable_validation=True,
                strip_important=False,
                keep_style_tags=False
            )
            # Run the transform
            inlined_html = p.transform()
            print("Successfully inlined CSS with Premailer.")
            
            # Debug: Check if styles were actually inlined
            if 'style=' in inlined_html:
                print("DEBUG: Inline styles found in processed HTML")
                style_count = inlined_html.count('style=')
                print(f"DEBUG: {style_count} style attributes added")
            else:
                print("WARNING: No inline styles found after Premailer processing!")
        
    except Exception as e:
        print(f"Error during CSS inlining: {e}")
        traceback.print_exc()
        # Fallback to original content
        inlined_html = html_content
    
    # The rest of the function remains the same...
    if MOCK_MODE or not mailchimp:
        msg = "Test email sent!" if request.json.get('test_mode') else "Newsletter sent!"
        return jsonify({"success": True, "message": f"[MOCK] {msg}"})
    
    try:
        campaign_data = {
            "type": "regular", "recipients": {"list_id": os.environ.get("MAILCHIMP_LIST_ID")},
            "settings": {
                "subject_line": f"Alphaminr - {datetime.now().strftime('%B %d, %Y')}", "title": f"Alphaminr {datetime.now().strftime('%Y-%m-%d')}",
                "from_name": "Alphaminr", "reply_to": os.environ.get("REPLY_TO_EMAIL")
            }
        }
        campaign = mailchimp.campaigns.create(campaign_data)
        campaign_id = campaign['id']
        
        mailchimp.campaigns.set_content(campaign_id, {"html": inlined_html})

        if request.json.get('test_mode'):
            test_payload = {"test_emails": [os.environ.get("EDITOR_EMAIL")], "send_type": "html"}
            mailchimp.campaigns.send_test_email(campaign['id'], test_payload)
            return jsonify({"success": True, "message": "Test email sent!"})
        else:
            mailchimp.campaigns.send(campaign['id'])
            return jsonify({"success": True, "message": "Newsletter sent successfully!"})
    except ApiClientError as e:
        return jsonify({"error": f"Mailchimp error: {e.text}"}), 500

@app.route('/api/generate-newsletter', methods=['POST'])
@login_required
def generate_newsletter():
    """Generate a new newsletter using the generation script."""
    if MOCK_MODE:
        # In mock mode, simulate generation
        from datetime import datetime
        mock_id = f"alphaminr_{datetime.now().strftime('%Y-%m-%d')}.html"
        return jsonify({
            "success": True, 
            "message": "[MOCK] Newsletter generated!", 
            "newsletter_id": mock_id
        })
    
    try:
        # Check for existing lock file
        lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generation.lock')
        if os.path.exists(lock_file):
            return jsonify({
                "error": "Newsletter generation is already in progress. Please wait for it to complete."
            }), 409  # Conflict status code
        
        # No need to check for script - we're using the API endpoint directly
        
        # Old subprocess code removed - now using direct API call
        
        # Call the Railway backend API
        try:
            import requests
            import time
            
            # Get Railway backend URL from environment
            railway_url = os.environ.get('RAILWAY_BACKEND_URL', 'http://localhost:5000')
            api_url = f"{railway_url}/api/generate"
            
            print(f"[DEBUG] Calling Railway backend: {api_url}")
            
            # Make the API call to Railway backend
            response = requests.post(api_url, json={}, timeout=300)  # 5 minute timeout
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    html_content = data.get('html', '')
                    newsletter_id = data.get('newsletter_id', f"alphaminr_{datetime.now().strftime('%Y-%m-%d_%H%M')}.html")
                    
                    # Save the newsletter to newsletters directory
                    newsletter_path = os.path.join(NEWSLETTER_DIR, newsletter_id)
                    
                    # Ensure newsletters directory exists
                    os.makedirs(NEWSLETTER_DIR, exist_ok=True)
                    
                    with open(newsletter_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"[DEBUG] Newsletter saved to: {newsletter_path}")
                    
                    # Also save to database for tracking
                    try:
                        init_database()
                        save_newsletter_to_db(newsletter_id, html_content)
                        print(f"[DEBUG] Newsletter saved to database: {newsletter_id}")
                    except Exception as db_error:
                        print(f"[DEBUG] Database save failed (non-critical): {db_error}")
                    
                    return jsonify({
                        "success": True,
                        "message": f"Newsletter generated successfully! Saved as {newsletter_id}",
                        "newsletter_id": newsletter_id,
                        "generation_time": data.get('generation_time_seconds', 0),
                        "total_time": data.get('total_time_seconds', 0)
                    })
                else:
                    return jsonify({
                        "error": f"Backend generation failed: {data.get('error', 'Unknown error')}"
                    }), 500
            else:
                return jsonify({
                    "error": f"API call failed with status {response.status_code}: {response.text}"
                }), 500
                
        except Exception as e:
            print(f"[DEBUG] API call failed: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": f"Failed to generate newsletter: {str(e)}",
                "traceback": traceback.format_exc(),
                "railway_url": railway_url
            }), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to start generation: {str(e)}"}), 500

@app.route('/api/generation-status', methods=['GET'])
@login_required
def generation_status():
    """Check if a new newsletter has been generated recently."""
    try:
        # Check if generation is in progress
        lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generation.lock')
        if os.path.exists(lock_file):
            return jsonify({
                "status": "in_progress",
                "message": "Newsletter generation is currently running..."
            })
        
        # Check for recent newsletters
        newsletter_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'newsletters')
        if os.path.exists(newsletter_dir):
            files = [f for f in os.listdir(newsletter_dir) if f.endswith('.html')]
            if files:
                # Get the most recent file
                latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(newsletter_dir, x)))
                return jsonify({
                    "status": "completed",
                    "message": f"Latest newsletter: {latest_file}",
                    "latest_file": latest_file
                })
        
        return jsonify({
            "status": "idle",
            "message": "No generation in progress and no newsletters found"
        })
        
    except Exception as e:
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500

@app.route('/api/generation-logs', methods=['GET'])
@login_required
def generation_logs():
    """Get the latest generation logs."""
    try:
        import tempfile
        tmp_dir = tempfile.gettempdir()
        
        # Try to get final logs first, then fall back to regular logs
        final_log_file = os.path.join(tmp_dir, 'generation_final.log')
        log_file = os.path.join(tmp_dir, 'generation.log')
        
        if os.path.exists(final_log_file):
            with open(final_log_file, 'r') as f:
                logs = f.read()
            return jsonify({"logs": logs, "source": "final", "path": final_log_file})
        elif os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
            return jsonify({"logs": logs, "source": "regular", "path": log_file})
        else:
            return jsonify({"logs": "No logs available yet", "source": "none", "tmp_dir": tmp_dir})
    except Exception as e:
        return jsonify({"error": f"Failed to read logs: {str(e)}"}), 500

@app.route('/api/debug-files', methods=['GET'])
@login_required
def debug_files():
    """Debug endpoint to check what files exist."""
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        files_info = {}
        
        # Check various log files in both base_dir and /tmp
        import tempfile
        tmp_dir = tempfile.gettempdir()
        
        log_files = ['generation.log', 'generation_final.log', 'generation.lock']
        for filename in log_files:
            # Check in base directory
            filepath = os.path.join(base_dir, filename)
            tmp_filepath = os.path.join(tmp_dir, filename)
            
            files_info[filename] = {
                "base_dir": {
                    "path": filepath,
                    "exists": os.path.exists(filepath)
                },
                "tmp_dir": {
                    "path": tmp_filepath,
                    "exists": os.path.exists(tmp_filepath)
                }
            }
            
            # If exists in tmp, get content
            if os.path.exists(tmp_filepath):
                try:
                    with open(tmp_filepath, 'r') as f:
                        content = f.read()
                    files_info[filename]["tmp_dir"]["size"] = len(content)
                    files_info[filename]["tmp_dir"]["content_preview"] = content[:500] if content else "empty"
                except Exception as e:
                    files_info[filename]["tmp_dir"]["error"] = str(e)
        
        # Check newsletters directory
        newsletter_dir = os.path.join(base_dir, 'newsletters')
        if os.path.exists(newsletter_dir):
            files_info['newsletters'] = {
                "exists": True,
                "files": os.listdir(newsletter_dir)
            }
        else:
            files_info['newsletters'] = {"exists": False}
        
        return jsonify({
            "base_dir": base_dir,
            "tmp_dir": tmp_dir,
            "files": files_info
        })
        
    except Exception as e:
        return jsonify({"error": f"Debug failed: {str(e)}"}), 500

@app.route('/api/newsletters', methods=['GET'])
@login_required
def get_newsletters():
    """Get list of generated newsletters."""
    try:
        newsletters = []
        
        # Check newsletters directory
        if os.path.exists(NEWSLETTER_DIR):
            for filename in os.listdir(NEWSLETTER_DIR):
                if filename.endswith('.html'):
                    filepath = os.path.join(NEWSLETTER_DIR, filename)
                    stat = os.stat(filepath)
                    newsletters.append({
                        'filename': filename,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'size': stat.st_size,
                        'location': 'newsletters'
                    })
        
        
        # Sort by creation time (newest first)
        newsletters.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify(newsletters)
    except Exception as e:
        return jsonify({"error": f"Failed to list newsletters: {str(e)}"}), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "imports": {
            "premailer": PREMAILER_AVAILABLE,
            "github_helper": GITHUB_HELPER_AVAILABLE,
            "mailchimp": MAILCHIMP_AVAILABLE,
            "anthropic": ANTHROPIC_AVAILABLE
        }
    })

@app.route('/api/test')
def test_endpoint():
    """Minimal test endpoint to check if Flask is working"""
    try:
        return jsonify({
            "status": "ok",
            "message": "Flask is working",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/template-debug')
def template_debug():
    """Debug template directory and files"""
    try:
        import os
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        debug_info = {
            "template_folder": app.template_folder,
            "template_dir_exists": os.path.exists(template_dir),
            "template_dir_path": template_dir,
            "current_dir": os.path.dirname(__file__),
            "files_in_template_dir": []
        }
        
        if os.path.exists(template_dir):
            debug_info["files_in_template_dir"] = os.listdir(template_dir)
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/debug-newsletter/<newsletter_id>', methods=['GET'])
@login_required
def debug_newsletter_content(newsletter_id):
    """Debug endpoint to test newsletter content retrieval"""
    try:
        print(f"[DEBUG] Testing newsletter content retrieval for ID: {newsletter_id}")
        
        # Test Railway fetch
        railway_url = os.environ.get('RAILWAY_BACKEND_URL', 'http://localhost:5000')
        api_url = f"{railway_url}/newsletter/{newsletter_id}"
        
        debug_info = {
            "newsletter_id": newsletter_id,
            "railway_url": railway_url,
            "api_url": api_url,
            "tests": {}
        }
        
        # Test 1: Direct Railway API call
        try:
            import requests
            response = requests.get(api_url, timeout=10)
            debug_info["tests"]["railway_api"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "content_length": len(response.text) if response.text else 0,
                "content_preview": response.text[:200] if response.text else "No content"
            }
        except Exception as e:
            debug_info["tests"]["railway_api"] = {
                "error": str(e),
                "success": False
            }
        
        # Test 2: get_newsletter_content function
        try:
            content = get_newsletter_content(newsletter_id)
            debug_info["tests"]["get_newsletter_content"] = {
                "success": content is not None,
                "content_length": len(content) if content else 0,
                "content_preview": content[:200] if content else "No content"
            }
        except Exception as e:
            debug_info["tests"]["get_newsletter_content"] = {
                "error": str(e),
                "success": False
            }
        
        # Test 3: Local file check
        file_path = os.path.join(NEWSLETTER_DIR, newsletter_id)
        debug_info["tests"]["local_file"] = {
            "file_path": file_path,
            "exists": os.path.exists(file_path),
            "is_file": os.path.isfile(file_path) if os.path.exists(file_path) else False
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Debug failed: {str(e)}", "traceback": traceback.format_exc()}), 500

@app.route('/api/env-check')
def env_check():
    """Check environment variables without complex imports"""
    try:
        env_vars = {
            "SECRET_KEY": "Set" if os.environ.get('SECRET_KEY') else "Not set",
            "EDITOR_PASSWORD": "Set" if os.environ.get('EDITOR_PASSWORD') else "Not set", 
            "RAILWAY_BACKEND_URL": os.environ.get('RAILWAY_BACKEND_URL', 'Not set'),
            "ANTHROPIC_API_KEY": "Set" if os.environ.get('ANTHROPIC_API_KEY') else "Not set",
            "MAILCHIMP_API_KEY": "Set" if os.environ.get('MAILCHIMP_API_KEY') else "Not set"
        }
        
        return jsonify({
            "status": "ok",
            "environment_variables": env_vars
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/debug-backend')
def debug_backend():
    """Debug endpoint to check backend connection and environment"""
    try:
        railway_url = os.environ.get('RAILWAY_BACKEND_URL', 'http://localhost:5000')
        
        # Test backend connection
        import requests
        backend_status = "Unknown"
        backend_error = None
        backend_response = None
        
        try:
            response = requests.get(f"{railway_url}/health", timeout=10)
            backend_status = f"Status: {response.status_code}"
            backend_response = response.text
            if response.status_code != 200:
                backend_error = response.text
        except Exception as e:
            backend_status = "Failed to connect"
            backend_error = str(e)
        
        debug_info = {
            "railway_backend_url": railway_url,
            "backend_status": backend_status,
            "backend_error": backend_error,
            "backend_response": backend_response,
            "environment_check": {
                "SECRET_KEY": "Set" if os.environ.get('SECRET_KEY') else "Not set",
                "EDITOR_PASSWORD": "Set" if os.environ.get('EDITOR_PASSWORD') else "Not set",
                "RAILWAY_BACKEND_URL": "Set" if os.environ.get('RAILWAY_BACKEND_URL') else "Not set"
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

# --- LOCAL DEVELOPMENT ---
if __name__ == '__main__':
    if not os.path.exists(NEWSLETTER_DIR): os.makedirs(NEWSLETTER_DIR)
    if not app.config['SECRET_KEY']: print("Warning: SECRET_KEY is not set. Sessions will not be secure.")
    if not EDITOR_PASSWORD: print("Warning: EDITOR_PASSWORD is not set. The editor is not password-protected.")
    app.run(debug=True, host='127.0.0.1', port=5001)