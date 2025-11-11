"""
FastAPI REST API for Job Scheduler
Provides endpoints for job management and real-time updates via WebSocket
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import json
from datetime import datetime

from scheduler import (
    JobScheduler, 
    SchedulingAlgorithm, 
    Job,
    get_scheduler
)

app = FastAPI(
    title="Multi-threaded Job Scheduler API",
    description="REST API for managing and monitoring multi-threaded job execution",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class JobSubmitRequest(BaseModel):
    name: str = Field(..., description="Job name")
    burst_time: float = Field(..., gt=0, description="Job execution time in seconds")
    priority: int = Field(5, ge=1, le=10, description="Job priority (1=highest, 10=lowest)")


class JobResponse(BaseModel):
    job_id: str
    name: str
    burst_time: float
    priority: int
    status: str
    arrival_time: float
    start_time: Optional[float]
    completion_time: Optional[float]
    remaining_time: Optional[float]
    waiting_time: float
    turnaround_time: float
    thread_id: Optional[int]
    result: Optional[str]
    error: Optional[str]


class SchedulerConfigRequest(BaseModel):
    max_workers: int = Field(4, ge=1, le=16, description="Maximum number of worker threads")
    algorithm: str = Field("fcfs", description="Scheduling algorithm (fcfs, sjf, priority, round_robin)")
    quantum: Optional[float] = Field(2.0, gt=0, description="Time quantum for Round Robin (seconds)")


class SchedulerStatusResponse(BaseModel):
    is_running: bool
    is_paused: bool
    algorithm: str
    max_workers: int
    statistics: dict


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# Callback for job status changes
def job_status_callback(job: Job):
    """Called when job status changes - broadcasts to WebSocket clients"""
    asyncio.create_task(manager.broadcast({
        "type": "job_update",
        "data": job.to_dict()
    }))


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    scheduler = get_scheduler()
    scheduler.add_callback(job_status_callback)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Multi-threaded Job Scheduler API",
        "version": "1.0.0",
        "endpoints": {
            "jobs": "/jobs",
            "scheduler": "/scheduler",
            "statistics": "/statistics",
            "websocket": "/ws"
        }
    }


@app.post("/jobs", response_model=dict, status_code=201)
async def submit_job(request: JobSubmitRequest):
    """Submit a new job to the scheduler"""
    scheduler = get_scheduler()
    
    job_id = scheduler.submit_job(
        name=request.name,
        burst_time=request.burst_time,
        priority=request.priority
    )
    
    return {
        "job_id": job_id,
        "message": "Job submitted successfully",
        "status": "pending"
    }


@app.get("/jobs", response_model=List[JobResponse])
async def get_all_jobs():
    """Get all jobs"""
    scheduler = get_scheduler()
    jobs = scheduler.get_all_jobs()
    return [JobResponse(**job.to_dict()) for job in jobs]


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job by ID"""
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(**job.to_dict())


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending job"""
    scheduler = get_scheduler()
    
    if scheduler.cancel_job(job_id):
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (not pending or not found)")


@app.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return {"message": "Scheduler started", "status": "running"}


@app.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
    return {"message": "Scheduler stopped", "status": "stopped"}


@app.post("/scheduler/pause")
async def pause_scheduler():
    """Pause the scheduler"""
    scheduler = get_scheduler()
    scheduler.pause()
    return {"message": "Scheduler paused", "status": "paused"}


@app.post("/scheduler/resume")
async def resume_scheduler():
    """Resume the scheduler"""
    scheduler = get_scheduler()
    scheduler.resume()
    return {"message": "Scheduler resumed", "status": "running"}


@app.post("/scheduler/configure")
async def configure_scheduler(config: SchedulerConfigRequest):
    """Configure scheduler (requires restart)"""
    global scheduler
    
    # Stop existing scheduler
    old_scheduler = get_scheduler()
    if old_scheduler.running:
        old_scheduler.stop()
    
    # Create new scheduler with new configuration
    try:
        algorithm = SchedulingAlgorithm(config.algorithm.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid algorithm: {config.algorithm}")
    
    from scheduler import scheduler as global_scheduler
    global_scheduler = JobScheduler(
        max_workers=config.max_workers,
        algorithm=algorithm
    )
    
    if config.quantum:
        global_scheduler.quantum = config.quantum
    
    global_scheduler.add_callback(job_status_callback)
    
    return {
        "message": "Scheduler configured successfully",
        "config": {
            "max_workers": config.max_workers,
            "algorithm": config.algorithm,
            "quantum": config.quantum
        }
    }


@app.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """Get scheduler status and statistics"""
    scheduler = get_scheduler()
    stats = scheduler.get_statistics()
    
    return SchedulerStatusResponse(
        is_running=scheduler.running,
        is_paused=scheduler.paused,
        algorithm=scheduler.algorithm.value,
        max_workers=scheduler.max_workers,
        statistics=stats
    )


@app.get("/statistics")
async def get_statistics():
    """Get detailed scheduler statistics"""
    scheduler = get_scheduler()
    return scheduler.get_statistics()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial status
        scheduler = get_scheduler()
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to job scheduler",
                "statistics": scheduler.get_statistics()
            }
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client requests
            try:
                message = json.loads(data)
                
                if message.get("type") == "get_jobs":
                    jobs = scheduler.get_all_jobs()
                    await websocket.send_json({
                        "type": "jobs_list",
                        "data": [job.to_dict() for job in jobs]
                    })
                
                elif message.get("type") == "get_statistics":
                    stats = scheduler.get_statistics()
                    await websocket.send_json({
                        "type": "statistics",
                        "data": stats
                    })
            
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/demo/populate")
async def populate_demo_jobs():
    """Populate scheduler with demo jobs for testing"""
    scheduler = get_scheduler()
    
    demo_jobs = [
        {"name": "Data Processing", "burst_time": 5.0, "priority": 2},
        {"name": "Image Rendering", "burst_time": 8.0, "priority": 3},
        {"name": "Database Backup", "burst_time": 10.0, "priority": 5},
        {"name": "Email Notification", "burst_time": 2.0, "priority": 1},
        {"name": "Report Generation", "burst_time": 6.0, "priority": 4},
        {"name": "File Compression", "burst_time": 4.0, "priority": 3},
        {"name": "API Sync", "burst_time": 3.0, "priority": 2},
        {"name": "Cache Cleanup", "burst_time": 7.0, "priority": 6},
    ]
    
    job_ids = []
    for job_data in demo_jobs:
        job_id = scheduler.submit_job(**job_data)
        job_ids.append(job_id)
    
    return {
        "message": f"Created {len(demo_jobs)} demo jobs",
        "job_ids": job_ids
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
