from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from ..schemas import job
import datetime
import logging
from src.core.configs.celery_config import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/", response_model=List[job.Job])
def get_all_jobs():
    """
    Get all Celery tasks (jobs) with their current status.
    """
    try:
        # Get active tasks
        active_tasks = celery_app.control.inspect().active()
        scheduled_tasks = celery_app.control.inspect().scheduled()
        reserved_tasks = celery_app.control.inspect().reserved()
        
        jobs = []
        
        # Process active tasks
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    jobs.append(job.Job(
                        id=task['id'],
                        status='running',
                        created_at=datetime.datetime.fromtimestamp(task['time_start'])
                    ))
        
        # Process scheduled tasks
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    jobs.append(job.Job(
                        id=task['id'],
                        status='scheduled',
                        created_at=datetime.datetime.fromtimestamp(task['eta'])
                    ))
        
        # Process reserved tasks
        if reserved_tasks:
            for worker, tasks in reserved_tasks.items():
                for task in tasks:
                    jobs.append(job.Job(
                        id=task['id'],
                        status='pending',
                        created_at=datetime.datetime.fromtimestamp(task['time_start'])
                    ))
        
        logger.info(f"Retrieved {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to get jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get jobs: {str(e)}"
        )

@router.get("/{task_id}", response_model=Dict[str, Any])
def get_job_status(task_id: str):
    """
    Get the status of a specific job by task ID.
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'current': 0,
                'total': 1,
                'status': 'Task is waiting to be processed...'
            }
        elif task_result.state != 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'current': task_result.info.get('current', 0) if isinstance(task_result.info, dict) else 0,
                'total': task_result.info.get('total', 1) if isinstance(task_result.info, dict) else 1,
                'status': task_result.info.get('status', '') if isinstance(task_result.info, dict) else str(task_result.info)
            }
            if task_result.result:
                response['result'] = task_result.result
        else:
            # Task failed
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'current': 1,
                'total': 1,
                'status': str(task_result.info),
                'error': True
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get job status for {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_jobs():
    """
    Get only active (running) jobs.
    """
    try:
        active_tasks = celery_app.control.inspect().active()
        
        jobs = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    jobs.append({
                        'task_id': task['id'],
                        'name': task['name'],
                        'args': task['args'],
                        'kwargs': task['kwargs'],
                        'worker': worker,
                        'time_start': datetime.datetime.fromtimestamp(task['time_start']).isoformat(),
                        'status': 'running'
                    })
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to get active jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active jobs: {str(e)}"
        )

@router.post("/{task_id}/cancel", status_code=200)
def cancel_job(task_id: str):
    """
    Cancel a running job.
    """
    try:
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Cancelled job: {task_id}")
        return {"message": f"Job {task_id} cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Failed to cancel job {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
def get_job_stats():
    """
    Get job statistics.
    """
    try:
        stats = celery_app.control.inspect().stats()
        active = celery_app.control.inspect().active()
        scheduled = celery_app.control.inspect().scheduled()
        reserved = celery_app.control.inspect().reserved()
        
        total_active = sum(len(tasks) for tasks in active.values()) if active else 0
        total_scheduled = sum(len(tasks) for tasks in scheduled.values()) if scheduled else 0
        total_reserved = sum(len(tasks) for tasks in reserved.values()) if reserved else 0
        
        return {
            'workers': len(stats) if stats else 0,
            'active_jobs': total_active,
            'scheduled_jobs': total_scheduled,
            'reserved_jobs': total_reserved,
            'total_jobs': total_active + total_scheduled + total_reserved,
            'worker_stats': stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get job stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job stats: {str(e)}"
        )