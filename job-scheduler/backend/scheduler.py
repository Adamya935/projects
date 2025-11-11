"""
Multi-threaded Job Scheduler with Multiple Scheduling Algorithms
Supports concurrent job execution with thread pool management
"""

import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
from concurrent.futures import ThreadPoolExecutor, Future
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulingAlgorithm(Enum):
    FCFS = "fcfs"  # First Come First Serve
    SJF = "sjf"    # Shortest Job First
    PRIORITY = "priority"  # Priority Scheduling
    ROUND_ROBIN = "round_robin"  # Round Robin
    MULTI_LEVEL = "multi_level"  # Multi-Level Queue


@dataclass
class Job:
    """Represents a job to be scheduled and executed"""
    job_id: str
    name: str
    burst_time: float  # Execution time in seconds
    priority: int = 5  # 1 (highest) to 10 (lowest)
    status: JobStatus = JobStatus.PENDING
    arrival_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    remaining_time: Optional[float] = None
    waiting_time: float = 0.0
    turnaround_time: float = 0.0
    thread_id: Optional[int] = None
    result: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.remaining_time is None:
            self.remaining_time = self.burst_time
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return self.priority < other.priority
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary for API responses"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "status": self.status.value,
            "arrival_time": self.arrival_time,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "remaining_time": self.remaining_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "thread_id": self.thread_id,
            "result": self.result,
            "error": self.error
        }


