"""
TraceRoot Local - Single File Flask Application
Features: Dynamic bug generation and RCA via Ollama
"""

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import sqlite3
import json
import subprocess
import requests
import os
import io
import re
import time

try:
    from openpyxl import Workbook  # type: ignore
    from openpyxl.styles import Font, PatternFill, Alignment  # type: ignore
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# Get the directory of the current app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=BASE_DIR, static_folder=os.path.join(BASE_DIR, '.'), static_url_path='')
app.config['JSON_SORT_KEYS'] = False

# ============================================================================
# DATABASE & DATA GENERATION
# ============================================================================

DB_FILE = ':memory:'  # Use in-memory database for simplicity
BUGS_CACHE = None
INCIDENTS_CACHE = None
RCA_CACHE = {}  # Store generated RCAs: {bug_id: rca_text}

def init_database():
    """Initialize in-memory database with bug and incident data"""
    global BUGS_CACHE, INCIDENTS_CACHE
    
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create bugs table
    cursor.execute('''
        CREATE TABLE bugs (
            bug_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            repro_steps TEXT,
            status TEXT,
            priority TEXT,
            severity INTEGER,
            assigned_to TEXT,
            created_date TEXT,
            environment TEXT,
            category TEXT,
            type TEXT
        )
    ''')
    conn.commit()
    
    # Generate bugs dynamically
    bugs = generate_bugs_dynamic(200)
    for bug in bugs:
        bug['type'] = 'bugs'
        cursor.execute('''
            INSERT INTO bugs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bug['bug_id'],
            bug['title'],
            bug['description'],
            bug['repro_steps'],
            bug['status'],
            bug['priority'],
            bug['severity'],
            bug['assigned_to'],
            bug['created_date'],
            bug['environment'],
            bug['category'],
            bug['type']
        ))
    conn.commit()
    
    # Generate incidents dynamically
    incidents = generate_incidents_dynamic(100)
    for incident in incidents:
        incident['type'] = 'incidents'
        cursor.execute('''
            INSERT INTO bugs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident['bug_id'],
            incident['title'],
            incident['description'],
            incident['repro_steps'],
            incident['status'],
            incident['priority'],
            incident['severity'],
            incident['assigned_to'],
            incident['created_date'],
            incident['environment'],
            incident['category'],
            incident['type']
        ))
    conn.commit()
    
    BUGS_CACHE = bugs
    INCIDENTS_CACHE = incidents
    return conn

