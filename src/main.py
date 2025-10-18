"""
Main entry point for the CMDB application.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.main import app

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("CMDB_HOST", "0.0.0.0")
    port = int(os.getenv("CMDB_PORT", "8000"))
    debug = os.getenv("CMDB_DEBUG", "false").lower() == "true"
    
    print(f"Starting CMDB API server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Swagger UI available at: http://{host}:{port}/docs")
    print(f"ReDoc available at: http://{host}:{port}/redoc")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
