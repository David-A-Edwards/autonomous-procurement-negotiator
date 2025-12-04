import streamlit as st
import os
import tempfile
import sys
import requests
import time
import re
import json
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Procure AI Negotiator", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        font-family: 'DM Sans', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #f1f5f9;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .main-header {
        color: #f1f5f9;
        font-size: 32px;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 15px;
        margin-bottom: 32px;
    }
    
    /* Progress stepper */
    .progress-container {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .progress-steps {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .step {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
    }
    
    .step-complete { background: rgba(16, 185, 129, 0.15); color: #10b981; }
    .step-active { background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%); color: white; }
    .step-pending { background: rgba(71, 85, 105, 0.3); color: #64748b; }
    
    .step-info { display: flex; flex-direction: column; }
    .step-label { color: #f1f5f9; font-size: 14px; font-weight: 500; }
    .step-label-pending { color: #64748b; }
    .step-number { color: #64748b; font-size: 12px; }
    
    .step-connector {
        flex: 1;
        height: 2px;
        margin: 0 16px;
        background: rgba(71, 85, 105, 0.3);
        border-radius: 1px;
    }
    .step-connector-complete { background: rgba(16, 185, 129, 0.3); }
    
    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .section-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .section-icon-blue { background: rgba(59, 130, 246, 0.15); }
    .section-icon-green { background: rgba(16, 185, 129, 0.15); }
    .section-icon-purple { background: rgba(168, 85, 247, 0.15); }
    
    .section-title { color: #f1f5f9; font-size: 16px; font-weight: 500; margin: 0; }
    .section-subtitle { color: #64748b; font-size: 13px; margin: 0; }
    
    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }
    .badge-warning { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .badge-success { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: #10b981; }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .stTextInput > label {
        color: #64748b !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-weight: 600 !important;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    
    .stTextArea > label { color: #94a3b8 !important; }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.3);
        border: 2px dashed rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 20px;
    }
    
    [data-testid="stFileUploader"] label { color: #94a3b8 !important; }
    
    /* Primary button */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 30px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px);
    }
    
    /* Secondary button - using custom class via container */
    div[data-testid="column"]:nth-child(2) .stButton > button,
    div[data-testid="column"]:nth-child(3) .stButton > button {
        background: rgba(71, 85, 105, 0.4) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        box-shadow: none !important;
    }
    
    div[data-testid="column"]:nth-child(2) .stButton > button:hover,
    div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        background: rgba(71, 85, 105, 0.6) !important;
        box-shadow: none !important;
        transform: none;
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
    }
    
    .stSelectbox > label {
        color: #64748b !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-weight: 600 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        color: #94a3b8 !important;
    }
    
    /* Status widget */
    [data-testid="stStatusWidget"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 12px !important;
    }
    
    /* Divider */
    hr { border-color: rgba(148, 163, 184, 0.1) !important; }
    
    /* Alert boxes */
    .stAlert {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
    }
    
    div[data-testid="stAlert"] > div { color: #f59e0b !important; }
    
    .element-container:has(.stSuccess) .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #10b981 !important;
    }
    
    .element-container:has(.stWarning) .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.2) !important;
        color: #f59e0b !important;
    }
    
    .element-container:has(.stError) .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        color: #ef4444 !important;
    }
    
    /* Markdown text */
    .stMarkdown { color: #94a3b8; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f1f5f9 !important; }
    .stMarkdown strong { color: #f1f5f9; }
    
    /* Logo */
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 32px; }
    .logo-icon {
        width: 44px; height: 44px;
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px;
    }
    .logo-text { font-size: 18px; font-weight: 600; color: #f1f5f9; }
    .logo-subtext { font-size: 12px; color: #64748b; margin-top: -2px; }
    
    /* Governance panel */
    .governance-panel {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-top: 24px;
    }
    .governance-header {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 16px; color: #f1f5f9;
        font-size: 14px; font-weight: 500;
    }
    .toggle-container {
        display: flex; justify-content: space-between;
        align-items: center; padding: 8px 0;
    }
    .toggle-label { color: #94a3b8; font-size: 13px; }
    .toggle-active {
        background: #10b981; width: 40px; height: 22px;
        border-radius: 11px; position: relative;
    }
    .toggle-active::after {
        content: ''; position: absolute; right: 2px; top: 2px;
        width: 18px; height: 18px; background: white; border-radius: 50%;
    }
    
    /* File upload success */
    .file-uploaded {
        display: flex; align-items: center; gap: 16px; padding: 16px;
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px; margin-top: 12px;
    }
    .file-icon {
        width: 48px; height: 48px;
        background: rgba(16, 185, 129, 0.1);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
    }
    .file-info { flex: 1; }
    .file-name { color: #f1f5f9; font-weight: 500; }
    .file-meta { color: #64748b; font-size: 13px; }
    .file-check { color: #10b981; font-size: 20px; }
    
    /* Email draft */
    .email-draft {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 24px;
        color: #cbd5e1;
        line-height: 1.7;
        font-size: 14px;
        white-space: pre-wrap;
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* Agent log styling */
    .agent-log {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: #94a3b8;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }
    
    .agent-log .agent-name { color: #3b82f6; font-weight: 600; }
    .agent-log .tool-name { color: #10b981; }
    .agent-log .thought { color: #f59e0b; }
    .agent-log .output { color: #a855f7; }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: rgba(71, 85, 105, 0.4) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        box-shadow: none !important;
    }
    
    /* Toggle switch styling */
    [data-testid="stToggle"] {
        background: transparent !important;
    }
    
    [data-testid="stToggle"] label {
        color: #94a3b8 !important;
        font-size: 13px !important;
    }
    
    [data-testid="stToggle"] [data-baseweb="checkbox"] {
        background-color: #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- HELPER CLASSES ---
class CleanCallbackHandler:
    """Cleaner callback handler that formats CrewAI output nicely."""
    
    def __init__(self, container):
        self.container = container
        self.logs = []
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.last_update = time.time()
        # Capture the script context from the main thread for thread-safety
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        self._ctx = get_script_run_ctx()
    
    def _ensure_context(self):
        """Re-attach Streamlit context for background threads."""
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx
            import threading
            add_script_run_ctx(threading.current_thread(), self._ctx)
        except Exception:
            pass
    
    def _clean_text(self, text):
        """Remove ANSI codes and clean up formatting."""
        text = self.ansi_escape.sub('', text)
        # Remove excessive pipe characters and weird formatting
        text = re.sub(r'\s*\|\s*\|\s*', ' ', text)
        text = re.sub(r'\s*\|\s*', ' ', text)
        text = re.sub(r'─+', '', text)
        text = re.sub(r'╭─+╮', '', text)
        text = re.sub(r'╰─+╯', '', text)
        text = re.sub(r'│', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _format_log_entry(self, text):
        """Format a log entry with nice styling."""
        clean = self._clean_text(text)
        if not clean:
            return None
            
        # Detect and style different parts
        if 'Agent:' in clean or 'Agent Started' in clean:
            agent_match = re.search(r'Agent[:\s]+([A-Za-z\s]+)', clean)
            if agent_match:
                return f"🤖 <span class='agent-name'>{agent_match.group(1).strip()}</span>"
        
        if 'Task:' in clean:
            task_match = re.search(r'Task[:\s]+(.+)', clean)
            if task_match:
                return f"📋 {task_match.group(1).strip()}"
        
        if 'Thought:' in clean:
            thought_match = re.search(r'Thought[:\s]+(.+)', clean)
            if thought_match:
                return f"💭 <span class='thought'>{thought_match.group(1).strip()}</span>"
        
        if 'Using Tool:' in clean or 'Tool:' in clean:
            tool_match = re.search(r'(?:Using )?Tool[:\s]+(.+)', clean)
            if tool_match:
                return f"🔧 <span class='tool-name'>{tool_match.group(1).strip()}</span>"
        
        if 'Action:' in clean:
            return f"➡️ {clean.replace('Action:', '').strip()}"
        
        if 'Observation:' in clean or 'Tool Output' in clean:
            return f"👁️ <span class='output'>Result received</span>"
        
        if 'Final Answer:' in clean:
            return f"✅ <span class='output'>Task completed</span>"
        
        # Skip noise
        if len(clean) < 10 or clean.startswith('{') or clean.startswith('"query"'):
            return None
            
        return None
    
    def write(self, data):
        formatted = self._format_log_entry(data)
        if formatted and formatted not in self.logs[-5:] if self.logs else True:
            self.logs.append(formatted)
            
            if time.time() - self.last_update > 0.3:
                self._ensure_context()
                try:
                    # Show last 15 log entries
                    display_logs = self.logs[-15:]
                    html = "<div class='agent-log'>" + "<br>".join(display_logs) + "</div>"
                    self.container.markdown(html, unsafe_allow_html=True)
                    self.last_update = time.time()
                except Exception:
                    pass
    
    def flush(self):
        if self.logs:
            self._ensure_context()
            try:
                display_logs = self.logs[-15:]
                html = "<div class='agent-log'>" + "<br>".join(display_logs) + "</div>"
                self.container.markdown(html, unsafe_allow_html=True)
            except Exception:
                pass


class PerplexitySearchTool(BaseTool):
    name: str = "Perplexity Search"
    description: str = "A fast search engine. Use this for all research tasks."

    def _run(self, query: str) -> str:
        current_date = datetime.now().strftime("%B %Y")
        
        url = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": f"You are a research assistant. Today's date is {current_date}. Always provide the most recent and up-to-date information available. When discussing financial data, prioritise 2024 and 2025 figures over older data. Be precise and factual."},
                {"role": "user", "content": query}
            ]
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
            "Content-Type": "application/json"
        }
        if not os.getenv('PERPLEXITY_API_KEY'):
            return "Error: Perplexity API Key is missing."
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code != 200:
                return f"Perplexity Error: {response.text}"
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Perplexity Failed: {e}"


# --- SESSION STATE ---
if "research_results" not in st.session_state:
    st.session_state.research_results = None
if "analyst_results" not in st.session_state:
    st.session_state.analyst_results = None
if "strategy_proposal" not in st.session_state:
    st.session_state.strategy_proposal = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "final_email" not in st.session_state:
    st.session_state.final_email = None
if "vendor_name_saved" not in st.session_state:
    st.session_state.vendor_name_saved = ""
if "human_in_loop" not in st.session_state:
    st.session_state.human_in_loop = True
if "audit_logging" not in st.session_state:
    st.session_state.audit_logging = True
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">⚡</div>
            <div>
                <div class="logo-text">Procure</div>
                <div class="logo-subtext">AI Negotiator</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### Navigation")
    st.markdown("🧠 **Negotiation**")
    st.markdown("<span style='color: #64748b;'>📄 Contracts</span>", unsafe_allow_html=True)
    st.markdown("<span style='color: #64748b;'>🏢 Vendors</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    model_choice = st.selectbox("AI MODEL", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0)
    
    # Governance section with real toggles
    st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 12px; padding: 16px; margin-top: 24px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #f1f5f9; font-size: 14px; font-weight: 500;">
                🛡️ Governance
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Real working toggles - key syncs with session state (initialized above)
    st.toggle("Human in Loop", key="human_in_loop")
    st.toggle("Audit Logging", key="audit_logging")
    
    # Show audit log if there are entries
    if st.session_state.audit_log:
        with st.expander(f"📋 Audit Log ({len(st.session_state.audit_log)} events)"):
            for entry in reversed(st.session_state.audit_log[-10:]):  # Show last 10
                st.markdown(f"**{entry['timestamp']}**")
                st.markdown(f"_{entry['event']}_ - {entry['details']}")
                st.markdown("---")
    
    st.markdown("---")
    env_perplexity = os.getenv("PERPLEXITY_API_KEY")
    if env_perplexity:
        st.success("⚡ Perplexity Active")
    else:
        st.warning("⚠️ Using Serper")


# --- HELPER FUNCTIONS ---
def log_audit_event(event_type: str, details: str):
    """Log an event to the audit trail if audit logging is enabled."""
    # Check if we have a valid Streamlit context
    ctx = get_script_run_ctx()
    if ctx is None:
        return  # Skip logging if called from background thread
    
    if st.session_state.get("audit_logging", True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.audit_log.append({
            "timestamp": timestamp,
            "event": event_type,
            "details": details
        })


def render_progress_steps(current_step, container=None):
    steps = [("Configure", "⚙️"), ("Upload", "📤"), ("Analyze", "🔍"), ("Refine", "✏️"), ("Generate", "📧")]
    
    html = '<div class="progress-container"><div class="progress-steps">'
    
    for i, (label, icon) in enumerate(steps):
        step_num = i + 1
        
        if step_num < current_step:
            status_class, label_class, circle_content = "step-complete", "step-label", "✓"
        elif step_num == current_step:
            status_class, label_class, circle_content = "step-active", "step-label", icon
        else:
            status_class, label_class, circle_content = "step-pending", "step-label step-label-pending", str(step_num)
        
        html += f'''
            <div class="step">
                <div class="step-circle {status_class}">{circle_content}</div>
                <div class="step-info">
                    <div class="{label_class}">{label}</div>
                    <div class="step-number">Step {step_num}</div>
                </div>
            </div>
        '''
        
        if i < len(steps) - 1:
            connector_class = "step-connector-complete" if step_num < current_step else ""
            html += f'<div class="step-connector {connector_class}"></div>'
    
    html += '</div></div>'
    
    if container:
        container.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def generate_pdf(email_content, vendor_name):
    """Generate a PDF from the email content."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Heading1']
        story.append(Paragraph(f"Negotiation Email - {vendor_name}", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Content
        body_style = styles['Normal']
        body_style.fontSize = 11
        body_style.leading = 16
        
        for para in email_content.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.replace('\n', '<br/>'), body_style))
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    except ImportError:
        # Fallback: create a simple text file if reportlab not available
        buffer = BytesIO()
        buffer.write(f"Negotiation Email - {vendor_name}\n\n".encode('utf-8'))
        buffer.write(email_content.encode('utf-8'))
        buffer.seek(0)
        return buffer


# --- MAIN INTERFACE ---
st.markdown('<h1 class="main-header">Autonomous Procurement Negotiator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered contract analysis and negotiation strategy generation</p>', unsafe_allow_html=True)

# Create a placeholder for progress steps - will be filled after we know inputs
progress_placeholder = st.empty()

# Input Section
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
        <div class="section-header">
            <div class="section-icon section-icon-blue">🏢</div>
            <div><p class="section-title">Vendor Details</p></div>
        </div>
    """, unsafe_allow_html=True)
    vendor_name = st.text_input("VENDOR NAME", placeholder="e.g., WeWork", label_visibility="visible")

with col2:
    st.markdown("""
        <div class="section-header">
            <div class="section-icon section-icon-green">📄</div>
            <div><p class="section-title">Contract Document</p></div>
        </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload contract file", type=["txt", "pdf"], label_visibility="collapsed")
    
    if uploaded_file:
        file_size = len(uploaded_file.getvalue()) / 1024
        st.markdown(f"""
            <div class="file-uploaded">
                <div class="file-icon">📄</div>
                <div class="file-info">
                    <div class="file-name">{uploaded_file.name}</div>
                    <div class="file-meta">{file_size:.1f} KB • Uploaded successfully</div>
                </div>
                <div class="file-check">✓</div>
            </div>
        """, unsafe_allow_html=True)

# Calculate current step based on actual state
if st.session_state.final_email:
    display_step = 5
elif st.session_state.strategy_proposal:
    display_step = 4
elif uploaded_file and vendor_name:
    display_step = 3  # Ready to analyse
elif vendor_name or uploaded_file:
    display_step = 2  # Partially complete
else:
    display_step = 1  # Initial state

# Now render the progress bar into the placeholder at the top
render_progress_steps(display_step, progress_placeholder)


# --- STAGE 1: ANALYSIS ---
st.markdown("<br>", unsafe_allow_html=True)

if st.button("🔍 Analyze & Propose Strategy", use_container_width=True):
    if not vendor_name or not uploaded_file:
        st.error("⚠️ Please provide both Vendor Name and Contract document.")
    else:
        # Audit log
        log_audit_event("Analysis Started", f"Vendor: {vendor_name}, File: {uploaded_file.name}")
        
        # Update step to Analyze
        st.session_state.current_step = 3
        st.session_state.vendor_name_saved = vendor_name
        os.environ["OPENAI_MODEL_NAME"] = model_choice
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        research_tool = PerplexitySearchTool() if os.getenv("PERPLEXITY_API_KEY") else SerperDevTool()
        file_tool = FileReadTool(file_path=tmp_path)

        researcher = Agent(
            role='Senior Vendor Intelligence Officer',
            goal=f'Uncover the latest financial risks and current market position for {vendor_name}',
            verbose=True,
            backstory="Forensic accountant specialising in current financial analysis. You always search for the most recent data from 2024-2025, never relying on outdated information.",
            tools=[research_tool],
            max_iter=2
        )

        analyst = Agent(
            role='Procurement Risk Analyst',
            goal='Identify dangerous clauses',
            verbose=True,
            backstory="Skeptical lawyer focusing on termination traps.",
            tools=[file_tool]
        )

        negotiator = Agent(
            role='Lead Negotiator',
            goal='Formulate a winning negotiation strategy',
            verbose=True,
            backstory="Master strategist. You plan the deal before you write the email.",
        )

        current_year = datetime.now().year
        
        task1 = Task(
            description=f"Research {vendor_name}'s CURRENT financial status, market position, and any recent news from {current_year}. Focus on the most recent quarterly results, any financial difficulties, market challenges, or strategic changes. Do NOT use data older than 2024.",
            expected_output="A current risk report with 2024-2025 financial data.",
            agent=researcher
        )
        task2 = Task(description="Analyse the contract and summarise red flags.", expected_output="Red Flag list.", agent=analyst)
        task3 = Task(
            description=(
                "Review the Research and Contract Analysis. "
                f"Using the CURRENT {current_year} financial data and market conditions from the research, "
                "synthesize a 5-point Negotiation Strategy. "
                "For each point, explain WHY we have leverage based on current circumstances. "
                "Reference specific recent figures and events where possible. "
                "Do NOT write the email yet. Just the strategy plan."
            ),
            expected_output="A bulleted negotiation strategy based on current 2024-2025 data.",
            agent=negotiator
        )

        crew_stage_1 = Crew(agents=[researcher, analyst, negotiator], tasks=[task1, task2, task3], process=Process.sequential)

        with st.status("🔍 Analysing vendor and contract...", expanded=True):
            log_container = st.empty()
            callback_handler = CleanCallbackHandler(log_container)
            sys.stdout = callback_handler
            
            try:
                crew_stage_1.kickoff()
                
                st.session_state.research_results = task1.output.raw
                st.session_state.analyst_results = task2.output.raw
                st.session_state.strategy_proposal = task3.output.raw
                st.session_state.current_step = 4
                
                # Audit log
                log_audit_event("Analysis Complete", f"Strategy generated for {vendor_name}")
            finally:
                sys.stdout = sys.__stdout__
                os.unlink(tmp_path)
        
        st.rerun()


# --- STAGE 2: STRATEGY REFINEMENT ---
if st.session_state.strategy_proposal:
    st.markdown("---")
    
    # Raw Intelligence
    st.markdown("""
        <div class="section-header">
            <div class="section-icon section-icon-purple">👁️</div>
            <div>
                <p class="section-title">Raw Intelligence</p>
                <p class="section-subtitle">Research and contract analysis data</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("View Research & Contract Analysis"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**📊 Research Findings**")
            st.markdown(st.session_state.research_results)
        with col_b:
            st.markdown("**🚩 Contract Red Flags**")
            st.markdown(st.session_state.analyst_results)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Strategy Section
    vendor_display = st.session_state.vendor_name_saved or vendor_name
    
    # Show different UI based on Human in Loop setting
    if st.session_state.human_in_loop:
        st.markdown(f"""
            <div class="section-header">
                <div class="section-icon section-icon-blue">✨</div>
                <div>
                    <p class="section-title">Negotiation Strategy</p>
                    <p class="section-subtitle">AI-generated strategy for {vendor_display}</p>
                </div>
                <div style="margin-left: auto;">
                    <span class="badge badge-warning">⚠️ Review Required</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 Human in Loop is ON. Review and edit the strategy below before generating the email.")
    else:
        st.markdown(f"""
            <div class="section-header">
                <div class="section-icon section-icon-blue">✨</div>
                <div>
                    <p class="section-title">Negotiation Strategy</p>
                    <p class="section-subtitle">AI-generated strategy for {vendor_display}</p>
                </div>
                <div style="margin-left: auto;">
                    <span class="badge badge-success">✓ Auto Mode</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.warning("⚡ Human in Loop is OFF. Strategy will be used as-is. Toggle it ON in the sidebar to review before generating.")
    
    final_strategy = st.text_area(
        "Strategy (Editable):", 
        value=st.session_state.strategy_proposal, 
        height=300,
        label_visibility="collapsed",
        disabled=not st.session_state.human_in_loop  # Disable editing if Human in Loop is off
    )

    # Buttons in proper layout
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        generate_clicked = st.button("📧 Generate Final Email", use_container_width=True, key="gen_email")
    
    with btn_col2:
        regen_clicked = st.button("🔄 Regenerate Strategy", use_container_width=True, key="regen_strategy")
    
    if generate_clicked:
        # Audit log
        review_mode = "with human review" if st.session_state.human_in_loop else "auto mode (no review)"
        log_audit_event("Email Generation Started", f"Generating email for {vendor_display} - {review_mode}")
        
        st.session_state.current_step = 5
        os.environ["OPENAI_MODEL_NAME"] = model_choice
        
        negotiator = Agent(
            role='Lead Negotiator',
            goal='Draft the perfect email',
            verbose=True,
            backstory="Master negotiator. You write professional, firm, and persuasive emails.",
        )

        final_prompt = f"""
        Draft a negotiation email to {vendor_display} based STRICTLY on this strategy:
        
        {final_strategy}
        
        Keep the tone professional but firm. Use the specific leverage points mentioned in the strategy.
        Include a clear subject line at the start.
        """

        task_final = Task(description=final_prompt, expected_output="Final Email Draft.", agent=negotiator)
        crew_stage_2 = Crew(agents=[negotiator], tasks=[task_final], process=Process.sequential)

        with st.status("✍️ Crafting email...", expanded=True):
            log_container = st.empty()
            callback_handler = CleanCallbackHandler(log_container)
            sys.stdout = callback_handler
            
            try:
                crew_stage_2.kickoff()
                st.session_state.final_email = task_final.output.raw
                
                # Audit log
                log_audit_event("Email Generated", f"Draft ready for {vendor_display}")
            finally:
                sys.stdout = sys.__stdout__
        
        st.rerun()
    
    if regen_clicked:
        log_audit_event("Strategy Regeneration", f"User requested new strategy for {vendor_display}")
        st.session_state.strategy_proposal = None
        st.session_state.current_step = 2
        st.rerun()


# --- FINAL EMAIL OUTPUT ---
if st.session_state.final_email:
    st.markdown("---")
    
    st.markdown(f"""
        <div class="section-header">
            <div class="section-icon section-icon-green">📧</div>
            <div>
                <p class="section-title">Final Draft</p>
                <p class="section-subtitle">Ready for review and sending</p>
            </div>
            <div style="margin-left: auto;">
                <span class="badge badge-success">✓ Draft Ready</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display email in styled container
    st.markdown(f"""<div class="email-draft">{st.session_state.final_email}</div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons
    col_e1, col_e2, col_e3 = st.columns(3)
    
    vendor_display = st.session_state.vendor_name_saved or vendor_name
    
    with col_e1:
        st.info("📤 'Send to Vendor' requires email integration (SMTP setup)")
    
    with col_e2:
        # Copy to clipboard button with JavaScript
        import html
        escaped_email = html.escape(st.session_state.final_email).replace('\n', '\\n').replace("'", "\\'")
        copy_js = f"""
        <button onclick="
            navigator.clipboard.writeText('{escaped_email}'.replace(/\\\\n/g, '\\n'));
            this.innerHTML='✅ Copied!';
            this.style.background='#10b981';
            setTimeout(()=>{{this.innerHTML='📋 Copy to Clipboard';this.style.background='#3b82f6';}}, 2000);
        " style="
            width: 100%;
            padding: 0.75rem 1rem;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        ">📋 Copy to Clipboard</button>
        """
        st.components.v1.html(copy_js, height=50)
    
    with col_e3:
        # PDF Download
        try:
            pdf_buffer = generate_pdf(st.session_state.final_email, vendor_display)
            st.download_button(
                label="📥 Download as PDF",
                data=pdf_buffer,
                file_name=f"negotiation_email_{vendor_display.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            # Fallback to text file
            st.download_button(
                label="📥 Download as TXT",
                data=st.session_state.final_email,
                file_name=f"negotiation_email_{vendor_display.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start New Negotiation", use_container_width=True):
        log_audit_event("Session Reset", "User started new negotiation")
        st.session_state.research_results = None
        st.session_state.analyst_results = None
        st.session_state.strategy_proposal = None
        st.session_state.final_email = None
        st.session_state.current_step = 1
        st.session_state.vendor_name_saved = ""
        st.rerun()