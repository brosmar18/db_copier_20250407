import tkinter as tk
from tkinter import ttk, messagebox
from gui.login_page import LoginPage
from gui.db_management_page import DBManagementPage
from gui.restore_page import RestorePage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AppDev Station")
        self.geometry("1400x900")  # Larger default size for better visibility
        self.minsize(1000, 700)  # Increased minimum size

        # Performance optimization: Configure window for better rendering
        self.configure(bg="white")

        # Optimize for modern displays with better scaling
        try:
            self.tk.call("tk", "scaling", 1.2)  # Increased scaling for better visibility
        except:
            pass

        # Setup minimal styles first
        self.setup_minimal_styles()

        # Create basic structure
        self.setup_basic_structure()

        # Shared state
        self.db_credentials = {}
        self.frames = {}

        # Show login page immediately for faster startup
        self.show_frame("LoginPage")

    def setup_minimal_styles(self):
        """Setup only essential styles for faster startup with new color scheme"""
        style = ttk.Style()
        style.theme_use("clam")

        # Improved base styles with larger fonts and new colors
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white", font=("Segoe UI", 13))
        style.configure("TButton", font=("Segoe UI", 12), padding=(12, 8))
        style.configure("TEntry", font=("Segoe UI", 12), padding=8)

        # Navigation styles with new color scheme
        style.configure("Nav.TFrame", background="#181F67", relief="flat")  # New dark blue
        style.configure(
            "Nav.TLabel",
            background="#181F67",  # New dark blue
            foreground="white",
            font=("Segoe UI", 16, "bold"),
            padding=(0, 15)
        )
        style.configure(
            "Nav.TButton",
            background="#7BB837",  # New green
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            padding=(20, 12),
            borderwidth=0,
            relief="flat",
            focuscolor="none"
        )
        style.map("Nav.TButton", 
                 background=[("active", "#6FA02E"), ("pressed", "#5F8A26")],  # Darker greens
                 relief=[("pressed", "flat"), ("!pressed", "flat")])  # Keep flat appearance

    def setup_basic_structure(self):
        """Create basic application structure quickly"""
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Navigation bar with increased height and new color
        self.nav_bar = ttk.Frame(self, style="Nav.TFrame", height=70)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        self.nav_bar.grid_remove()
        self.nav_bar.grid_propagate(False)

        # Container for pages
        self.container = ttk.Frame(self)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Build navigation after idle for better startup
        self.after_idle(self.build_nav_bar)

    def build_nav_bar(self):
        """Build navigation bar lazily with improved sizing and new colors"""
        # Clear existing widgets
        for widget in self.nav_bar.winfo_children():
            widget.destroy()

        # Title with more padding
        title_label = ttk.Label(
            self.nav_bar, text="PostgreSQL DB Manager", style="Nav.TLabel"
        )
        title_label.pack(side="left", padx=30, pady=15)

        # Button frame
        btn_frame = ttk.Frame(self.nav_bar, style="Nav.TFrame")
        btn_frame.pack(side="right", padx=30, pady=12)

        # Navigation buttons with better spacing
        buttons = [
            ("DB Management", "DBManagementPage"),
            ("Restore", "RestorePage"),
            ("Logout", None),
        ]

        for i, (text, page) in enumerate(buttons):
            if text == "Logout":
                btn = ttk.Button(
                    btn_frame, text=text, command=self.logout, style="Nav.TButton"
                )
            else:
                btn = ttk.Button(
                    btn_frame,
                    text=text,
                    command=lambda p=page: self.show_frame(p),
                    style="Nav.TButton",
                )
            btn.pack(side="left", padx=8)

    def create_frame(self, page_class):
        """Create frame lazily when first needed"""
        page_name = page_class.__name__
        if page_name not in self.frames:
            frame = page_class(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        return self.frames[page_name]

    def show_frame(self, page_name):
        """Show frame, creating it if necessary"""
        # Map page names to classes
        page_classes = {
            "LoginPage": LoginPage,
            "DBManagementPage": DBManagementPage,
            "RestorePage": RestorePage,
        }

        if page_name in page_classes:
            frame = self.create_frame(page_classes[page_name])
            frame.tkraise()

            # Generate show frame event
            try:
                frame.event_generate("<<ShowFrame>>")
            except:
                pass

        # Show/hide navigation
        if page_name == "LoginPage":
            self.nav_bar.grid_remove()
        else:
            self.nav_bar.grid()

    def logout(self):
        """Logout and return to login page"""
        # Clear credentials
        self.db_credentials = {}

        # Clear any cached frames except login for memory efficiency
        frames_to_clear = ["DBManagementPage", "RestorePage"]
        for frame_name in frames_to_clear:
            if frame_name in self.frames:
                self.frames[frame_name].destroy()
                del self.frames[frame_name]

        # Show login page
        self.show_frame("LoginPage")

    def run(self):
        """Start the application with error handling"""
        try:
            self.mainloop()
        except Exception as e:
            messagebox.showerror(
                "Application Error", f"An unexpected error occurred:\n{str(e)}"
            )


if __name__ == "__main__":
    app = App()
    app.run()