import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import sys
from dotenv import load_dotenv
import logging
import html
import pyperclip

# Configure Streamlit for better JavaScript support
st.set_page_config(
    page_title="Augur - AI-Powered Incident Analysis",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "🔮 Augur - AI-Powered Incident Post-Mortem Report Generator"
    }
)

# Add src directory to path to allow for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from analyzer import IncidentAnalyzer
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Manual fallback: read .env file directly to ensure it's loaded
env_path = Path('.env')
if env_path.exists():
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
    except Exception as e:
        pass  # Silently handle any errors

# Set up logging to a file
logging.basicConfig(
    filename='augur_app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

def generate_audience_summary(report_md, prompt):
    """Generate an audience-specific summary using the LLM."""
    from src.analyzer import IncidentAnalyzer
    analyzer = IncidentAnalyzer(api_key=getattr(st.session_state, 'user_api_key', None))
    summary_prompt = f"""
You are an expert communicator. Here is a post-mortem report:

{report_md}

{prompt}
"""
    response = analyzer.llm.invoke(summary_prompt)
    return response.content.strip()

# --- Helper Functions ---
def get_available_demos():
    demo_path = 'incidents'
    if os.path.exists(demo_path):
        return [d for d in os.listdir(demo_path) if os.path.isdir(os.path.join(demo_path, d))]
    return []

def save_uploaded_files(uploaded_files):
    temp_dir = "temp_incident"
    logs_path = os.path.join(temp_dir, "logs")
    metrics_path = os.path.join(temp_dir, "metrics")
    # Clean up any previous temp incident
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(logs_path, exist_ok=True)
    os.makedirs(metrics_path, exist_ok=True)
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".log":
            file_path = os.path.join(logs_path, filename)
        elif ext == ".csv":
            file_path = os.path.join(metrics_path, filename)
        else:
            file_path = os.path.join(temp_dir, filename)  # fallback for unknown types
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    return temp_dir

def analyze_incident_data(incident_path, api_key=None):
    try:
        logging.info(f"Starting analysis for: {incident_path}")
        analyzer = IncidentAnalyzer(api_key=api_key)
        results = analyzer.generate_report(incident_path)
        if isinstance(results, str):
            logging.warning("Analyzer returned a string instead of a dict. Wrapping for compatibility.")
            results = {"report_markdown": results, "timeline_events": [], "metrics_df": None}
        
        # Get the raw context for chat
        try:
            raw_context, _ = analyzer._load_and_prepare_data(incident_path)
            results['raw_context'] = raw_context
        except Exception as e:
            logging.warning(f"Could not load raw context for chat: {e}")
            results['raw_context'] = ""
        
        results['analyzer'] = analyzer  # Attach analyzer for chat
        logging.info(f"Analysis complete for: {incident_path}")
        return results
    except Exception as e:
        logging.error(f"Failed to analyze incident: {incident_path} | Error: {e}")
        st.error(f"Failed to analyze incident: {e}")
        return None

def handle_chat_submission():
    """Handle chat message submission without triggering full page rerun."""
    if st.session_state.pending_chat_message:
        prompt = st.session_state.pending_chat_message
        st.session_state.pending_chat_message = None
        
        # Add user message to history
        st.session_state.chat_history.append(("user", prompt))
        
        # Get AI response
        if 'analyzer' in st.session_state and st.session_state.analyzer:
            raw_context = getattr(st.session_state, 'raw_context_for_chat', None)
            report_context = getattr(st.session_state, 'report_for_chat', None)
            response = st.session_state.analyzer.follow_up_question(prompt, raw_context, report_context)
            st.session_state.chat_history.append(("assistant", response))
        
        st.session_state.chat_processed = True

def chat_callback():
    """Callback function for chat form submission."""
    if st.session_state.chat_text_input_unique:
        st.session_state.pending_chat_message = st.session_state.chat_text_input_unique
        st.session_state.chat_text_input_unique = ""  # Clear the input

# --- Inject custom CSS for modern look ---
st.markdown("""
<style>
/* Hide noscript message */
noscript {
    display: none !important;
}

/* Ensure JavaScript functionality */
.stApp {
    min-height: 100vh;
}

/* Main button style for primary action */
.stButton>button[kind="primary"] {
    background-color: #4A90E2;
    color: white;
}
.stButton>button[kind="primary"]:hover {
    background-color: #357ABD;
    color: white;
}

/* General button and component styling */
.stButton>button, .stSelectbox, .stTextInput, .stFileUploader {
    border-radius: 8px !important;
}

/* Basic chat input styling */
.stChatInput {
    background: transparent !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
}
</style>

<script>
// Ensure proper app initialization
document.addEventListener('DOMContentLoaded', function() {
    // Hide any noscript messages
    const noscriptElements = document.querySelectorAll('noscript');
    noscriptElements.forEach(function(element) {
        element.style.display = 'none';
    });
    
    // Ensure Streamlit app is properly loaded
    if (typeof window.parent !== 'undefined' && window.parent.postMessage) {
        window.parent.postMessage({type: 'streamlit:setComponentValue'}, '*');
    }
});

// Additional JavaScript to handle any loading issues
window.addEventListener('load', function() {
    // Remove any noscript messages that might appear
    const noscriptElements = document.querySelectorAll('noscript');
    noscriptElements.forEach(function(element) {
        element.remove();
    });
});
</script>
""", unsafe_allow_html=True)

# --- Set wide layout ---
st.set_page_config(
    page_title="Augur",
    page_icon="🔮",
    layout="wide"
)

# --- Session State Initialization ---
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'incident_id' not in st.session_state:
    st.session_state.incident_id = None
if 'report' not in st.session_state:
    st.session_state.report = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'pending_chat_message' not in st.session_state:
    st.session_state.pending_chat_message = None
if 'chat_processed' not in st.session_state:
    st.session_state.chat_processed = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📄 Post-Mortem Report"

# --- Home View ---
def render_home_view():
    st.title("🔮 Augur")
    st.markdown("### AI-Powered Incident Post-Mortem Generator")
    st.write("Select one of the options below to get started with AI-powered incident analysis.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("#### Explore Demo Incidents")
            st.write("Experience Augur with pre-generated, realistic incident scenarios.")
            demo_incidents = get_available_demos()
            demo_choice = st.selectbox(
                "Choose a Demo Incident:",
                options=["--Select--"] + demo_incidents,
                key="demo_select"
            )
            if st.button("Analyze Demo", use_container_width=True, type="primary", key="analyze_demo_btn"):
                if demo_choice != "--Select--":
                    st.session_state.incident_id = demo_choice
                    st.session_state.current_view = 'analysis'
                    st.session_state.report = None
                    st.session_state.analyzer = None
                    st.session_state.chat_history = []
                    st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("#### Analyze Your Own Data")
            st.write("Upload your incident logs and metrics for personalized analysis. **No data is stored by the application.** All data is sent directly to Google AI API for processing.")
            st.markdown(
                '''
                <style>
                .help-link {
                    color: #4A90E2;
                    font-size: 0.95em;
                    text-decoration: underline;
                    cursor: pointer;
                }
                </style>
                ''',
                unsafe_allow_html=True
            )
            
            # Add the header for the API key input
            st.markdown('<label for="user_api_key_input" style="font-weight: 500;">Enter your Google AI API Key:</label>', unsafe_allow_html=True)
            
            # Replace the button and complex state management with a simple expander
            with st.expander("🔑 How do I get a Google AI API Key?", expanded=False):
                st.info("""
**To use Augur's AI features, you'll need a Google AI API Key.**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and sign in with your Google account.
2. Click **Create API Key** and follow the prompts.
3. Copy the generated key and paste it here.
4. Keep your key secure—do not share it publicly.

[Read the official Google API Key documentation](https://aistudio.google.com/app/apikey)
                """)
                    
            user_api_key = st.text_input(
                "Google AI API Key",  # Non-empty label for accessibility
                type="password",
                key="user_api_key",
                label_visibility="collapsed"
            )
            uploaded_files = st.file_uploader(
                "Upload your incident files", 
                accept_multiple_files=True, 
                key="user_upload",
                help="Supported file types: .log (log files), .csv (metrics data), .txt (text files), .json (structured data)"
            )
            if st.button("Analyze My Data", use_container_width=True, key="analyze_user_btn"):
                if not st.session_state.user_api_key:
                    st.warning("Please enter your Google AI API Key.")
                elif not uploaded_files:
                    st.warning("Please upload your incident files.")
                else:
                    temp_path = save_uploaded_files(uploaded_files)
                    st.session_state.incident_id = temp_path
                    st.session_state.current_view = 'analysis'
                    st.session_state.report = None
                    st.session_state.analyzer = None
                    st.session_state.chat_history = []
                    st.rerun()

# --- Horizontal Timeline Renderer ---
def render_horizontal_timeline(timeline_events):
    """
    Renders a dynamic, horizontal timeline with visible time markers.
    The granularity of markers changes based on the total duration.
    """
    from datetime import datetime, timedelta
    import re
    import html
    import logging

    def parse_start_time(time_str: str) -> datetime | None:
        """Extracts start time from various formats."""
        match = re.match(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}(?::\d{2})?)", time_str)
        if not match:
            return None
        time_part = match.group(1)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(time_part, fmt)
            except ValueError:
                pass
        return None

    if not timeline_events:
        st.info("No timeline events to display.")
        return

    parsed_events = []
    for event in timeline_events:
        dt = parse_start_time(event.get('time', ''))
        if dt:
            parsed_events.append({'dt': dt, 'data': event})

    if len(parsed_events) < 2:
        st.info("A timeline requires at least two events with valid timestamps.")
        return

    start_time = min(e['dt'] for e in parsed_events)
    end_time = max(e['dt'] for e in parsed_events)
    duration = end_time - start_time

    markers = []
    if duration.total_seconds() > 1:
        if duration < timedelta(hours=2):
            step, fmt = timedelta(minutes=10), '%H:%M'
            start_marker = start_time.replace(second=0, microsecond=0) - timedelta(minutes=start_time.minute % 10)
        elif duration < timedelta(days=2):
            step, fmt = timedelta(hours=1), '%H:00'
            start_marker = start_time.replace(minute=0, second=0, microsecond=0)
        else:
            step, fmt = timedelta(days=1), '%b %d'
            start_marker = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

        current_marker_time = start_marker
        while current_marker_time <= end_time + step:
            if current_marker_time >= start_time - step:
                markers.append({'dt': current_marker_time, 'label': current_marker_time.strftime(fmt)})
            current_marker_time += step

    st.markdown("""
    <style>
    .timeline-horizontal {
        position: relative;
        width: 100%;
        max-width: 900px;
        height: 70px; /* Increased height for labels */
        margin: 2em auto;
    }
    .timeline-horizontal .line {
        position: absolute;
        top: 25px; /* Position line higher */
        left: 0;
        width: 100%;
        height: 4px;
        background: #e0e7ef;
        z-index: 0;
    }
    .timeline-horizontal .line.highlight {
        background: #4A90E2;
    }
    .timeline-dot {
        position: absolute;
        top: 25px;
        z-index: 1;
        width: 20px;
        height: 20px;
        background: #4A90E2;
        border-radius: 50%;
        border: 3px solid #fff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        cursor: pointer;
        transform: translate(-50%, -50%);
        transition: transform 0.2s ease-out, box-shadow 0.2s ease-out;
    }
    .timeline-dot:hover {
        transform: translate(-50%, -60%) scale(1.2); /* Raise up and scale */
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); /* Enhance shadow */
        z-index: 2; /* Bring to front */
    }
    .timeline-dot:hover .timeline-tooltip { visibility: visible; opacity: 1; }
    .timeline-tooltip {
        visibility: hidden; width: 260px; background: #222; color: #fff;
        text-align: left; border-radius: 6px; padding: 10px 14px;
        position: absolute; z-index: 10; bottom: 30px; left: 50%;
        transform: translateX(-50%); opacity: 0; transition: opacity 0.2s;
        font-size: 0.95rem; pointer-events: none;
    }
    .timeline-label {
        position: absolute;
        top: 50px; /* Position labels below the line */
        transform: translateX(-50%);
        font-size: 0.8rem;
        color: #6c757d;
    }
    </style>
    """, unsafe_allow_html=True)

    html_parts = ['<div class="timeline-horizontal">', '<div class="line"></div>']
    
    # Render time markers
    if duration.total_seconds() > 0:
        for marker in markers:
            pos_percent = ((marker['dt'] - start_time).total_seconds() / duration.total_seconds()) * 100
            if 0 <= pos_percent <= 100:
                html_parts.append(f'<div class="timeline-label" style="left: {pos_percent}%;">{marker["label"]}</div>')

    # Render event dots
    for event in parsed_events:
        pos_percent = ((event['dt'] - start_time).total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 50
        
        safe_time = html.escape(event['data'].get('time', ''))
        safe_event = html.escape(event['data'].get('event', ''))

        dot_html = (
            f'<div class="timeline-dot" style="left: {pos_percent}%;">'
            f'<div class="timeline-tooltip"><b>{safe_time}</b><br/>{safe_event}</div>'
            '</div>'
        )
        html_parts.append(dot_html)

    html_parts.append('</div>')
    final_html = "".join(html_parts)
    st.markdown(final_html, unsafe_allow_html=True)

# --- Timeline with Events Renderer ---
def render_timeline_with_events(timeline_events):
    """
    Render a horizontal timeline chart only. If an event has a time range, show a shaded region for that range.
    """
    from datetime import datetime, timedelta
    import html
    import re

    if not timeline_events or len(timeline_events) < 2:
        st.info("No significant timeline events found for charting.")
        return

    # Parse times for positioning
    def parse_time(time_str):
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)", time_str)
        if not match:
            return None
        time_part = match.group(1)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(time_part, fmt)
            except ValueError:
                pass
        return None

    # Detect range events and normal events
    parsed_events = []
    range_events = []
    for event in timeline_events:
        time_field = event.get('time', '')
        # Range: YYYY-MM-DD HH:MM:SS - HH:MM:SS or - YYYY-MM-DD HH:MM:SS
        range_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)\s*-\s*(\d{2}:\d{2}(?::\d{2})?|\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)", time_field)
        if range_match:
            start_str = range_match.group(1)
            end_str = range_match.group(2)
            start_dt = parse_time(start_str)
            # If end_str is just a time, prepend the date from start_str
            if re.match(r"^\d{2}:\d{2}(?::\d{2})?$", end_str):
                date_part = start_str.split()[0]
                end_str_full = f"{date_part} {end_str}"
            else:
                end_str_full = end_str
            end_dt = parse_time(end_str_full)
            if start_dt and end_dt:
                range_events.append({'start': start_dt, 'end': end_dt, 'data': event})
            continue
        # Normal event
        dt = parse_time(time_field)
        if dt:
            parsed_events.append({'dt': dt, 'data': event})

    if not parsed_events and not range_events:
        st.info("A timeline requires at least two events with valid timestamps.")
        return

    # For timeline bounds, consider all points
    all_times = [e['dt'] for e in parsed_events] + [r['start'] for r in range_events] + [r['end'] for r in range_events]
    start_time = min(all_times)
    end_time = max(all_times)
    duration = end_time - start_time

    # CSS for timeline and range
    st.markdown("""
    <style>
    .timeline-horizontal { position: relative; width: 100%; max-width: 900px; height: 70px; margin: 2em auto; }
    .timeline-horizontal .line { position: absolute; top: 25px; left: 0; width: 100%; height: 4px; background: #e0e7ef; z-index: 0; }
    .timeline-dot { position: absolute; top: 25px; z-index: 2; width: 20px; height: 20px; background: #4A90E2; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.08); cursor: pointer; transform: translate(-50%, -50%); transition: transform 0.2s, box-shadow 0.2s; }
    .timeline-dot:hover { transform: translate(-50%, -60%) scale(1.2); box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 3; }
    .timeline-dot:hover .timeline-tooltip { visibility: visible; opacity: 1; }
    .timeline-tooltip { visibility: hidden; width: 260px; background: #222; color: #fff; text-align: left; border-radius: 6px; padding: 10px 14px; position: absolute; z-index: 10; bottom: 30px; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; font-size: 0.95rem; pointer-events: none; }
    .timeline-label { position: absolute; top: 50px; transform: translateX(-50%); font-size: 0.8rem; color: #6c757d; }
    .timeline-range { position: absolute; top: 18px; height: 20px; background: rgba(76, 175, 80, 0.18); border-radius: 8px; z-index: 1; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

    # Build the timeline HTML
    html_parts = ['<div class="timeline-horizontal">', '<div class="line"></div>']

    # Render range bars first (behind dots)
    for r in range_events:
        left = ((r['start'] - start_time).total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 0
        right = ((r['end'] - start_time).total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 100
        width = right - left
        safe_time = html.escape(r['data'].get('time', ''))
        safe_event = html.escape(r['data'].get('event', ''))
        html_parts.append(
            f'<div class="timeline-range" style="left: {left}%; width: {width}%;" title="{safe_time}: {safe_event}"></div>'
        )

    # Render event dots
    for idx, event in enumerate(parsed_events):
        pos_percent = ((event['dt'] - start_time).total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 50
        safe_time = html.escape(event['data'].get('time', ''))
        safe_event = html.escape(event['data'].get('event', ''))
        dot_html = (
            f'<div class="timeline-dot" style="left: {pos_percent}%;">'
            f'<div class="timeline-tooltip"><b>{safe_time}</b><br/>{safe_event}</div>'
            '</div>'
        )
        html_parts.append(dot_html)
    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)

# --- Analysis View ---
def render_analysis_view():
    if st.button("⬅️ Back to Home", key="back_home_btn"):
        st.session_state.current_view = 'home'
        st.session_state.incident_id = None
        st.session_state.analysis_results = None
        st.session_state.chat_history = []
        # Clear the conversation memory
        if 'analyzer' in st.session_state and st.session_state.analyzer:
            st.session_state.analyzer.clear_conversation()
        if os.path.exists("temp_incident"):
            shutil.rmtree("temp_incident")
        st.rerun()

    st.header(f"Analysis for Incident: `{os.path.basename(str(st.session_state.incident_id))}`")

    # Generate analysis if not already done
    if 'analysis_results' not in st.session_state or st.session_state.analysis_results is None:
        with st.spinner("Generating post-mortem report and visuals..."):
            incident_id = str(st.session_state.incident_id)
            demo_path = os.path.join('incidents', incident_id)
            if os.path.isdir(demo_path):
                results = analyze_incident_data(demo_path)
            else:
                api_key = getattr(st.session_state, 'user_api_key', None)
                results = analyze_incident_data(incident_id, api_key)
            st.session_state.analysis_results = results
            # Store the report for chat context
            if results and 'report_markdown' in results:
                st.session_state.report_for_chat = results['report_markdown']
                # Store the raw incident context for chat
                if 'raw_context' in results:
                    st.session_state.raw_context_for_chat = results['raw_context']
            
            # Silently initialize the chat system in the background
            if results and 'analyzer' in results:
                analyzer = results['analyzer']
                st.session_state.analyzer = analyzer  # Store analyzer in session state
                raw_context = getattr(st.session_state, 'raw_context_for_chat', None)
                report_context = getattr(st.session_state, 'report_for_chat', None)
                if raw_context and report_context and not analyzer.conversation_initialized:
                    analyzer.initialize_conversation(raw_context, report_context)

    results = st.session_state.analysis_results
    if not results:
        st.error("Could not generate the analysis. Please go back and try again.")
        return

    # Create tabs
    report_tab, chat_tab, actions_tab = st.tabs(["📄 Post-Mortem Report", "💬 Chat with Augur", "⚡️ Suggested Actions & Code"])

    with report_tab:
        report_md = results.get('report_markdown', '')
        timeline_events = results.get('timeline_events', [])
        import re
        # Find the Timeline of Events section header
        timeline_header_match = re.search(r'(#+\s*Timeline of Events.*?)(\n)', report_md)
        if timeline_header_match:
            before = report_md[:timeline_header_match.start(1)]
            header = timeline_header_match.group(1)
            after = report_md[timeline_header_match.end(2):]
            st.markdown(before)
            st.markdown(header)
            render_timeline_with_events(timeline_events)
            st.markdown(after)
        else:
            # fallback: just render timeline at the top
            render_timeline_with_events(timeline_events)
            st.markdown(report_md)

        # --- Audience-Aware Summaries ---
        st.markdown('---')
        st.markdown('### Generate Audience-Specific Summaries')
        
        # Executive Summary Expander
        with st.expander("📊 Executive Summary", expanded=False):
            if 'audience_summaries' not in st.session_state:
                st.session_state.audience_summaries = {}
            
            if 'executive_summary_generated' not in st.session_state:
                st.session_state.executive_summary_generated = False
            
            if not st.session_state.executive_summary_generated:
                with st.spinner('Generating executive summary...'):
                    summary = generate_audience_summary(
                        report_md,
                        "Using the full report as context, rewrite it for a non-technical CEO. Focus only on business and customer impact. Keep it under 100 words and remove all technical jargon."
                    )
                    st.session_state.audience_summaries['executive'] = summary
                    st.session_state.executive_summary_generated = True
            
            # Create a container for the summary and copy button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(st.session_state.audience_summaries['executive'])
            with col2:
                if st.button('📋', key='copy_exec_summary', help='Copy Executive Summary to clipboard'):
                    pyperclip.copy(st.session_state.audience_summaries['executive'])
                    st.success('Copied!')
        
        # Customer Support Briefing Expander
        with st.expander("🎧 Customer Support Briefing", expanded=False):
            if 'customer_summary_generated' not in st.session_state:
                st.session_state.customer_summary_generated = False
            
            if not st.session_state.customer_summary_generated:
                with st.spinner('Generating customer support briefing...'):
                    summary = generate_audience_summary(
                        report_md,
                        "Rewrite the report as an internal briefing for the customer support team. Explain what customers might have experienced and provide a simple, safe-to-share explanation of the issue."
                    )
                    st.session_state.audience_summaries['customer'] = summary
                    st.session_state.customer_summary_generated = True
            
            # Create a container for the summary and copy button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(st.session_state.audience_summaries['customer'])
            with col2:
                if st.button('📋', key='copy_cust_summary', help='Copy Customer Support Briefing to clipboard'):
                    pyperclip.copy(st.session_state.audience_summaries['customer'])
                    st.success('Copied!')

    with chat_tab:
        st.subheader("Chat with Your Incident")
        st.write("Ask questions about the incident analysis, timeline, root cause, or impact. I'll help you understand the details!")
        
        # Add a clear conversation button
        if st.button("🗑️ Clear Conversation", key="clear_chat"):
            if 'analyzer' in st.session_state and st.session_state.analyzer:
                st.session_state.analyzer.clear_conversation()
            st.session_state.chat_history = []
            st.rerun()
        
        # Display chat history
        for author, message in st.session_state.chat_history:
            with st.chat_message(author):
                st.markdown(message)
        
        # Chat input at the bottom
        if prompt := st.chat_input("Ask a follow-up question...", key="chat_input_key"):
            # Check if analyzer is available
            if 'analyzer' not in st.session_state or st.session_state.analyzer is None:
                st.error("Chat system is not ready. Please refresh the page and try again.")
            else:
                # Add user message to history
                st.session_state.chat_history.append(("user", prompt))
                
                # Display user message immediately
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get AI response
                with st.spinner("Thinking..."):
                    # Get both raw context and report context for the chat
                    raw_context = getattr(st.session_state, 'raw_context_for_chat', None)
                    report_context = getattr(st.session_state, 'report_for_chat', None)
                    response = st.session_state.analyzer.follow_up_question(prompt, raw_context, report_context)
                    
                    # Add AI response to history
                    st.session_state.chat_history.append(("assistant", response))
                    
                    # Display AI response immediately
                    with st.chat_message("assistant"):
                        st.markdown(response)

    with actions_tab:
        st.subheader("Suggested Monitoring as Code")
        monitoring_code = results.get('monitoring_code', '').strip()
        regression_test_code = results.get('regression_test_code', '').strip()
        if monitoring_code:
            st.markdown(monitoring_code)
        else:
            st.info("No monitoring code suggestion was generated for this incident.")
        if regression_test_code:
            st.markdown('---')
            st.subheader("Suggested Regression Test")
            st.markdown(regression_test_code)

# --- Main App Router ---
if st.session_state.current_view == 'home':
    render_home_view()
else:
    render_analysis_view()

def handle_chat_message(user_message: str, report: str, analyzer):
    """Handle chat messages and return AI response."""
    if not analyzer:
        return "I'm sorry, but I don't have access to the analyzer. Please try analyzing an incident first."
    
    try:
        # For backward compatibility, we'll pass the report as both contexts
        response = analyzer.follow_up_question(user_message, report, report)
        return response
    except Exception as e:
        return f"I'm sorry, but I encountered an error while processing your question: {str(e)}"

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d;'>
        <p>🔮 Augur - AI-Powered Incident Analysis | Built with Streamlit & LangChain</p>
        <p>For educational and demonstration purposes. Always validate AI-generated reports.</p>
        <p><a href="https://github.com/jessemillerjom/augur" target="_blank" style="color: #6c757d; text-decoration: none;">📁 View on GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
) 