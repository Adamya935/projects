import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

const COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  pending: '#6b7280',
  running: '#3b82f6',
  completed: '#10b981',
  failed: '#ef4444',
  cancelled: '#9ca3af'
};

function App() {
  const [jobs, setJobs] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  
  // Form state
  const [jobName, setJobName] = useState('');
  const [burstTime, setBurstTime] = useState(5);
  const [priority, setPriority] = useState(5);
  const [algorithm, setAlgorithm] = useState('fcfs');
  const [maxWorkers, setMaxWorkers] = useState(4);

  // Connect to WebSocket
  useEffect(() => {
    const connectWebSocket = () => {
      const websocket = new WebSocket(WS_URL);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
      };
      
      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'job_update') {
          setJobs(prevJobs => {
            const index = prevJobs.findIndex(j => j.job_id === message.data.job_id);
            if (index >= 0) {
              const newJobs = [...prevJobs];
              newJobs[index] = message.data;
              return newJobs;
            } else {
              return [...prevJobs, message.data];
            }
          });
        } else if (message.type === 'statistics') {
          setStatistics(message.data);
        }
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      setWs(websocket);
    };
    
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Fetch initial data
  useEffect(() => {
    fetchJobs();
    fetchStatistics();
    fetchSchedulerStatus();
    
    const interval = setInterval(() => {
      fetchStatistics();
      fetchSchedulerStatus();
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs`);
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE}/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/scheduler/status`);
      const data = await response.json();
      setSchedulerStatus(data);
    } catch (error) {
      console.error('Error fetching scheduler status:', error);
    }
  };

  const submitJob = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${API_BASE}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: jobName || `Job-${Date.now()}`,
          burst_time: parseFloat(burstTime),
          priority: parseInt(priority)
        })
      });
      
      if (response.ok) {
        setJobName('');
        setBurstTime(5);
        setPriority(5);
        fetchJobs();
      }
    } catch (error) {
      console.error('Error submitting job:', error);
    }
  };

  const startScheduler = async () => {
    try {
      await fetch(`${API_BASE}/scheduler/start`, { method: 'POST' });
      fetchSchedulerStatus();
    } catch (error) {
      console.error('Error starting scheduler:', error);
    }
  };

  const stopScheduler = async () => {
    try {
      await fetch(`${API_BASE}/scheduler/stop`, { method: 'POST' });
      fetchSchedulerStatus();
    } catch (error) {
      console.error('Error stopping scheduler:', error);
    }
  };

  const pauseScheduler = async () => {
    try {
      await fetch(`${API_BASE}/scheduler/pause`, { method: 'POST' });
      fetchSchedulerStatus();
    } catch (error) {
      console.error('Error pausing scheduler:', error);
    }
  };

  const resumeScheduler = async () => {
    try {
      await fetch(`${API_BASE}/scheduler/resume`, { method: 'POST' });
      fetchSchedulerStatus();
    } catch (error) {
      console.error('Error resuming scheduler:', error);
    }
  };

  const configureScheduler = async () => {
    try {
      await fetch(`${API_BASE}/scheduler/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_workers: parseInt(maxWorkers),
          algorithm: algorithm,
          quantum: 2.0
        })
      });
      fetchSchedulerStatus();
    } catch (error) {
      console.error('Error configuring scheduler:', error);
    }
  };

  const populateDemoJobs = async () => {
    try {
      await fetch(`${API_BASE}/demo/populate`, { method: 'POST' });
      fetchJobs();
    } catch (error) {
      console.error('Error populating demo jobs:', error);
    }
  };

  const cancelJob = async (jobId) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
      fetchJobs();
    } catch (error) {
      console.error('Error cancelling job:', error);
    }
  };

  // Calculate chart data
  const statusChartData = useMemo(() => {
    if (!statistics) return [];
    return [
      { name: 'Completed', value: statistics.completed, color: COLORS.completed },
      { name: 'Running', value: statistics.running, color: COLORS.running },
      { name: 'Pending', value: statistics.pending, color: COLORS.pending },
      { name: 'Failed', value: statistics.failed, color: COLORS.failed }
    ].filter(item => item.value > 0);
  }, [statistics]);

  const jobTimelineData = useMemo(() => {
    return jobs
      .filter(job => job.completion_time)
      .sort((a, b) => a.completion_time - b.completion_time)
      .slice(-10)
      .map(job => ({
        name: job.name.substring(0, 15),
        waiting: parseFloat(job.waiting_time.toFixed(2)),
        turnaround: parseFloat(job.turnaround_time.toFixed(2))
      }));
  }, [jobs]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-lg border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Multi-threaded Job Scheduler
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Real-time job scheduling with multiple algorithms
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                <span className="text-sm font-medium">{connected ? 'Connected' : 'Disconnected'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Jobs</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{statistics.total_jobs}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📋</span>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</p>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">{statistics.completed}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">✅</span>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Running</p>
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">{statistics.running}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">⚡</span>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Wait Time</p>
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">{statistics.avg_waiting_time}s</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">⏱️</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Controls */}
          <div className="space-y-6">
            {/* Job Submission Form */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Submit New Job</h2>
              <form onSubmit={submitJob} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Job Name
                  </label>
                  <input
                    type="text"
                    value={jobName}
                    onChange={(e) => setJobName(e.target.value)}
                    placeholder="Enter job name"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Burst Time (seconds): {burstTime}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={burstTime}
                    onChange={(e) => setBurstTime(e.target.value)}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Priority (1=highest, 10=lowest): {priority}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 shadow-lg"
                >
                  Submit Job
                </button>
              </form>

              <button
                onClick={populateDemoJobs}
                className="w-full mt-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
              >
                Add Demo Jobs
              </button>
            </div>

            {/* Scheduler Controls */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Scheduler Controls</h2>
              
              {schedulerStatus && (
                <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      schedulerStatus.is_running && !schedulerStatus.is_paused
                        ? 'bg-green-100 text-green-800'
                        : schedulerStatus.is_paused
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {schedulerStatus.is_running && !schedulerStatus.is_paused ? 'Running' : schedulerStatus.is_paused ? 'Paused' : 'Stopped'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Algorithm:</span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white uppercase">{schedulerStatus.algorithm}</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={startScheduler}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Start
                </button>
                <button
                  onClick={stopScheduler}
                  className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Stop
                </button>
                <button
                  onClick={pauseScheduler}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Pause
                </button>
                <button
                  onClick={resumeScheduler}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Resume
                </button>
              </div>
            </div>

            {/* Configuration */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Configuration</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Algorithm
                  </label>
                  <select
                    value={algorithm}
                    onChange={(e) => setAlgorithm(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="fcfs">FCFS (First Come First Serve)</option>
                    <option value="sjf">SJF (Shortest Job First)</option>
                    <option value="priority">Priority Scheduling</option>
                    <option value="round_robin">Round Robin</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max Workers: {maxWorkers}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="16"
                    value={maxWorkers}
                    onChange={(e) => setMaxWorkers(e.target.value)}
                    className="w-full"
                  />
                </div>

                <button
                  onClick={configureScheduler}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Apply Configuration
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Visualizations */}
          <div className="lg:col-span-2 space-y-6">
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Status Distribution */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Job Status Distribution</h3>
                {statusChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={statusChartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {statusChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    No data available
                  </div>
                )}
              </div>

              {/* Job Timeline */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Job Performance (Last 10)</h3>
                {jobTimelineData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={jobTimelineData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#6b7280" angle={-45} textAnchor="end" height={80} />
                      <YAxis stroke="#6b7280" />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="waiting" fill="#f59e0b" name="Wait Time (s)" />
                      <Bar dataKey="turnaround" fill="#3b82f6" name="Turnaround (s)" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    No completed jobs yet
                  </div>
                )}
              </div>
            </div>

            {/* Job List */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Job Queue ({jobs.length})</h3>
              <div className="overflow-x-auto">
                <div className="max-h-96 overflow-y-auto scrollbar-hide">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Job ID</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Burst</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Priority</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Thread</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {jobs.length === 0 ? (
                        <tr>
                          <td colSpan="7" className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                            No jobs in queue. Submit a job to get started!
                          </td>
                        </tr>
                      ) : (
                        jobs.map((job) => (
                          <tr key={job.job_id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                              {job.job_id}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {job.name}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                job.status === 'completed' ? 'bg-green-100 text-green-800' :
                                job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                                job.status === 'failed' ? 'bg-red-100 text-red-800' :
                                job.status === 'cancelled' ? 'bg-gray-100 text-gray-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {job.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {job.burst_time}s
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {job.priority}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                              {job.thread_id || '-'}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              {job.status === 'pending' && (
                                <button
                                  onClick={() => cancelJob(job.job_id)}
                                  className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 font-medium"
                                >
                                  Cancel
                                </button>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
