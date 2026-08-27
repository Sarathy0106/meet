import sys
import os

# Add parent directory to sys.path for Vercel serverless function execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
