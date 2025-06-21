import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from db import create_database, restore_database, terminate_and_delete_database
from gui.snake_game import SnakeGame


class RestorePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.restore_thread = None
        self._widgets_created = False

        # Bind to show frame event for lazy loading
        self.bind("<<ShowFrame>>", self.on_show_frame)

    def create_widgets(self):
        """Create widgets lazily with new color scheme"""
        if self._widgets_created:
            return

        # Setup styles with new color scheme
        style = ttk.Style(self)
        style.configure(
            "Restore.Horizontal.TProgressbar",
            troughcolor="#E8E8E8",
            background="#7BB837",  # New green
            borderwidth=2
        )

        # Main container with increased padding
        main_frame = ttk.Frame(self, padding=40)
        main_frame.pack(expand=True, fill="both")

        # Content frame (centered)
        content_frame = ttk.Frame(main_frame)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title with new color scheme
        title = ttk.Label(
            content_frame, 
            text="Database Restore", 
            font=("Segoe UI", 24, "bold"),
            foreground="#181F67"  # New dark blue
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 40))

        # Form fields with new color scheme
        self.create_form_fields(content_frame)

        # Action buttons with new color scheme
        self.create_action_buttons(content_frame)

        # Progress section with new color scheme
        self.create_progress_section(content_frame)

        # Snake game with better sizing
        self.snake_game = SnakeGame(content_frame, width=400, height=280)
        self.snake_game.grid(row=8, column=0, columnspan=3, pady=25)  # Updated row number
        self.snake_game.grid_remove()

        # Navigation button with secondary styling
        style.configure(
            "NavSecondary.TButton",
            background="#939498",  # Gray for secondary navigation
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none"
        )
        style.map("NavSecondary.TButton", background=[("active", "#7A7A7E")])  # Darker gray on hover

        back_btn = ttk.Button(
            content_frame,
            text="← Back to Management",
            command=lambda: self.controller.show_frame("DBManagementPage"),
            style="NavSecondary.TButton",
        )
        back_btn.grid(row=9, column=0, columnspan=3, pady=20)  # Updated row number

        # Auto-detect PostgreSQL installation
        self.auto_detect_postgresql()

        self._widgets_created = True

    def auto_detect_postgresql(self):
        """Automatically detect the best PostgreSQL installation"""
        common_paths = [
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin", 
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
            r"C:\Program Files\PostgreSQL\13\bin",
            r"C:\Program Files\PostgreSQL\12\bin",
        ]
        
        for path in common_paths:
            pg_restore_path = os.path.join(path, "pg_restore.exe")
            if os.path.exists(pg_restore_path):
                self.pg_restore_path_var.set(path)
                return
        
        # If no installation found, keep the default but show a warning
        print("Warning: No PostgreSQL installation detected. Using default path.")

    def create_form_fields(self, parent):
        """Create form input fields with new color scheme"""
        # Database name with new colors
        ttk.Label(
            parent, 
            text="New Database Name:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=1, column=0, sticky="e", padx=(0, 20), pady=15)

        self.db_name_var = tk.StringVar()
        self.db_name_entry = ttk.Entry(
            parent, 
            textvariable=self.db_name_var, 
            font=("Segoe UI", 13),
            width=40
        )
        self.db_name_entry.grid(row=1, column=1, padx=8, pady=15, sticky="ew")

        # Backup file with new color scheme
        ttk.Label(
            parent, 
            text="Backup File:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=2, column=0, sticky="e", padx=(0, 20), pady=15)

        self.backup_file_var = tk.StringVar()
        self.backup_file_entry = ttk.Entry(
            parent, 
            textvariable=self.backup_file_var, 
            font=("Segoe UI", 13),
            width=40
        )
        self.backup_file_entry.grid(row=2, column=1, padx=8, pady=15, sticky="ew")

        # Browse button with consistent styling
        style = ttk.Style()
        style.configure(
            "Browse.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(18, 10),
            background="#7BB837",  # Green to match theme
            foreground="white",
            borderwidth=0,
            relief="flat",
            focuscolor="none"
        )
        style.map("Browse.TButton", background=[("active", "#6FA02E")])  # Darker green on hover
        
        browse_btn = ttk.Button(
            parent, 
            text="Browse...", 
            command=self.browse_file,
            style="Browse.TButton"
        )
        browse_btn.grid(row=2, column=2, padx=(20, 0), pady=15)

        # PostgreSQL binary path with improved default and help text
        ttk.Label(
            parent, 
            text="PostgreSQL Bin Path:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=3, column=0, sticky="e", padx=(0, 20), pady=15)

        # Updated default path to use a more recent PostgreSQL version
        self.pg_restore_path_var = tk.StringVar(
            value=r"C:\Program Files\PostgreSQL\15\bin"  # Updated to version 15
        )
        self.pg_restore_path_entry = ttk.Entry(
            parent,
            textvariable=self.pg_restore_path_var,
            font=("Segoe UI", 13),
            width=40
        )
        self.pg_restore_path_entry.grid(row=3, column=1, padx=8, pady=15, sticky="ew")

        # Browse button for PostgreSQL path
        browse_pg_btn = ttk.Button(
            parent, 
            text="Browse...", 
            command=self.browse_postgresql_path,
            style="Browse.TButton"
        )
        browse_pg_btn.grid(row=3, column=2, padx=(20, 0), pady=15)

        # Add help text for PostgreSQL path
        help_label = ttk.Label(
            parent,
            text="Note: Use PostgreSQL 15+ for modern backup files. Common paths:\n"
                 "• C:\\Program Files\\PostgreSQL\\15\\bin\n"
                 "• C:\\Program Files\\PostgreSQL\\16\\bin\n"
                 "• C:\\Program Files\\PostgreSQL\\17\\bin",
            font=("Segoe UI", 10),
            foreground="#939498",
            justify="left"
        )
        help_label.grid(row=4, column=0, columnspan=3, pady=(5, 0), sticky="w")

    def create_action_buttons(self, parent):
        """Create action buttons with new color scheme"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=5, column=0, columnspan=3, pady=35)  # Updated row number

        # Configure enhanced button styles with new colors
        style = ttk.Style()
        style.configure(
            "RestorePrimary.TButton",
            background="#7BB837",  # New green
            foreground="white",
            font=("Segoe UI", 14, "bold"),
            padding=(35, 18),
            borderwidth=0,
            relief="flat",
            focuscolor="none"
        )
        style.map("RestorePrimary.TButton", background=[("active", "#6FA02E")])  # Darker green on hover

        style.configure(
            "RestoreSecondary.TButton",
            background="#939498",  # Gray for secondary actions
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            padding=(25, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none"
        )
        style.map("RestoreSecondary.TButton", background=[("active", "#7A7A7E")])  # Darker gray on hover

        self.restore_btn = ttk.Button(
            button_frame,
            text="🗄️ Restore Database",
            command=self.start_restore,
            style="RestorePrimary.TButton",
        )
        self.restore_btn.pack(side="left", padx=15)

        clear_btn = ttk.Button(
            button_frame,
            text="Clear Form",
            command=self.clear_form,
            style="RestoreSecondary.TButton",
        )
        clear_btn.pack(side="left", padx=15)

    def create_progress_section(self, parent):
        """Create progress display section with new color scheme"""
        self.progress_frame = ttk.Frame(parent)
        self.progress_frame.grid(row=6, column=0, columnspan=3, pady=25, sticky="ew")  # Updated row number

        # Progress label with new color scheme
        self.progress_label = ttk.Label(
            self.progress_frame, 
            text="Restore Progress:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        )
        self.progress_label.pack(anchor="w", pady=(0, 12))

        # Progress bar with new color scheme
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="indeterminate",
            style="Restore.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(0, 15))

        # Status label with new color scheme
        self.status_label = ttk.Label(
            self.progress_frame, 
            text="", 
            font=("Segoe UI", 12),
            foreground="#181F67"  # New dark blue
        )
        self.status_label.pack(anchor="w")

        # Entertainment message with new color scheme
        self.entertainment_label = ttk.Label(
            self.progress_frame,
            text="🎮 Enjoy the snake game while waiting!",
            font=("Segoe UI", 12, "italic"),
            foreground="#939498",  # New gray
        )
        self.entertainment_label.pack(anchor="w", pady=(15, 0))

        # Hide initially
        self.progress_frame.grid_remove()

    def on_show_frame(self, event):
        """Handle frame show event"""
        if not self._widgets_created:
            self.create_widgets()

    def browse_file(self):
        """Browse for backup file"""
        file_types = [
            ("PostgreSQL Backup Files", "*.backup"),
            ("SQL Files", "*.sql"),
            ("All Files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            title="Select Database Backup File", filetypes=file_types
        )

        if file_path:
            self.backup_file_var.set(file_path)

    def browse_postgresql_path(self):
        """Browse for PostgreSQL bin directory"""
        initial_dir = self.pg_restore_path_var.get()
        if not os.path.exists(initial_dir):
            initial_dir = r"C:\Program Files\PostgreSQL"

        directory = filedialog.askdirectory(
            title="Select PostgreSQL bin Directory",
            initialdir=initial_dir
        )

        if directory:
            # Validate that this directory contains pg_restore.exe
            pg_restore_path = os.path.join(directory, "pg_restore.exe")
            if os.path.exists(pg_restore_path):
                self.pg_restore_path_var.set(directory)
            else:
                messagebox.showwarning(
                    "Invalid Directory",
                    f"The selected directory does not contain pg_restore.exe.\n\n"
                    f"Please select a PostgreSQL bin directory (e.g., C:\\Program Files\\PostgreSQL\\15\\bin)"
                )

    def clear_form(self):
        """Clear all form fields"""
        self.db_name_var.set("")
        self.backup_file_var.set("")
        self.hide_progress()

    def start_restore(self):
        """Start the restore operation"""
        # Validate inputs
        db_name = self.db_name_var.get().strip()
        backup_file = self.backup_file_var.get().strip()
        pg_restore_dir = self.pg_restore_path_var.get().strip()

        if not db_name:
            messagebox.showerror("Input Error", "Please enter a database name.")
            return
        if not backup_file:
            messagebox.showerror("Input Error", "Please select a backup file.")
            return

        # Show progress and start game
        self.show_progress("Initializing restore operation...")
        self.disable_ui()

        # Show snake game for entertainment
        self.snake_game.grid()

        # Start restore in background
        self.restore_thread = threading.Thread(
            target=self.perform_restore,
            args=(db_name, backup_file, pg_restore_dir),
            daemon=True,
        )
        self.restore_thread.start()

    def perform_restore(self, db_name, backup_file, pg_restore_dir):
        """Perform restore operation in background"""
        credentials = self.controller.db_credentials

        try:
            # Update status
            self.update_status("Creating new database...")
            create_database(credentials, db_name)

            self.update_status("Restoring data from backup...")
            restore_database(credentials, db_name, backup_file, pg_restore_dir)

            # Success
            self.after(0, lambda: self.restore_success(db_name))

        except Exception as e:
            # Cleanup on error
            try:
                terminate_and_delete_database(credentials, db_name)
            except:
                pass  # Ignore cleanup errors

            self.after(0, lambda: self.restore_error(str(e)))

    def restore_success(self, db_name):
        """Handle successful restore"""
        self.hide_progress()
        self.enable_ui()

        # Get snake game score
        score = self.snake_game.high_score
        commentary = self.snake_game.generate_commentary(score)

        # Show success message with game stats
        message = (
            f"Database '{db_name}' restored successfully! 🎉\n\n"
            f"🐍 Your snake game score: {score}\n"
            f"{commentary}"
        )

        messagebox.showinfo("Restore Complete", message)

        # Reset form
        self.clear_form()
        self.snake_game.grid_remove()

    def restore_error(self, error_message):
        """Handle restore error"""
        self.hide_progress()
        self.enable_ui()
        self.snake_game.grid_remove()

        messagebox.showerror(
            "Restore Failed", f"Database restore failed:\n\n{error_message}"
        )

    def update_status(self, message):
        """Update status from background thread"""
        self.after(0, lambda: self.status_label.config(text=message))

    def show_progress(self, initial_message):
        """Show progress section"""
        self.progress_frame.grid()
        self.progress_bar.start(8)
        self.status_label.config(text=initial_message)

    def hide_progress(self):
        """Hide progress section"""
        self.progress_bar.stop()
        self.progress_frame.grid_remove()

    def disable_ui(self):
        """Disable form controls during operation"""
        self.restore_btn.config(state="disabled")
        self.db_name_entry.config(state="disabled")
        self.backup_file_entry.config(state="disabled")
        self.pg_restore_path_entry.config(state="disabled")

    def enable_ui(self):
        """Re-enable form controls after operation"""
        self.restore_btn.config(state="normal")
        self.db_name_entry.config(state="normal")
        self.backup_file_entry.config(state="normal")
        self.pg_restore_path_entry.config(state="normal")