class JobScheduler:
    """Multi-threaded job scheduler with multiple scheduling algorithms"""
    
    def __init__(self, max_workers: int = 4, algorithm: SchedulingAlgorithm = SchedulingAlgorithm.FCFS):
        self.max_workers = max_workers
        self.algorithm = algorithm
        self.jobs: Dict[str, Job] = {}
        self.job_queue: Queue = Queue()
        self.priority_queue: PriorityQueue = PriorityQueue()
        self.executor: Optional[ThreadPoolExecutor] = None
        self.running = False
        self.paused = False
        self.lock = threading.Lock()
        self.scheduler_thread: Optional[threading.Thread] = None
        self.quantum = 2.0  # Time quantum for Round Robin (seconds)
        self.callbacks: List[Callable] = []
        
        logger.info(f"JobScheduler initialized with {max_workers} workers using {algorithm.value} algorithm")
    
    def add_callback(self, callback: Callable):
        """Add callback function to be called on job status changes"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, job: Job):
        """Notify all registered callbacks about job status change"""
        for callback in self.callbacks:
            try:
                callback(job)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def submit_job(self, name: str, burst_time: float, priority: int = 5) -> str:
        """Submit a new job to the scheduler"""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            job_id=job_id,
            name=name,
            burst_time=burst_time,
            priority=priority
        )
        
        with self.lock:
            self.jobs[job_id] = job
            
            if self.algorithm == SchedulingAlgorithm.PRIORITY:
                self.priority_queue.put(job)
            else:
                self.job_queue.put(job)
        
        logger.info(f"Job {job_id} ({name}) submitted with burst_time={burst_time}s, priority={priority}")
        self._notify_callbacks(job)
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        with self.lock:
            return list(self.jobs.values())
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                self._notify_callbacks(job)
                logger.info(f"Job {job_id} cancelled")
                return True
        return False
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.paused = False
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Start scheduler thread based on algorithm
        if self.algorithm == SchedulingAlgorithm.ROUND_ROBIN:
            self.scheduler_thread = threading.Thread(target=self._round_robin_scheduler, daemon=True)
        else:
            self.scheduler_thread = threading.Thread(target=self._standard_scheduler, daemon=True)
        
        self.scheduler_thread.start()
        logger.info(f"Scheduler started with {self.algorithm.value} algorithm")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler stopped")
    
    def pause(self):
        """Pause the scheduler"""
        self.paused = True
        logger.info("Scheduler paused")
    
    def resume(self):
        """Resume the scheduler"""
        self.paused = False
        logger.info("Scheduler resumed")
    
    def _standard_scheduler(self):
        """Standard scheduler for FCFS, SJF, Priority algorithms"""
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            
            try:
                # Get next job based on algorithm
                job = self._get_next_job()
                
                if job and job.status == JobStatus.PENDING:
                    # Submit job to thread pool
                    future = self.executor.submit(self._execute_job, job)
                    future.add_done_callback(lambda f, j=job: self._job_completed(j, f))
                else:
                    time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(0.1)
    
    def _round_robin_scheduler(self):
        """Round Robin scheduler with time quantum"""
        active_jobs: List[Job] = []
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            
            try:
                # Add new jobs from queue
                while not self.job_queue.empty():
                    job = self.job_queue.get_nowait()
                    if job.status == JobStatus.PENDING:
                        active_jobs.append(job)
                
                if not active_jobs:
                    time.sleep(0.1)
                    continue
                
                # Process each job for quantum time
                job = active_jobs.pop(0)
                
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Execute job for quantum time or remaining time
                exec_time = min(self.quantum, job.remaining_time)
                future = self.executor.submit(self._execute_job_partial, job, exec_time)
                future.result()  # Wait for completion
                
                # Check if job is complete
                if job.remaining_time <= 0:
                    job.status = JobStatus.COMPLETED
                    job.completion_time = time.time()
                    job.turnaround_time = job.completion_time - job.arrival_time
                    self._notify_callbacks(job)
                    logger.info(f"Job {job.job_id} completed (Round Robin)")
                else:
                    # Re-add to queue
                    active_jobs.append(job)
            
            except Exception as e:
                logger.error(f"Round Robin scheduler error: {e}")
                time.sleep(0.1)
    
    def _get_next_job(self) -> Optional[Job]:
        """Get next job based on scheduling algorithm"""
        if self.algorithm == SchedulingAlgorithm.PRIORITY:
            if not self.priority_queue.empty():
                return self.priority_queue.get()
        
        elif self.algorithm == SchedulingAlgorithm.SJF:
            # Get all pending jobs and sort by burst time
            with self.lock:
                pending_jobs = [j for j in self.jobs.values() if j.status == JobStatus.PENDING]
                if pending_jobs:
                    return min(pending_jobs, key=lambda j: j.burst_time)
        
        elif self.algorithm == SchedulingAlgorithm.FCFS:
            if not self.job_queue.empty():
                return self.job_queue.get()
        
        return None
    
    def _execute_job(self, job: Job):
        """Execute a job (simulated work)"""
        job.status = JobStatus.RUNNING
        job.start_time = time.time()
        job.waiting_time = job.start_time - job.arrival_time
        job.thread_id = threading.get_ident()
        
        self._notify_callbacks(job)
        logger.info(f"Job {job.job_id} started on thread {job.thread_id}")
        
        try:
            # Simulate job execution
            time.sleep(job.burst_time)
            job.result = f"Job {job.name} completed successfully"
            
        except Exception as e:
            job.error = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
    
    def _execute_job_partial(self, job: Job, exec_time: float):
        """Execute a job for a specific time quantum"""
        if job.start_time is None:
            job.status = JobStatus.RUNNING
            job.start_time = time.time()
            job.waiting_time = job.start_time - job.arrival_time
            job.thread_id = threading.get_ident()
            self._notify_callbacks(job)
            logger.info(f"Job {job.job_id} started on thread {job.thread_id}")
        
        # Execute for quantum time
        time.sleep(exec_time)
        job.remaining_time -= exec_time
        
        logger.info(f"Job {job.job_id} executed for {exec_time}s, remaining: {job.remaining_time}s")
    
    def _job_completed(self, job: Job, future: Future):
        """Callback when job completes"""
        try:
            future.result()  # Check for exceptions
            job.status = JobStatus.COMPLETED
            job.completion_time = time.time()
            job.turnaround_time = job.completion_time - job.arrival_time
            
            logger.info(f"Job {job.job_id} completed. TAT: {job.turnaround_time:.2f}s, Wait: {job.waiting_time:.2f}s")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
        
        finally:
            self._notify_callbacks(job)
    
    def get_statistics(self) -> Dict:
        """Get scheduler statistics"""
        with self.lock:
            jobs = list(self.jobs.values())
            
            total_jobs = len(jobs)
            completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
            running_jobs = [j for j in jobs if j.status == JobStatus.RUNNING]
            pending_jobs = [j for j in jobs if j.status == JobStatus.PENDING]
            failed_jobs = [j for j in jobs if j.status == JobStatus.FAILED]
            
            avg_waiting_time = sum(j.waiting_time for j in completed_jobs) / len(completed_jobs) if completed_jobs else 0
            avg_turnaround_time = sum(j.turnaround_time for j in completed_jobs) / len(completed_jobs) if completed_jobs else 0
            
            return {
                "total_jobs": total_jobs,
                "completed": len(completed_jobs),
                "running": len(running_jobs),
                "pending": len(pending_jobs),
                "failed": len(failed_jobs),
                "avg_waiting_time": round(avg_waiting_time, 2),
                "avg_turnaround_time": round(avg_turnaround_time, 2),
                "algorithm": self.algorithm.value,
                "max_workers": self.max_workers,
                "is_running": self.running,
                "is_paused": self.paused
            }


# Global scheduler instance
scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """Get or create global scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = JobScheduler(max_workers=4, algorithm=SchedulingAlgorithm.FCFS)
    return scheduler