def generate_bugs_dynamic(count=200):
    """Generate realistic bug data dynamically with unique variations"""
    
    bug_titles = [
        "PDF export truncates data rows",
        "Database connection pool exhaustion",
        "API timeout on batch processing",
        "Data mismatch in claims processing",
        "Memory leak in background service",
        "User permissions not syncing correctly",
        "Search filter returns duplicate results",
        "CSV import validation missing",
        "Authentication token expiration issue",
        "Database JOIN produces null values",
        "Report generation fails with large datasets",
        "Email notification delivery delay",
        "Dashboard widgets not refreshing",
        "File upload size limit exceeded",
        "Date parsing error in legacy format",
        "Cache invalidation not triggering",
        "Workflow automation halts unexpectedly",
        "Performance degradation on queries",
        "Data validation rules not enforced",
        "Special characters corrupted in export"
    ]
    
    description_templates = [
        "Issue with {module} functionality causing {problem}. {details} {impact}",
        "{symptom} in {module}. Users report {issue}. {root_cause} {mitigation}",
        "{module} experiencing {problem} under {condition}. {evidence} {consequence}",
        "Critical issue in {module}: {description}. {frequency} {severity_desc}",
        "{module} failure causing {impact_area} to {consequence}. {details}"
    ]
    
    modules = ["PDF export", "Database layer", "API service", "Claims processor", "Cache system", 
               "Authentication", "Search engine", "Import module", "Dashboard", "File storage",
               "Date parser", "Workflow engine", "Query optimizer", "Validation layer", "Email service"]
    problems = ["incomplete data processing", "connection pool exhaustion", "timeout failures", 
                "data inconsistency", "memory leaks", "synchronization delays", "duplicate entries",
                "missing validation", "token expiration", "NULL value handling"]
    
    details_list = ["Records are truncated.", "System becomes unresponsive.", "Partial data loss occurs.",
                    "Performance degrades significantly.", "Users unable to access features."]
    
    impact_list = ["Affects compliance.", "Impacts user experience.", "Causes cascading failures.",
                   "Requires manual intervention.", "System becomes unstable."]
    
    statuses = ["New", "Closed", "Resolved", "In Progress", "On Hold"]
    priorities = ["P1", "P2", "P3", "P4", "P5"]
    severities = [1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
    environments = ["PRD", "UAT", "DEV", "CRT"]
    categories = [
        "PDF Export", "Database Performance", "API Integration", 
        "Data Mismatch", "Memory Management", "Security & Access", 
        "Data Validation", "Import/Export", "Authentication", 
        "Infrastructure"
    ]
    
    team_members = [
        "Alice Johnson", "Bob Smith", "Charlie Brown",
        "Diana Prince", "Eve Wilson", "Frank Miller",
        "Grace Lee", "Henry Davis", "Iris Chen",
        "Jack Thompson"
    ]
    
    bugs = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        bug_id = f"60{1000 + i}"
        # Create unique title by combining base titles
        title = random.choice(bug_titles)
        
        # Create unique description using templates
        module = random.choice(modules)
        problem = random.choice(problems)
        detail = random.choice(details_list)
        impact = random.choice(impact_list)
        description = f"{module} experiencing {problem}. {detail} {impact}"
        
        # Create unique reproduction steps
        repro = f"STEPS TO REPRODUCE:\n1. Initiate operation in {module}\n2. Monitor for {problem}\n3. Check system logs for errors\n4. Verify data integrity\n5. RESULT: {problem.capitalize()} detected.\n\nEXPECTED: Normal operation.\nACTUAL: {problem.capitalize()} issue confirmed."
        
        status = random.choice(statuses)
        priority = random.choice(priorities)
        severity = random.choice(severities)
        assigned = random.choice(team_members)
        environment = random.choice(environments)
        category = random.choice(categories)
        created_by = assigned  # For bugs, created_by is same as assigned_to
        
        # Random date within past year
        random_date = start_date + timedelta(days=random.randint(0, 365))
        created_date = random_date.strftime("%Y-%m-%d")
        
        bugs.append({
            'bug_id': bug_id,
            'title': title,
            'description': description,
            'repro_steps': repro,
            'status': status,
            'priority': priority,
            'severity': severity,
            'assigned_to': assigned,
            'created_by': created_by,
            'created_date': created_date,
            'environment': environment,
            'category': category
        })
    
    return bugs

def generate_incidents_dynamic(count=100):
    """Generate realistic incident data dynamically with unique variations"""
    
    incident_titles = [
        "Production Database Down",
        "API Service Unavailable",
        "Network Connectivity Loss",
        "Authentication Service Degraded",
        "Payment Gateway Timeout",
        "Email Service Failure",
        "Storage Quota Exceeded",
        "CPU Utilization Critical",
        "Data Replication Failure",
        "Load Balancer Offline",
        "Security Breach Detected",
        "Backup Failed",
        "Certificate Expiration",
        "Memory Exhaustion",
        "Disk Space Critical"
    ]
    
    incident_modules = ["database", "API service", "network", "authentication", "payment gateway",
                        "email service", "storage system", "compute resources", "data replication", 
                        "load balancer", "security system", "backup system", "SSL certificate", 
                        "memory system", "disk system"]
    
    incident_statuses = ["ACTIVE", "RESOLVED", "INVESTIGATING", "ESCALATED", "MONITORING"]
    priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    severities = [1, 1, 1, 2, 2]
    environments = ["PRD", "CRT"]
    categories = ["Infrastructure", "Database", "Network", "Security", "Storage"]
    
    team_members = [
        "Alice Johnson", "Bob Smith", "Charlie Brown",
        "Diana Prince", "Eve Wilson", "Frank Miller",
        "Grace Lee", "Henry Davis", "Iris Chen",
        "Jack Thompson"
    ]
    
    incidents = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        incident_id = f"60{5000 + i}"
        module = random.choice(incident_modules)
        base_title = random.choice(incident_titles)
        title = f"INC {incident_id} - {base_title}"
        
        # Create unique description
        impact_areas = ["service", "users", "operations", "data integrity", "customer access"]
        time_frames = ["5 minutes", "15 minutes", "1 hour", "2 hours", "30 minutes"]
        impact = random.choice(impact_areas)
        timeframe = random.choice(time_frames)
        description = f"{module.capitalize()} experiencing critical failure affecting {impact}. Service down for approximately {timeframe}. All dependent services unable to process requests. Immediate mitigation required."
        
        repro = f"INCIDENT TIMELINE:\n1. Issue detected by monitoring system at {start_date.strftime('%H:%M')}\n2. Alerts triggered to on-call team\n3. Investigation commenced on {module}\n4. Root cause identified in {module}\n5. Mitigation applied and service restored\n\nIMPACT: Service unavailable to users. Revenue impact detected."
        status = random.choice(incident_statuses)
        priority = random.choice(priorities)
        severity = random.choice(severities)
        assigned = random.choice(team_members)
        created_by = random.choice([m for m in team_members if m != assigned])  # Different person for incidents
        environment = random.choice(environments)
        category = random.choice(categories)
        
        # Random date within past year
        random_date = start_date + timedelta(days=random.randint(0, 365))
        created_date = random_date.strftime("%Y-%m-%d")
        
        incidents.append({
            'bug_id': incident_id,
            'title': title,
            'description': description,
            'repro_steps': repro,
            'status': status,
            'priority': priority,
            'severity': severity,
            'assigned_to': assigned,
            'created_by': created_by,
            'created_date': created_date,
            'environment': environment,
            'category': category
        })
    
    return incidents

def get_bugs_by_month(month_number=None):
    """Filter bugs and incidents by month or return all if no month is provided"""
    all_items = BUGS_CACHE + INCIDENTS_CACHE if INCIDENTS_CACHE else BUGS_CACHE
    
    if month_number is None or month_number == 'all':
        return all_items

    filtered = []
    for item in all_items:
        date_obj = datetime.strptime(item['created_date'], "%Y-%m-%d")
        if date_obj.month == month_number:
            filtered.append(item)
    return filtered

def get_bugs_by_date_range(start_date_str, end_date_str, bugs_only=False):
    """Filter bugs and incidents by date range (YYYY-MM-DD format)"""
    all_items = BUGS_CACHE + INCIDENTS_CACHE if INCIDENTS_CACHE else BUGS_CACHE
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return all_items
    
    filtered = []
    for item in all_items:
        date_obj = datetime.strptime(item['created_date'], "%Y-%m-%d")
        if start_date <= date_obj <= end_date:
            # If bugs_only flag is True, filter to only 'bugs' type (exclude incidents)
            if bugs_only and str(item.get('type', 'bugs')).lower() != 'bugs':
                continue
            filtered.append(item)
    return filtered

def get_bug_by_id(bug_id):
    """Get single bug or incident by ID"""
    all_items = BUGS_CACHE + INCIDENTS_CACHE if INCIDENTS_CACHE else BUGS_CACHE
    for item in all_items:
        if item['bug_id'] == bug_id:
            return item
    return None

# ============================================================================
# OLLAMA RCA GENERATION
# ============================================================================

OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')


def generate_rca_via_ollama(bug_data, fast: bool = False):
    """Generate RCA using local Ollama model."""
    def rca_fallback(bug_data, reason=None):
        """Deterministic fallback RCA generator when Ollama isn't available.

        Produces per-bug unique RCAs based on keywords in title/description so
        each bug gets a different, sensible-looking RCA even without the model.
        """
        title = bug_data.get('title', '')
        desc = bug_data.get('description', '')
        priority = bug_data.get('priority', '')
        text = (title + ' ' + desc).lower()
        mapping = {
            'memory': 'Memory Management',
            'timeout': 'Timeout / Performance',
            'database': 'Database',
            'db': 'Database',
            'pdf': 'Export / PDF',
            'cache': 'Cache Invalidation',
            'token': 'Authentication / Token',
            'csv': 'Import / CSV',
            'import': 'Import / Parsing',
            'export': 'Export / Parsing',
            'join': 'Database JOIN',
            'email': 'Notification / Email',
            'dashboard': 'Real-time / Dashboard',
            'file': 'File Upload',
            'date': 'Date Parsing',
            'workflow': 'Workflow Automation',
            'search': 'Search / Filtering',
            'performance': 'Performance',
            'validation': 'Data Validation',
            'character': 'Encoding / Characters',
            'encoding': 'Encoding / Characters'
        }

        bug_type = 'General Functional Bug'
        for k, v in mapping.items():
            if k in text:
                bug_type = v
                break

        # deterministic variation: derive index from numeric parts of bug_id
        try:
            id_digits = int(''.join(ch for ch in (bug_data.get('bug_id') or '') if ch.isdigit()) or 0)
        except Exception:
            id_digits = 0

        rca_templates = [
            ("Underlying {component} inefficiency causing slow operations under load.", "System performance degrades significantly when processing large data sets or under concurrent load. This impacts end-user experience and causes cascading failures in dependent systems. Bottleneck occurs in the {component} layer where resources are exhausted."),
            ("Missing indexes and inefficient query plan causing table scans and delays.", "Database queries perform full table scans instead of using indexed lookups, resulting in exponential performance degradation. Query execution time increases dramatically with data volume. The query optimizer is not using available indexes effectively."),
            ("Resource exhaustion combined with heavy queries leads to timeouts and failures.", "System resources (memory, CPU, connections) become depleted during peak usage or bulk operations. Requests timeout after exceeding the configured threshold. Connection pool exhaustion prevents new requests from being processed."),
            ("Incorrect validation or missing safeguards results in repeated expensive operations.", "Input validation logic is missing or incomplete, allowing invalid data to trigger expensive re-processing loops. The system lacks defensive checks to prevent cascading failures. Duplicate or unnecessary operations occur due to lack of idempotency."),
            ("Configuration mismatch causes degraded performance for large datasets.", "System configuration parameters are not optimized for the actual data volume and concurrent load. Performance tuning was done for a smaller dataset that no longer matches production scale. Resource limits are insufficient for current operational requirements.")
        ]

        comp = bug_type.split('/')[0].strip().lower()
        template_idx = id_digits % len(rca_templates)

        rca_summary, rca_detail = rca_templates[template_idx]
        rca_text = rca_summary.replace('{component}', comp) + " " + rca_detail.replace('{component}', comp)

        # Make RCA reference the title for uniqueness and clarity
        title_snippet = (title[:60]) if len(title) > 60 else title

        rca_lines = [
            f"Bug type : {bug_type}",
            f"RCA : {rca_text} Specifically affects: {title_snippet}."
        ]
        return '\n'.join(rca_lines)
    # Build a per-bug prompt including the bug_id to encourage unique outputs
    base_prompt = f"""Analyze this bug briefly.

Unique ID: {bug_data.get('bug_id')}
Title: {bug_data.get('title')}
Priority: {bug_data.get('priority')}
Description: {bug_data.get('description')}

Provide ONLY:
Bug type : [One line classification]
RCA : [2-3 crisp lines of root cause]
Resolution : [1-2 lines of fix]"""

    last_err = None
    if fast:
        # Fast mode: single, short attempt to Ollama then immediate fallback if it fails
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': base_prompt,
                    'stream': False,
                    'temperature': 0.35
                },
                headers={'Content-Type': 'application/json'},
                timeout=8
            )
            if response.status_code == 200:
                try:
                    payload = response.json()
                    response_text = payload.get('response') or payload.get('result') or payload.get('output') or str(payload)
                    if response_text and len(response_text.strip()) >= 20:
                        return response_text
                except ValueError:
                    last_err = 'invalid JSON from model'
            else:
                last_err = f'status {response.status_code}'
        except requests.exceptions.RequestException as e:
            last_err = str(e)

        # Fast fallback
        return rca_fallback(bug_data, reason=f"ollama fast-fail ({last_err})")

    # Slow/robust mode: try multiple times with increasing temperature to get varied outputs
    for attempt in range(1, 4):
        temp = 0.25 + 0.15 * (attempt - 1)  # 0.25, 0.4, 0.55
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': base_prompt,
                    'stream': False,
                    'temperature': temp
                },
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code != 200:
                last_err = f"status {response.status_code}"
                time.sleep(0.4 * attempt)
                continue

            try:
                payload = response.json()
            except ValueError:
                last_err = "invalid JSON from model"
                time.sleep(0.2 * attempt)
                continue

            response_text = payload.get('response') or payload.get('result') or payload.get('output') or str(payload)
            if not response_text or len(response_text.strip()) < 20:
                last_err = "empty or short response"
                time.sleep(0.2 * attempt)
                continue

            return response_text

        except requests.exceptions.RequestException as e:
            last_err = str(e)
            time.sleep(0.4 * attempt)
            continue

    return rca_fallback(bug_data, reason=f"ollama failed ({last_err})")


