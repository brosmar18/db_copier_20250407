import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import time

class ServicesPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.services_data = []
        self.search_term = ""

        # Set custom styles
        style = ttk.Style(self)
        style.configure("Custom.Treeview.Heading",
                        background="#181F67",
                        foreground="white",
                        font=("Helvetica", 12, "bold"))
        style.configure("Custom.Treeview",
                        font=("Helvetica", 10))
        style.map("Custom.Treeview.Heading", background=[("active", "#7BB837")])

        # Page layout
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Header with title and refresh button
        header_frame = ttk.Frame(outer_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="System Services", font=("Helvetica", 16, "bold"))
        title_label.pack(side="left")
        
        # Refresh button
        self.refresh_btn = ttk.Button(header_frame, text="Refresh", command=self.refresh_services)
        self.refresh_btn.pack(side="right")
        
        # Search bar
        search_frame = ttk.Frame(outer_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Status filter
        filter_frame = ttk.Frame(outer_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Status:").pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, 
                                   values=["All", "Running", "Stopped", "Paused"])
        status_combo.pack(side="left")
        status_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Services treeview with scrollbar
        self.tree_frame = ttk.Frame(outer_frame)
        self.tree_frame.pack(fill="both", expand=True)
        
        # Create treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=("name", "display_name", "status", "start_type"),
                               show="headings", style="Custom.Treeview")
        
        # Define headings
        self.tree.heading("name", text="Service Name")
        self.tree.heading("display_name", text="Display Name")
        self.tree.heading("status", text="Status")
        self.tree.heading("start_type", text="Start Type")
        
        # Define columns
        self.tree.column("name", width=150, anchor="w")
        self.tree.column("display_name", width=250, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("start_type", width=150, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Progress indicator
        self.progress_frame = ttk.Frame(outer_frame)
        self.progress_frame.pack(fill="x", pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x")
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(anchor="w")
        
        # Hide progress initially
        self.progress_frame.pack_forget()
        
        # Bind event to load services when frame is shown
        self.bind("<<ShowFrame>>", self.on_show_frame)
    
    def on_show_frame(self, event):
        """Load services when the frame is shown"""
        if not self.services_data:
            self.refresh_services()
    
    def refresh_services(self):
        """Reload the list of services from the system"""
        # Clear existing data
        self.tree.delete(*self.tree.get_children())
        
        # Show progress
        self.progress_frame.pack(fill="x", pady=10)
        self.progress_var.set(0)
        self.progress_label.config(text="Loading services...")
        self.refresh_btn.config(state="disabled")
        
        # Start loading thread
        threading.Thread(target=self._load_services_thread, daemon=True).start()
    
    def _load_services_thread(self):
        """Background thread to load services"""
        try:
            # Use PowerShell to get services
            cmd = ["powershell", "-Command", 
                   "Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Csv -NoTypeInformation"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Process output
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                # Skip header line
                self.services_data = []
                for i, line in enumerate(lines[1:]):
                    if not line.strip():
                        continue
                    
                    # Split CSV line, handle quotes
                    parts = [p.strip('"') for p in line.split(',')]
                    if len(parts) >= 4:
                        service = {
                            'name': parts[0],
                            'display_name': parts[1],
                            'status': parts[2],
                            'start_type': parts[3]
                        }
                        self.services_data.append(service)
                    
                    # Update progress
                    progress = min(100, int((i / len(lines)) * 100))
                    self.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Apply filters and populate tree
                self.after(0, self.apply_filters)
            else:
                # Show error if command failed
                self.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to retrieve services:\n{result.stderr}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", f"An error occurred while retrieving services:\n{str(e)}"))
        finally:
            # Hide progress and enable refresh button
            self.after(0, lambda: self.progress_frame.pack_forget())
            self.after(0, lambda: self.refresh_btn.config(state="normal"))
    
    def on_search_change(self, *args):
        """Handle search text changes"""
        self.search_term = self.search_var.get().lower()
        self.apply_filters()
    
    def apply_filters(self, *args):
        """Apply search and status filters to the services list"""
        # Clear current tree
        self.tree.delete(*self.tree.get_children())
        
        # Get current filters
        search = self.search_term
        status_filter = self.status_var.get()
        
        # Apply filters and populate tree
        for service in self.services_data:
            # Check if service matches search term
            if (search and search not in service['name'].lower() and 
                search not in service['display_name'].lower()):
                continue
            
            # Check if service matches status filter
            if status_filter != "All" and service['status'] != status_filter:
                continue
            
            # Insert matching service
            self.tree.insert("", "end", values=(
                service['name'],
                service['display_name'],
                service['status'],
                service['start_type']
            ))