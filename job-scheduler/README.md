# Multi-threaded Job Scheduler

A comprehensive job scheduling system with multi-threading support, featuring a Python backend with FastAPI and a modern React frontend.

## Features

### Backend (Python)
- **Multi-threaded Job Execution**: Uses `ThreadPoolExecutor` for concurrent job processing
- **Multiple Scheduling Algorithms**:
  - FCFS (First Come First Serve)
  - SJF (Shortest Job First)
  - Priority Scheduling
  - Round Robin with configurable time quantum
- **Real-time Monitoring**: WebSocket support for live job status updates
- **Thread Pool Management**: Configurable number of worker threads
- **Job Status Tracking**: Complete lifecycle tracking (pending → running → completed/failed)

### API (FastAPI)
- RESTful endpoints for job management
- WebSocket for real-time updates
- Job submission, cancellation, and monitoring
- Scheduler control (start/stop/pause/resume)
- Configuration management
- Statistics and performance metrics

### Frontend (React + Tailwind CSS)
- Modern, responsive dashboard
- Real-time job queue visualization
- Interactive charts and metrics (Recharts)
- Job submission form with priority and burst time controls
- Scheduler controls and configuration
- Live status updates via WebSocket
- Performance analytics (waiting time, turnaround time)

## Architecture

```
job-scheduler/
├── backend/
│   ├── scheduler.py      # Core multi-threaded scheduler
│   ├── api.py           # FastAPI REST API + WebSocket
│   └── requirements.txt # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.jsx      # Main React application
    │   ├── main.jsx     # React entry point
    │   └── index.css    # Tailwind CSS styles
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── postcss.config.js
```

## Installation

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the FastAPI server:
```bash
python api.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

### 1. Start the Backend
```bash
cd backend
python api.py
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Access the Dashboard
Open your browser and navigate to `http://localhost:3000`

### 4. Using the Scheduler

1. **Configure the Scheduler**:
   - Select scheduling algorithm (FCFS, SJF, Priority, Round Robin)
   - Set maximum number of worker threads (1-16)
   - Click "Apply Configuration"

2. **Start the Scheduler**:
   - Click "Start" button to begin processing jobs

3. **Submit Jobs**:
   - Enter job name
   - Set burst time (execution duration in seconds)
   - Set priority (1=highest, 10=lowest)
   - Click "Submit Job"

4. **Monitor Execution**:
   - View real-time job status in the job queue table
   - Monitor statistics (total jobs, completed, running, avg wait time)
   - Analyze performance with charts

5. **Control Scheduler**:
   - **Pause**: Temporarily stop processing new jobs
   - **Resume**: Continue processing after pause
   - **Stop**: Completely stop the scheduler

## API Endpoints

### Job Management
- `POST /jobs` - Submit a new job
- `GET /jobs` - Get all jobs
- `GET /jobs/{job_id}` - Get specific job
- `DELETE /jobs/{job_id}` - Cancel a pending job

### Scheduler Control
- `POST /scheduler/start` - Start the scheduler
- `POST /scheduler/stop` - Stop the scheduler
- `POST /scheduler/pause` - Pause the scheduler
- `POST /scheduler/resume` - Resume the scheduler
- `POST /scheduler/configure` - Configure scheduler settings
- `GET /scheduler/status` - Get scheduler status

### Statistics
- `GET /statistics` - Get detailed statistics

### WebSocket
- `WS /ws` - Real-time updates

### Demo
- `POST /demo/populate` - Add demo jobs for testing

## Scheduling Algorithms

### FCFS (First Come First Serve)
Jobs are executed in the order they arrive. Simple and fair but may lead to convoy effect.

### SJF (Shortest Job First)
Jobs with shortest burst time are executed first. Minimizes average waiting time but may cause starvation.

### Priority Scheduling
Jobs are executed based on priority (1=highest, 10=lowest). Higher priority jobs execute first.

### Round Robin
Each job gets a fixed time quantum (2 seconds). Jobs are executed in circular order, ensuring fairness.

## Multi-threading Details

- **Thread Pool**: Uses `concurrent.futures.ThreadPoolExecutor`
- **Configurable Workers**: 1-16 worker threads
- **Thread Safety**: Uses locks for shared data structures
- **Concurrent Execution**: Multiple jobs can run simultaneously
- **Thread Tracking**: Each job tracks which thread executed it

## Performance Metrics

- **Waiting Time**: Time between job arrival and start of execution
- **Turnaround Time**: Total time from arrival to completion
- **Average Metrics**: Calculated across all completed jobs
- **Real-time Updates**: Metrics update as jobs complete

## Technologies Used

### Backend
- Python 3.x
- FastAPI (REST API framework)
- Uvicorn (ASGI server)
- Threading & concurrent.futures (Multi-threading)
- WebSockets (Real-time communication)

### Frontend
- React 18
- Vite (Build tool)
- Tailwind CSS (Styling)
- Recharts (Data visualization)
- WebSocket API (Real-time updates)

## Example Usage

### Submit a Job via API
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Processing",
    "burst_time": 5.0,
    "priority": 3
  }'
```

### Get All Jobs
```bash
curl http://localhost:8000/jobs
```

### Start Scheduler
```bash
curl -X POST http://localhost:8000/scheduler/start
```

### Configure Scheduler
```bash
curl -X POST http://localhost:8000/scheduler/configure \
  -H "Content-Type: application/json" \
  -d '{
    "max_workers": 8,
    "algorithm": "priority",
    "quantum": 2.0
  }'
```

## Testing

1. Click "Add Demo Jobs" to populate the queue with sample jobs
2. Configure the scheduler with desired algorithm
3. Click "Start" to begin processing
4. Watch real-time updates in the dashboard
5. Monitor thread IDs to see concurrent execution
6. Analyze performance metrics and charts

## Troubleshooting

### Backend Issues
- Ensure Python 3.x is installed
- Check if port 8000 is available
- Verify all dependencies are installed

### Frontend Issues
- Ensure Node.js 16+ is installed
- Check if port 3000 is available
- Clear browser cache if WebSocket connection fails

### WebSocket Connection
- Ensure backend is running before starting frontend
- Check browser console for connection errors
- Verify CORS settings if accessing from different origin

## License

MIT License - Feel free to use and modify as needed.
