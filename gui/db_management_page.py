import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlparse
from datetime import datetime
from db import (
    fetch_databases,
    get_database_details,
    get_tables_for_database,
    get_columns_for_table,
    get_table_details,
    terminate_and_delete_database,
    copy_database_logic,
    rename_database,
    execute_sql_query,
)


class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_db = None
        self.all_databases = []
        self.all_items = []
        self.context_menu_dbs = []  # Changed to support multiple selections
        self.protected_databases = [
            "postgres",
            "template0",
            "template1",
        ]  # System databases to protect
        self.current_view = "normal"  # Track current view: "normal" or "query"

        # Query history storage - dictionary with database names as keys
        self.query_history = (
            {}
        )  # {db_name: [{'timestamp': datetime, 'query': str, 'success': bool, 'result_count': int}]}

        # --- Enhanced Styles ---
        style = ttk.Style(self)
        style.theme_use("clam")

        # Custom Treeview styles
        style.configure(
            "Custom.Treeview.Heading",
            background="#2C3E50",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.configure(
            "Custom.Treeview",
            font=("Segoe UI", 10),
            rowheight=25,
            fieldbackground="white",
        )
        style.map("Custom.Treeview.Heading", background=[("active", "#34495E")])
        style.map("Custom.Treeview", background=[("selected", "#3498DB")])

        # History Treeview styles
        style.configure(
            "History.Treeview.Heading",
            background="#34495E",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.configure(
            "History.Treeview",
            font=("Segoe UI", 9),
            rowheight=22,
            fieldbackground="#FAFAFA",
        )
        style.map("History.Treeview.Heading", background=[("active", "#2C3E50")])
        style.map("History.Treeview", background=[("selected", "#5DADE2")])

        # Modern button styles
        style.configure(
            "Primary.TButton",
            background="#3498DB",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#2980B9"), ("pressed", "#21618C")],
        )

        style.configure(
            "Success.TButton",
            background="#27AE60",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Success.TButton",
            background=[("active", "#229954"), ("pressed", "#1E8449")],
        )

        style.configure(
            "Danger.TButton",
            background="#E74C3C",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Danger.TButton", background=[("active", "#C0392B"), ("pressed", "#A93226")]
        )

        style.configure(
            "Secondary.TButton",
            background="#95A5A6",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#7F8C8D"), ("pressed", "#566573")],
        )

        style.configure(
            "Warning.TButton",
            background="#F39C12",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Warning.TButton",
            background=[("active", "#E67E22"), ("pressed", "#CA6F1E")],
        )

        style.configure(
            "Accent.TButton",
            background="#9B59B6",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Accent.TButton", background=[("active", "#8E44AD"), ("pressed", "#7D3C98")]
        )

        # Compact button style for headers
        style.configure(
            "Compact.TButton",
            background="#34495E",
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat",
            focuscolor="none",
        )
        style.map(
            "Compact.TButton",
            background=[("active", "#2C3E50"), ("pressed", "#1B2631")],
        )

        # Query interface styles
        style.configure("Query.TFrame", background="#F8F9FA", relief="flat")
        style.configure(
            "QueryHeader.TLabel",
            background="#F8F9FA",
            foreground="#2C3E50",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "QuerySubHeader.TLabel",
            background="#F8F9FA",
            foreground="#34495E",
            font=("Segoe UI", 10, "bold"),
        )

        # Enhanced dialog styles
        style.configure("Dialog.TFrame", background="#2C3E50", relief="flat")
        style.configure(
            "Dialog.TLabel",
            background="#2C3E50",
            foreground="white",
            font=("Segoe UI", 11),
        )
        style.configure(
            "DialogHeader.TLabel",
            background="#2C3E50",
            foreground="#F1C40F",
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "DialogHighlight.TLabel",
            background="#2C3E50",
            foreground="#E74C3C",
            font=("Segoe UI", 11, "bold"),
        )

        # PanedWindow styles for professional appearance
        style.configure(
            "TPanedwindow", background="#E8E8E8", relief="flat", borderwidth=0
        )
        style.configure(
            "Sash", sashthickness=6, background="#BDC3C7", relief="flat", borderwidth=0
        )

        # --- Layout with Resizable Panels ---
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=15, pady=15)

        # Create PanedWindow for resizable panels
        self.main_paned = ttk.PanedWindow(outer_frame, orient="horizontal")
        self.main_paned.pack(expand=True, fill="both")

        # Create left and right frames with minimum widths
        left_frame = ttk.Frame(self.main_paned)
        left_frame.config(width=300)  # Set minimum width for database panel
        self.right_frame = ttk.Frame(self.main_paned)
        self.right_frame.config(width=600)  # Set minimum width for content panel

        # Add frames to paned window with weight distribution
        self.main_paned.add(left_frame, weight=1)
        self.main_paned.add(self.right_frame, weight=2)

        # Set initial sash position (30% left, 70% right for typical 1200px width)
        self.after_idle(lambda: self.main_paned.sashpos(0, 350))

        # --- LEFT PANE: DATABASES ---
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x", pady=(0, 15))

        title_label = ttk.Label(
            left_header,
            text="Databases",
            font=("Segoe UI", 16, "bold"),
            foreground="#2C3E50",
        )
        title_label.pack(side="left", anchor="w")

        refresh_btn = ttk.Button(
            left_header,
            text="Refresh",
            command=self.load_databases,
            style="Compact.TButton",
        )
        refresh_btn.pack(side="right", padx=(10, 0))

        # Enhanced search
        self.db_search_var = tk.StringVar()
        db_search_frame = ttk.Frame(left_frame)
        db_search_frame.pack(fill="x", pady=(0, 10))

        search_label = ttk.Label(
            db_search_frame,
            text="Search:",
            font=("Segoe UI", 10, "bold"),
            foreground="#34495E",
        )
        search_label.pack(side="left", padx=(0, 8))

        self.db_search_entry = ttk.Entry(
            db_search_frame, textvariable=self.db_search_var, font=("Segoe UI", 10)
        )
        self.db_search_entry.pack(side="left", fill="x", expand=True)
        self.db_search_entry.bind("<KeyRelease>", self.filter_databases)

        # Enhanced treeview
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(expand=True, fill="both")

        self.db_tree = ttk.Treeview(
            tree_frame,
            columns=("Database",),
            show="headings",
            selectmode="extended",
            style="Custom.Treeview",
        )
        self.db_tree.heading("Database", text="Database Name")
        self.db_tree.column("Database", anchor="w", width=250)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.db_tree.yview
        )
        self.db_tree.configure(yscrollcommand=scrollbar.set)

        self.db_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

        self.db_tree.bind("<<TreeviewSelect>>", self.on_db_select)

        # --- CONTEXT MENU: dynamically updated based on selection ---
        self.db_context_menu = tk.Menu(
            self,
            tearoff=0,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#2C3E50",
            activebackground="#3498DB",
            activeforeground="white",
            borderwidth=1,
            relief="solid",
        )

        # bind right-click / ctrl+click / menu key
        self.db_tree.bind("<Button-3>", self.show_db_context_menu)
        self.db_tree.bind("<Control-Button-1>", self.show_db_context_menu)
        self.db_tree.bind("<Button-2>", self.show_db_context_menu)
        self.db_tree.bind("<App>", self.show_db_context_menu_keyboard)
        self.db_tree.bind("<Shift-F10>", self.show_db_context_menu_keyboard)

        # Configure right frame for switching between views - removed pack_propagate restriction
        # The PanedWindow will handle the sizing constraints

        # Create both views
        self.create_normal_view()
        self.create_query_view()

        # Start with normal view - ensure query frame is hidden initially
        self.query_frame.pack_forget()

        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    def create_normal_view(self):
        """Create the normal view (details, tables, fields)"""
        self.normal_frame = ttk.Frame(self.right_frame)
        self.normal_frame.pack(fill="both", expand=True)
        self.normal_frame.columnconfigure(0, weight=1)

        # === NORMAL VIEW: DETAILS & TABLES/FIELDS ===
        details_header = ttk.Label(
            self.normal_frame,
            text="Database Details",
            font=("Segoe UI", 16, "bold"),
            foreground="#2C3E50",
        )
        details_header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.details_text = tk.Text(
            self.normal_frame,
            wrap="word",
            font=("Segoe UI", 10),
            height=6,
            bg="#F8F9FA",
            fg="#2C3E50",
            relief="solid",
            borderwidth=1,
        )
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.details_text.config(state="disabled")
        self.normal_frame.rowconfigure(1, weight=0)

        # Table/field search & header
        self.item_search_var = tk.StringVar()
        item_search_frame = ttk.Frame(self.normal_frame)
        item_search_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        search_label2 = ttk.Label(
            item_search_frame,
            text="Search Tables:",
            font=("Segoe UI", 10, "bold"),
            foreground="#34495E",
        )
        search_label2.pack(side="left", padx=(0, 8))

        self.item_search_entry = ttk.Entry(
            item_search_frame, textvariable=self.item_search_var, font=("Segoe UI", 10)
        )
        self.item_search_entry.pack(side="left", fill="x", expand=True)
        self.item_search_entry.bind("<KeyRelease>", self.filter_items)

        header_frame_right = ttk.Frame(self.normal_frame)
        header_frame_right.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        self.right_label = ttk.Label(
            header_frame_right,
            text="Tables",
            font=("Segoe UI", 14, "bold"),
            foreground="#2C3E50",
        )
        self.right_label.pack(side="left")

        self.back_button = ttk.Button(
            header_frame_right,
            text="Refresh Tables",
            command=self.back_to_tables,
            style="Compact.TButton",
        )
        self.back_button.pack(side="right")
        self.back_button.grid_remove()

        # Tables/fields trees
        self.bottom_frame = ttk.Frame(self.normal_frame)
        self.bottom_frame.grid(row=4, column=0, sticky="nsew")
        self.normal_frame.rowconfigure(4, weight=1)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)

        # Tables tree with scrollbar
        tables_container = ttk.Frame(self.bottom_frame)
        tables_container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tables_container.columnconfigure(0, weight=1)
        tables_container.rowconfigure(0, weight=1)

        self.item_tree = ttk.Treeview(
            tables_container,
            columns=("Item",),
            show="headings",
            style="Custom.Treeview",
        )
        self.item_tree.heading("Item", text="Table Name")
        self.item_tree.column("Item", anchor="w", width=200)

        tables_scrollbar = ttk.Scrollbar(
            tables_container, orient="vertical", command=self.item_tree.yview
        )
        self.item_tree.configure(yscrollcommand=tables_scrollbar.set)

        self.item_tree.grid(row=0, column=0, sticky="nsew")
        tables_scrollbar.grid(row=0, column=1, sticky="ns")
        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # Fields tree with scrollbar
        fields_container = ttk.Frame(self.bottom_frame)
        fields_container.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        fields_container.columnconfigure(0, weight=1)
        fields_container.rowconfigure(0, weight=1)

        self.fields_tree = ttk.Treeview(
            fields_container,
            columns=("Field",),
            show="headings",
            style="Custom.Treeview",
        )
        self.fields_tree.heading("Field", text="Fields")
        self.fields_tree.column("Field", anchor="w", width=200)

        fields_scrollbar = ttk.Scrollbar(
            fields_container, orient="vertical", command=self.fields_tree.yview
        )
        self.fields_tree.configure(yscrollcommand=fields_scrollbar.set)

        self.fields_tree.grid(row=0, column=0, sticky="nsew")
        fields_scrollbar.grid(row=0, column=1, sticky="ns")

    def create_query_view(self):
        """Create the SQL query interface view with tabs for Query and History"""
        self.query_frame = ttk.Frame(self.right_frame, style="Query.TFrame")
        self.query_frame.pack(fill="both", expand=True)
        self.query_frame.columnconfigure(0, weight=1)
        self.query_frame.rowconfigure(1, weight=1)  # Notebook should expand

        # Header with database name and back button
        header_frame = ttk.Frame(self.query_frame, style="Query.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)

        self.query_db_label = ttk.Label(
            header_frame,
            text="SQL Query Interface",
            style="QueryHeader.TLabel",
        )
        self.query_db_label.grid(row=0, column=0, sticky="w")

        back_btn = ttk.Button(
            header_frame,
            text="← Back to Tables",
            command=self.show_normal_view,
            style="Secondary.TButton",
        )
        back_btn.grid(row=0, column=2, sticky="e", padx=(20, 0))

        # Create notebook for tabs
        self.query_notebook = ttk.Notebook(self.query_frame)
        self.query_notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        # Create Query Tab
        self.create_query_tab()

        # Create History Tab
        self.create_history_tab()

        # Enhanced status bar
        status_frame = ttk.Frame(self.query_frame, style="Query.TFrame")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        status_bg_frame = ttk.Frame(status_frame)
        status_bg_frame.pack(fill="x")
        status_bg_frame.configure(style="Query.TFrame")

        self.status_label = ttk.Label(
            status_bg_frame,
            text="Ready to execute queries...",
            font=("Segoe UI", 10, "italic"),
            foreground="#7F8C8D",
            background="#F8F9FA",
        )
        self.status_label.pack(side="left", padx=10, pady=8)

    def create_query_tab(self):
        """Create the main query tab"""
        query_tab = ttk.Frame(self.query_notebook, style="Query.TFrame")
        self.query_notebook.add(query_tab, text="Query")

        query_tab.columnconfigure(0, weight=1)
        query_tab.rowconfigure(2, weight=1)  # Results section should expand

        # SQL Editor Section
        editor_frame = ttk.Frame(query_tab, style="Query.TFrame")
        editor_frame.grid(row=0, column=0, sticky="ew", pady=(10, 15))
        editor_frame.columnconfigure(0, weight=1)

        editor_label = ttk.Label(
            editor_frame, text="SQL Query:", style="QuerySubHeader.TLabel"
        )
        editor_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # SQL text editor with scrollbar
        editor_container = ttk.Frame(editor_frame, style="Query.TFrame")
        editor_container.grid(row=1, column=0, sticky="ew")
        editor_container.columnconfigure(0, weight=1)

        self.sql_text = tk.Text(
            editor_container,
            height=8,
            font=("Consolas", 11),
            bg="white",
            fg="#2C3E50",
            insertbackground="#2C3E50",
            selectbackground="#3498DB",
            selectforeground="white",
            wrap="none",
            relief="solid",
            borderwidth=1,
        )

        # Add scrollbars for SQL editor
        sql_scrollbar_v = ttk.Scrollbar(
            editor_container, orient="vertical", command=self.sql_text.yview
        )
        sql_scrollbar_h = ttk.Scrollbar(
            editor_container, orient="horizontal", command=self.sql_text.xview
        )
        self.sql_text.configure(
            yscrollcommand=sql_scrollbar_v.set, xscrollcommand=sql_scrollbar_h.set
        )

        self.sql_text.grid(row=0, column=0, sticky="nsew")
        sql_scrollbar_v.grid(row=0, column=1, sticky="ns")
        sql_scrollbar_h.grid(row=1, column=0, sticky="ew")

        editor_container.grid_rowconfigure(0, weight=1)

        # Enhanced button frame
        button_frame = ttk.Frame(query_tab, style="Query.TFrame")
        button_frame.grid(row=1, column=0, sticky="ew", pady=(15, 15))

        execute_btn = ttk.Button(
            button_frame,
            text="Execute Query",
            command=self.execute_query,
            style="Success.TButton",
        )
        execute_btn.pack(side="left", padx=(0, 15))

        format_btn = ttk.Button(
            button_frame,
            text="Format SQL",
            command=self.format_sql,
            style="Accent.TButton",
        )
        format_btn.pack(side="left", padx=(0, 15))

        clear_btn = ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_query,
            style="Secondary.TButton",
        )
        clear_btn.pack(side="left")

        # Results section
        results_frame = ttk.Frame(query_tab, style="Query.TFrame")
        results_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)

        results_label = ttk.Label(
            results_frame, text="Query Results:", style="QuerySubHeader.TLabel"
        )
        results_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # Results treeview with scrollbars
        results_container = ttk.Frame(results_frame, style="Query.TFrame")
        results_container.grid(row=1, column=0, sticky="nsew")
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(0, weight=1)

        self.results_tree = ttk.Treeview(results_container, style="Custom.Treeview")

        # Add scrollbars for results
        results_scrollbar_v = ttk.Scrollbar(
            results_container, orient="vertical", command=self.results_tree.yview
        )
        results_scrollbar_h = ttk.Scrollbar(
            results_container, orient="horizontal", command=self.results_tree.xview
        )
        self.results_tree.configure(
            yscrollcommand=results_scrollbar_v.set,
            xscrollcommand=results_scrollbar_h.set,
        )

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        results_scrollbar_v.grid(row=0, column=1, sticky="ns")
        results_scrollbar_h.grid(row=1, column=0, sticky="ew")

    def create_history_tab(self):
        """Create the query history tab"""
        history_tab = ttk.Frame(self.query_notebook, style="Query.TFrame")
        self.query_notebook.add(history_tab, text="History")

        history_tab.columnconfigure(0, weight=1)
        history_tab.rowconfigure(1, weight=1)

        # History header and controls
        history_header_frame = ttk.Frame(history_tab, style="Query.TFrame")
        history_header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 15))
        history_header_frame.columnconfigure(1, weight=1)

        history_label = ttk.Label(
            history_header_frame, text="Query History:", style="QuerySubHeader.TLabel"
        )
        history_label.grid(row=0, column=0, sticky="w")

        # Clear history button
        clear_history_btn = ttk.Button(
            history_header_frame,
            text="Clear History",
            command=self.clear_query_history,
            style="Danger.TButton",
        )
        clear_history_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # History treeview with scrollbars
        history_container = ttk.Frame(history_tab, style="Query.TFrame")
        history_container.grid(row=1, column=0, sticky="nsew")
        history_container.columnconfigure(0, weight=1)
        history_container.rowconfigure(0, weight=1)

        self.history_tree = ttk.Treeview(
            history_container,
            columns=("timestamp", "preview", "status", "rows"),
            show="headings",
            style="History.Treeview",
        )

        # Configure columns
        self.history_tree.heading("timestamp", text="Time")
        self.history_tree.heading("preview", text="Query Preview")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("rows", text="Rows")

        self.history_tree.column("timestamp", width=120, minwidth=120)
        self.history_tree.column("preview", width=400, minwidth=200)
        self.history_tree.column("status", width=80, minwidth=80)
        self.history_tree.column("rows", width=60, minwidth=60)

        # Add scrollbars for history
        history_scrollbar_v = ttk.Scrollbar(
            history_container, orient="vertical", command=self.history_tree.yview
        )
        history_scrollbar_h = ttk.Scrollbar(
            history_container, orient="horizontal", command=self.history_tree.xview
        )
        self.history_tree.configure(
            yscrollcommand=history_scrollbar_v.set,
            xscrollcommand=history_scrollbar_h.set,
        )

        self.history_tree.grid(row=0, column=0, sticky="nsew")
        history_scrollbar_v.grid(row=0, column=1, sticky="ns")
        history_scrollbar_h.grid(row=1, column=0, sticky="ew")

        # Bind events for history interaction
        self.history_tree.bind("<Double-1>", self.load_query_from_history)
        self.history_tree.bind("<Button-3>", self.show_history_context_menu)

        # Create history context menu
        self.history_context_menu = tk.Menu(
            self,
            tearoff=0,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#2C3E50",
            activebackground="#3498DB",
            activeforeground="white",
            borderwidth=1,
            relief="solid",
        )
        self.history_context_menu.add_command(
            label="Copy Query to Editor", command=self.copy_query_to_editor
        )
        self.history_context_menu.add_command(
            label="Copy Query to Clipboard", command=self.copy_query_to_clipboard
        )
        self.history_context_menu.add_separator()
        self.history_context_menu.add_command(
            label="Remove from History", command=self.remove_from_history
        )

    def show_normal_view(self):
        """Switch to normal view (tables/details)"""
        self.current_view = "normal"
        self.query_frame.pack_forget()
        self.normal_frame.pack(fill="both", expand=True)

    def show_query_view(self, db_name):
        """Switch to query view for the specified database"""
        self.current_view = "query"
        self.query_db_name = db_name

        # Update the header to show which database is being queried
        self.query_db_label.config(text=f"SQL Query Interface - Database: {db_name}")

        # Clear previous query and results
        self.sql_text.delete("1.0", tk.END)
        self.results_tree.delete(*self.results_tree.get_children())
        self.status_label.config(text="Ready to execute queries...")

        # Load history for this database
        self.load_query_history()

        # Switch views
        self.normal_frame.pack_forget()
        self.query_frame.pack(fill="both", expand=True)

        # Focus on SQL editor
        self.sql_text.focus()

    def add_to_query_history(self, query, success, result_count=0):
        """Add a query to the history for the current database"""
        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name

        # Initialize history for database if needed
        if db_name not in self.query_history:
            self.query_history[db_name] = []

        # Create history entry
        history_entry = {
            "timestamp": datetime.now(),
            "query": query.strip(),
            "success": success,
            "result_count": result_count,
        }

        # Add to beginning of list (newest first)
        self.query_history[db_name].insert(0, history_entry)

        # Keep only last 100 queries per database
        if len(self.query_history[db_name]) > 100:
            self.query_history[db_name] = self.query_history[db_name][:100]

        # Refresh history display if we're in query view
        if self.current_view == "query":
            self.load_query_history()

    def create_smart_query_preview(self, query, max_length=65):
        """Create an intelligent preview of the SQL query"""
        # Clean up the query - remove empty lines and comments
        lines = [line.strip() for line in query.strip().split("\n")]
        lines = [line for line in lines if line and not line.startswith("--")]

        if not lines:
            return "Empty query"

        # Join all meaningful lines and clean whitespace
        clean_query = " ".join(lines)
        clean_query = " ".join(
            clean_query.split()
        )  # Replace multiple spaces with single space

        # Detect query type and extract key information
        upper_query = clean_query.upper()

        try:
            if upper_query.startswith("SELECT"):
                return self._create_select_preview(clean_query, max_length)
            elif upper_query.startswith("INSERT"):
                return self._create_insert_preview(clean_query, max_length)
            elif upper_query.startswith("UPDATE"):
                return self._create_update_preview(clean_query, max_length)
            elif upper_query.startswith("DELETE"):
                return self._create_delete_preview(clean_query, max_length)
            elif upper_query.startswith("CREATE"):
                return self._create_create_preview(clean_query, max_length)
            elif upper_query.startswith("ALTER"):
                return self._create_alter_preview(clean_query, max_length)
            elif upper_query.startswith("DROP"):
                return self._create_drop_preview(clean_query, max_length)
            else:
                # For other queries, truncate intelligently
                return self._truncate_query(clean_query, max_length)
        except:
            # If any parsing fails, fall back to simple truncation
            return self._truncate_query(clean_query, max_length)

    def _create_select_preview(self, query, max_length):
        """Create preview for SELECT statements"""
        upper_query = query.upper()
        from_pos = upper_query.find(" FROM ")

        if from_pos == -1:
            return self._truncate_query(query, max_length)

        # Extract the SELECT part (columns)
        select_part = query[6:from_pos].strip()  # Remove "SELECT"

        # Extract table name (first word after FROM)
        after_from = query[from_pos + 6 :].strip()
        table_parts = after_from.split()
        table_name = table_parts[0] if table_parts else "table"

        # Clean up columns - remove extra whitespace
        columns = " ".join(select_part.split())

        # Create intelligent column preview
        if "*" in columns:
            column_preview = "*"
        elif "," in columns:
            # Multiple columns - show first few
            col_list = [col.strip() for col in columns.split(",")]
            if len(col_list) <= 2:
                column_preview = columns
            else:
                column_preview = f"{col_list[0]}, {col_list[1]}, ..."
        else:
            # Single column
            column_preview = columns

        # Limit column preview length
        if len(column_preview) > 25:
            column_preview = column_preview[:22] + "..."

        preview = f"SELECT {column_preview} FROM {table_name}"
        return self._truncate_query(preview, max_length)

    def _create_insert_preview(self, query, max_length):
        """Create preview for INSERT statements"""
        upper_query = query.upper()
        into_pos = upper_query.find(" INTO ")

        if into_pos == -1:
            return self._truncate_query(query, max_length)

        # Extract table name
        after_into = query[into_pos + 6 :].strip()
        table_parts = after_into.split()
        table_name = table_parts[0] if table_parts else "table"

        # Check if it's INSERT INTO ... VALUES or INSERT INTO ... SELECT
        if "VALUES" in upper_query:
            preview = f"INSERT INTO {table_name} VALUES"
        elif "SELECT" in upper_query:
            preview = f"INSERT INTO {table_name} SELECT"
        else:
            preview = f"INSERT INTO {table_name}"

        return self._truncate_query(preview, max_length)

    def _create_update_preview(self, query, max_length):
        """Create preview for UPDATE statements"""
        parts = query.split()
        if len(parts) >= 2:
            table_name = parts[1]
            preview = f"UPDATE {table_name} SET"
            return self._truncate_query(preview, max_length)

        return self._truncate_query(query, max_length)

    def _create_delete_preview(self, query, max_length):
        """Create preview for DELETE statements"""
        upper_query = query.upper()
        from_pos = upper_query.find(" FROM ")

        if from_pos == -1:
            return self._truncate_query(query, max_length)

        # Extract table name
        after_from = query[from_pos + 6 :].strip()
        table_parts = after_from.split()
        table_name = table_parts[0] if table_parts else "table"

        preview = f"DELETE FROM {table_name}"
        return self._truncate_query(preview, max_length)

    def _create_create_preview(self, query, max_length):
        """Create preview for CREATE statements"""
        parts = query.split()
        if len(parts) >= 3:
            object_type = parts[1].upper()  # TABLE, INDEX, VIEW, etc.
            object_name = parts[2]
            preview = f"CREATE {object_type} {object_name}"
            return self._truncate_query(preview, max_length)

        return self._truncate_query(query, max_length)

    def _create_alter_preview(self, query, max_length):
        """Create preview for ALTER statements"""
        parts = query.split()
        if len(parts) >= 3:
            object_type = parts[1].upper()  # TABLE, INDEX, etc.
            object_name = parts[2]
            preview = f"ALTER {object_type} {object_name}"
            return self._truncate_query(preview, max_length)

        return self._truncate_query(query, max_length)

    def _create_drop_preview(self, query, max_length):
        """Create preview for DROP statements"""
        parts = query.split()
        if len(parts) >= 3:
            object_type = parts[1].upper()  # TABLE, INDEX, etc.
            object_name = parts[2]
            preview = f"DROP {object_type} {object_name}"
            return self._truncate_query(preview, max_length)

        return self._truncate_query(query, max_length)

    def _truncate_query(self, query, max_length):
        """Truncate query with ellipsis if needed"""
        if len(query) <= max_length:
            return query
        else:
            return query[: max_length - 3] + "..."

    def load_query_history(self):
        """Load and display query history for current database"""
        # Clear existing history display
        self.history_tree.delete(*self.history_tree.get_children())

        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name

        if db_name not in self.query_history:
            return

        # Populate history tree
        for entry in self.query_history[db_name]:
            # Format timestamp
            time_str = entry["timestamp"].strftime("%H:%M:%S")

            # Create intelligent query preview
            preview = self.create_smart_query_preview(entry["query"])

            # Status
            status = "Success" if entry["success"] else "Error"

            # Result count
            rows = str(entry["result_count"]) if entry["success"] else "-"

            # Insert into tree
            self.history_tree.insert(
                "", tk.END, values=(time_str, preview, status, rows)
            )

    def load_query_from_history(self, event):
        """Load selected query from history into editor (double-click)"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # Get the selected item index
        item = selection[0]
        index = self.history_tree.index(item)

        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name
        if db_name not in self.query_history or index >= len(
            self.query_history[db_name]
        ):
            return

        # Get the query
        query = self.query_history[db_name][index]["query"]

        # Load into editor
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.insert("1.0", query)

        # Switch to query tab
        self.query_notebook.select(0)

        # Focus on editor
        self.sql_text.focus()

    def show_history_context_menu(self, event):
        """Show context menu for history items"""
        # Select the item that was right-clicked
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            try:
                self.history_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.history_context_menu.grab_release()

    def copy_query_to_editor(self):
        """Copy selected query from history to editor"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # Get the selected item index
        item = selection[0]
        index = self.history_tree.index(item)

        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name
        if db_name not in self.query_history or index >= len(
            self.query_history[db_name]
        ):
            return

        # Get the query
        query = self.query_history[db_name][index]["query"]

        # Load into editor
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.insert("1.0", query)

        # Switch to query tab
        self.query_notebook.select(0)

        # Focus on editor
        self.sql_text.focus()

    def copy_query_to_clipboard(self):
        """Copy selected query from history to clipboard"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # Get the selected item index
        item = selection[0]
        index = self.history_tree.index(item)

        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name
        if db_name not in self.query_history or index >= len(
            self.query_history[db_name]
        ):
            return

        # Get the query
        query = self.query_history[db_name][index]["query"]

        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(query)

        # Update status
        self.status_label.config(text="Query copied to clipboard")

    def remove_from_history(self):
        """Remove selected query from history"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # Get the selected item index
        item = selection[0]
        index = self.history_tree.index(item)

        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name
        if db_name not in self.query_history or index >= len(
            self.query_history[db_name]
        ):
            return

        # Remove from history
        del self.query_history[db_name][index]

        # Refresh display
        self.load_query_history()

        # Update status
        self.status_label.config(text="Query removed from history")

    def clear_query_history(self):
        """Clear all query history for current database"""
        if not hasattr(self, "query_db_name"):
            return

        db_name = self.query_db_name

        # Confirm deletion
        result = messagebox.askyesno(
            "Clear History",
            f"Are you sure you want to clear all query history for database '{db_name}'?\n\nThis action cannot be undone.",
            icon="warning",
        )

        if result:
            # Clear history
            if db_name in self.query_history:
                self.query_history[db_name] = []

            # Refresh display
            self.load_query_history()

            # Update status
            self.status_label.config(text="Query history cleared")

    # --- Database loading/filtering/selection methods ---
    def load_databases(self):
        self.db_tree.delete(*self.db_tree.get_children())
        creds = self.controller.db_credentials
        if not creds:
            return
        self.all_databases = sorted(fetch_databases(creds))
        for db in self.all_databases:
            self.db_tree.insert("", tk.END, values=(db,))
        self.db_search_var.set("")
        self.clear_details()
        self.back_button.grid_remove()
        self.right_label.config(text="Tables")
        self.item_search_var.set("")
        self.item_tree.delete(*self.item_tree.get_children())
        self.fields_tree.delete(*self.fields_tree.get_children())

        # If we're in query view, switch back to normal view
        if self.current_view == "query":
            self.show_normal_view()

    def clear_details(self):
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state="disabled")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def filter_databases(self, event):
        term = self.db_search_var.get().lower()
        filtered = [db for db in self.all_databases if term in db.lower()]
        self.db_tree.delete(*self.db_tree.get_children())
        for db in filtered:
            self.db_tree.insert("", tk.END, values=(db,))

    def on_db_select(self, event):
        selected = self.db_tree.selection()
        if not selected:
            return
        db_name = self.db_tree.item(selected[0])["values"][0]
        self.current_db = db_name

        # Only update details if we're in normal view
        if self.current_view == "normal":
            creds = self.controller.db_credentials
            details = get_database_details(creds, db_name) or {}
            details_str = (
                "\n".join(f"{k}: {v}" for k, v in details.items())
                or "No details available."
            )
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(tk.END, details_str)
            self.details_text.config(state="disabled")

            tables = sorted(get_tables_for_database(creds, db_name) or [])
            self.all_items = tables
            self.populate_items(tables, header="Table Name")
            self.right_label.config(text="Tables")
            self.back_button.grid_remove()
            self.item_search_var.set("")
            self.fields_tree.delete(*self.fields_tree.get_children())

    def populate_items(self, items, header="Table Name"):
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_tree.heading("Item", text=header)
        for item in items:
            self.item_tree.insert("", tk.END, values=(item,))

    def filter_items(self, event):
        term = self.item_search_var.get().lower()
        filtered = [it for it in self.all_items if term in it.lower()]
        self.populate_items(filtered, header="Table Name")

    def on_item_select(self, event):
        selected = self.item_tree.selection()
        if not selected:
            return
        table_name = self.item_tree.item(selected[0])["values"][0]
        creds = self.controller.db_credentials
        td = get_table_details(creds, self.current_db, table_name) or {}
        details_str = (
            f"Table Name: {td.get('Table Name')}\nRecord Count: {td.get('Record Count')}\n"
            if td
            else "No table details available.\n"
        )
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")

        cols = sorted(get_columns_for_table(creds, self.current_db, table_name) or [])
        self.fields_tree.delete(*self.fields_tree.get_children())
        for col in cols:
            self.fields_tree.insert("", tk.END, values=(col,))
        if not cols:
            self.fields_tree.insert("", tk.END, values=("No fields available",))

    def back_to_tables(self):
        if not self.current_db:
            return
        creds = self.controller.db_credentials
        tables = sorted(get_tables_for_database(creds, self.current_db) or [])
        self.all_items = tables
        self.populate_items(tables, header="Table Name")
        self.right_label.config(text="Tables")
        self.back_button.grid_remove()
        self.item_search_var.set("")
        details = get_database_details(creds, self.current_db) or {}
        ds = (
            "\n".join(f"{k}: {v}" for k, v in details.items())
            or "No details available."
        )
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, ds)
        self.details_text.config(state="disabled")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def is_protected_database(self, db_name):
        """Check if a database is protected from deletion"""
        return db_name.lower() in [db.lower() for db in self.protected_databases]

    def get_deletable_databases(self, db_names):
        """Filter out protected databases from a list"""
        return [db for db in db_names if not self.is_protected_database(db)]

    def get_protected_databases(self, db_names):
        """Get only protected databases from a list"""
        return [db for db in db_names if self.is_protected_database(db)]

    # --- CONTEXT-MENU HANDLERS ---
    def show_db_context_menu(self, event):
        item = self.db_tree.identify_row(event.y)
        if not item:
            return

        # If clicked item is not in current selection, select only it
        if item not in self.db_tree.selection():
            self.db_tree.selection_set(item)

        # Get all selected items
        selected_items = self.db_tree.selection()
        if not selected_items:
            return

        selected_dbs = [self.db_tree.item(i)["values"][0] for i in selected_items]
        self.context_menu_dbs = selected_dbs

        # Update menu labels based on selection count
        self.update_context_menu_labels(len(selected_dbs))

        try:
            self.db_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.db_context_menu.grab_release()

    def show_db_context_menu_keyboard(self, event):
        selected = self.db_tree.selection()
        if not selected:
            return

        selected_dbs = [self.db_tree.item(i)["values"][0] for i in selected]
        self.context_menu_dbs = selected_dbs

        # Update menu labels based on selection count
        self.update_context_menu_labels(len(selected_dbs))

        # Get position from first selected item
        item = selected[0]
        bbox = self.db_tree.bbox(item)
        if not bbox:
            return
        x = self.db_tree.winfo_rootx() + bbox[0] + bbox[2] // 2
        y = self.winfo_rooty() + bbox[1] + bbox[3] // 2
        try:
            self.db_context_menu.tk_popup(x, y)
        finally:
            self.db_context_menu.grab_release()

    def update_context_menu_labels(self, count):
        """Update context menu labels based on number of selected databases"""
        # Clear existing menu
        self.db_context_menu.delete(0, "end")

        # Check if any selected databases are deletable
        deletable_dbs = self.get_deletable_databases(self.context_menu_dbs)
        protected_dbs = self.get_protected_databases(self.context_menu_dbs)

        if count == 1:
            self.db_context_menu.add_command(
                label="Clone Database", command=self.clone_database
            )
            # Only show rename for non-protected databases
            if not self.is_protected_database(self.context_menu_dbs[0]):
                self.db_context_menu.add_command(
                    label="Rename Database", command=self.rename_database
                )
            self.db_context_menu.add_command(
                label="Query Database", command=self.open_query_interface
            )
            self.db_context_menu.add_separator()

            # Only show delete for non-protected databases
            if not self.is_protected_database(self.context_menu_dbs[0]):
                self.db_context_menu.add_command(
                    label="Delete Database", command=self.delete_database_from_context
                )
            else:
                self.db_context_menu.add_command(
                    label="System Database (Protected)",
                    command=self.show_protection_message,
                )
        else:
            self.db_context_menu.add_command(
                label="Clone Database", command=self.clone_database
            )
            self.db_context_menu.add_separator()

            # Show delete option only if there are deletable databases
            if deletable_dbs:
                if protected_dbs:
                    # Some protected, some deletable
                    self.db_context_menu.add_command(
                        label=f"Delete {len(deletable_dbs)} Databases",
                        command=self.delete_database_from_context,
                    )
                    self.db_context_menu.add_command(
                        label=f"{len(protected_dbs)} Protected",
                        command=self.show_protection_message,
                    )
                else:
                    # All deletable
                    self.db_context_menu.add_command(
                        label=f"Delete {count} Databases",
                        command=self.delete_database_from_context,
                    )
            else:
                # All protected
                self.db_context_menu.add_command(
                    label=f"All {count} Databases Protected",
                    command=self.show_protection_message,
                )

    def clone_database(self):
        """Open dialog for naming and quantity of cloned DBs."""
        # Only allow cloning one database at a time
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Clone Limitation",
                "Please select only one database to clone.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        source_db = self.context_menu_dbs[0]

        import datetime

        timestamp = datetime.now().strftime("%Y%m%d")
        default_name = f"{source_db}_copy_{timestamp}"

        dialog = tk.Toplevel(self)
        dialog.title("Clone Database")
        dialog.transient(self)
        dialog.grab_set()

        # Apply enhanced styling
        dialog.configure(bg="#2C3E50")

        # Setup custom styles for this dialog
        style = ttk.Style()

        # Enhanced dialog styles
        style.configure("CloneDialog.TFrame", background="#2C3E50", relief="flat")
        style.configure(
            "CloneDialog.TLabel",
            background="#2C3E50",
            foreground="white",
            font=("Segoe UI", 11),
        )
        style.configure(
            "CloneDialog.TEntry",
            font=("Segoe UI", 11),
            fieldbackground="white",
            borderwidth=2,
            relief="flat",
        )
        style.configure(
            "CloneDialog.TSpinbox",
            font=("Segoe UI", 11),
            fieldbackground="white",
            borderwidth=2,
            relief="flat",
        )

        # Variables
        name_var = tk.StringVar(value=default_name)
        copies_var = tk.IntVar(value=1)
        self.clone_in_progress = False

        # Main content frame with enhanced styling
        content_frame = ttk.Frame(dialog, style="CloneDialog.TFrame", padding=40)
        content_frame.pack(fill="both", expand=True)

        # Configure grid weights for proper expansion
        content_frame.columnconfigure(1, weight=1)

        # Header
        header_label = ttk.Label(
            content_frame,
            text="Clone Database",
            style="DialogHeader.TLabel",
            font=("Segoe UI", 16, "bold"),
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Layout with styled widgets
        ttk.Label(
            content_frame, text="New Database Name:", style="CloneDialog.TLabel"
        ).grid(row=1, column=0, padx=(0, 20), pady=(0, 15), sticky="w")

        name_entry = ttk.Entry(
            content_frame, textvariable=name_var, width=35, style="CloneDialog.TEntry"
        )
        name_entry.grid(row=1, column=1, pady=(0, 15), sticky="ew")

        ttk.Label(
            content_frame, text="Number of Copies:", style="CloneDialog.TLabel"
        ).grid(row=2, column=0, padx=(0, 20), pady=(0, 25), sticky="w")

        copies_spin = ttk.Spinbox(
            content_frame,
            from_=1,
            to=100,
            textvariable=copies_var,
            width=10,
            style="CloneDialog.TSpinbox",
        )
        copies_spin.grid(row=2, column=1, pady=(0, 25), sticky="w")

        # Progress bar (initially hidden)
        progress_bar = ttk.Progressbar(content_frame, mode="indeterminate")
        progress_bar.grid(row=4, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        progress_bar.grid_remove()

        # Status label (initially hidden)
        status_label = ttk.Label(content_frame, text="", style="CloneDialog.TLabel")
        status_label.grid(row=5, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        status_label.grid_remove()

        # Button handlers
        def update_status(message):
            """Update status label from background thread"""
            dialog.after(0, lambda: status_label.config(text=message))

        def perform_clone():
            """Perform the actual cloning operation"""
            new_name = name_var.get().strip() or default_name
            count = copies_var.get()
            credentials = self.controller.db_credentials

            try:
                for i in range(count):
                    if count == 1:
                        current_name = new_name
                    else:
                        current_name = f"{new_name}_{i+1:02d}"

                    update_status(f"Cloning {source_db} to {current_name}...")
                    copy_database_logic(
                        credentials, source_db, current_name, update_status
                    )

                # Success - update UI
                dialog.after(
                    0, lambda: self.finish_clone_success(dialog, count, new_name)
                )

            except Exception as e:
                # Error - show error message
                dialog.after(0, lambda: self.finish_clone_error(dialog, str(e)))

        def on_ok():
            if self.clone_in_progress:
                return

            new_name = name_var.get().strip() or default_name
            count = copies_var.get()

            if not new_name:
                messagebox.showwarning("Input Error", "Please enter a database name.")
                return

            # Disable buttons and show progress
            self.clone_in_progress = True
            ok_btn.config(state="disabled")
            cancel_btn.config(text="Close", state="disabled")
            name_entry.config(state="disabled")
            copies_spin.config(state="disabled")

            progress_bar.grid()
            progress_bar.start(10)
            status_label.grid()
            status_label.config(text="Starting clone operation...")

            # Start cloning in background thread
            clone_thread = threading.Thread(target=perform_clone, daemon=True)
            clone_thread.start()

        def on_cancel():
            if not self.clone_in_progress:
                dialog.destroy()

        # Enhanced buttons
        btn_frame = ttk.Frame(content_frame, style="CloneDialog.TFrame")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        ok_btn = ttk.Button(
            btn_frame, text="Clone Database", command=on_ok, style="Success.TButton"
        )
        ok_btn.pack(side="left", padx=20)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="Secondary.TButton"
        )
        cancel_btn.pack(side="right", padx=20)

        # Set size and center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (350 // 2)
        dialog.geometry(f"500x350+{x}+{y}")
        dialog.deiconify()

        # Focus and wait
        name_entry.focus()
        dialog.wait_window()

    def rename_database(self):
        """Open dialog for renaming a database."""
        # Only allow renaming one database at a time
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Rename Limitation",
                "Please select only one database to rename.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        source_db = self.context_menu_dbs[0]

        # Check if database is protected
        if self.is_protected_database(source_db):
            messagebox.showwarning(
                "Protected Database",
                f"Cannot rename '{source_db}' because it is a protected system database.\n\n"
                "System databases (postgres, template0, template1) are critical for "
                "PostgreSQL operation and cannot be renamed.",
            )
            return

        dialog = tk.Toplevel(self)
        dialog.title("Rename Database")
        dialog.transient(self)
        dialog.grab_set()

        # Apply enhanced styling
        dialog.configure(bg="#2C3E50")

        # Variables
        new_name_var = tk.StringVar(value=source_db)
        self.rename_in_progress = False

        # Main content frame with enhanced styling
        content_frame = ttk.Frame(dialog, style="Dialog.TFrame", padding=40)
        content_frame.pack(fill="both", expand=True)

        # Configure grid weights for proper expansion
        content_frame.columnconfigure(1, weight=1)

        # Header
        header_label = ttk.Label(
            content_frame,
            text="Rename Database",
            style="DialogHeader.TLabel",
            font=("Segoe UI", 16, "bold"),
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Current database name (read-only)
        ttk.Label(content_frame, text="Current Name:", style="Dialog.TLabel").grid(
            row=1, column=0, padx=(0, 20), pady=(0, 15), sticky="w"
        )

        current_name_entry = ttk.Entry(content_frame, width=35, font=("Segoe UI", 11))
        current_name_entry.insert(0, source_db)
        current_name_entry.config(state="readonly")
        current_name_entry.grid(row=1, column=1, pady=(0, 15), sticky="ew")

        # New database name entry
        ttk.Label(content_frame, text="New Name:", style="Dialog.TLabel").grid(
            row=2, column=0, padx=(0, 20), pady=(0, 25), sticky="w"
        )

        new_name_entry = ttk.Entry(
            content_frame, textvariable=new_name_var, width=35, font=("Segoe UI", 11)
        )
        new_name_entry.grid(row=2, column=1, pady=(0, 25), sticky="ew")

        # Progress bar (initially hidden)
        progress_bar = ttk.Progressbar(content_frame, mode="indeterminate")
        progress_bar.grid(row=4, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        progress_bar.grid_remove()

        # Status label (initially hidden)
        status_label = ttk.Label(content_frame, text="", style="Dialog.TLabel")
        status_label.grid(row=5, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        status_label.grid_remove()

        # Button handlers
        def update_status(message):
            """Update status label from background thread"""
            dialog.after(0, lambda: status_label.config(text=message))

        def perform_rename():
            """Perform the actual rename operation"""
            new_name = new_name_var.get().strip()
            credentials = self.controller.db_credentials

            try:
                rename_database(credentials, source_db, new_name, update_status)

                # Success - update UI
                dialog.after(
                    0, lambda: self.finish_rename_success(dialog, source_db, new_name)
                )

            except Exception as e:
                # Error - show error message
                dialog.after(0, lambda: self.finish_rename_error(dialog, str(e)))

        def on_rename():
            if self.rename_in_progress:
                return

            new_name = new_name_var.get().strip()

            if not new_name:
                messagebox.showwarning(
                    "Input Error", "Please enter a new database name."
                )
                return

            if new_name == source_db:
                messagebox.showwarning(
                    "Input Error", "New name must be different from current name."
                )
                return

            # Disable buttons and show progress
            self.rename_in_progress = True
            rename_btn.config(state="disabled")
            cancel_btn.config(text="Close", state="disabled")
            current_name_entry.config(state="disabled")
            new_name_entry.config(state="disabled")

            progress_bar.grid()
            progress_bar.start(10)
            status_label.grid()
            status_label.config(text="Starting rename operation...")

            # Start renaming in background thread
            rename_thread = threading.Thread(target=perform_rename, daemon=True)
            rename_thread.start()

        def on_cancel():
            if not self.rename_in_progress:
                dialog.destroy()

        # Enhanced buttons
        btn_frame = ttk.Frame(content_frame, style="Dialog.TFrame")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        rename_btn = ttk.Button(
            btn_frame,
            text="Rename Database",
            command=on_rename,
            style="Warning.TButton",
        )
        rename_btn.pack(side="left", padx=20)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="Secondary.TButton"
        )
        cancel_btn.pack(side="right", padx=20)

        # Set size and center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (380 // 2)
        dialog.geometry(f"500x380+{x}+{y}")
        dialog.deiconify()

        # Focus on new name entry and select all text for easy editing
        new_name_entry.focus()
        new_name_entry.select_range(0, tk.END)
        dialog.wait_window()

    def open_query_interface(self):
        """Open SQL query interface for the selected database in the right pane."""
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Query Limitation",
                "Please select only one database to query.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        db_name = self.context_menu_dbs[0]
        self.show_query_view(db_name)

    def execute_query(self):
        """Execute the SQL query in background thread."""
        sql_query = self.sql_text.get("1.0", tk.END).strip()

        if not sql_query:
            messagebox.showwarning(
                "Empty Query", "Please enter a SQL query to execute."
            )
            return

        if not hasattr(self, "query_db_name"):
            messagebox.showerror("No Database", "No database selected for query.")
            return

        # Update status and disable execute button during execution
        self.status_label.config(text="Executing query...")

        def query_worker():
            credentials = self.controller.db_credentials
            try:
                result = execute_sql_query(credentials, self.query_db_name, sql_query)
                self.after(0, lambda: self.display_query_results(result, sql_query))
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"Execution error: {str(e)}",
                    "execution_time_ms": 0,
                }
                self.after(
                    0, lambda: self.display_query_results(error_result, sql_query)
                )

        threading.Thread(target=query_worker, daemon=True).start()

    def display_query_results(self, result, original_query):
        """Display query results in the treeview and add to history."""
        # Clear previous results
        self.results_tree.delete(*self.results_tree.get_children())

        # Update status
        if result["success"]:
            status_text = (
                f"{result['message']} (Execution time: {result['execution_time_ms']}ms)"
            )
        else:
            status_text = result["message"]

        self.status_label.config(text=status_text)

        # Add to query history
        result_count = result.get("row_count", 0) if result["success"] else 0
        self.add_to_query_history(original_query, result["success"], result_count)

        if not result["success"]:
            # Show error in results area
            self.results_tree["columns"] = ("Error",)
            self.results_tree["show"] = "headings"
            self.results_tree.heading("Error", text="Error Message")
            self.results_tree.column("Error", width=800)
            self.results_tree.insert("", tk.END, values=(result["message"],))
            return

        # Display results for successful queries
        if result["query_type"] == "SELECT" and result["columns"]:
            # Configure columns
            self.results_tree["columns"] = result["columns"]
            self.results_tree["show"] = "headings"

            # Set up column headers and widths
            for col in result["columns"]:
                self.results_tree.heading(col, text=col)
                self.results_tree.column(col, width=150, minwidth=100)

            # Insert data rows
            for row in result["rows"]:
                # Convert any None values to empty strings for display
                display_row = [str(val) if val is not None else "" for val in row]
                self.results_tree.insert("", tk.END, values=display_row)

        elif result["query_type"] == "MODIFICATION":
            # Show modification results
            self.results_tree["columns"] = ("Result",)
            self.results_tree["show"] = "headings"
            self.results_tree.heading("Result", text="Query Result")
            self.results_tree.column("Result", width=800)
            self.results_tree.insert("", tk.END, values=(result["message"],))

    def clear_query(self):
        """Clear the SQL editor."""
        self.sql_text.delete("1.0", tk.END)

    def format_sql(self):
        """Format and beautify the SQL in the editor."""
        try:
            # Get current SQL content
            current_sql = self.sql_text.get("1.0", tk.END).strip()

            if not current_sql:
                messagebox.showinfo(
                    "No SQL to Format", "Please enter some SQL code to format."
                )
                return

            # Format the SQL using sqlparse with enhanced formatting
            formatted_sql = sqlparse.format(
                current_sql,
                reindent=True,  # Proper indentation
                keyword_case="upper",  # SELECT, FROM, WHERE in uppercase
                identifier_case="lower",  # table_names, column_names in lowercase
                strip_comments=False,  # Keep -- comments
                indent_width=4,  # 4-space indentation for better readability
                wrap_after=60,  # Wrap lines after 60 characters
                comma_first=False,  # Comma at end of line, not beginning
                use_space_around_operators=True,  # Spaces around = < > operators
            )

            # Additional custom formatting for SELECT lists
            lines = formatted_sql.split("\n")
            formatted_lines = []
            in_select = False
            select_items = []

            for line in lines:
                stripped = line.strip()

                # Detect start of SELECT statement
                if stripped.upper().startswith("SELECT"):
                    in_select = True
                    # Check if SELECT is on same line as columns
                    if len(stripped) > 6:  # More than just "SELECT"
                        # Extract the part after SELECT
                        select_part = stripped[6:].strip()
                        formatted_lines.append("SELECT")
                        if select_part:
                            select_items.append(select_part)
                    else:
                        formatted_lines.append("SELECT")
                    continue

                # Detect end of SELECT clause
                elif in_select and any(
                    stripped.upper().startswith(keyword)
                    for keyword in [
                        "FROM",
                        "WHERE",
                        "GROUP BY",
                        "HAVING",
                        "ORDER BY",
                        "LIMIT",
                        "UNION",
                        "JOIN",
                        "INNER JOIN",
                        "LEFT JOIN",
                        "RIGHT JOIN",
                    ]
                ):
                    # Process accumulated SELECT items BEFORE adding the current line
                    if select_items:
                        formatted_lines.extend(self._format_select_items(select_items))
                        select_items = []
                    in_select = False
                    formatted_lines.append(line)  # Add the FROM/WHERE/etc line
                    continue

                # Accumulate SELECT items
                elif in_select:
                    if stripped:
                        select_items.append(stripped)
                    continue

                else:
                    formatted_lines.append(line)

            # Handle case where SELECT is at end of query
            if select_items:
                formatted_lines.extend(self._format_select_items(select_items))

            # Join back together
            final_formatted = "\n".join(formatted_lines)

            # Replace content with formatted version
            self.sql_text.delete("1.0", tk.END)
            self.sql_text.insert("1.0", final_formatted)

            # Update status
            self.status_label.config(text="SQL formatted successfully!")

        except Exception as e:
            messagebox.showerror("Format Error", f"Failed to format SQL:\n{str(e)}")

    def _format_select_items(self, items):
        """Helper method to format SELECT items with proper indentation."""
        formatted_items = []

        # Join all items and split by comma to handle multi-line cases
        all_items = " ".join(items)
        columns = [col.strip() for col in all_items.split(",") if col.strip()]

        for i, column in enumerate(columns):
            # Clean up the column (remove extra spaces, etc.)
            column = " ".join(column.split())

            # Add proper indentation and comma
            if i == len(columns) - 1:  # Last item, no comma
                formatted_items.append(f"    {column}")
            else:  # Add comma
                formatted_items.append(f"    {column},")

        return formatted_items

    def show_protection_message(self):
        """Show information about protected databases"""
        protected_list = ", ".join(self.get_protected_databases(self.context_menu_dbs))
        messagebox.showinfo(
            "Protected System Databases",
            f"The following databases are protected from modification:\n\n{protected_list}\n\n"
            "These are critical system databases required for PostgreSQL to function properly. "
            "They cannot be deleted, renamed, or modified to ensure system stability.",
        )

    def finish_clone_success(self, dialog, count, base_name):
        """Handle successful clone completion"""
        self.clone_in_progress = False
        if count == 1:
            message = f"Database '{base_name}' cloned successfully!"
        else:
            message = f"{count} database copies created successfully with base name '{base_name}'!"

        messagebox.showinfo("Clone Complete", message)
        dialog.destroy()

        # Refresh the database list to show the new databases
        self.load_databases()

    def finish_clone_error(self, dialog, error_message):
        """Handle clone operation error"""
        self.clone_in_progress = False
        messagebox.showerror(
            "Clone Error", f"Failed to clone database:\n{error_message}"
        )
        dialog.destroy()

    def finish_rename_success(self, dialog, old_name, new_name):
        """Handle successful rename completion"""
        self.rename_in_progress = False
        messagebox.showinfo(
            "Rename Complete",
            f"Database '{old_name}' has been successfully renamed to '{new_name}'!",
        )
        dialog.destroy()

        # Refresh the database list to show the renamed database
        self.load_databases()

    def finish_rename_error(self, dialog, error_message):
        """Handle rename operation error"""
        self.rename_in_progress = False
        messagebox.showerror(
            "Rename Error", f"Failed to rename database:\n{error_message}"
        )
        dialog.destroy()

    def delete_database_from_context(self):
        """Delete selected databases from context menu with styled confirmation dialog"""
        all_selected_dbs = self.context_menu_dbs
        if not all_selected_dbs:
            return

        # Filter out protected databases
        deletable_dbs = self.get_deletable_databases(all_selected_dbs)
        protected_dbs = self.get_protected_databases(all_selected_dbs)

        # If no databases can be deleted, show protection message
        if not deletable_dbs:
            self.show_protection_message()
            return

        # If some databases are protected, show warning about what will be deleted
        if protected_dbs:
            protected_list = ", ".join(protected_dbs)
            warning_result = messagebox.showwarning(
                "Protected Databases Detected",
                f"The following protected databases will be skipped:\n{protected_list}\n\n"
                f"Only {len(deletable_dbs)} database(s) will be deleted:\n{', '.join(deletable_dbs)}\n\n"
                "Do you want to continue with deleting the non-protected databases?",
                type=messagebox.OKCANCEL,
            )
            if warning_result != "ok":
                return

        # Use only deletable databases for the deletion dialog
        db_names = deletable_dbs

        # Create custom confirmation dialog
        dialog = tk.Toplevel(self)
        dialog.title("Delete Database(s)")
        dialog.transient(self)
        dialog.grab_set()

        # Apply enhanced styling
        dialog.configure(bg="#2C3E50")

        # Main content frame with enhanced styling
        content_frame = ttk.Frame(dialog, style="Dialog.TFrame", padding=40)
        content_frame.pack(fill="both", expand=True)

        # Warning header
        if len(db_names) == 1:
            header_text = "Delete Database"
            warning_text = (
                "This will permanently delete the database and all its data.\n"
                "This action cannot be undone."
            )
        else:
            header_text = f"Delete {len(db_names)} Databases"
            warning_text = (
                f"This will permanently delete {len(db_names)} databases and all their data.\n"
                "This action cannot be undone."
            )

        header_label = ttk.Label(
            content_frame,
            text=header_text,
            style="DialogHeader.TLabel",
            font=("Segoe UI", 16, "bold"),
        )
        header_label.pack(pady=(0, 25))

        # Database names highlight
        if len(db_names) == 1:
            db_label = ttk.Label(
                content_frame, text=f'"{db_names[0]}"', style="DialogHighlight.TLabel"
            )
            db_label.pack(pady=(0, 20))
        else:
            # Create a frame for multiple database names
            db_frame = ttk.Frame(content_frame, style="Dialog.TFrame")
            db_frame.pack(pady=(0, 20))

            # Show database names in a more compact way
            if len(db_names) <= 3:
                for db_name in db_names:
                    db_label = ttk.Label(
                        db_frame, text=f'"{db_name}"', style="DialogHighlight.TLabel"
                    )
                    db_label.pack()
            else:
                # For many databases, show first 2 and count
                for db_name in db_names[:2]:
                    db_label = ttk.Label(
                        db_frame, text=f'"{db_name}"', style="DialogHighlight.TLabel"
                    )
                    db_label.pack()
                more_label = ttk.Label(
                    db_frame,
                    text=f"+ {len(db_names) - 2} more...",
                    style="DialogHighlight.TLabel",
                )
                more_label.pack()

        # Warning message
        warning_label = ttk.Label(
            content_frame, text=warning_text, style="Dialog.TLabel", justify="center"
        )
        warning_label.pack(pady=(0, 30))

        # Button handlers
        def on_delete():
            dialog.destroy()
            self.perform_multiple_database_deletion(db_names)

        def on_cancel():
            dialog.destroy()

        # Enhanced buttons
        btn_frame = ttk.Frame(content_frame, style="Dialog.TFrame")
        btn_frame.pack(pady=(20, 0))

        if len(db_names) == 1:
            delete_text = "Delete Database"
        else:
            delete_text = f"Delete All ({len(db_names)})"

        delete_btn = ttk.Button(
            btn_frame, text=delete_text, command=on_delete, style="Danger.TButton"
        )
        delete_btn.pack(side="left", padx=20)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="Secondary.TButton"
        )
        cancel_btn.pack(side="right", padx=20)

        # Set size and center the dialog
        min_height = 320 if len(db_names) <= 3 else 360
        dialog.minsize(450, min_height)

        dialog.withdraw()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (min_height // 2)
        dialog.geometry(f"450x{min_height}+{x}+{y}")
        dialog.deiconify()

        # Focus on cancel button by default (safer)
        cancel_btn.focus()
        dialog.wait_window()

    def perform_multiple_database_deletion(self, db_names):
        """Perform deletion of multiple databases in background thread"""

        def deletion_worker():
            credentials = self.controller.db_credentials
            errors = []
            successful_deletions = []

            for db_name in db_names:
                try:
                    terminate_and_delete_database(credentials, db_name)
                    successful_deletions.append(db_name)
                except Exception as e:
                    errors.append(f"{db_name}: {str(e)}")

            # Update UI on main thread
            self.after(
                0, lambda: self.finish_multiple_deletion(successful_deletions, errors)
            )

        # Start deletion in background thread
        threading.Thread(target=deletion_worker, daemon=True).start()

    def finish_multiple_deletion(self, successful_deletions, errors):
        """Handle completion of multiple database deletions"""
        # Refresh the database list
        self.load_databases()

        if errors and successful_deletions:
            # Partial success
            success_msg = f"Successfully deleted: {', '.join(successful_deletions)}"
            error_msg = f"Failed to delete:\n" + "\n".join(errors)
            messagebox.showwarning("Partial Success", f"{success_msg}\n\n{error_msg}")
        elif errors:
            # All failed
            error_msg = "Failed to delete databases:\n" + "\n".join(errors)
            messagebox.showerror("Deletion Error", error_msg)
        else:
            # All successful
            if len(successful_deletions) == 1:
                messagebox.showinfo(
                    "Deletion Complete",
                    f"Database '{successful_deletions[0]}' has been successfully deleted.",
                )
            else:
                messagebox.showinfo(
                    "Deletion Complete",
                    f"{len(successful_deletions)} databases have been successfully deleted.",
                )
