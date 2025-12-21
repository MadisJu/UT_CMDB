import uvicorn
import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logging_adapter import configure_logging
configure_logging()

from src.api.main import app
from src.core.configs.config import settings

processes = []

def signal_handler(signum, frame):
    print("\nShutting down CMDB components...")
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    sys.exit(0)

def check_port_available(host, port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except (OSError, socket.error):
        return False

def find_available_port(host, start_port):
    port = start_port
    max_attempts = 10
    attempts = 0
    
    while attempts < max_attempts:
        if check_port_available(host, port):
            return port
        port += 1
        attempts += 1
    
    raise RuntimeError(f"No available port found starting from {start_port} after {max_attempts} attempts")

def start_celery_worker():
    print("Starting Celery worker...")
    worker_process = subprocess.Popen([
        sys.executable, "-m", "celery", 
        "-A", "src.worker.main", 
        "worker", 
        "--loglevel=info",
        "--concurrency=2"
    ], cwd=project_root)
    processes.append(worker_process)
    return worker_process

def start_celery_beat():
    print("Starting Celery beat scheduler...")
    beat_process = subprocess.Popen([
        sys.executable, "-m", "celery", 
        "-A", "src.scheduler.celery_app", 
        "beat", 
        "--loglevel=info"
    ], cwd=project_root)
    processes.append(beat_process)
    return beat_process

def start_api_server(host, port, debug):
    print(f"Starting CMDB API server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Swagger UI available at: http://{host}:{port}/docs")
    print(f"ReDoc available at: http://{host}:{port}/redoc")
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info"
        )
    except OSError as e:
        if "address already in use" in str(e):
            print(f" Port {port} is already in use. Please stop the existing process or change the port in .env file.")
        else:
            print(f"Error starting API server: {e}")
        raise

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration from settings
    host = settings.cmdb_host
    port = settings.cmdb_port
    debug = settings.cmdb_debug
    
    print(f"   Configuration:")
    print(f"   Environment: {settings.env}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Jira URL: {settings.jira_url or 'Not configured'}")
    print(f"   Discovery Interval: {settings.cmdb_interval_seconds}s")
    print("=" * 50)
    
    try:
        # Start Celery worker
        worker_process = start_celery_worker()
        time.sleep(2) 
        
        # Start Celery beat scheduler
        beat_process = start_celery_beat()
        time.sleep(2)  
        
        print(" All background services started successfully!")
        print("=" * 50)
        
        # Start API server 
        start_api_server(host, port, debug)
        
    except KeyboardInterrupt:
        print("\n Received interrupt signal")
    except Exception as e:
        print(f" Error starting CMDB: {e}")
    finally:
        signal_handler(None, None)