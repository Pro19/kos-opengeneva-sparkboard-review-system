#!/usr/bin/env python3
"""
Script to run the REST API server
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Run the API server"""
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("API_LOG_LEVEL", "info")
    
    print(f"Starting Ontology-Driven Hackathon Review API...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Auto-reload: {reload}")
    print(f"Log level: {log_level}")
    print()
    print("API Documentation will be available at:")
    print(f"  - Swagger UI: http://localhost:{port}/docs")
    print(f"  - ReDoc: http://localhost:{port}/redoc")
    print(f"  - Scalar: http://localhost:{port}/scalar")
    print(f"  - OpenAPI JSON: http://localhost:{port}/openapi.json")
    print()
    
    # Run the server
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )

if __name__ == "__main__":
    main()