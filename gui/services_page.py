import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from db.services_ops import (
    get_all_services, start_service, stop_service, restart_service, 
    get_service_status, is_admin
)

class ToggleSwitch(tk.Canvas):
    """Custom toggle switch widget"""
    def __init__(self, parent, width=60, height=30, bg="#f0f0f0", fg="#7BB837", 
                 text="", command=None, default_state=True):
        super().__init__(parent, width=width, height=height, bg=bg, 
                        highlightthickness=0, relief="flat")
        self.fg_color = fg
        self.bg_color = bg
        self.state = default_state  # True = ON, False = OFF
        self.command = command
        self.text = text
        
        # Draw initial state
        self.draw()
        
        # Bind click event
        self.bind("<Button-1>", self.toggle)
    
    def draw(self):
        """Draw the toggle switch based on current state"""
        self.delete("all")
        
        # Draw background
        if self.state:
            # ON state - colored background
            self.create_rectangle(0, 0, 60, 30, fill=self.fg_color, outline="", tags="bg")
            # Draw toggle circle on right
            self.create_oval(30, 2, 58, 28, fill="white", outline="", tags="switch")
            # Draw text
            self.create_text(20, 15, text="ON", fill="white", font=("Segoe UI", 9, "bold"))
        else:
            # OFF state - gray background
            self.create_rectangle(0, 0, 60, 30, fill="#cccccc", outline="", tags="bg")
            # Draw toggle circle on left
            self.create_oval(2, 2, 30, 28, fill="white", outline="", tags="switch")
            # Draw text
            self.create_text(40, 15, text="OFF", fill="#666666", font=("Segoe UI", 9, "bold"))
        
        # Draw label text if provided
        if self.text:
            self.create_text(70, 15, text=self.text, anchor="w", 
                            fill="#212529", font=("Segoe UI", 10))
    
    def toggle(self, event=None):
        """Toggle the switch state"""
        self.state = not self.state
        self.draw()
        if self.command:
            self.command()
    
    def get(self):
        """Return current state"""
        return self.state
    
    def set(self, state):
        """Set state programmatically"""
        if self.state != state:
            self.state = state
            self.draw()
            if self.command:
                self.command()