def parse_rca_sections(text):
    """Parse RCA text into structured sections: bug_type, rca, recommendation.

    Looks for common headings (bug type, rca, root cause, resolution, recommendation).
    Returns dict with keys and string values (may be empty).
    """
    if not text:
        return {'bug_type': '', 'rca': '', 'recommendation': ''}

    # Normalize line endings and ensure spacing
    t = text.replace('\r\n', '\n').replace('\r', '\n')

    # Regex to find headings
    pattern = re.compile(r'(?mi)^(bug\s*type|classification|rca|root\s*cause(?:\s*analysis)?|resolution|recommendation)\s*[:\-–]\s*', re.MULTILINE)
    matches = list(pattern.finditer(t))
    sections = {}
    if matches:
        for idx, m in enumerate(matches):
            key = m.group(1).strip().lower()
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(t)
            val = t[start:end].strip()
            sections[key] = val

    # Map extracted keys to standard names
    bug_type = sections.get('bug type') or sections.get('classification') or ''
    rca = sections.get('rca') or sections.get('root cause') or sections.get('root cause analysis') or ''
    recommendation = sections.get('resolution') or sections.get('recommendation') or ''

    # If no headings found, attempt simple heuristics: split by double newline
    if not (bug_type or rca or recommendation):
        parts = [p.strip() for p in re.split(r'\n\n+', t) if p.strip()]
        if parts:
            # first part could be bug type if short
            if len(parts[0].split()) <= 6:
                bug_type = parts[0]
                if len(parts) > 1:
                    rca = parts[1]
                if len(parts) > 2:
                    recommendation = parts[2]
            else:
                rca = parts[0]
                if len(parts) > 1:
                    recommendation = parts[1]

    # Fallback: if still no bug_type, try to extract from first line starting with "bug"
    if not bug_type and t:
        first_line = t.split('\n')[0]
        if 'bug' in first_line.lower() and ':' in first_line:
            bug_type = first_line.split(':', 1)[1].strip()
    
    # Final fallback: if no bug_type found anywhere, set a generic one
    if not bug_type:
        bug_type = 'Functional Bug'

    return {'bug_type': bug_type.strip(), 'rca': rca.strip(), 'recommendation': recommendation.strip()}


