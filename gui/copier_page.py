import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db import fetch_databases, copy_database_logic

class CopierPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # State variables
        self.all_databases = []
        self.selected_source_db = None
        self.copy_thread = None

        # Set up a clean, simple layout
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Database Copier", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Source database selection
        source_frame = ttk.LabelFrame(main_frame, text="Select Source Database")
        source_frame.pack(fill="x", pady=(0, 15))
        
        # Search bar
        search_frame = ttk.Frame(source_frame)
        search_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_databases)  # Update as user types
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=5)
        
        clear_btn = ttk.Button(search_frame, text="Clear", width=8, 
                             command=lambda: self.search_var.set(""))
        clear_btn.pack(side="left")

        # Database listbox
        listbox_frame = ttk.Frame(source_frame)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        self.db_listbox = tk.Listbox(listbox_frame, height=8)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.db_listbox.yview)
        self.db_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.db_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.db_listbox.bind("<<ListboxSelect>>", self.on_db_select)

        # Refresh button
        refresh_btn = ttk.Button(source_frame, text="Refresh List", command=self.refresh_databases)
        refresh_btn.pack(side="bottom", padx=10, pady=(0, 10))

        # Target database configuration
        target_frame = ttk.LabelFrame(main_frame, text="Target Database")
        target_frame.pack(fill="x", pady=(0, 15))

        target_name_frame = ttk.Frame(target_frame)
        target_name_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(target_name_frame, text="New Database Name:").pack(side="left")
        
        self.target_name_var = tk.StringVar()
        self.target_name_entry = ttk.Entry(target_name_frame, textvariable=self.target_name_var, width=30)
        self.target_name_entry.pack(side="left", padx=10)

        # Action button
        self.copy_btn = ttk.Button(main_frame, text="Copy Database", command=self.start_copy)
        self.copy_btn.pack(pady=15)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress")
        progress_frame.pack(fill="x", pady=(0, 15))

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(anchor="w", padx=10, pady=(10, 5))

        progress_bar_frame = ttk.Frame(progress_frame)
        progress_bar_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_bar_frame, mode="determinate")
        self.progress_bar.pack(side="left", fill="x", expand=True)
        
        self.progress_percent = ttk.Label(progress_bar_frame, text="0%", width=5)
        self.progress_percent.pack(side="left", padx=5)

        # Load databases when the frame is shown
        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    def load_databases(self):
        """Load the list of databases into the listbox."""
        credentials = self.controller.db_credentials
        if not credentials:
            return
        
        # Get the full list of databases
        self.all_databases = sorted(fetch_databases(credentials))
        
        # Apply any current search filter
        self.filter_databases()
        
        # Update status
        self.status_label.config(text=f"Loaded {len(self.all_databases)} databases")

    def filter_databases(self, *args):
        """Filter the database list based on search text."""
        search_text = self.search_var.get().lower()
        
        # Clear the listbox
        self.db_listbox.delete(0, tk.END)
        
        # Filter databases by search text
        for db in self.all_databases:
            if search_text in db.lower():
                self.db_listbox.insert(tk.END, db)
        
        # If nothing matches, show a message
        if self.db_listbox.size() == 0 and search_text:
            self.db_listbox.insert(tk.END, "No matching databases found")
            self.db_listbox.itemconfig(0, fg="gray")

    def refresh_databases(self):
        """Reload the database list."""
        # Clear search field
        self.search_var.set("")
        
        # Reload databases
        self.load_databases()
        
        # Reset progress indicators
        self.progress_bar["value"] = 0
        self.progress_percent.config(text="0%")

    def on_db_select(self, event):
        """Handle database selection."""
        selection = self.db_listbox.curselection()
        if not selection:
            return
        
        # Get selected database name
        index = selection[0]
        db_name = self.db_listbox.get(index)
        
        # Ignore selection if it's the "No matching databases" message
        if db_name == "No matching databases found":
            return
            
        self.selected_source_db = db_name
        
        # Suggest a target name
        self.target_name_var.set(f"{db_name}_copy")
        
        # Update status
        self.status_label.config(text=f"Selected database: {db_name}")

    def start_copy(self):
        """Start the database copy process."""
        if not self.selected_source_db:
            messagebox.showwarning("Selection Required", "Please select a source database.")
            return
        
        target_name = self.target_name_var.get().strip()
        if not target_name:
            messagebox.showwarning("Name Required", "Please enter a name for the target database.")
            return
        
        # Disable the copy button during the operation
        self.copy_btn.config(state="disabled")
        
        # Reset progress indicators
        self.progress_bar["value"] = 0
        self.progress_percent.config(text="0%")
        self.status_label.config(text="Starting copy operation...")
        
        # Start the copy process in a background thread
        self.copy_thread = threading.Thread(
            target=self.execute_copy,
            args=(self.selected_source_db, target_name),
            daemon=True
        )
        self.copy_thread.start()
        
        # Start progress updates
        self.after(100, self.update_progress)

    def execute_copy(self, source_db, target_db):
        """Execute the database copy operation."""
        try:
            # Perform the copy operation
            credentials = self.controller.db_credentials
            copy_database_logic(credentials, source_db, target_db, self.update_status)
            
            # Show success message
            self.after(0, lambda: self.copy_completed(target_db))
            
        except Exception as e:
            # Show error message
            self.after(0, lambda: self.copy_failed(str(e)))

    def update_status(self, message):
        """Update the status message during copy operation."""
        self.after(0, lambda msg=message: self.status_label.config(text=msg))

    def update_progress(self):
        """Update the progress display during copy operation."""
        if self.copy_thread and self.copy_thread.is_alive():
            # Simulate progress
            current_value = self.progress_bar["value"]
            if current_value < 95:
                # Simple linear progress
                new_value = current_value + 5
                self.progress_bar["value"] = new_value
                self.progress_percent.config(text=f"{int(new_value)}%")
            
            # Continue updates
            self.after(300, self.update_progress)
        else:
            # Copy is complete
            self.progress_bar["value"] = 100
            self.progress_percent.config(text="100%")

    def copy_completed(self, target_db):
        """Handle successful copy completion."""
        # Update UI
        self.status_label.config(text="Copy completed successfully!")
        self.progress_bar["value"] = 100
        self.progress_percent.config(text="100%")
        
        # Re-enable copy button
        self.copy_btn.config(state="normal")
        
        # Refresh database list
        self.load_databases()
        
        # Show success message
        messagebox.showinfo("Copy Complete", f"Database '{target_db}' was created successfully!")

    def copy_failed(self, error_message):
        """Handle copy operation failure."""
        # Update UI
        self.status_label.config(text=f"Copy failed")
        
        # Re-enable copy button
        self.copy_btn.config(state="normal")
        
        # Show error message
        messagebox.showerror("Copy Failed", f"Database copy operation failed:\n{error_message}")