class ErrorDialog(tk.Toplevel):
    """Custom error dialog with detailed information"""
    def __init__(self, parent, title, error_message):
        super().__init__(parent)
        self.title(title)
        self.grab_set()  # Make dialog modal
        self.resizable(False, False)
        
        # Set minimum width for error dialog
        self.minsize(500, 200)
        
        # Add padding
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)
        
        # Error icon
        error_frame = ttk.Frame(frame)
        error_frame.pack(fill="x", pady=(0, 10))
        
        error_icon = tk.Label(error_frame, text="❌", font=("Segoe UI", 36), fg="#dc3545")
        error_icon.pack(side="left", padx=(0, 15))
        
        error_title = ttk.Label(error_frame, text="Operation Failed", 
                              font=("Segoe UI", 16, "bold"))
        error_title.pack(side="left", anchor="n")
        
        # Error message in a scrollable text widget
        message_frame = ttk.LabelFrame(frame, text="Error Details")
        message_frame.pack(fill="both", expand=True)
        
        # Scrolled text for the error message
        message_text = tk.Text(message_frame, wrap="word", height=8, width=60, 
                             font=("Segoe UI", 10))
        message_scroll = ttk.Scrollbar(message_frame, command=message_text.yview)
        message_text.configure(yscrollcommand=message_scroll.set)
        
        message_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        message_scroll.pack(side="right", fill="y")
        
        # Insert error message
        message_text.insert("1.0", error_message)
        message_text.config(state="disabled")  # Make read-only
        
        # Close button
        close_btn = ttk.Button(frame, text="Close", command=self.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Center the dialog on the parent window
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Bind escape key to close dialog
        self.bind("<Escape>", lambda e: self.destroy())

class AdminWarningDialog(tk.Toplevel):
    """Dialog to warn about running without administrator privileges"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Administrator Privileges Warning")
        self.grab_set()
        self.resizable(False, False)
        
        # Set dialog size
        self.minsize(450, 200)
        
        # Add padding
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)
        
        # Warning icon and title
        warning_frame = ttk.Frame(frame)
        warning_frame.pack(fill="x", pady=(0, 10))
        
        warning_icon = tk.Label(warning_frame, text="⚠️", font=("Segoe UI", 36), fg="#ffc107")
        warning_icon.pack(side="left", padx=(0, 15))
        
        warning_title = ttk.Label(warning_frame, text="Limited Permissions", 
                                font=("Segoe UI", 16, "bold"))
        warning_title.pack(side="left", anchor="n")
        
        # Warning message
        message_label = ttk.Label(frame, 
                                text="This application is not running with administrator privileges. "
                                     "Some operations on system services may fail without elevated permissions.\n\n"
                                     "For full functionality, please restart the application by right-clicking "
                                     "and selecting 'Run as administrator'.",
                                wraplength=400, justify="left")
        message_label.pack(fill="x", pady=10)
        
        # Close button
        close_btn = ttk.Button(frame, text="Continue Anyway", command=self.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Center the dialog on the parent window
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

class ServicesPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.services_data = []
        self.search_term = ""
        self.active_threads = {}
        
        # Configure custom colors and styles
        self.colors = {
            "bg_dark": "#1e1e2e",
            "bg_light": "#f8f9fa",
            "primary": "#7BB837",
            "secondary": "#6c757d",
            "success": "#28a745",
            "danger": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8",
            "text_dark": "#212529",
            "text_light": "#f8f9fa"
        }

        # Set custom styles
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # Configure treeview styles
        style.configure("Modern.Treeview",
                        background=self.colors["bg_light"],
                        foreground=self.colors["text_dark"],
                        rowheight=40,
                        fieldbackground=self.colors["bg_light"],
                        font=("Segoe UI", 10))
        
        style.configure("Modern.Treeview.Heading",
                        background=self.colors["primary"],
                        foreground=self.colors["text_light"],
                        relief="flat",
                        font=("Segoe UI", 11, "bold"))
                        
        style.map("Modern.Treeview",
                  background=[("selected", self.colors["primary"])],
                  foreground=[("selected", self.colors["text_light"])])
                  
        # Button styles
        style.configure("Success.TButton", 
                        background=self.colors["success"],
                        foreground=self.colors["text_light"],
                        font=("Segoe UI", 9))
                        
        style.configure("Danger.TButton", 
                        background=self.colors["danger"],
                        foreground=self.colors["text_light"],
                        font=("Segoe UI", 9))
                        
        style.configure("Warning.TButton", 
                        background=self.colors["warning"],
                        foreground=self.colors["text_dark"],
                        font=("Segoe UI", 9))
                        
        style.configure("Info.TButton", 
                        background=self.colors["info"],
                        foreground=self.colors["text_light"],
                        font=("Segoe UI", 9))
        
        # Main container frame
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Header with title and refresh button
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Title with icon
        title_label = ttk.Label(header_frame, text="⚙️ System Services", 
                               font=("Segoe UI", 18, "bold"))
        title_label.pack(side="left")
        
        # Show admin status indicator
        admin_status = "✅ Admin" if is_admin() else "⚠️ Limited Permissions"
        admin_color = self.colors["success"] if is_admin() else self.colors["warning"]
        self.admin_label = tk.Label(header_frame, text=admin_status, 
                                  font=("Segoe UI", 10), fg=admin_color)
        self.admin_label.pack(side="left", padx=15)
        self.admin_label.bind("<Button-1>", self.show_admin_info)
        
        # Refresh button with icon
        self.refresh_btn = ttk.Button(header_frame, text="🔄 Refresh", 
                                    command=self.refresh_services,
                                    style="Info.TButton")
        self.refresh_btn.pack(side="right")
        
        # Toggle filters row - simplified with clear labels
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill="x", pady=(0, 15))
        
        # Create toggle switches for collectiveServer and postgres
        collective_frame = ttk.Frame(filter_frame)
        collective_frame.pack(side="left", padx=(0, 30))
        
        collective_label = ttk.Label(collective_frame, text="Show 'collectiveServer' services:", 
                                   font=("Segoe UI", 10))
        collective_label.pack(side="left", padx=(0, 10))
        
        self.collective_toggle = ToggleSwitch(collective_frame, 
                                            command=self.apply_filters, default_state=True)
        self.collective_toggle.pack(side="left")
        
        # Postgres toggle
        postgres_frame = ttk.Frame(filter_frame)
        postgres_frame.pack(side="left")
        
        postgres_label = ttk.Label(postgres_frame, text="Show 'postgres' services:", 
                                 font=("Segoe UI", 10))
        postgres_label.pack(side="left", padx=(0, 10))
        
        self.postgres_toggle = ToggleSwitch(postgres_frame,
                                          command=self.apply_filters, default_state=True)
        self.postgres_toggle.pack(side="left")
        
        # General filter row (search and status)
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 15))
        
        # Search box with icon
        search_container = ttk.Frame(search_frame)
        search_container.pack(side="left", fill="x", expand=True)
        
        search_icon = ttk.Label(search_container, text="🔍")
        search_icon.pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        search_entry = ttk.Entry(search_container, textvariable=self.search_var, 
                               font=("Segoe UI", 10), width=30)
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Status filter dropdown
        filter_container = ttk.Frame(search_frame)
        filter_container.pack(side="right", padx=(20, 0))
        
        filter_label = ttk.Label(filter_container, text="Status Filter:", 
                               font=("Segoe UI", 10))
        filter_label.pack(side="left", padx=(0, 5))
        
        self.status_var = tk.StringVar(value="All")
        status_values = ["All", "Running", "Stopped", "Paused"]
        status_combo = ttk.Combobox(filter_container, textvariable=self.status_var, 
                                  values=status_values, width=15, 
                                  font=("Segoe UI", 10), state="readonly")
        status_combo.pack(side="left")
        status_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Main content split into two sections
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Create the treeview inside a frame (for border effect)
        tree_frame_border = ttk.Frame(content_frame, padding=1)
        tree_frame_border.pack(side="left", fill="both", expand=True)
        
        tree_frame = ttk.Frame(tree_frame_border)
        tree_frame.pack(fill="both", expand=True)
        
        # Define columns for the treeview - removed display_name as requested
        columns = ("name", "status")
        
        # Create treeview with fixed height rows
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                               style="Modern.Treeview", selectmode="browse")
        
        # Configure headings
        self.tree.heading("name", text="Service Name")
        self.tree.heading("status", text="Status")
        
        # Configure columns
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        
        # Vertical scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        # Horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar_x.set)
        
        # Pack the treeview and scrollbars
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_service_select)
        
        # Service actions panel
        action_panel = ttk.Frame(content_frame, padding=10, width=200)
        action_panel.pack(side="right", fill="y")
        
        # Keep the panel width fixed
        action_panel.pack_propagate(False)
        
        # Service info section
        self.service_info_frame = ttk.LabelFrame(action_panel, text="Service Information", padding=10)
        self.service_info_frame.pack(fill="x", pady=(0, 15))
        
        self.selected_service_name = ttk.Label(self.service_info_frame, text="No service selected", 
                                             font=("Segoe UI", 10, "bold"), wraplength=180)
        self.selected_service_name.pack(fill="x")
        
        self.selected_service_status = ttk.Label(self.service_info_frame, text="")
        self.selected_service_status.pack(fill="x", pady=(5, 0))
        
        # Service actions section
        action_frame = ttk.LabelFrame(action_panel, text="Service Actions", padding=10)
        action_frame.pack(fill="x")
        
        # Start button
        self.start_btn = ttk.Button(action_frame, text="▶️ Start Service", command=self.start_selected_service,
                                  style="Success.TButton", width=20)
        self.start_btn.pack(fill="x", pady=5)
        
        # Stop button
        self.stop_btn = ttk.Button(action_frame, text="⏹️ Stop Service", command=self.stop_selected_service,
                                 style="Danger.TButton", width=20)
        self.stop_btn.pack(fill="x", pady=5)
        
        # Restart button
        self.restart_btn = ttk.Button(action_frame, text="🔄 Restart Service", command=self.restart_selected_service,
                                    style="Warning.TButton", width=20)
        self.restart_btn.pack(fill="x", pady=5)
        
        # Disable buttons initially
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.restart_btn.config(state="disabled")
        
        # Status bar at the bottom
        self.status_bar = ttk.Label(main_frame, text="Ready", anchor="w", 
                                  font=("Segoe UI", 9))
        self.status_bar.pack(fill="x", pady=(10, 0))
        
        # Progress indicator
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill="x", pady=(10, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x")
        
        # Hide progress initially
        self.progress_frame.pack_forget()
        
        # Current selected service
        self.current_service = None
        
        # Bind event to load services when frame is shown
        self.bind("<<ShowFrame>>", self.on_show_frame)
        
    def on_show_frame(self, event):
        """Load services when the frame is shown"""
        # Show admin warning if not running as admin
        if not is_admin() and not hasattr(self, '_admin_warning_shown'):
            self._admin_warning_shown = True
            self.after(500, self.show_admin_warning)
            
        if not self.services_data:
            self.refresh_services()
    
    def show_admin_warning(self):
        """Show a warning dialog if not running as admin"""
        AdminWarningDialog(self)
    
    def show_admin_info(self, event=None):
        """Show info about admin privileges when indicator is clicked"""
        if is_admin():
            messagebox.showinfo("Administrator Privileges", 
                              "The application is running with administrator privileges. "
                              "You have full control over system services.")
        else:
            self.show_admin_warning()
    
    def refresh_services(self):
        """Reload the list of services from the system"""
        # Clear existing data
        self.tree.delete(*self.tree.get_children())
        
        # Reset current selection
        self.current_service = None
        self.selected_service_name.config(text="No service selected")
        self.selected_service_status.config(text="")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.restart_btn.config(state="disabled")
        
        # Show progress
        self.progress_frame.pack(fill="x", pady=(10, 0))
        self.progress_var.set(0)
        self.status_bar.config(text="Loading services...")
        self.refresh_btn.config(state="disabled")
        
        # Start loading thread
        threading.Thread(target=self._load_services_thread, daemon=True).start()
    
    def _load_services_thread(self):
        """Background thread to load services"""
        try:
            # Get all services using our services_ops module
            services = get_all_services()
            
            if services:
                self.services_data = services
                # Update progress
                for i in range(0, 101, 5):
                    self.after(0, lambda p=i: self.progress_var.set(p))
                    time.sleep(0.01)  # Simulate loading
                
                # Apply filters and populate tree
                self.after(0, self.apply_filters)
                self.after(0, lambda: self.status_bar.config(
                    text=f"Loaded {len(services)} services successfully"))
            else:
                # Show error if no services were returned
                self.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to retrieve services"))
                self.after(0, lambda: self.status_bar.config(
                    text="Failed to load services"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", f"An error occurred while retrieving services:\n{str(e)}"))
            self.after(0, lambda: self.status_bar.config(
                text="Error loading services"))
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
        show_collective = self.collective_toggle.get()
        show_postgres = self.postgres_toggle.get()
        
        # Track visible services count
        visible_count = 0
        total_matching = 0
        
        # Apply filters and populate tree
        for service in self.services_data:
            service_name = service['name'].lower()
            
            # Count how many services would match our toggle filters
            matches_toggles = True
            if show_collective or show_postgres:
                # If both toggles are on, we check if matches either
                if show_collective and show_postgres:
                    if "collectiveserver" not in service_name and "postgres" not in service_name:
                        matches_toggles = False
                # If only collectiveServer toggle is on
                elif show_collective and "collectiveserver" not in service_name:
                    matches_toggles = False
                # If only postgres toggle is on
                elif show_postgres and "postgres" not in service_name:
                    matches_toggles = False
            
            if matches_toggles:
                total_matching += 1
                
                # Now check other filters
                # Check if service matches search term
                if search and search not in service_name and search not in service['display_name'].lower():
                    continue
                
                # Check if service matches status filter
                if status_filter != "All" and service['status'] != status_filter:
                    continue
                
                # Insert matching service - removed display_name as requested
                self.tree.insert("", "end", values=(
                    service['name'],
                    self._format_status(service['status'])
                ))
                
                visible_count += 1
        
        # Update status bar with filter info
        self.status_bar.config(text=f"Showing {visible_count} of {total_matching} matching services ({len(self.services_data)} total)")
    
    def _format_status(self, status):
        """Format the status with an appropriate icon"""
        if status == "Running":
            return "✅ Running"
        elif status == "Stopped":
            return "⛔ Stopped"
        elif status == "Paused":
            return "⏸️ Paused"
        else:
            return status
    
    def on_service_select(self, event):
        """Handle service selection from the treeview"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Get the service details
        item = selected_items[0]
        values = self.tree.item(item)['values']
        service_name = values[0]
        
        # Set the current service
        self.current_service = service_name
        
        # Update service info in the panel
        self.selected_service_name.config(text=service_name)
        
        # Find the status
        status = None
        for service in self.services_data:
            if service['name'] == service_name:
                status = service['status']
                break
        
        if status:
            self.selected_service_status.config(text=f"Status: {self._format_status(status)}")
            
            # Enable/disable buttons based on status
            if status == "Running":
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
                self.restart_btn.config(state="normal")
            elif status == "Stopped":
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                self.restart_btn.config(state="disabled")
            elif status == "Paused":
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="normal")
                self.restart_btn.config(state="disabled")
            else:
                # Unknown status, enable all buttons
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="normal")
                self.restart_btn.config(state="normal")
    
    def start_selected_service(self):
        """Start the currently selected service"""
        if not self.current_service:
            return
        
        self.status_bar.config(text=f"Starting service '{self.current_service}'...")
        
        def callback(success, message):
            if success:
                self.status_bar.config(text=f"Service '{self.current_service}' started successfully")
                # Update the service status in the UI
                self.update_service_status(self.current_service)
            else:
                self.status_bar.config(text=f"Failed to start service '{self.current_service}'")
                # Show detailed error dialog
                ErrorDialog(self, "Start Service Failed", message)
        
        # Start the service
        start_service(self.current_service, callback)
    
    def stop_selected_service(self):
        """Stop the currently selected service"""
        if not self.current_service:
            return
        
        self.status_bar.config(text=f"Stopping service '{self.current_service}'...")
        
        def callback(success, message):
            if success:
                self.status_bar.config(text=f"Service '{self.current_service}' stopped successfully")
                # Update the service status in the UI
                self.update_service_status(self.current_service)
            else:
                self.status_bar.config(text=f"Failed to stop service '{self.current_service}'")
                # Show detailed error dialog
                ErrorDialog(self, "Stop Service Failed", message)
        
        # Stop the service (uses force by default now)
        stop_service(self.current_service, callback)
    
    def restart_selected_service(self):
        """Restart the currently selected service"""
        if not self.current_service:
            return
        
        self.status_bar.config(text=f"Restarting service '{self.current_service}'...")
        
        def callback(success, message):
            if success:
                self.status_bar.config(text=f"Service '{self.current_service}' restarted successfully")
                # Update the service status in the UI
                self.update_service_status(self.current_service)
            else:
                self.status_bar.config(text=f"Failed to restart service '{self.current_service}'")
                # Show detailed error dialog
                ErrorDialog(self, "Restart Service Failed", message)
        
        # Restart the service
        restart_service(self.current_service, callback)
    
    def update_service_status(self, service_name):
        """Update the status of a service in the UI after an action"""
        # Wait a moment for the service status to update
        self.after(1000, lambda: self._refresh_service_item(service_name))
    
    def _refresh_service_item(self, service_name):
        """Refresh a specific service item in the treeview"""
        # Get the current status
        new_status = get_service_status(service_name)
        
        if new_status:
            # Update the service in our data
            for service in self.services_data:
                if service['name'] == service_name:
                    service['status'] = new_status
                    break
            
            # Update the selected service info panel
            if self.current_service == service_name:
                self.selected_service_status.config(text=f"Status: {self._format_status(new_status)}")
                
                # Update button states
                if new_status == "Running":
                    self.start_btn.config(state="disabled")
                    self.stop_btn.config(state="normal")
                    self.restart_btn.config(state="normal")
                elif new_status == "Stopped":
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.restart_btn.config(state="disabled")
                elif new_status == "Paused":
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="normal")
                    self.restart_btn.config(state="disabled")
            
            # Find and update the item in the treeview
            for item_id in self.tree.get_children():
                item_values = self.tree.item(item_id)['values']
                if item_values[0] == service_name:
                    # Update the status display - removed display_name column
                    self.tree.item(item_id, values=(
                        item_values[0],
                        self._format_status(new_status)
                    ))
                    break
                    
            # Apply filters again in case status filter is active
            self.apply_filters()