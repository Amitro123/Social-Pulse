import os
from dotenv import load_dotenv
#change this file amitro to d
def load_config():
    """Load environment variables"""
    load_dotenv()
    
    return {
        "serpapi": {
            "api_key": os.getenv("SERPAPI_KEY"),
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
    }
