import tkinter as tk
from tkinter import ttk, messagebox
from gui.login_page import LoginPage
from gui.copier_page import CopierPage
from gui.db_management_page import DBManagementPage

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PostgreSQL Database Manager")
        self.geometry("800x600")
        
        # Setup custom styles
        self.setup_styles()
        
        # Create Navigation Bar (initially hidden)
        self.nav_bar = ttk.Frame(self, style="Nav.TFrame")
        self.build_nav_bar()
        self.nav_bar.pack_forget()
        
        # Container for pages (below the nav bar)
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        # Dictionary to hold our pages
        self.frames = {}
        
        # Shared state (e.g. credentials) goes here
        self.db_credentials = {}
        
        # Initialize pages
        for Page in (LoginPage, CopierPage, DBManagementPage):
            page_name = Page.__name__
            frame = Page(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("LoginPage")
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # using 'clam' to allow easier customization
        
        # Global widget styles
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("TEntry", font=("Helvetica", 10), padding=5)
        
        # Navigation bar styles
        style.configure("Nav.TFrame", background="#181F67")
        style.configure("Nav.TLabel", background="#181F67", foreground="white", font=("Helvetica", 14, "bold"))
        style.configure("Nav.TButton", background="#7BB837", foreground="white", font=("Helvetica", 10, "bold"), padding=5)
        style.map("Nav.TButton", background=[("active", "#6AA62F")])
        
        # Logout button (distinct style)
        style.configure("Logout.TButton", background="#939498", foreground="white", font=("Helvetica", 10, "bold"), padding=5)
        style.map("Logout.TButton", background=[("active", "#7A7A7A")])
    
    def build_nav_bar(self):
        # Clear any previous nav bar widgets
        for widget in self.nav_bar.winfo_children():
            widget.destroy()
        
        # Title label on the nav bar
        title_label = ttk.Label(self.nav_bar, text="PostgreSQL DB Manager", style="Nav.TLabel")
        title_label.pack(side="left", padx=20, pady=10)
        
        # Navigation buttons container
        btn_frame = ttk.Frame(self.nav_bar, style="Nav.TFrame")
        btn_frame.pack(side="right", padx=20)
        
        # Page navigation buttons
        copier_btn = ttk.Button(btn_frame, text="Copier", style="Nav.TButton",
                                  command=lambda: self.show_frame("CopierPage"))
        copier_btn.pack(side="left", padx=5)
        
        db_mgmt_btn = ttk.Button(btn_frame, text="DB Management", style="Nav.TButton",
                                 command=lambda: self.show_frame("DBManagementPage"))
        db_mgmt_btn.pack(side="left", padx=5)
        
        # Distinct logout button
        logout_btn = ttk.Button(btn_frame, text="Logout", style="Logout.TButton",
                                command=self.logout)
        logout_btn.pack(side="left", padx=5)
    
    def show_frame(self, page_name):
        """Raise the frame corresponding to page_name."""
        frame = self.frames[page_name]
        frame.tkraise()
        frame.event_generate("<<ShowFrame>>")
        
        # Show nav bar for all pages except the login page
        if page_name == "LoginPage":
            self.nav_bar.pack_forget()
        else:
            self.nav_bar.pack(fill="x", side="top")
    
    def logout(self):
        """Clear credentials and return to the login page."""
        self.db_credentials = {}
        self.show_frame("LoginPage")

if __name__ == "__main__":
    app = App()
    app.mainloop()
