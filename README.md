# ComplegalAI - Workers Compensation Medical Report Rater

ComplegalAI is a Streamlit application that allows users to upload multiple PDF medical reports and chat with them using the Gemini 2.5 Pro model. The application is designed to help rate medical reports for workers compensation cases.

## Features

- Upload multiple PDF medical reports at once
- View the names of uploaded PDF files
- Chat with the medical reports using the Gemini 2.5 Pro model
- Get expert analysis and ratings for workers compensation cases
- Large context window (1 million tokens) to handle extensive medical documentation
- Automatic inclusion of the pdrs.pdf reference file in the background for every chat session
- Option to start chatting immediately with just the reference materials

## Requirements

- Python 3.9+
- Gemini API key (obtain from [Google AI Studio](https://ai.google.dev/))

## Installation

### Standard Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Docker Installation

If you prefer to use Docker:

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Build and run the Docker container:
   ```
   # Using docker-compose (recommended)
   docker-compose up -d

   # Or using Docker directly
   docker build -t complegalai .
   docker run -p 8501:8501 -e GEMINI_API_KEY=your_api_key_here complegalai
   ```

3. Access the application at http://localhost:8501

## Setup

1. Create a `.env` file in the project directory based on the `.env.example` template:
   ```
   # Copy the example file
   cp .env.example .env
   
   # Edit the .env file and add your Gemini API key
   # GEMINI_API_KEY=your_api_key_here
   ```

2. Test your API key to ensure it's working correctly:
   ```
   python test_api_key.py
   ```
   
   If your API key is valid, you should see a success message. If not, check that you've entered the correct API key.

## Usage

### Quick Start

For Unix-based systems (Linux/macOS):
```
chmod +x run_app.sh  # Make the script executable (first time only)
./run_app.sh
```

For Windows:
```
run_app.bat
```

These scripts will:
1. Check if Python is installed
2. Create a virtual environment if it doesn't exist
3. Install the required dependencies
4. Create a `.env` file from the template if it doesn't exist
5. Start the Streamlit application

### Manual Start

If you prefer to start the application manually:

1. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501).

3. If you've set up your API key in the `.env` file, the application will automatically use it. Otherwise, you'll need to enter your Gemini API key in the sidebar.

4. You have two options to start a chat session:
   - **Option 1:** Upload one or more PDF medical reports using the file uploader in the sidebar, then click the "Process Medical Reports" button to analyze them.
   - **Option 2:** Click the "Start Chat" button to begin a chat session with just the background pdrs.pdf reference file.

5. Once the chat session is initialized, you can start chatting with the AI about the medical reports.

6. If you uploaded PDFs, their names will be displayed in the sidebar for reference.

## How It Works

1. The application automatically uploads the pdrs.pdf reference file in the background for every chat session.
2. Users can upload additional PDF medical reports, which are also uploaded to the Gemini API.
3. All PDFs (user-uploaded and the background pdrs.pdf) are used as context for the Gemini 2.5 Pro model.
4. The model analyzes the medical reports and provides insights based on workers compensation guidelines.
5. Users can ask questions about the reports and get detailed responses from the AI.
6. Users can also start a chat session without uploading any PDFs, which will still include the pdrs.pdf reference file in the background.

## Privacy and Security

- Your API key is stored only in the current session and is not saved or shared.
- PDF files are temporarily stored on your local machine during processing and then deleted.
- The PDFs are uploaded to the Gemini API for analysis but are automatically deleted after 48 hours according to Google's policy.

## Troubleshooting

- If you encounter errors related to the API key, ensure that you have entered a valid Gemini API key.
- If PDF processing fails, check that your PDFs are valid and not corrupted.
- For large PDFs, processing may take some time. Please be patient.

### Cleanup

If you encounter issues or want to start fresh, you can use the cleanup script:

```
# Basic cleanup (removes temporary files and cache)
python cleanup.py

# Reset environment variables (.env file)
python cleanup.py --reset-env

# Reset everything (environment, virtual environment, etc.)
python cleanup.py --reset-all
```

This script helps clean up temporary files, reset the application state, and fix common issues.

## License

[Specify your license here]
