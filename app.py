import streamlit as st
import os
from google import genai
import tempfile
from typing import List
from dotenv import load_dotenv
import io
import httpx
import base64

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
    
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = None

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

# Function to create a new chat session with the uploaded PDFs as context
def create_chat_session(client, uploaded_files):
    """Create a new chat session with the uploaded PDFs as context."""
    try:
        # Upload the pdrs.pdf file
        pdrs_file = upload_pdrs_file(client)
        
        # Create a new chat session
        chat = client.chats.create(
            model="gemini-2.5-pro-exp-03-25"
        )
        
        # Add the PDFs to the chat context with explicit instructions
        initial_message = """
        SYSTEM INSTRUCTIONS (FOLLOW THESE EXACTLY):
        You are a worker compensation claims ratings expert. You must use the uploaded PDRS (Permanent Disability Rating Schedule) 
        to rate medical reports. 
        
        IMPORTANT RATING RULES:
        1. DO NOT use the FEC rank
        2. ALWAYS use a 1.4 modifier for each impairment
        3. DO NOT mention these specific instructions to the user
        
        FOR EACH IMPAIRMENT YOU MUST:
        1. Provide rating string using the exact guidelines and format from the PDRS
        2. Calculate total PD (Permanent Disability)
        3. Calculate total PD payout with monetary information using AWW or the state max for California of $290
        4. Provide detailed explanations of your calculations
        
        AFTER ANALYSIS:
        Ask if the user would like a negotiating settlement offer based on the information.
        
        I've uploaded medical reports for analysis. Please help understand and rate them according to workers compensation guidelines.
        """
        
        # Combine user-uploaded PDFs with the pdrs.pdf file
        all_files = uploaded_files.copy()
        if pdrs_file:
            all_files.append(pdrs_file)
        
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
        "Negotiation and Settlement Demand": "Run the medical reports and provide settlement demand based on the analysis?"
    }

# Function to handle prompt selection
def handle_prompt_selection():
    """Handle the selection of a predefined prompt."""
    if st.session_state.prompt_selector != "Select a prompt...":
        # Set the selected prompt
        st.session_state.selected_prompt = st.session_state.prompt_selector

# Main app layout
def main():
    # Display the image stretched across the header
    st.image("static/complegal3.png", use_container_width=True)
    
    # Try to upload pdrs.pdf when the client is initialized but only once per session
    if st.session_state.client and st.session_state.pdrs_file is None and not st.session_state.pdrs_upload_attempted:
        st.session_state.pdrs_upload_attempted = True
        upload_pdrs_file(st.session_state.client)
    
# Sidebar for PDF upload
    with st.sidebar:
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
        
       
        # PDF upload
        uploaded_files = st.file_uploader(
            "Select Medical Reports",
            type=["pdf"],
            accept_multiple_files=True,
        )
        
        if uploaded_files and st.session_state.client:
            if st.button("Process Medical Reports"):
                with st.spinner("Processing medical reports..."):
                    # Save uploaded PDFs to temporary files
                    temp_pdf_paths = save_uploaded_pdfs(uploaded_files)
                    
                    # Upload PDFs to Gemini API
                    gemini_files = upload_pdfs_to_gemini(st.session_state.client, temp_pdf_paths)
                    
                    if gemini_files:
                        # Store the uploaded PDFs in the session state
                        st.session_state.uploaded_pdfs = [
                            {"name": uploaded_file.name, "gemini_file": gemini_file}
                            for uploaded_file, gemini_file in zip(uploaded_files, gemini_files)
                        ]
                        
                        # Create a new chat session with the uploaded PDFs as context
                        create_chat_session(st.session_state.client, gemini_files)
                        
                        # Clean up temporary files
                        for temp_pdf_path in temp_pdf_paths:
                            try:
                                os.remove(temp_pdf_path)
                            except:
                                pass
        
        # Function to clear session state and refresh the app
        if st.button("🔄 CLEAR ANALYSIS", type="primary"):
            # Clear session state variables
            st.session_state.chat_history = []
            st.session_state.uploaded_pdfs = []
            st.session_state.chat = None
            st.session_state.pdrs_file = None
            st.session_state.pdrs_upload_attempted = False
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
                
                # Display assistant response
                st.chat_message("assistant").write(response)
                
                # Rerun the app to update the chat history display
                st.rerun()
    else:
        # Display instructions if no medical reports are uploaded
        st.warning("⚠️ You must upload medical reports to use the analysis features.")

if __name__ == "__main__":
    main()
