# TraceRoot Local - Bug Analysis Platform

A single-file Flask application for analyzing and managing bug reports with AI-powered Root Cause Analysis (RCA) using Ollama.

## 🎯 Features

- **Dynamic Bug Generation**: ~200 realistic bugs generated automatically with diverse data
- **Month-Based Filtering**: Filter bugs by month of creation
- **Real-Time Search**: Filter bugs by ID or title
- **Interactive UI**: Modern dark-themed glassmorphism design
- **Bug Details Modal**: View comprehensive bug information
- **RCA Generation**: AI-powered Root Cause Analysis via Ollama (local model)
- **Statistics Dashboard**: View bug counts by status and priority

## 📋 Prerequisites

- Python 3.8+
- Ollama (optional, for RCA generation)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd TraceRoot
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask - Web framework
- Requests - HTTP library
- Python-PPTX - PowerPoint generation
- ReportLab - PDF generation
- OpenPyXL - Excel file handling

### 4. Install & Start Ollama (Optional - for RCA Generation)

For Root Cause Analysis generation, install Ollama from [ollama.ai](https://ollama.ai)

Then run:
```bash
ollama run mistral
# or
ollama run llama2
```

### 5. Run the Application

```bash
python app.py
```

The app will start on `http://127.0.0.1:5000`

## 🎮 Usage

### Landing Page
1. Enter an ADO Board URL (any URL works, it's for UI purposes)
2. Select a month from the dropdown
3. Click "Continue"

### Bug Results Page
- **Search**: Use the search bar to filter by Bug ID or Title
- **View Details**: Click any bug card to open the details modal
- **Generate RCA**: RCA is automatically generated when you open a bug (requires Ollama running)

### Bug Details Modal
- View all bug information: status, priority, severity, etc.
- Read description and reproduction steps
- View AI-generated Root Cause Analysis
- Download report as PDF or Word

## 📊 Data Structure

Each bug includes:
- `bug_id`: Unique identifier (#601000, #601001, etc.)
- `title`: Bug title/summary
- `description`: Detailed description
- `repro_steps`: Step-by-step reproduction instructions
- `status`: New, Closed, Resolved, In Progress, On Hold
- `priority`: P1, P2, P3, P4, P5
- `severity`: 1 (High), 2 (Medium), 3 (Low)
- `assigned_to`: Team member name
- `created_date`: Random date across past 365 days
- `environment`: PRD, UAT, DEV, STAGING
- `category`: Data Processing, API Integration, Authentication, etc.

## 🖼️ UI Design

- **Dark Gradient Background**: #0f172a → #1e293b
- **Glassmorphism Cards**: Blur + transparency effect
- **Smooth Animations**: Hover effects and transitions
- **Responsive Layout**: Grid adapts to screen size
- **Modal Popups**: Animated overlays for bug details

## 🔧 Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Landing page |
| `/results` | GET/POST | Bug results page |
| `/api/bugs` | GET | Get bugs by month (JSON) |
| `/api/bug/<id>` | GET | Get single bug details (JSON) |
| `/api/rca/<id>` | GET | Generate RCA via Ollama (JSON) |

## 🤖 RCA Generation (Ollama Integration)

The app calls Ollama's local API for Root Cause Analysis:

```
POST http://localhost:11434/api/generate
```

**Note**: If Ollama is not running, the RCA will show a helpful message.

## 🎨 Libraries Used

- **Flask**: Web framework
- **requests**: HTTP calls to Ollama

## ⚡ Performance

- **Bugs**: ~200 dynamically generated bugs loaded in memory
- **Speed**: Sub-100ms response times
- **Memory**: Minimal footprint (~10MB with all bugs)

## 🛑 Troubleshooting

### "Ollama not running" message
- Start Ollama with: `ollama run mistral` or `ollama run llama2`
- Wait 30 seconds for model to load
- RCA will generate once connection established

### Bugs not showing
- Ensure you selected a month with bugs (most months have 15-20 bugs)
- Try December or other months

## 📝 Notes

- All bugs are generated randomly on app startup
- Data is stored in-memory (lost on app restart)
- No external files or databases required
- Everything is contained in `app.py`

## 📄 License

Open source - feel free to modify and extend!

---

**TraceRoot Local** - Single-File Bug Analysis Platform
