import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record, default=str)

def configure_logging(log_dir: Optional[Union[str, Path]] = None, level: str = "INFO") -> None:
    """
    Configures the logging system.
    """
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    else:
        log_dir = Path(log_dir)
        
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    root_logger.handlers = []
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)
    
    app_log_path = log_dir / "app.log"
    file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)
    
    audit_logger = logging.getLogger("audit")
    audit_logger.propagate = False 
    audit_logger.setLevel(logging.INFO)
    
    audit_log_path = log_dir / "audit.log"
    audit_handler = logging.FileHandler(audit_log_path, encoding="utf-8")
    audit_handler.setFormatter(JsonFormatter())
    audit_logger.addHandler(audit_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    """
    return logging.getLogger(name)


def audit_log(
    action: str, 
    admin_id: str, 
    target: str, 
    old_value: Any = None, 
    new_value: Any = None, 
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs an audit event to the audit log.
    Satisfies SR-05 (Audit Logging).
    """
    logger = logging.getLogger("audit")
    
    payload = {
        "event_type": "audit",
        "action": action,
        "admin_id": admin_id,
        "target": target,
    }
    
    if old_value is not None:
        payload["old_value"] = old_value
    if new_value is not None:
        payload["new_value"] = new_value
    if details:
        payload["details"] = details
        
    
    logger.info(action, extra={"extra_data": payload})


def record_job_run(
    job_name: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    processed_count: int = 0,
    diagnostics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a job execution result.
    Satisfies SR-04 and SR-06.
    """
    logger = logging.getLogger("jobs")
    
    duration = (end_time - start_time).total_seconds()
    
    payload = {
        "event_type": "job_run",
        "job_name": job_name,
        "start_time": start_time.isoformat() + "Z",
        "end_time": end_time.isoformat() + "Z",
        "duration_seconds": duration,
        "status": status, # success, failure, warning
        "processed_count": processed_count,
    }
    
    if diagnostics:
        payload["diagnostics"] = diagnostics
        
    logger.info(f"Job {job_name} finished with status {status}", extra={"extra_data": payload})