def truncate_sentences(text, max_sentences=3):
    """Return first max_sentences sentences from text (naive split)."""
    if not text:
        return ''
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(sentences[:max_sentences]).strip()

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    """Results page - supports both date range and month filtering"""
    # Handle date range parameters (new method)
    start_date = request.args.get('start_date') or request.form.get('start_date')
    end_date = request.args.get('end_date') or request.form.get('end_date')
    
    # Handle month parameter (legacy method)
    month = request.args.get('month') or request.form.get('month')
    
    # If no date range provided, try to use month
    if not start_date or not end_date:
        if month == 'all':
            month = 'all'
        else:
            try:
                month = int(month) if month else 1
            except:
                month = 1
    
    # Pass parameters to template
    return render_template('results.html', month=month, start_date=start_date, end_date=end_date)

@app.route('/stories')
def stories():
    """Bug stories page"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    return render_template('stories.html', start_date=start_date, end_date=end_date)

@app.route('/api/stories')
def api_stories():
    """Get bug stories filtered by month or date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    month_raw = request.args.get('month', 'all')
    
    # Support both new date range and old month parameters
    if start_date and end_date:
        stories = get_bugs_by_date_range(start_date, end_date)
    elif month_raw == 'all':
        stories = get_bugs_by_month()
    else:
        try:
            month = int(month_raw)
        except ValueError:
            month = None
        stories = get_bugs_by_month(month)
    return jsonify(stories)

