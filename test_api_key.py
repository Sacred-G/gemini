
import os
import sys
from dotenv import load_dotenv
from google import genai

def test_api_key(api_key=None):
    """Test if the provided Gemini API key is valid."""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=api_key)
        
        # Try a simple request to verify the API key
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents="Hello, can you confirm this API key is working?"
        )
        
        # If we get here, the API key is valid
        print("✅ API key is valid!")
        print("\nSample response from Gemini:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        return True
    
    except Exception as e:
        # If there's an error, the API key might be invalid
        print("❌ Error testing API key:")
        print(str(e))
        return False

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if API key is provided as command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print("Testing API key provided as command line argument...")
        test_api_key(api_key)
    
    # Otherwise, check for API key in environment variables
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            print("Testing API key from environment variables...")
            test_api_key(api_key)
        else:
            print("❌ No API key found!")
            print("Please provide your Gemini API key in one of the following ways:")
            print("1. Create a .env file with GEMINI_API_KEY=your_api_key")
            print("2. Run this script with the API key as an argument:")
            print("   python test_api_key.py your_api_key")
