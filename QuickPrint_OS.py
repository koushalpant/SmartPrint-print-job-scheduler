import time
import threading
from queue import Queue
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import tkinter.messagebox as mb
import ctypes


# Job class to represent a print job

class PrintJob:
    def __init__(self, job_id, document_name, num_pages, priority):
        self.job_id = job_id
        self.document_name = document_name
        self.num_pages = num_pages
        self.priority = priority
        self.submission_time = time.time()

    def __repr__(self):
        return f"Job[{self.job_id}] - {self.document_name} ({self.num_pages} pages, Priority {self.priority})"


# Combined Priority + SJN Scheduler

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


# Round Robin Scheduling Manager

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


# GUI Interface

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("dark-blue")

class PrintJob:
    def __init__(self, job_id, document_name, num_pages, priority):
        self.job_id = job_id
        self.document_name = document_name
        self.num_pages = num_pages
        self.priority = priority

    def __repr__(self):
        return f"{self.document_name} ({self.num_pages} pages, P{self.priority})"

class PrintSchedulerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🖨️ QuickPrint Scheduler")
        self.jobs = []
        self.job_id_counter = 1

        self.configure(padx=20, pady=20)
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.build_ui()
        self.state("zoomed")

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, corner_radius=10)
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="🖨️ QuickPrint Scheduler", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=15, pady=15)
        self.theme_switch = ctk.CTkSwitch(header, text="Light Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="right", padx=15)

        # Form Frame
        form = ctk.CTkFrame(self)
        form.pack(fill="x", pady=10)

        self.doc_name = ctk.CTkEntry(form, placeholder_text="Document Name")
        self.pages = ctk.CTkEntry(form, placeholder_text="Number of Pages")
        self.priority = ctk.CTkEntry(form, placeholder_text="Priority (1 = High)")

        self.doc_name.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.pages.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.priority.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        form.grid_columnconfigure((0, 1, 2), weight=1)

        self.add_btn = ctk.CTkButton(form, text="➕ Add Job", command=self.add_job)
        self.add_btn.grid(row=0, column=3, padx=10)

        # Table
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True, pady=10)
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 20), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 25, "bold"))

        self.tree = ttk.Treeview(self.table_frame, columns=("ID", "Name", "Pages", "Priority"), show="headings", height=6)
        for col in ("ID", "Name", "Pages", "Priority"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Control Buttons
        control = ctk.CTkFrame(self)
        control.pack(fill="x", pady=10)

        self.start_btn = ctk.CTkButton(control, text="▶️ Start Round Robin", command=self.start_printing)
        self.clear_btn = ctk.CTkButton(control, text="🧹 Clear Jobs", command=self.clear_jobs)

        self.start_btn.pack(side="left", padx=10, pady=10)
        self.clear_btn.pack(side="left", padx=10, pady=10)

        # Progress & Output
        self.output_box = ctk.CTkTextbox(self, height=180)
        self.output_box.pack(fill="both", expand=False, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(self, height=10)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def toggle_theme(self):

        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Light Mode")

    def add_job(self):
        name = self.doc_name.get()
        try:
            pages = int(self.pages.get())
            priority = int(self.priority.get())
        except ValueError:
            mb.showerror("Error", "Pages and Priority must be integers.")
            return

        job = PrintJob(self.job_id_counter, name, pages, priority)
        self.jobs.append(job)
        self.tree.insert('', 'end', values=(job.job_id, job.document_name, job.num_pages, job.priority))
        self.job_id_counter += 1

        self.doc_name.delete(0, 'end')
        self.pages.delete(0, 'end')
        self.priority.delete(0, 'end')

    def clear_jobs(self):
        self.jobs.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.output_box.delete("1.0", "end")
        self.progress_bar.set(0)

    def start_printing(self):
        if not self.jobs:
            mb.showinfo("No Jobs", "Add some jobs before starting.")
            return

        def worker():
            total_pages = sum(job.num_pages for job in self.jobs)
            printed_pages = 0
            time_slice = 5

            while any(job.num_pages > 0 for job in self.jobs):
                for job in self.jobs:
                    if job.num_pages > 0:
                        pages_to_print = min(time_slice, job.num_pages)
                        self.output_box.insert("end", f"🖨️ {job.document_name} - Printing {pages_to_print} pages...\n")
                        self.output_box.see("end")
                        time.sleep(0.3 * pages_to_print)
                        job.num_pages -= pages_to_print
                        printed_pages += pages_to_print
                        progress = printed_pages / total_pages
                        self.progress_bar.set(progress)
                        self.update_idletasks()

        threading.Thread(target=worker).start()

if __name__ == "__main__":
    app = PrintSchedulerApp()
    app.state("zoomed")
    app.mainloop()
