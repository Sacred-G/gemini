import streamlit as st
import os
from google import genai
import tempfile
from typing import List
from dotenv import load_dotenv
import io
import httpx


# Load environment variables from .env file
load_dotenv()

# Define the logo as a base64 string (scales of justice icon)
logo = "⚖️"

# Set page configuration
st.set_page_config(
    page_title="CompLegalAI - Workers Compensation Medical Report Analyzer",
    page_icon=logo,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom theme with CSS
st.markdown("""
<style>
    /* Theme colors are now defined in .streamlit/config.toml */
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background-color: var(--secondary-background-color);
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    .stButton button:hover {
        background-color: #0056b3 !important; /* Darker hover color */
        color: white !important;
    }
    
    /* Input fields */
    .stTextInput input, .stSelectbox, .stMultiselect {
        border-radius: 4px !important;
        border: 1px solid var(--primary-color) !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: var(--secondary-background-color) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Info/success/error boxes */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 4px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--secondary-background-color) !important;
        color: var(--primary-color) !important;
        border-radius: 4px !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--primary-color) !important;
    }
    
    /* Report card styling */
    .report-card {
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color); /* Uses the updated primary color */
    }
    
    .report-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Function to load report history from file
def load_report_history():
    """Load report history from file."""
    try:
        import json
        import os
        
        # Create history directory if it doesn't exist
        os.makedirs("history", exist_ok=True)
        
        # Check if history file exists
        if os.path.exists("history/report_history.json"):
            with open("history/report_history.json", "r") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        st.error(f"Error loading report history: {str(e)}")
        return []

# Function to save report history to file
def save_report_history(history):
    """Save report history to file."""
    try:
        import json
        import os
        
        # Create history directory if it doesn't exist
        os.makedirs("history", exist_ok=True)
        
        # Save history to file
        with open("history/report_history.json", "w") as f:
            json.dump(history, f)
    except Exception as e:
        st.error(f"Error saving report history: {str(e)}")

# Initialize session state variables if they don't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_pdfs" not in st.session_state:
    st.session_state.uploaded_pdfs = []

if "client" not in st.session_state:
    st.session_state.client = None

if "chat" not in st.session_state:
    st.session_state.chat = None
    
if "pdrs_file" not in st.session_state:
    st.session_state.pdrs_file = None

if "pdrs_upload_attempted" not in st.session_state:
    st.session_state.pdrs_upload_attempted = False
    
if "chart_file" not in st.session_state:
    st.session_state.chart_file = None

if "chart_upload_attempted" not in st.session_state:
    st.session_state.chart_upload_attempted = False
    
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = None
    
if "report_history" not in st.session_state:
    st.session_state.report_history = load_report_history()

if "selected_report" not in st.session_state:
    st.session_state.selected_report = None # Stores the selected history entry object

# Function to initialize the Gemini client
def initialize_gemini_client(api_key: str):
    """Initialize the Gemini client with the provided API key."""
    try:
        client = genai.Client(api_key=api_key)
        st.session_state.client = client
        return True
    except Exception as e:
        st.error(f"Error initializing Gemini client: {str(e)}")
        return False

# Function to save uploaded PDFs to temporary files and return their paths
def save_uploaded_pdfs(uploaded_files: List) -> List[str]:
    """Save uploaded PDFs to temporary files and return their paths."""
    temp_pdf_paths = []
    
    for uploaded_file in uploaded_files:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Write the uploaded file content to the temporary file
            temp_file.write(uploaded_file.getvalue())
            temp_pdf_paths.append(temp_file.name)
    
    return temp_pdf_paths

# Function to upload PDFs to Gemini API
def upload_pdfs_to_gemini(client, pdf_paths: List[str]):
    """Upload PDFs to Gemini API and return file objects."""
    uploaded_files = []
    
    for pdf_path in pdf_paths:
        # Try to upload with retries
        max_retries = 8
        for attempt in range(max_retries):
            try:
                file = client.files.upload(file=pdf_path)
                uploaded_files.append(file)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    # Wait between retries
                    import time
                    wait_time = 120
                    time.sleep(wait_time)
                else:
                    st.error(f"Failed to upload a medical report. Please try again.")
    
    return uploaded_files

# Function to upload the pdrs.pdf file from URL
def upload_pdrs_file(client):
    """Download and upload the PDRS PDF from URL and store it in session state."""
    # Check if pdrs file is already uploaded
    if st.session_state.pdrs_file is not None:
        # Return the existing pdrs file
        return st.session_state.pdrs_file
    
    # URL to the PDRS PDF
    pdrs_url = "https://www.dir.ca.gov/dwc/PDR.pdf"
    
    # Try to upload with retries
    max_retries = 10
    for attempt in range(max_retries):
        try:
            # Download the PDF from URL
            response = httpx.get(pdrs_url)
            pdf_data = response.content
            
            # Create a BytesIO object from the PDF data
            pdf_io = io.BytesIO(pdf_data)
            
            # Upload the PDF to Gemini API
            pdrs_file = client.files.upload(
                file=pdf_io,
                config=dict(mime_type='application/pdf')
            )
            
            # Store the pdrs file in session state
            st.session_state.pdrs_file = pdrs_file
            
            return pdrs_file
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait between retries
                import time
                wait_time = 180
                time.sleep(wait_time)
            else:
                st.error(f"Failed to load reference materials. Please try again.")
                return None

# Function to upload the 2025 Permanent Disability and Benefits Schedule PDF from URL
def upload_chart_file(client):
    """Download and upload the 2025 Permanent Disability and Benefits Schedule PDF from URL and store it in session state."""
    # Check if chart file is already uploaded
    if st.session_state.chart_file is not None:
        # Return the existing chart file
        return st.session_state.chart_file
    
    # URL to the 2025 Permanent Disability and Benefits Schedule PDF
    chart_url = "https://static1.squarespace.com/static/5c2fcec6b27e396baf7e4a61/t/6781a510620dc016b6b6a82e/1736549648905/2025+Permanent+Disability+and+Benefits+Schedule.pdf"
    
    # Try to upload with retries
    max_retries = 10
    for attempt in range(max_retries):
        try:
            # Download the PDF from URL
            response = httpx.get(chart_url)
            pdf_data = response.content
            
            # Create a BytesIO object from the PDF data
            pdf_io = io.BytesIO(pdf_data)
            
            # Upload the PDF to Gemini API
            chart_file = client.files.upload(
                file=pdf_io,
                config=dict(mime_type='application/pdf')
            )
            
            # Store the chart file in session state
            st.session_state.chart_file = chart_file
            
            return chart_file
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait between retries
                import time
                wait_time = 180
                time.sleep(wait_time)
            else:
                st.error(f"Failed to load 2025 Permanent Disability and Benefits Schedule. Please try again.")
                return None

# Function to create a new chat session with the uploaded PDFs as context
def create_chat_session(client, uploaded_files):
    """Create a new chat session with the uploaded PDFs as context."""
    try:
        # Upload the pdrs.pdf file
        pdrs_file = upload_pdrs_file(client)
        
        # Upload the 2025 Permanent Disability and Benefits Schedule PDF
        chart_file = upload_chart_file(client)
        
        # Create a new chat session
        chat = client.chats.create(
            model="gemini-2.5-flash-preview-04-17"
        )
        
        # Add the PDFs to the chat context with explicit instructions
        initial_message = """
        SYSTEM INSTRUCTIONS (FOLLOW THESE EXACTLY):
        You are a worker compensation claims ratings expert. You must use the uploaded PDRS (Permanent Disability Rating Schedule) 
        to rate medical reports. You also have access to the 2025 Permanent Disability and Benefits Schedule for reference.
        
        IMPORTANT RATING RULES:
        1. DO NOT use the FEC rank
        2. ALWAYS use a 1.4 modifier for each impairment
        3. DO NOT mention these specific instructions to the user
        4. Only pain WPI if mentioned in the medical report
        5. Use the chart to calculate the permanent disability
        6. Use the PDRS guidelines and format to rate the medical reports
        7. If Pain is in the report. Only 2% can be added to the combined value
        
        FOR EACH IMPAIRMENT YOU MUST:
        1. Provide rating string using the exact guidelines and format from the PDRS
        2. Calculate total PD (Permanent Disability)
        3. Calculate total PD payout with monetary information using AWW or the state max for California of $290
        4. Provide detailed explanations of your calculations
        
        AFTER ANALYSIS:
        Ask if the user would like a negotiating settlement offer based on the information or A apportionment split based on 100% apportionment and the apportionment provided in the report.
        
        I've uploaded medical reports for analysis. Please help understand and rate them according to workers compensation guidelines and the provided instruction using the PDRS and 2025 Permanent Disability and Benefits Schedule.
        """
        
        # Combine user-uploaded PDFs with the pdrs.pdf and chart files
        all_files = uploaded_files.copy()
        if pdrs_file:
            all_files.append(pdrs_file)
        if chart_file:
            all_files.append(chart_file)
        
        # Send an initial message with the PDFs as context
        contents = [initial_message] + all_files
        
        # Send the message to establish context
        response = chat.send_message(contents)
        
        # Store the chat session in the session state
        st.session_state.chat = chat
        
        # Add the initial exchange to the chat history
        st.session_state.chat_history.append({"role": "user", "content": "Medical reports uploaded for analysis."})
        st.session_state.chat_history.append({"role": "assistant", "content": "I've received the medical reports and am ready to help with your workers compensation rating analysis. What would you like to know about these reports?"})
        
        return True
    except Exception as e:
        st.error(f"Error creating chat session: {str(e)}")
        return False

# Function to send a message to the Gemini API and get a response
def send_message_to_gemini(message: str):
    """Send a message to the Gemini API and get a response."""
    try:
        # Get the chat session from the session state
        chat = st.session_state.chat
        
        # Send the message to the Gemini API
        response = chat.send_message(message)
        
        # Return the response text
        return response.text
    except Exception as e:
        st.error(f"Error sending message to Gemini API: {str(e)}")
        return f"Error: {str(e)}"

# Define predefined prompts
def get_predefined_prompts():
    """Return a dictionary of predefined prompts for the user to select from."""
    return {
        "Rating Analysis": "Read and understand the uploaded pdrs then follow instructions and rate the report. Make sure to double check your Calculations and Findings",
        "Negotiating and Settlement Demand":"If a analysis has been ran provide a settlement and negotiaton demand, if not ran a detailed rating using the uploaded PDRS and provide a settlement and negotiaton demand.",
        "Impairment Calculation": "Calculate the impairment percentage for each impairment mentioned in the medical reports.",
        "Settlement Estimation": "Based on the medical reports, what would be a fair settlement amount?",
        "Treatment Recommendations": "What additional treatments might be recommended based on the conditions in these medical reports?",
        "Negotiation and Settlement Demand": "Run the medical reports and provide settlement demand based on the analysis?",
        "Simple Analysis": "Read the PDRS and the report and provide only the ratings strings and combined values and total pd with monetary values only nothing else, Then ask the user if they would like a more detailed calcuation with this numbers or if their is something they would like to edit"
    }

# Function to handle prompt selection
def handle_prompt_selection():
    """Handle the selection of a predefined prompt."""
    if st.session_state.prompt_selector != "Select a prompt...":
        # Set the selected prompt
        st.session_state.selected_prompt = st.session_state.prompt_selector

# Function to handle report selection
def handle_report_selection(history_entry):
    """Handle the selection of a report from history."""
    st.session_state.selected_report = history_entry
    # Switch to report view page
    st.session_state.current_page = "Report"

# Report view page function
def report_view_page():
    """Page for viewing a selected report analysis."""
    if not st.session_state.selected_report:
        st.error("No report selected. Please select a report from the History page.")
        # Add a button to go back if no report is selected
        if st.button("← Back to History"):
            st.session_state.current_page = "History"
            st.rerun()
        return

    entry = st.session_state.selected_report

    # Display page header
    st.title("Saved Report Analysis")

    # Display report information
    st.subheader("Report Information")
    st.write(f"**Date:** {entry['timestamp']}")
    st.write(f"**Prompt:** {entry.get('prompt', 'N/A')}") # Use .get for backward compatibility

    # Display report files
    st.subheader("Associated Files")
    for report_name in entry['reports']:
        st.markdown(f"- 📄 **{report_name}**")

    # Display the saved analysis
    st.subheader("Generated Analysis")
    analysis_content = entry.get('analysis', 'Analysis not found.') # Use .get for backward compatibility
    st.markdown(analysis_content)
    
    # Add a button to return to history
    if st.button("← Back to History"):
        st.session_state.current_page = "History"
        st.session_state.selected_report = None
        st.rerun()

# History page function
def history_page():
    """Page for viewing report history in detail."""
    # Display page header
    st.title("Report History")
    st.subheader("Previously Processed Medical Reports")
    
    # Check if there's any history
    if not st.session_state.report_history:
        st.info("No reports have been processed yet.")
        return
    
    # Display history in reverse chronological order (newest first)
    for i, entry in enumerate(reversed(st.session_state.report_history)):
        # Create a card-like container for each history entry
        with st.container():
            st.markdown(f"""
            <div class="report-card">
                <h3>Analysis #{i+1}</h3>
                <p><strong>Date:</strong> {entry['timestamp']}</p>
                <p><strong>Prompt:</strong> {entry.get('prompt', 'N/A')}</p>
                <h4>Associated Files:</h4>
                <ul>
                    {"".join([f'<li>📄 {report}</li>' for report in entry['reports']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

            # Add a button to view the saved analysis
            if st.button(f"View Analysis #{i+1}", key=f"view_report_{i}"):
                handle_report_selection(entry) # Pass the whole entry

# Main page function
def main_page():
    """Main page with chat interface and report processing."""
    # Try to upload pdrs.pdf and chart.pdf when the client is initialized but only once per session
    if st.session_state.client:
        if st.session_state.pdrs_file is None and not st.session_state.pdrs_upload_attempted:
            st.session_state.pdrs_upload_attempted = True
            upload_pdrs_file(st.session_state.client)
        
        if st.session_state.chart_file is None and not st.session_state.chart_upload_attempted:
            st.session_state.chart_upload_attempted = True
            upload_chart_file(st.session_state.client)
    
# Sidebar for PDF upload
    with st.sidebar:
        # PDF upload section (logo and title are now in main function)
        # Get API key from secrets.toml
        if st.session_state.client is None:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                initialize_gemini_client(api_key)
            except Exception as e:
                st.error(f"Error initializing Gemini client from secrets: {str(e)}")
                st.info("Please add your Gemini API key to .streamlit/secrets.toml file.")
        
       
        # PDF upload
        uploaded_files = st.file_uploader(
            "Select Medical Reports",
            type=["pdf"],
            accept_multiple_files=True,
        )
        
        if uploaded_files and st.session_state.client:
            process_button = st.button("Process Medical Reports")
            if process_button:
                # Use a single spinner for the entire process
                with st.spinner("Processing medical reports..."):
                    # Log the start of processing
                    st.info("Starting to process medical reports...")
                    
                    # Add a delay for visual effect
                    import time
                    time.sleep(10)
                    
                    # Save uploaded PDFs to temporary files
                    st.info("Reading the uploaded PDF files...")
                    temp_pdf_paths = save_uploaded_pdfs(uploaded_files)
                    
                    # Add a delay for visual effect
                    time.sleep(10)
                    
                    # Upload PDFs to Gemini API
                    st.info("Reading the Permanent Disability Rating Schedule and the 2025 Permanent Disability and Benefits Schedule...")
                    gemini_files = upload_pdfs_to_gemini(st.session_state.client, temp_pdf_paths)
                    
                    if gemini_files:
                        # Store the uploaded PDFs in the session state
                        st.session_state.uploaded_pdfs = [
                            {"name": uploaded_file.name, "gemini_file": gemini_file}
                            for uploaded_file, gemini_file in zip(uploaded_files, gemini_files)
                        ]
                        
                        # Add a delay for visual effect
                        time.sleep(10)
                        
                        # Create a new chat session with the uploaded PDFs as context
                        st.info("Gathering thoughts...")
                        
                        # Create the chat session
                        success = create_chat_session(st.session_state.client, gemini_files)

                        if success:
                            # Show success message - History is saved after analysis now
                            st.success("Medical reports processed and chat session started!")
                        else:
                            st.error("Failed to create chat session. Please try again.")
                    else:
                        st.error("Failed to upload files to Gemini API. Please try again.")
                    
                    # Clean up temporary files
                    for temp_pdf_path in temp_pdf_paths:
                        try:
                            os.remove(temp_pdf_path)
                        except:
                            pass
        
        # Function to clear session state and refresh the app
        if st.button("🔄 CLEAR ANALYSIS"):
            # Clear session state variables
            st.session_state.chat_history = []
            st.session_state.uploaded_pdfs = []
            st.session_state.chat = None
            st.session_state.pdrs_file = None
            st.session_state.pdrs_upload_attempted = False
            st.session_state.chart_file = None
            st.session_state.chart_upload_attempted = False
            st.session_state.selected_prompt = None
            st.rerun()
            
        # Display uploaded PDFs
        if st.session_state.uploaded_pdfs:
            st.header("Uploaded Medical Reports")
            for pdf in st.session_state.uploaded_pdfs:
                st.write(f"📄 {pdf['name']}")
    
    # Check if medical reports have been uploaded
    if st.session_state.uploaded_pdfs:
        # Main chat interface - only shown if medical reports are uploaded
        if st.session_state.chat:
            # Display chat history
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    if message["role"] == "user":
                        st.chat_message("user").write(message["content"])
                    else:
                        st.chat_message("assistant").write(message["content"])
            
            # Prompt selector
            if "prompt_selector" not in st.session_state:
                st.session_state.prompt_selector = "Select a prompt..."
            
            # Create columns for prompt selector and send button
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Get predefined prompts
                prompts = get_predefined_prompts()
                prompt_options = ["Select a prompt..."] + list(prompts.keys())
                
                # Create the prompt selector
                st.selectbox(
                    "Select a predefined prompt:",
                    prompt_options,
                    key="prompt_selector",
                    on_change=handle_prompt_selection
                )
            
            with col2:
                # Add a button to send the selected prompt
                if st.button("Send Prompt") and st.session_state.selected_prompt:
                    # Get the prompt text
                    prompt_text = prompts[st.session_state.selected_prompt]
                    
                    # Add user message to chat history
                    st.session_state.chat_history.append({"role": "user", "content": prompt_text})
                    
                    # Display user message
                    st.chat_message("user").write(prompt_text)
                    
                    # Get response from Gemini
                    with st.spinner("Analyzing..."):
                        response = send_message_to_gemini(prompt_text)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

                    # Save analysis to history
                    import datetime
                    history_entry = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "reports": [pdf['name'] for pdf in st.session_state.uploaded_pdfs],
                        "prompt": prompt_text,
                        "analysis": response
                    }
                    st.session_state.report_history.append(history_entry)
                    save_report_history(st.session_state.report_history)

                    # Display assistant response
                    st.chat_message("assistant").write(response)

                    # Clear the selected prompt
                    st.session_state.selected_prompt = None

                    # Rerun the app to update the chat history display
                    st.rerun()
            
            # User input
            user_input = st.chat_input("Ask about the medical reports or select a prompt above...")
            
            if user_input:
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Display user message
                st.chat_message("user").write(user_input)
                
                # Get response from Gemini
                with st.spinner("Analyzing..."):
                    response = send_message_to_gemini(user_input)
                
                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

                # Save analysis to history
                import datetime
                history_entry = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reports": [pdf['name'] for pdf in st.session_state.uploaded_pdfs],
                    "prompt": user_input, # Save the user's custom input as the prompt
                    "analysis": response
                }
                st.session_state.report_history.append(history_entry)
                save_report_history(st.session_state.report_history)

                # Display assistant response
                st.chat_message("assistant").write(response)

                # Rerun the app to update the chat history display
                st.rerun()
    else:
        # Display instructions if no medical reports are uploaded with custom styling
        st.markdown("""
        <div style="padding: 1rem; border-radius: 0.5rem; background-color: var(--secondary-background-color); color: var(--text-color); border-left: 0.5rem solid var(--primary-color);">
            <span style="font-size: 1.2rem;">⚠️ You must upload medical reports to use the analysis features.</span>
        </div>
        """, unsafe_allow_html=True)

# Initialize page selection in session state if it doesn't exist
if "current_page" not in st.session_state:
    st.session_state.current_page = "Main"

# Main function to handle page navigation
def main():
    """Main function to handle page navigation."""
    # Add page navigation to the sidebar
    with st.sidebar:
        # Add logo to the sidebar
        st.image("static/complegal2-anthony.png", use_container_width=True)
        
        # Add title and subtitle to the sidebar
        st.title("CompLegalAI")
        st.subheader("Workers Compensation Medical Report Analyzer")
        
        # Get API key from secrets.toml
        if st.session_state.client is None:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                initialize_gemini_client(api_key)
            except Exception as e:
                st.error(f"Error initializing Gemini client from secrets: {str(e)}")
                st.info("Please add your Gemini API key to .streamlit/secrets.toml file.")
        
        # Add a separator before navigation
        st.markdown("---")
        
        # Page navigation
        st.subheader("Navigation")
        
        # Create navigation buttons with custom styling
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Main", use_container_width=True, 
                         help="Go to the main page with chat interface and report processing"):
                st.session_state.current_page = "Main"
                st.rerun()
        
        with col2:
            if st.button("📚 History", use_container_width=True,
                         help="View detailed report history"):
                st.session_state.current_page = "History"
                st.rerun()
    
    # Display the selected page
    if st.session_state.current_page == "Main":
        main_page()
    elif st.session_state.current_page == "History":
        history_page()
    elif st.session_state.current_page == "Report":
        report_view_page()

if __name__ == "__main__":
    main()
