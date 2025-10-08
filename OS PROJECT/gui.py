# scheduler.py
import random

class Job:
    def _init_(self, job_id, burst_time, priority=3):
        self.job_id = job_id
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority

def fcfs(jobs):
    t = 0
    schedule = []
    for job in jobs:
        schedule.append((t, job.job_id))
        t += job.burst_time
    return schedule

def sjf(jobs):
    jobs = sorted(jobs, key=lambda j: j.burst_time)
    t = 0
    schedule = []
    for job in jobs:
        schedule.append((t, job.job_id))
        t += job.burst_time
    return schedule

def priority_scheduling(jobs):
    jobs = sorted(jobs, key=lambda j: j.priority)
    t = 0
    schedule = []
    for job in jobs:
        schedule.append((t, job.job_id))
        t += job.burst_time
    return schedule

def round_robin(jobs, quantum=2):
    t = 0
    schedule = []
    queue = jobs[:]
    while queue:
        job = queue.pop(0)
        if job.remaining_time > quantum:
            schedule.append((t, job.job_id))
            t += quantum
            job.remaining_time -= quantum
            queue.append(job)
        else:
            schedule.append((t, job.job_id))
            t += job.remaining_time
            job.remaining_time = 0
    return schedule

def run_scheduler(jobs, algorithm="FCFS"):
    """Run the selected scheduling algorithm on a list of jobs."""
    if algorithm.upper() == "FCFS":
        return fcfs(jobs)
    elif algorithm.upper() == "SJF":
        return sjf(jobs)
    elif algorithm.upper() == "PRIORITY":
        return priority_scheduling(jobs)
    elif algorithm.upper() == "RR":
        return round_robin(jobs)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")