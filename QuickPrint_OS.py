import time
import threading
from queue import Queue
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------
# Job class to represent a print job
# ----------------------------
class PrintJob:
    def __init__(self, job_id, document_name, num_pages, priority):
        self.job_id = job_id
        self.document_name = document_name
        self.num_pages = num_pages
        self.priority = priority
        self.submission_time = time.time()

    def __repr__(self):
        return f"Job[{self.job_id}] - {self.document_name} ({self.num_pages} pages, Priority {self.priority})"

# ----------------------------
# Combined Priority + SJN Scheduler
# ----------------------------
class PrioritySJNQueue:
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def process_jobs(self, output_callback):
        self.jobs.sort(key=lambda job: (job.priority, job.num_pages))
        for job in self.jobs:
            output_callback(f"Processing: {job}")
            for page in range(1, job.num_pages + 1):
                output_callback(f"\tPrinting page {page}/{job.num_pages} of '{job.document_name}'...")
                time.sleep(0.5)
            output_callback(f"Completed: {job}\n")

# ----------------------------
# Round Robin Scheduling Manager
# ----------------------------
class RoundRobinPrintQueue:
    def __init__(self, time_slice=10):
        self.jobs = []
        self.time_slice = time_slice

    def add_job(self, job):
        self.jobs.append(job)

    def process_jobs(self, output_callback):
        output_callback(f"Starting Round Robin Scheduling with time slice = {self.time_slice} pages")
        while any(job.num_pages > 0 for job in self.jobs):
            for job in self.jobs:
                if job.num_pages > 0:
                    output_callback(f"Processing: {job}")
                    pages_to_print = min(self.time_slice, job.num_pages)
                    for page in range(pages_to_print):
                        output_callback(f"\tPrinting page {page+1}/{job.num_pages} of '{job.document_name}'...")
                        time.sleep(0.5)
                    job.num_pages -= pages_to_print
                    if job.num_pages == 0:
                        output_callback(f"Completed: {job}\n")

# ----------------------------
# GUI Interface
# ----------------------------
def start_gui():
    job_list = []
    job_counter = [1]

    def submit_job():
        name = doc_name_entry.get()
        try:
            pages = int(num_pages_entry.get())
            priority = int(priority_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Pages and Priority must be integers")
            return
        job = PrintJob(job_counter[0], name, pages, priority)
        job_list.append(job)
        job_counter[0] += 1
        job_queue.insert('', 'end', values=(job.job_id, name, pages, priority))
        doc_name_entry.delete(0, tk.END)
        num_pages_entry.delete(0, tk.END)
        priority_entry.delete(0, tk.END)

    def process_queue():
        output_text.delete('1.0', tk.END)
        algorithm = algorithm_var.get()

        if algorithm == "Round Robin":
            scheduler = RoundRobinPrintQueue()
        else:
            scheduler = PrioritySJNQueue()

        for job in job_list:
            scheduler.add_job(job)

        def run():
            scheduler.process_jobs(lambda msg: output_text.insert(tk.END, msg + "\n"))

        threading.Thread(target=run).start()

    def clear_jobs():
        job_list.clear()
        job_queue.delete(*job_queue.get_children())
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, "All jobs cleared.")

    # GUI Layout
    root = tk.Tk()
    root.title("QuickPrint - Smart Print Scheduler")
    root.geometry("600x650")
    root.configure(bg="#dbeeff")  # Light blue background

    style = ttk.Style()
    style.layout("Custom.Treeview", [('Custom.Treeview.treearea', {'sticky': 'nswe'})])
    style.map("Custom.Treeview", background=[('selected', '#cceeff')])
    style.configure("Custom.Treeview", borderwidth=1, relief="solid", rowheight=25)
    style.configure("Custom.Treeview", borderwidth=1, relief="solid")
    style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

    title = tk.Label(root, text="QuickPrint Scheduler", font=("Helvetica", 16, "bold"), bg="#dbeeff", fg="#333")
    title.pack(pady=10)

    form_frame = tk.Frame(root, bg="#dbeeff")
    form_frame.pack(pady=5)

    tk.Label(form_frame, text="Document Name:", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=2, sticky='e')
    tk.Label(form_frame, text="Number of Pages:", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=2, sticky='e')
    tk.Label(form_frame, text="Priority (1=High):", bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=2, sticky='e')

    doc_name_entry = tk.Entry(form_frame)
    num_pages_entry = tk.Entry(form_frame)
    priority_entry = tk.Entry(form_frame)
    doc_name_entry.grid(row=0, column=1, padx=5)
    num_pages_entry.grid(row=1, column=1, padx=5)
    priority_entry.grid(row=2, column=1, padx=5)

    tk.Button(form_frame, text="Add Print Job", command=submit_job, bg="#4CAF50", fg="white").grid(row=3, column=0, columnspan=2, pady=5)

    algo_frame = tk.Frame(root, bg="#dbeeff")
    algo_frame.pack(pady=5)

    tk.Label(algo_frame, text="Select Scheduling Algorithm:", bg="#f0f0f0").grid(row=0, column=0, columnspan=2)
    algorithm_var = tk.StringVar(value="Round Robin")
    algorithm_menu = ttk.Combobox(algo_frame, textvariable=algorithm_var, state="readonly")
    algorithm_menu['values'] = ["Round Robin", "Priority + SJN"]
    algorithm_menu.grid(row=1, column=0, columnspan=2, pady=5)

    tk.Button(algo_frame, text="Start Scheduling", command=process_queue, bg="#2196F3", fg="white").grid(row=2, column=0, pady=5)
    tk.Button(algo_frame, text="Clear Jobs", command=clear_jobs, bg="#f44336", fg="white").grid(row=2, column=1, pady=5)

    job_queue = ttk.Treeview(root, columns=("ID", "Name", "Pages", "Priority"), show='headings', height=5, style='Custom.Treeview')
    for col in ("ID", "Name", "Pages", "Priority"):
        job_queue.heading(col, text=col)
        job_queue.column(col, anchor="center", width=140, minwidth=100)
    job_queue.pack(pady=10)

    output_label = tk.Label(root, text="Output Log:", font=("Helvetica", 12, "bold"), bg="#f0f0f0")
    output_label.pack()

    output_text = tk.Text(root, height=12, width=70, bg="white", fg="black", font=("Courier", 10))
    output_text.pack(pady=5)

    root.mainloop()

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    start_gui()