@app.route('/api/bugs')
def api_bugs():
    """Get bugs AND incidents filtered by month or date range (for display on page)"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    month_raw = request.args.get('month', '1')
    
    # Support both new date range and old month parameters
    if start_date and end_date:
        bugs = get_bugs_by_date_range(start_date, end_date, bugs_only=False)
    elif month_raw == 'all':
        bugs = get_bugs_by_month()
    else:
        try:
            month = int(month_raw)
        except ValueError:
            month = 1
        bugs = get_bugs_by_month(month)
    return jsonify(bugs)

@app.route('/api/rca/<bug_id>')
def api_rca(bug_id):
    """Generate RCA for a bug (check cache first)"""
    bug = get_bug_by_id(bug_id)
    if not bug:
        return jsonify({'rca': 'Bug not found'})
    
    # Check if RCA is already cached
    if bug_id in RCA_CACHE:
        return jsonify({'rca': RCA_CACHE[bug_id]})
    
    rca = generate_rca_via_ollama(bug)
    RCA_CACHE[bug_id] = rca  # Cache the RCA
    return jsonify({'rca': rca})

@app.route('/api/bug/<bug_id>')
def api_bug_detail(bug_id):
    """Get single bug details"""
    bug = get_bug_by_id(bug_id)
    if bug:
        return jsonify(bug)
    return jsonify({'error': 'Bug not found'}), 404

@app.route('/api/generate-all-rcas', methods=['POST'])
def generate_all_rcas():
    """Generate RCA for all bugs in specified month or date range (parallel execution)"""
    month_raw = request.json.get('month', 'all')
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    ids = request.json.get('ids')

    # If explicit ids provided, generate RCAs only for those IDs (visible page selection)
    if ids and isinstance(ids, list):
        bugs = [get_bug_by_id(bid) for bid in ids]
        bugs = [b for b in bugs if b]
        if not bugs:
            return jsonify({'error': 'No valid bug IDs provided'}), 404
    else:
        # Support both new date range and old month parameters
        if start_date and end_date:
            bugs = get_bugs_by_date_range(start_date, end_date)
        elif month_raw == 'all':
            bugs = get_bugs_by_month()
        else:
            try:
                month = int(month_raw)
            except ValueError:
                return jsonify({'error': 'Invalid month'}), 400
            bugs = get_bugs_by_month(month)
    
    if not bugs:
        return jsonify({'error': 'No bugs found for the selected period'}), 404
    
    # Generate RCAs in parallel for all bugs (fast mode: single short model attempt then fallback)
    results = []
    max_workers = min(50, len(bugs))  # Increase concurrency for speed; careful with Ollama capacity
    
    def generate_for_bug(bug):
        """Generate RCA for a single bug"""
        try:
            # Check cache first
            if bug['bug_id'] in RCA_CACHE:
                return {
                    'bug_id': bug['bug_id'],
                    'title': bug['title'],
                    'priority': bug['priority'],
                    'rca': RCA_CACHE[bug['bug_id']],
                    'status': 'cached'
                }
            # Generate new RCA using fast mode for bulk operations
            rca = generate_rca_via_ollama(bug, fast=True)
            RCA_CACHE[bug['bug_id']] = rca
            return {
                'bug_id': bug['bug_id'],
                'title': bug['title'],
                'priority': bug['priority'],
                'rca': rca,
                'status': 'generated'
            }
        except Exception as e:
            return {
                'bug_id': bug['bug_id'],
                'title': bug['title'],
                'priority': bug['priority'],
                'rca': f'Error: {str(e)}',
                'status': 'error'
            }
    
    # Execute in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(generate_for_bug, bug) for bug in bugs]
        for future in as_completed(futures):
            results.append(future.result())
    # Summarize results
    generated = sum(1 for r in results if r.get('status') == 'generated')
    cached = sum(1 for r in results if r.get('status') == 'cached')
    errors = sum(1 for r in results if r.get('status') == 'error')

    return jsonify({
        'success': True,
        'total': len(results),
        'generated': generated,
        'cached': cached,
        'errors': errors,
        'results': results
    })

@app.route('/api/export-rcas', methods=['POST'])
def export_rcas():
    """Export bugs data to Excel file with RCAs (requires ids list from page)"""
    if not OPENPYXL_AVAILABLE:
        return jsonify({'error': 'openpyxl not installed. Run: pip install openpyxl'}), 500
    
    try:
        request_data = request.json or {}
        ids = request_data.get('ids')
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        
        # REQUIRED: Use only the ids provided from the page (exact bugs displayed)
        if not ids or not isinstance(ids, list):
            return jsonify({'error': 'ids parameter required: list of bug IDs to export'}), 400
        
        # Get the exact items (bugs and incidents) from the ids list
        items = [get_bug_by_id(bid) for bid in ids]
        items = [b for b in items if b]  # Remove None values
        
        if not items:
            return jsonify({'error': 'No valid items found for the provided IDs'}), 404
        
        # Generate RCAs for all items (in parallel) to ensure they're in cache
        def generate_for_bug(item):
            """Generate RCA for a single item"""
            item_id = item['bug_id']
            if item_id not in RCA_CACHE:
                rca = generate_rca_via_ollama(item, fast=True)
                RCA_CACHE[item_id] = rca
            return item_id
        
        # Execute RCA generation in parallel
        with ThreadPoolExecutor(max_workers=min(20, len(items))) as executor:
            futures = [executor.submit(generate_for_bug, item) for item in items]
            for future in as_completed(futures):
                future.result()
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'Bug Report'
        
        # Add header row with all required columns
        headers = ['Bug Number', 'Bug Title', 'Type', 'Environment', 'Priority', 'Severity', 'RCA', 'Bug Type', 'Status', 'Created By', 'Assigned To']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF", size=12)
            cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Set column widths
        ws.column_dimensions['A'].width = 15  # Bug Number
        ws.column_dimensions['B'].width = 45  # Bug Title
        ws.column_dimensions['C'].width = 12  # Type
        ws.column_dimensions['D'].width = 12  # Environment
        ws.column_dimensions['E'].width = 12  # Priority
        ws.column_dimensions['F'].width = 12  # Severity
        ws.column_dimensions['G'].width = 50  # RCA
        ws.column_dimensions['H'].width = 20  # Bug Type
        ws.column_dimensions['I'].width = 12  # Status
        ws.column_dimensions['J'].width = 15  # Created By
        ws.column_dimensions['K'].width = 15  # Assigned To
        
        # Add data rows
        for row_num, item in enumerate(items, 2):
            item_id = item['bug_id']
            
            # Get RCA from cache (guaranteed to exist after generation above)
            rca_text = RCA_CACHE.get(item_id, '')
            
            # Parse RCA sections
            parsed = parse_rca_sections(rca_text)
            bug_type = parsed.get('bug_type') or 'Functional Bug'
            rca_field = truncate_sentences(parsed.get('rca') or rca_text, max_sentences=3) if rca_text else 'RCA pending'
            
            # Populate cells
            ws.cell(row=row_num, column=1).value = item_id
            ws.cell(row=row_num, column=2).value = item['title']
            ws.cell(row=row_num, column=3).value = item.get('type', 'bugs')
            ws.cell(row=row_num, column=4).value = item.get('environment', '')
            ws.cell(row=row_num, column=5).value = item.get('priority', '')
            ws.cell(row=row_num, column=6).value = item.get('severity', '')
            ws.cell(row=row_num, column=7).value = rca_field
            ws.cell(row=row_num, column=8).value = bug_type
            ws.cell(row=row_num, column=9).value = item['status']
            ws.cell(row=row_num, column=10).value = item.get('created_by', item.get('assigned_to', ''))
            ws.cell(row=row_num, column=11).value = item['assigned_to']
            
            # Format cells
            for col in range(1, 12):
                cell = ws.cell(row=row_num, column=col)
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            # Set row height for readability
            ws.row_dimensions[row_num].height = 60
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generate filename based on date range
        if start_date and end_date:
            filename = f'Bug_Report_{start_date}_to_{end_date}.xlsx'
        else:
            filename = f'Bug_Report.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error exporting Excel: {str(e)}")
        return jsonify({'error': f'Error exporting data: {str(e)}'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🚀 Initializing TraceRoot Local...")
    print("📊 Generating 200 bugs dynamically...")
    init_database()
    print(f"✅ Loaded {len(BUGS_CACHE)} bugs in memory")
    print("\n" + "="*60)
    print("App is running in:")
    print("   http://127.0.0.1:5000")
    print("\n" + "="*60)
    print("Bug Stories:")
    print("http://127.0.0.1:5000/stories")
    app.run(debug=True, port=5000)
    