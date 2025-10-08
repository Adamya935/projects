# ml_model.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def simulate_workloads(n=500):
    """Simulate workloads and label them with a best algorithm using rules."""
    np.random.seed(42)
    data = []
    for _ in range(n):
        job_length = np.random.randint(1, 20)
        priority = np.random.randint(1, 5)
        load = np.random.randint(1, 100)

        if job_length <= 5:
            label = "SJF"
        elif priority == 1:
            label = "PRIORITY"
        elif load > 70:
            label = "RR"
        else:
            label = "FCFS"

        data.append([job_length, priority, load, label])

    return pd.DataFrame(data, columns=["job_length", "priority", "load", "best_algo"])

def train_model():
    """Train a RandomForest model on simulated workloads and save it."""
    df = simulate_workloads()
    X = df[["job_length", "priority", "load"]]
    y = df["best_algo"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, "scheduler_model.pkl")
    print("✅ Model trained and saved as scheduler_model.pkl")

def load_model():
    """Load the trained ML model from file."""
    return joblib.load("scheduler_model.pkl")

def predict_best_algo(model, job_length, priority, load):
    """Predict the best scheduling algorithm for a new job."""
    X = [[job_length, priority, load]]
    return model.predict(X)[0]

if _name_ == "_main_":
    train_model()

    import tkinter as tk
from gui import SchedulerGUI

if _name_ == "_main_":
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()
    import tkinter as tk
from tkinter import ttk, messagebox
import random
from scheduler import Job, run_scheduler
from ml_model import load_model, predict_best_algo

class SchedulerGUI:
    def _init_(self, root):
        self.root = root
        self.root.title("AI-Driven Smart Job Scheduler")
        self.jobs = []
        self.job_id = 0
        self.model = load_model()

        self.tree = ttk.Treeview(root, columns=("burst", "priority"), show="headings")
        self.tree.heading("burst", text="Burst Time")
        self.tree.heading("priority", text="Priority")
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(root)
        frame.pack()

        tk.Button(frame, text="Add Job", command=self.add_job).pack(side="left", padx=5)
        tk.Button(frame, text="Run Scheduler", command=self.run).pack(side="left", padx=5)

        self.result_label = tk.Label(root, text="", font=("Arial", 12, "bold"))
        self.result_label.pack(pady=10)

    def add_job(self):
        self.job_id += 1
        burst = random.randint(1, 10)
        priority = random.randint(1, 10)
        job = {"job_id": self.job_id, "burst_time": burst, "priority": priority}
        self.jobs.append(job)
        self.tree.insert("", "end", values=(burst, priority))

    def run(self):
        if not self.jobs:
            messagebox.showwarning("Warning", "No jobs to schedule!")
            return

        algo = predict_best_algo(self.jobs, self.model)
        self.result_label.config(text=f"🤖 ML Chose: {algo}")

        jobs = [Job(j["job_id"], j["burst_time"], j["priority"]) for j in self.jobs]
        scheduled_jobs = run_scheduler(algo, jobs)

        result = "\n".join([f"Job{j.job_id} | Wait: {j.waiting_time} | TAT: {j.turnaround_time}" 
                            for j in scheduled_jobs])
        messagebox.showinfo("Results", result)