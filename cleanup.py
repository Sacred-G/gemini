"""
Cleanup script for ComplegalAI application.

This script helps clean up temporary files and reset the application state.
Use it when you want to start fresh or troubleshoot issues.
"""

import os
import shutil
import glob
import argparse

def cleanup(reset_env=False, reset_all=False):
    """Clean up temporary files and optionally reset environment variables."""
    
    print("Cleaning up temporary files...")
    
    # Clean up __pycache__ directories
    for pycache_dir in glob.glob("**/__pycache__", recursive=True):
        print(f"Removing {pycache_dir}")
        shutil.rmtree(pycache_dir, ignore_errors=True)
    
    # Clean up temporary files
    for temp_file in glob.glob("**/temp_*.pdf", recursive=True):
        print(f"Removing {temp_file}")
        os.remove(temp_file)
    
    # Clean up Streamlit cache
    streamlit_cache = os.path.join(os.path.expanduser("~"), ".streamlit/cache")
    if os.path.exists(streamlit_cache):
        print(f"Removing Streamlit cache: {streamlit_cache}")
        shutil.rmtree(streamlit_cache, ignore_errors=True)
    
    # Reset environment variables if requested
    if reset_env or reset_all:
        if os.path.exists(".env"):
            print("Resetting .env file...")
            if os.path.exists(".env.backup"):
                os.remove(".env.backup")
            os.rename(".env", ".env.backup")
            shutil.copy(".env.example", ".env")
            print("Created new .env file from template. Your original file was backed up to .env.backup.")
    
    # Reset all if requested
    if reset_all:
        # Remove virtual environment
        if os.path.exists("venv"):
            print("Removing virtual environment...")
            shutil.rmtree("venv", ignore_errors=True)
        
        # Remove any other generated files
        for generated_file in ["*.pyc", "*.log"]:
            for file_path in glob.glob(generated_file):
                print(f"Removing {file_path}")
                os.remove(file_path)
    
    print("Cleanup complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up temporary files and reset application state.")
    parser.add_argument("--reset-env", action="store_true", help="Reset environment variables (.env file)")
    parser.add_argument("--reset-all", action="store_true", help="Reset everything (environment, virtual environment, etc.)")
    
    args = parser.parse_args()
    
    cleanup(reset_env=args.reset_env, reset_all=args.reset_all)
