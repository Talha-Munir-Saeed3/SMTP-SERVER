import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import queue
import re
from dotenv import load_dotenv
from email.utils import parseaddr
from db_manager import DatabaseManager

# Import our mail handling scripts
import send_mail
import recieve  

load_dotenv()

#Application Structure connection to database and GUI with login inbox view and etc
class EmailClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Client")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Initialize database manager
        self.db_manager = DatabaseManager(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USERNAME", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "email_client")
        )
        
        # Create database tables if they don't exist
        if not self.db_manager.create_tables():
            messagebox.showwarning("Database Warning","Could not connect to database. Email history will not be saved.")
    
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 11))
        self.style.configure('TLabel', font=('Arial', 11), background='#f0f0f0')
        self.style.configure('TEntry', font=('Arial', 11))
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'), background='#f0f0f0')
        
        # Email server configurations
        self.email_configs = {
            'Gmail': {
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'imap_host': 'imap.gmail.com',
                'imap_port': 993
            },
            'Yahoo': {
                'smtp_host': 'smtp.mail.yahoo.com',
                'smtp_port': 587,
                'imap_host': 'imap.mail.yahoo.com',
                'imap_port': 993
            },
            'Outlook/Hotmail': {
                'smtp_host': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'imap_host': 'outlook.office365.com',
                'imap_port': 993
            }
        }
        
        # User credentials and settings
        self.username = tk.StringVar(value=os.getenv('GMAIL_USERNAME', ''))
        self.password = tk.StringVar(value=os.getenv('GMAIL_APP_PASSWORD', ''))
        self.display_name = tk.StringVar()
        self.selected_provider = tk.StringVar(value='Gmail')  # Default provider
        
        # Email sending variables
        self.recipient_list = []
        self.attachment_list = []
        self.subject = tk.StringVar()
        self.message_text = None  # Will be initialized with the text widget
        self.html_mode = tk.BooleanVar(value=False)
        
        # Create UI widgets
        self.create_login_frame()
        self.create_send_frame()
        self.create_receive_frame()
        
        # Show login frame by default
        self.show_login_frame()
        #Producer Consumer example
        # For handling asynchronous tasks
        self.task_queue = queue.Queue()
        self.root.after(100, self.process_queue)
    
    def process_queue(self):
        """Process background tasks from the queue"""
        try:
            while True:
                task, args, kwargs = self.task_queue.get_nowait()
                task(*args, **kwargs)
                self.task_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)
    #User Interface are called upon when object is created
    #First window login
    def create_login_frame(self):
        """Create the login UI with improved layout"""
        self.login_frame = ttk.Frame(self.root, padding=30)
        
        # Create a title frame with centered header
        title_frame = ttk.Frame(self.login_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 25))
        
        header_label = ttk.Label(title_frame, text="Email Client Login", 
                                font=('Arial', 16, 'bold'), foreground='#333333')
        header_label.pack()
        
        # Email Provider Selection - row 1
        ttk.Label(self.login_frame, text="Email Provider:", 
                font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=8)
        provider_combo = ttk.Combobox(self.login_frame, textvariable=self.selected_provider, 
                                    values=list(self.email_configs.keys()), state='readonly', width=38)
        provider_combo.grid(row=1, column=1, sticky='we', pady=8)
        
        # Email Address - row 2
        ttk.Label(self.login_frame, text="Email Address:", 
                font=('Arial', 11)).grid(row=2, column=0, sticky='w', pady=8)
        ttk.Entry(self.login_frame, textvariable=self.username, width=40).grid(row=2, column=1, sticky='we', pady=8)
        
        # Password - row 3
        ttk.Label(self.login_frame, text="Password:", 
                font=('Arial', 11)).grid(row=3, column=0, sticky='w', pady=8)
        ttk.Entry(self.login_frame, textvariable=self.password, show='*', width=40).grid(row=3, column=1, sticky='we', pady=8)
        
        # Display Name - row 4
        ttk.Label(self.login_frame, text="Your Name:", 
                font=('Arial', 11)).grid(row=4, column=0, sticky='w', pady=8)
        ttk.Entry(self.login_frame, textvariable=self.display_name, width=40).grid(row=4, column=1, sticky='we', pady=8)
        
        # Login Button in a frame to center it - row 5
        button_frame = ttk.Frame(self.login_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        login_btn = ttk.Button(button_frame, text="Login", command=self.login, width=15)
        login_btn.pack(pady=5)
        
        # Info text - row 6
        info_text = "Note: For Gmail and some providers, you may need to use an App Password\ninstead of your regular password if 2FA is enabled."
        info_label = ttk.Label(self.login_frame, text=info_text, foreground='#555555', 
                            justify=tk.CENTER, font=('Arial', 10))
        info_label.grid(row=6, column=0, columnspan=2, pady=(10, 20))
        
        # Add separator before credits
        separator = ttk.Separator(self.login_frame, orient='horizontal')
        separator.grid(row=7, column=0, columnspan=2, sticky='ew', pady=15)
        
        # Credits at bottom - row 8
        credits_text = "Developed by Talha (22K-4465)"
        credits_label = ttk.Label(self.login_frame, text=credits_text, 
                                font=('Arial', 10, 'bold'), foreground='#333333',
                                justify=tk.CENTER)
        credits_label.grid(row=8, column=0, columnspan=2, pady=(0, 10))
        
        # Configure column weights to center the form
        self.login_frame.columnconfigure(0, weight=1)
        self.login_frame.columnconfigure(1, weight=1)
    #Composing Email Window
    def create_send_frame(self):
        """Create the email sending UI"""
        self.send_frame = ttk.Frame(self.root, padding=20)
        
        # Top action buttons
        btn_frame = ttk.Frame(self.send_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, sticky='we', pady=(0, 10))
        
        ttk.Button(btn_frame, text="Receive Mail", command=self.show_receive_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="History", command=self.show_email_history).pack(side=tk.LEFT, padx=5)  # Add this line
        ttk.Button(btn_frame, text="Logout", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Header
        header_label = ttk.Label(self.send_frame, text="Compose Email", style='Header.TLabel')
        header_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # To field with recipient management
        ttk.Label(self.send_frame, text="To:").grid(row=2, column=0, sticky='w', pady=5)
        recipient_frame = ttk.Frame(self.send_frame)
        recipient_frame.grid(row=2, column=1, sticky='we', pady=5)
        
        self.recipient_entry = ttk.Entry(recipient_frame, width=40)
        self.recipient_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(recipient_frame, text="Add", command=self.add_recipient).pack(side=tk.RIGHT, padx=5)
        ttk.Button(recipient_frame, text="Remove", command=self.remove_recipient).pack(side=tk.RIGHT, padx=5)
        ttk.Button(recipient_frame, text="Clear All", command=self.clear_recipients).pack(side=tk.RIGHT, padx=5)
        # Recipients list
        self.recipients_display = scrolledtext.ScrolledText(self.send_frame, height=2, width=40, wrap=tk.WORD)
        self.recipients_display.grid(row=3, column=1, sticky='we', pady=(0, 10))
        self.recipients_display.config(state=tk.DISABLED)
        
        # Subject
        ttk.Label(self.send_frame, text="Subject:").grid(row=4, column=0, sticky='w', pady=5)
        ttk.Entry(self.send_frame, textvariable=self.subject, width=40).grid(row=4, column=1, sticky='we', pady=5)
        
        # Message
        ttk.Label(self.send_frame, text="Message:").grid(row=5, column=0, sticky='nw', pady=5)
        
        # Text type toggle frame
        msg_toggle_frame = ttk.Frame(self.send_frame)
        msg_toggle_frame.grid(row=5, column=1, sticky='nwe', pady=(5, 0))
        
        ttk.Radiobutton(msg_toggle_frame, text="Plain Text", variable=self.html_mode, value=False, 
                       command=self.toggle_message_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(msg_toggle_frame, text="HTML", variable=self.html_mode, value=True,
                       command=self.toggle_message_mode).pack(side=tk.LEFT, padx=5)
        
        # Message text area
        self.message_text = scrolledtext.ScrolledText(self.send_frame, height=10, width=40, wrap=tk.WORD)
        self.message_text.grid(row=6, column=0, columnspan=2, sticky='nswe', pady=5)
        
        # Attachments
        ttk.Label(self.send_frame, text="Attachments:").grid(row=7, column=0, sticky='w', pady=5)
        attachment_frame = ttk.Frame(self.send_frame)
        attachment_frame.grid(row=7, column=1, sticky='we', pady=5)
        
        ttk.Button(attachment_frame, text="Add Files", command=self.add_attachments).pack(side=tk.LEFT, padx=5)
        ttk.Button(attachment_frame, text="Send Code Snippet", command=self.send_code_snippet).pack(side=tk.LEFT, padx=5)
        ttk.Button(attachment_frame, text="Remove", command=self.remove_attachment).pack(side=tk.LEFT, padx=5)
        ttk.Button(attachment_frame, text="Clear All", command=self.clear_attachments).pack(side=tk.LEFT, padx=5)
        
        # Attachments list
        self.attachments_display = scrolledtext.ScrolledText(self.send_frame, height=3, width=40, wrap=tk.WORD)
        self.attachments_display.grid(row=8, column=0, columnspan=2, sticky='we', pady=(0, 10))
        self.attachments_display.config(state=tk.DISABLED)
        
        # Send button
        ttk.Button(self.send_frame, text="Send Email", command=self.send_email).grid(row=9, column=0, columnspan=2, pady=10)
        
        # Status message
        self.send_status_var = tk.StringVar()
        ttk.Label(self.send_frame, textvariable=self.send_status_var, foreground='#555555').grid(
            row=10, column=0, columnspan=2, pady=(0, 10))
        
        # Configure grid expansion
        self.send_frame.columnconfigure(1, weight=1)
        self.send_frame.rowconfigure(6, weight=1)
    #Recieving Email Window
    def create_receive_frame(self):
        """Create the email receiving UI"""
        self.receive_frame = ttk.Frame(self.root, padding=20)
        
        # Top action buttons
        btn_frame = ttk.Frame(self.receive_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, sticky='we', pady=(0, 10))
        
        ttk.Button(btn_frame, text="Compose Email", command=self.show_send_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Email History", command=self.show_email_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Logout", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Header
        header_label = ttk.Label(self.receive_frame, text="Inbox", style='Header.TLabel')
        header_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Refresh button
        refresh_btn = ttk.Button(self.receive_frame, text="Check for New Emails", command=self.check_emails)
        refresh_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Create a frame for the email list
        self.email_list_frame = ttk.Frame(self.receive_frame)
        self.email_list_frame.grid(row=3, column=0, columnspan=2, sticky='nswe', pady=10)
        
        # Status message
        self.receive_status_var = tk.StringVar()
        ttk.Label(self.receive_frame, textvariable=self.receive_status_var, foreground='#555555').grid(
            row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Configure grid expansion
        self.receive_frame.columnconfigure(1, weight=1)
        self.receive_frame.rowconfigure(3, weight=1)

    #In a certain window showing other frames
    def show_login_frame(self):
        """Show the login frame and hide others"""
        self.send_frame.grid_forget()
        self.receive_frame.grid_forget()
        self.login_frame.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def show_send_frame(self):
        """Show the send email frame and hide others"""
        self.login_frame.grid_forget()
        self.receive_frame.grid_forget()
        self.send_frame.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def show_receive_frame(self):
        """Show the receive email frame and hide others"""
        self.login_frame.grid_forget()
        self.send_frame.grid_forget()
        self.receive_frame.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    #Email validation using build in lib
    def validate_email(self, email):
        """Validate email format"""
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True
        return False
 
    #Credintials
    def login(self):
        """Handle login process"""
        username = self.username.get()
        password = self.password.get()
        provider = self.selected_provider.get()
        display_name = self.display_name.get()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter your email and password.")
            return
        
        if not self.validate_email(username):
            messagebox.showerror("Login Error", "Please enter a valid email address.")
            return
        
        if not display_name:
            # Use username as display name if not provided
            self.display_name.set(username.split('@')[0])
        
        # Show a loading message
        self.root.config(cursor="wait")
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Connecting")
        loading_window.geometry("300x100")
        ttk.Label(loading_window, text="Connecting to email server...", padding=20).pack()
        
        # Start login process in a separate thread
        threading.Thread(target=self._login_thread, args=(username, password, provider, loading_window)).start()
    
    #Threading for error handling and establishin connection 
    def _login_thread(self, username, password, provider, loading_window):
        """Login process in a separate thread"""
        try:
            #Send_mail and Recieve file variables are called here
            # Update global variables in mail modules
            send_mail.username = username
            send_mail.password = password
            send_mail.name = self.display_name.get()
            
            recieve.username = username
            recieve.password = password
            recieve.host = self.email_configs[provider]['imap_host']
            
            # Test connection to SMTP server
            import smtplib
            import ssl
            
            # Try to connect to SMTP server
            server = smtplib.SMTP(self.email_configs[provider]['smtp_host'], 
                                 self.email_configs[provider]['smtp_port'])
            server.ehlo()
            ssl_context = ssl.create_default_context()
            server.starttls(context=ssl_context)
            server.login(username, password)
            server.quit()
            
            # If we get here, login was successful
            self.task_queue.put((self._login_success, (loading_window,), {}))
        except Exception as e:
            # Login failed
            self.task_queue.put((self._login_failed, (loading_window, str(e)), {}))
    
    def _login_success(self, loading_window):
        """Handle successful login"""
        loading_window.destroy()
        self.root.config(cursor="")
        
        # Save user to database
        self.current_user_id = self.db_manager.add_user(
            self.username.get(),
            self.display_name.get(),
            self.selected_provider.get()
        )
        
        self.show_send_frame()

    
    def _login_failed(self, loading_window, error_msg):
        """Handle failed login"""
        loading_window.destroy()
        self.root.config(cursor="")
        
        if "Authentication" in error_msg:
            messagebox.showerror("Login Error", "Username or password incorrect.")
        else:
            messagebox.showerror("Connection Error", 
                               f"Could not connect to email server.\n\nError: {error_msg}")
    
    def logout(self):
        """Handle logout"""
        # Clear sensitive data
        self.password.set("")
        self.recipient_list = []
        self.attachment_list = []
        self.subject.set("")
        if self.message_text:
            self.message_text.delete(1.0, tk.END)
        
        # Clear displays
        self.update_recipients_display()
        self.update_attachments_display()
        
        # Go back to login screen
        self.show_login_frame()

    #Sending Frame remove or add recipient box
    def add_recipient(self):
        """Add recipient to the list"""
        recipient = self.recipient_entry.get().strip()
        if not recipient:
            return
        
        # Validate email
        if not self.validate_email(recipient):
            messagebox.showerror("Invalid Email", f"'{recipient}' is not a valid email address.")
            return
        
        # Check if already in the list
        if recipient in self.recipient_list:
            messagebox.showinfo("Duplicate", f"'{recipient}' is already in the recipient list.")
            return
        
        # Add to list and update display
        self.recipient_list.append(recipient)
        self.recipient_entry.delete(0, tk.END)
        self.update_recipients_display()
    
    def remove_recipient(self):
        """Remove a selected recipient"""
        if not self.recipient_list:
            messagebox.showinfo("No Recipients", "There are no recipients to remove.")
            return
        
        # Create a dialog to select a recipient to remove
        remove_window = tk.Toplevel(self.root)
        remove_window.title("Remove Recipient")
        remove_window.geometry("400x250")
        remove_window.resizable(False, False)
        
        # Make window modal
        remove_window.transient(self.root)
        remove_window.grab_set()
        
        ttk.Label(remove_window, text="Select a recipient to remove:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Create a listbox for selection with scrollbar
        frame = ttk.Frame(remove_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        select_listbox = tk.Listbox(frame, width=40, height=8, font=('Arial', 10))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=select_listbox.yview)
        select_listbox.config(yscrollcommand=scrollbar.set)
        
        select_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Fill the listbox with recipients
        for recipient in self.recipient_list:
            select_listbox.insert(tk.END, recipient)
        
        # Select the first item by default if there are recipients
        if self.recipient_list:
            select_listbox.select_set(0)
            select_listbox.activate(0)
            select_listbox.see(0)
        
        # Add removal button
        def do_remove():
            # Get selected index
            selection = select_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a recipient to remove.")
                return
            
            # Get index and remove from list
            index = selection[0]
            if 0 <= index < len(self.recipient_list):
                removed = self.recipient_list.pop(index)
                self.update_recipients_display()
                remove_window.destroy()
                messagebox.showinfo("Recipient Removed", f"Removed '{removed}' from recipients.")
        
        button_frame = ttk.Frame(remove_window)
        button_frame.pack(pady=10, fill=tk.X, padx=10)
        
        ttk.Button(button_frame, text="Remove", command=do_remove, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=remove_window.destroy, width=15).pack(side=tk.RIGHT, padx=10)
        
        # Center the window on screen
        remove_window.update_idletasks()
        width = remove_window.winfo_width()
        height = remove_window.winfo_height()
        x = (remove_window.winfo_screenwidth() // 2) - (width // 2)
        y = (remove_window.winfo_screenheight() // 2) - (height // 2)
        remove_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Focus on the listbox
        select_listbox.focus_set()
        
        # Wait for window to close
        self.root.wait_window(remove_window)

    def clear_recipients(self):
        """Clear all recipients"""
        if not self.recipient_list:
            return
            
        if messagebox.askyesno("Confirm", "Remove all recipients?"):
            self.recipient_list = []
            self.update_recipients_display()

    def update_recipients_display(self):
        """Update the recipients display text area"""
        # Enable editing temporarily
        self.recipients_display.config(state=tk.NORMAL)
        
        # Clear current content
        self.recipients_display.delete(1.0, tk.END)
        
        # Add all recipients
        for recipient in self.recipient_list:
            self.recipients_display.insert(tk.END, f"{recipient}\n")
        
        # Disable editing again
        self.recipients_display.config(state=tk.DISABLED)
        
        # Update the UI state based on whether there are recipients
        if self.recipient_list:
            # If there are recipients, enable the management buttons
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Button) and child.cget("text") in ["Remove", "Clear All"]:
                    child.configure(state=tk.NORMAL)
        else:
            # If no recipients, disable the management buttons
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Button) and child.cget("text") in ["Remove", "Clear All"]:
                    child.configure(state=tk.DISABLED)
    #Attachments
    def add_attachments(self):
        """Add file attachments"""
        filepaths = filedialog.askopenfilenames(
            title="Select Files to Attach",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Images", "*.jpg *.jpeg *.png *.gif"),
                ("Documents", "*.pdf *.doc *.docx"),
                ("Code Files", "*.py *.js *.html *.css *.java *.cpp *.c *.h")
            ]
        )
        
        if not filepaths:
            return
        
        # Add selected files to attachment list
        for filepath in filepaths:
            if filepath not in self.attachment_list:
                self.attachment_list.append(filepath)
        
        # Update display
        self.update_attachments_display()
    
    def remove_attachment(self):
        """Remove a selected attachment"""
        if not self.attachment_list:
            messagebox.showinfo("No Attachments", "There are no attachments to remove.")
            return
        
        # Create a dialog to select an attachment to remove
        remove_window = tk.Toplevel(self.root)
        remove_window.title("Remove Attachment")
        remove_window.geometry("500x300")
        remove_window.resizable(False, False)
        
        # Make window modal
        remove_window.transient(self.root)
        remove_window.grab_set()
        
        ttk.Label(remove_window, text="Select an attachment to remove:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Create a listbox for selection with scrollbar
        frame = ttk.Frame(remove_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        select_listbox = tk.Listbox(frame, width=60, height=10, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=select_listbox.yview)
        select_listbox.config(yscrollcommand=scrollbar.set)
        
        select_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Fill the listbox with attachments
        for filepath in self.attachment_list:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath) / 1024  # KB
            if filesize < 1000:
                size_str = f"{filesize:.1f} KB"
            else:
                size_str = f"{filesize/1024:.1f} MB"
            select_listbox.insert(tk.END, f"{filename} ({size_str})")
        
        # Select the first item by default
        if self.attachment_list:
            select_listbox.select_set(0)
            select_listbox.activate(0)
            select_listbox.see(0)
        
        # Add removal button
        def do_remove():
            # Get selected index
            selection = select_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select an attachment to remove.")
                return
            
            # Get index and remove from list
            index = selection[0]
            if 0 <= index < len(self.attachment_list):
                removed = os.path.basename(self.attachment_list.pop(index))
                self.update_attachments_display()
                remove_window.destroy()
                messagebox.showinfo("Attachment Removed", f"Removed '{removed}' from attachments.")
        
        button_frame = ttk.Frame(remove_window)
        button_frame.pack(pady=10, fill=tk.X, padx=10)
        
        ttk.Button(button_frame, text="Remove", command=do_remove, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=remove_window.destroy, width=15).pack(side=tk.RIGHT, padx=10)
        
        # Center the window
        remove_window.update_idletasks()
        width = remove_window.winfo_width()
        height = remove_window.winfo_height()
        x = (remove_window.winfo_screenwidth() // 2) - (width // 2)
        y = (remove_window.winfo_screenheight() // 2) - (height // 2)
        remove_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Focus on the listbox
        select_listbox.focus_set()
        
        # Wait for window to close
        self.root.wait_window(remove_window)
    
    def clear_attachments(self):
        """Clear all attachments"""
        if not self.attachment_list:
            return
            
        if messagebox.askyesno("Confirm", "Remove all attachments?"):
            self.attachment_list = []
            self.update_attachments_display()
    
    def update_attachments_display(self):
        """Update the attachments display text area"""
        self.attachments_display.config(state=tk.NORMAL)
        self.attachments_display.delete(1.0, tk.END)
        
        for filepath in self.attachment_list:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath) / 1024  # KB
            if filesize < 1000:
                size_str = f"{filesize:.1f} KB"
            else:
                size_str = f"{filesize/1024:.1f} MB"
            
            self.attachments_display.insert(tk.END, f"{filename} ({size_str})\n")
        
        self.attachments_display.config(state=tk.DISABLED)
    
    #Selecting either plain text or html
    def toggle_message_mode(self):
        """Toggle between plain text and HTML mode"""
        is_html = self.html_mode.get()
        if is_html:
            # Give a hint for HTML mode
            if not self.message_text.get(1.0, tk.END).strip():
                self.message_text.insert(1.0, "<!DOCTYPE html>\n<html>\n<head>\n</head>\n<body>\n  <p>Your message here</p>\n</body>\n</html>")
        else:
            # If switching back to plain text, strip HTML if it looks like HTML
            current_text = self.message_text.get(1.0, tk.END).strip()
            if current_text.startswith("<!DOCTYPE html>") or current_text.startswith("<html"):
                # This is just a simple example - real HTML parsing would be more complex
                self.message_text.delete(1.0, tk.END)
    
    #Errors if no then send email button
    def send_email(self):
        """Send the email with attachments"""
        # Check if we have recipients
        if not self.recipient_list:
            messagebox.showerror("Error", "Please add at least one recipient.")
            return
        
        # Get subject and message
        subject = self.subject.get()
        if not subject:
            if not messagebox.askyesno("No Subject", "Send email without a subject?"):
                return
        
        message = self.message_text.get(1.0, tk.END).strip()
        if not message:
            if not messagebox.askyesno("Empty Message", "Send email with an empty message?"):
                return
        
        # Determine if we're sending HTML
        html_content = None
        if self.html_mode.get():
            html_content = message
            # For plain text part when HTML is used
            # Simple HTML to text conversion for demonstration
            plain_text = message.replace('<p>', '').replace('</p>', '\n\n')
            plain_text = re.sub(r'<[^>]*>', '', plain_text)
            message = plain_text
        
        # Start sending in a separate thread
        self.send_status_var.set("Sending email...")
        self.root.config(cursor="wait")
        
        threading.Thread(
            target=self._send_email_thread, 
            args=(subject, message, html_content, self.attachment_list.copy(), self.recipient_list.copy())
        ).start()
    
    #Uses our send_mail function
    def _send_email_thread(self, subject, text, html, files, recipients):
        """Send email in a separate thread"""
        try:
            # Use our send_mail module
            from_email = f"{send_mail.name}<{send_mail.username}>"
            
            send_mail.send_mail(
                text=text,
                subject=subject,
                from_email=from_email,
                to_emails=recipients,
                html=html,
                files=files if files else None
            )
            
            # If successful
            self.task_queue.put((self._send_success, (), {}))
        except Exception as e:
            # If failed
            self.task_queue.put((self._send_error, (str(e),), {}))
    #Sent
    def _send_success(self):
        """Handle successful email sending"""
        self.root.config(cursor="")
         # Save to database if connected
        if hasattr(self, 'current_user_id') and self.current_user_id:
            email_id = self.db_manager.save_sent_email(
                self.current_user_id,
                self.subject.get(),
                f"{self.display_name.get()} <{self.username.get()}>",
                self.recipient_list,
                self.message_text.get(1.0, tk.END),
                html_body=self.message_text.get(1.0, tk.END) if self.html_mode.get() else None,
                attachments=self.attachment_list
            )
        
        self.send_status_var.set("Email sent successfully!")
        
        # Clear the form for next email
        self.subject.set("")
        self.message_text.delete(1.0, tk.END)
        self.html_mode.set(False)
        self.attachment_list = []
        self.update_attachments_display()

    def _send_error(self, error_msg):
        """Handle email sending error"""
        self.root.config(cursor="")
        self.send_status_var.set("")
        messagebox.showerror("Sending Failed", f"Could not send email.\n\nError: {error_msg}")
    #Reciever Side of work in reciever frame
    def check_emails(self):
        """Check for new emails"""
        self.receive_status_var.set("Checking for new emails...")
        self.root.config(cursor="wait")
        
        # Start checking in a separate thread
        threading.Thread(target=self._check_emails_thread).start()
    #Uses our own recieve function
    def _check_emails_thread(self):
        """Check emails in a separate thread"""
        try:
            # Use our receive module
            emails = recieve.recieve_mail(save_attachments=True, save_content=True)
            
            # Update UI with results
            self.task_queue.put((self._display_emails, (emails,), {}))
        except Exception as e:
            self.task_queue.put((self._receive_error, (str(e),), {}))
    
    #Displaying and saving recieved emails
    def _display_emails(self, emails):
        """Display received emails in the UI"""
        self.root.config(cursor="")
        
        # Save to database if connected
        if hasattr(self, 'current_user_id') and self.current_user_id and emails:
            self.db_manager.save_received_emails(self.current_user_id, emails)
        
        # Clear previous emails
        for widget in self.email_list_frame.winfo_children():
            widget.destroy()
        
        if not emails:
            self.receive_status_var.set("No new emails found.")
            return
        
        self.receive_status_var.set(f"Found {len(emails)} new email(s).")
        
        # Create a scrollable frame for emails
        canvas = tk.Canvas(self.email_list_frame)
        scrollbar = ttk.Scrollbar(self.email_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add each email as a selectable item
        for i, email_data in enumerate(emails):
            email_frame = ttk.Frame(scrollable_frame, padding=5)
            email_frame.pack(fill="x", expand=True, pady=5)
            
            # Add a border
            email_frame.configure(style='TFrame', borderwidth=1, relief="solid")
            
            # Basic email info
            from_text = email_data.get('from', 'Unknown Sender')
            subject_text = email_data.get('subject', 'No Subject')
            date_text = email_data.get('date', 'Unknown Date')
            
            # Email number (from IMAP)
            email_number = str(i + 1)  # Default to index + 1 if not available
            
            # Header with email number, from and subject
            header_frame = ttk.Frame(email_frame)
            header_frame.pack(fill="x", expand=True)
            
            # Number badge
            number_label = ttk.Label(
                header_frame, 
                text=f"#{email_number}", 
                font=('Arial', 10, 'bold'),
                background='#007bff',
                foreground='white',
                padding=(5, 2)
            )
            number_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Info panel
            info_frame = ttk.Frame(header_frame)
            info_frame.pack(side=tk.LEFT, fill="x", expand=True)
            
            ttk.Label(info_frame, text=f"From: {from_text}", font=('Arial', 10, 'bold')).pack(anchor="w")
            ttk.Label(info_frame, text=f"Subject: {subject_text}").pack(anchor="w")
            ttk.Label(info_frame, text=f"Date: {date_text}", font=('Arial', 9)).pack(anchor="w")
            
            # Preview of body (if available)
            if 'body' in email_data:
                preview_text = email_data['body'][:100] + "..." if len(email_data['body']) > 100 else email_data['body']
                ttk.Label(email_frame, text=f"Preview: {preview_text}", wraplength=600).pack(anchor="w", pady=(5, 0))
            
            # Quick info about attachments
            attachment_count = len(email_data.get('attachments', []))
            content_files_count = len(email_data.get('content_files', []))
            
            if attachment_count > 0 or content_files_count > 0:
                files_info = []
                if attachment_count > 0:
                    files_info.append(f"{attachment_count} attachment(s)")
                if content_files_count > 0:
                    files_info.append(f"{content_files_count} content file(s)")
                
                attachments_label = ttk.Label(
                    email_frame, 
                    text="Files: " + ", ".join(files_info),
                    foreground="blue"
                )
                attachments_label.pack(anchor="w", pady=(5, 0))
            
            # Button to view detailed email
            view_btn = ttk.Button(
                email_frame,
                text="View Email",
                command=lambda data=email_data, idx=i: self.show_email_details(data, idx)
            )
            view_btn.pack(anchor="w", pady=(5, 0))
            
            # Add separator
            ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=5)
    #New window select email you want to see
    """BIG note
          THIS IS USING IMAP HENCE IF YOU MOVE OUT NO NEW EMAILS 
          WOULD THINK ITS SEEN
    """
    def show_email_details(self, email_data, email_index):
        """Show detailed view of an email in a new window"""
        # Create a new window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Email #{email_index + 1}: {email_data.get('subject', 'No Subject')}")
        detail_window.geometry("800x600")
        detail_window.minsize(800, 600)
        
        # Main frame with padding
        main_frame = ttk.Frame(detail_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Email header info section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", expand=False, pady=(0, 15))
        
        # Subject with larger font
        subject_text = email_data.get('subject', 'No Subject')
        subject_label = ttk.Label(header_frame, text=subject_text, font=('Arial', 14, 'bold'))
        subject_label.pack(anchor="w", pady=(0, 10))
        
        # From, To, Date in a grid
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(fill="x", expand=False)
        
        # From
        ttk.Label(info_frame, text="From:", width=10, font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=email_data.get('from', 'Unknown')).grid(row=0, column=1, sticky="w", pady=2)
        
        # To
        ttk.Label(info_frame, text="To:", width=10, font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=email_data.get('to', 'Unknown')).grid(row=1, column=1, sticky="w", pady=2)
        
        # Date
        ttk.Label(info_frame, text="Date:", width=10, font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=email_data.get('date', 'Unknown')).grid(row=2, column=1, sticky="w", pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Action buttons at the top (before notebook)
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.pack(fill="x", pady=(0, 10))
        
        # Reply button
        ttk.Button(
            action_button_frame,
            text="Reply",
            command=lambda: self.reply_to_email(email_data, detail_window)
        ).pack(side=tk.LEFT, padx=5)
        
        # Forward button
        ttk.Button(
            action_button_frame,
            text="Forward",
            command=lambda: self.forward_email(email_data, detail_window)
        ).pack(side=tk.LEFT, padx=5)
        
        # Print email button
        ttk.Button(
            action_button_frame,
            text="Print",
            command=lambda: self.print_email(email_data)
        ).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for different content views
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab for message body
        if 'body' in email_data or 'html_body' in email_data:
            body_frame = ttk.Frame(notebook, padding=10)
            notebook.add(body_frame, text="Message")
            
            # Text widget for body with scrollbar
            body_text = scrolledtext.ScrolledText(body_frame, wrap=tk.WORD)
            body_text.pack(fill="both", expand=True)
            
            # Insert plain text or HTML content
            if 'html_body' in email_data:
                # For simplicity, just show HTML source
                # In a real app, you might want to use a HTML renderer
                body_text.insert(tk.END, "HTML Content:\n\n")
                body_text.insert(tk.END, email_data['html_body'])
            elif 'body' in email_data:
                body_text.insert(tk.END, email_data['body'])
            
            body_text.config(state=tk.DISABLED)  # Make read-only
        
        # Tab for attachments if any
        attachments = email_data.get('attachments', [])
        content_files = email_data.get('content_files', [])
        
        if attachments or content_files:
            files_frame = ttk.Frame(notebook, padding=10)
            notebook.add(files_frame, text=f"Files ({len(attachments) + len(content_files)})")
            
            # Create a scrollable frame for files
            canvas = tk.Canvas(files_frame)
            scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=canvas.yview)
            scrollable_files_frame = ttk.Frame(canvas)
            
            scrollable_files_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_files_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Counters for file types
            code_files = 0
            image_files = 0
            audio_files = 0
            video_files = 0
            document_files = 0
            other_files = 0
            
            # Function to identify file type
            def get_file_type(file_info):
                file_type = file_info.get('type', '')
                is_code = file_info.get('is_code', False)
                
                if is_code or file_type.startswith('text/x-') or file_type in ['application/javascript', 'text/css', 'text/html', 'application/json']:
                    return 'code'
                elif file_type.startswith('image/'):
                    return 'image'
                elif file_type.startswith('audio/'):
                    return 'audio'
                elif file_type.startswith('video/'):
                    return 'video'
                elif file_type in ['application/pdf', 'application/msword', 'application/vnd.ms-excel']:
                    return 'document'
                else:
                    return 'other'
            
            # Header for files section
            ttk.Label(scrollable_files_frame, text="Attachments:", font=('Arial', 12, 'bold')).grid(
                row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
            
            # Column headers
            ttk.Label(scrollable_files_frame, text="Filename", font=('Arial', 10, 'bold')).grid(
                row=1, column=0, sticky="w", padx=5)
            ttk.Label(scrollable_files_frame, text="Type", font=('Arial', 10, 'bold')).grid(
                row=1, column=1, sticky="w", padx=5)
            ttk.Label(scrollable_files_frame, text="Size", font=('Arial', 10, 'bold')).grid(
                row=1, column=2, sticky="w", padx=5)
            ttk.Label(scrollable_files_frame, text="Actions", font=('Arial', 10, 'bold')).grid(
                row=1, column=3, sticky="w", padx=5)
            
            # Add separator below headers
            ttk.Separator(scrollable_files_frame, orient="horizontal").grid(
                row=2, column=0, columnspan=4, sticky="ew", pady=5)
            
            # Combine attachments and content_files for display
            all_files = []
            
            # Process attachments
            for attachment in attachments:
                file_type = get_file_type(attachment)
                
                # Update counters
                if file_type == 'code':
                    code_files += 1
                elif file_type == 'image':
                    image_files += 1
                elif file_type == 'audio':
                    audio_files += 1
                elif file_type == 'video':
                    video_files += 1
                elif file_type == 'document':
                    document_files += 1
                else:
                    other_files += 1
                
                all_files.append({
                    'filename': attachment.get('filename', 'Unnamed'),
                    'path': attachment.get('path', ''),
                    'type': file_type,
                    'mime_type': attachment.get('type', 'Unknown')
                })
            
            # Process content files
            for content_file in content_files:
                file_type = get_file_type(content_file)
                
                # Update counters
                if file_type == 'code':
                    code_files += 1
                elif file_type == 'image':
                    image_files += 1
                elif file_type == 'audio':
                    audio_files += 1
                elif file_type == 'video':
                    video_files += 1
                elif file_type == 'document':
                    document_files += 1
                else:
                    other_files += 1
                
                all_files.append({
                    'filename': content_file.get('filename', 'Unnamed'),
                    'path': content_file.get('path', ''),
                    'type': file_type,
                    'mime_type': content_file.get('type', 'Unknown')
                })
            
            # Display files
            for i, file_info in enumerate(all_files):
                row_index = i + 3  # Start after headers and separator
                
                # Filename
                ttk.Label(scrollable_files_frame, text=file_info['filename']).grid(
                    row=row_index, column=0, sticky="w", padx=5, pady=2)
                
                # Type with color coding
                type_colors = {
                    'code': '#007bff',  # Blue
                    'image': '#28a745',  # Green
                    'audio': '#fd7e14',  # Orange
                    'video': '#dc3545',  # Red
                    'document': '#6f42c1',  # Purple
                    'other': '#6c757d'   # Gray
                }
                
                type_label = ttk.Label(
                    scrollable_files_frame, 
                    text=file_info['type'].capitalize(),
                    foreground=type_colors.get(file_info['type'], 'black')
                )
                type_label.grid(row=row_index, column=1, sticky="w", padx=5, pady=2)
                
                # File size
                file_path = file_info['path']
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024:
                        size_text = f"{file_size} bytes"
                    elif file_size < 1024 * 1024:
                        size_text = f"{file_size/1024:.1f} KB"
                    else:
                        size_text = f"{file_size/(1024*1024):.1f} MB"
                else:
                    size_text = "Unknown"
                
                ttk.Label(scrollable_files_frame, text=size_text).grid(
                    row=row_index, column=2, sticky="w", padx=5, pady=2)
                
                # Actions buttons
                action_frame = ttk.Frame(scrollable_files_frame)
                action_frame.grid(row=row_index, column=3, sticky="w", padx=5, pady=2)
                
                # Open file button
                if os.path.exists(file_path):
                    ttk.Button(
                        action_frame,
                        text="Open",
                        command=lambda path=file_path: os.startfile(path)
                    ).pack(side=tk.LEFT, padx=2)
                
                    # Open containing folder button
                    ttk.Button(
                        action_frame,
                        text="Show in Folder",
                        command=lambda path=file_path: os.startfile(os.path.dirname(path))
                    ).pack(side=tk.LEFT, padx=2)
            
            # Summary section at the top of the files tab
            summary_frame = ttk.Frame(scrollable_files_frame)
            summary_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 15))
            
            summary_text = f"Total: {len(all_files)} file(s)"
            if code_files > 0:
                summary_text += f" • Code: {code_files}"
            if image_files > 0:
                summary_text += f" • Images: {image_files}"
            if audio_files > 0:
                summary_text += f" • Audio: {audio_files}"
            if video_files > 0:
                summary_text += f" • Video: {video_files}"
            if document_files > 0:
                summary_text += f" • Documents: {document_files}"
            if other_files > 0:
                summary_text += f" • Other: {other_files}"
            
            ttk.Label(summary_frame, text=summary_text).pack(anchor="w")
            
            # If we have a folder path, add a button to open it
            if 'email_folder' in email_data:
                folder_path = email_data['email_folder']
                ttk.Button(
                    summary_frame,
                    text="Open All Files Folder",
                    command=lambda path=folder_path: os.startfile(path)
                ).pack(anchor="w", pady=(5, 0))
        
        # Close button at the bottom
        ttk.Button(
            main_frame, 
            text="Close", 
            command=detail_window.destroy
        ).pack(pady=(10, 0))
        
        # Center the window on screen
        detail_window.update_idletasks()
        width = detail_window.winfo_width()
        height = detail_window.winfo_height()
        x = (detail_window.winfo_screenwidth() // 2) - (width // 2)
        y = (detail_window.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def reply_to_email(self, email_data, detail_window=None):
        """Open compose window pre-filled for reply"""
        try:
            # Close detail window if provided
            if detail_window:
                detail_window.destroy()
            
            # Switch to compose view
            self.show_send_frame()
            
            # Force UI update
            self.root.update_idletasks()
            
            # Get sender's email from 'from' field
            from_field = email_data.get('from', '')
            sender_email = ''
            
            # Extract email from format like "Name <email@example.com>"
            if '<' in from_field and '>' in from_field:
                sender_email = from_field.split('<')[1].split('>')[0]
            else:
                sender_email = from_field
            
            # Add to recipient list if not already there
            if sender_email and sender_email not in self.recipient_list:
                self.recipient_list.append(sender_email)
                self.update_recipients_display()
            
            # Set subject with Re: prefix if not already there
            original_subject = email_data.get('subject', '')
            if original_subject:
                if not original_subject.lower().startswith('re:'):
                    reply_subject = f"Re: {original_subject}"
                else:
                    reply_subject = original_subject
                self.subject.set(reply_subject)
            
            # Create reply template in message body
            original_body = email_data.get('body', '')
            date_str = email_data.get('date', '')
            from_str = email_data.get('from', '')
            
            reply_template = f"\n\n-------- Original Message --------\n"
            reply_template += f"From: {from_str}\n"
            reply_template += f"Date: {date_str}\n"
            reply_template += f"Subject: {original_subject}\n\n"
            
            # Add quoted original message
            quoted_body = ""
            for line in original_body.split('\n'):
                quoted_body += f"> {line}\n"
            
            reply_template += quoted_body
            
            # Set message text
            self.message_text.delete(1.0, tk.END)
            self.message_text.insert(1.0, reply_template)
            
            # Position cursor at top for reply
            self.message_text.mark_set(tk.INSERT, "1.0")
            self.message_text.focus()
        except Exception as e:
            messagebox.showerror("Reply Error", f"Could not prepare reply: {str(e)}")

    def forward_email(self, email_data, detail_window=None):
        """Open compose window pre-filled for forward"""
        try:
            # Close detail window if provided
            if detail_window:
                detail_window.destroy()
            
            # Switch to compose view
            self.show_send_frame()
            
            # Force UI update
            self.root.update_idletasks()
            
            # Clear recipients
            self.recipient_list = []
            self.update_recipients_display()
            
            # Set subject with Fwd: prefix if not already there
            original_subject = email_data.get('subject', '')
            if original_subject:
                if not original_subject.lower().startswith('fwd:'):
                    forward_subject = f"Fwd: {original_subject}"
                else:
                    forward_subject = original_subject
                self.subject.set(forward_subject)
            
            # Create forward template in message body
            original_body = email_data.get('body', '')
            date_str = email_data.get('date', '')
            from_str = email_data.get('from', '')
            to_str = email_data.get('to', '')
            
            forward_template = f"\n\n-------- Forwarded Message --------\n"
            forward_template += f"From: {from_str}\n"
            forward_template += f"Date: {date_str}\n"
            forward_template += f"Subject: {original_subject}\n"
            forward_template += f"To: {to_str}\n\n"
            forward_template += original_body
            
            # Set message text
            self.message_text.delete(1.0, tk.END)
            self.message_text.insert(1.0, forward_template)
            
            # Position cursor at top for adding message
            self.message_text.mark_set(tk.INSERT, "1.0")
            self.message_text.focus()
            
            # Handle attachments if any
            attachments = email_data.get('attachments', [])
            for attachment in attachments:
                file_path = attachment.get('path', '')
                if file_path and os.path.exists(file_path):
                    if file_path not in self.attachment_list:
                        self.attachment_list.append(file_path)
            
            # Update attachments display
            self.update_attachments_display()
        except Exception as e:
            messagebox.showerror("Forward Error", f"Could not prepare forward: {str(e)}")
    
    def print_email(self, email_data):
        """Print email contents (simplified implementation)"""
        try:
            # Create a print folder if it doesn't exist
            print_folder = os.path.join(os.path.expanduser("~"), "Downloads", "EmailPrints")
            if not os.path.exists(print_folder):
                os.makedirs(print_folder)
            
            # Create a descriptive filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subject = email_data.get('subject', 'No_Subject')
            # Clean subject for filename (remove invalid chars)
            safe_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)[:50]
            filename = f"Email_{safe_subject}_{timestamp}.txt"
            file_path = os.path.join(print_folder, filename)
            
            # Write email content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write email details to file
                f.write(f"Subject: {email_data.get('subject', '')}\n")
                f.write(f"From: {email_data.get('from', '')}\n")
                f.write(f"To: {email_data.get('to', '')}\n")
                f.write(f"Date: {email_data.get('date', '')}\n")
                f.write("\n" + "="*50 + "\n\n")
                
                # Write body
                if 'body' in email_data:
                    f.write(email_data['body'])
                elif 'html_body' in email_data:
                    # Simple HTML to text conversion
                    html_content = email_data['html_body']
                    plain_text = html_content.replace('<p>', '').replace('</p>', '\n\n')
                    plain_text = re.sub(r'<[^>]*>', '', plain_text)
                    f.write(plain_text)
                
                # List attachments
                attachments = email_data.get('attachments', [])
                content_files = email_data.get('content_files', [])
                
                if attachments or content_files:
                    f.write("\n\n" + "="*50 + "\n")
                    f.write("\nAttachments:\n")
                    
                    for i, attachment in enumerate(attachments):
                        f.write(f"{i+1}. {attachment.get('filename', 'unnamed')}\n")
                    
                    for i, content_file in enumerate(content_files, start=len(attachments)+1):
                        f.write(f"{i}. {content_file.get('filename', 'unnamed')}\n")
            
            # Open the file with the default text editor for printing
            os.startfile(file_path, 'print')
            
            # Show success message with file location
            messagebox.showinfo("Print Ready", 
                              f"Print file created and opened.\n\nFile saved to:\n{file_path}\n\nYou can print now or find the file later in:\n{print_folder}")
            
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print email: {str(e)}")
    
    def _receive_error(self, error_msg):
        """Handle email receiving error"""
        self.root.config(cursor="")
        self.receive_status_var.set("")
        messagebox.showerror("Error", f"Could not receive emails.\n\nError: {error_msg}")
    
    #Even if send 0 files 1 will be attached
    def save_email_as_text(self, email_data):
        """Save email contents to a text file"""
        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{email_data.get('subject', 'email').replace(':', '-')}.txt"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write email details to file
                f.write(f"Subject: {email_data.get('subject', '')}\n")
                f.write(f"From: {email_data.get('from', '')}\n")
                f.write(f"To: {email_data.get('to', '')}\n")
                f.write(f"Date: {email_data.get('date', '')}\n")
                f.write("\n" + "="*50 + "\n\n")
                
                # Write body
                if 'body' in email_data:
                    f.write(email_data['body'])
                elif 'html_body' in email_data:
                    # Simple HTML to text conversion
                    html_content = email_data['html_body']
                    plain_text = html_content.replace('<p>', '').replace('</p>', '\n\n')
                    plain_text = re.sub(r'<[^>]*>', '', plain_text)
                    f.write(plain_text)
                
                # List attachments
                attachments = email_data.get('attachments', [])
                content_files = email_data.get('content_files', [])
                
                if attachments or content_files:
                    f.write("\n\n" + "="*50 + "\n")
                    f.write("\nAttachments:\n")
                    
                    for i, attachment in enumerate(attachments):
                        f.write(f"{i+1}. {attachment.get('filename', 'unnamed')}\n")
                    
                    for i, content_file in enumerate(content_files, start=len(attachments)+1):
                        f.write(f"{i}. {content_file.get('filename', 'unnamed')}\n")
            
            messagebox.showinfo("Save Complete", f"Email saved successfully to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save email: {str(e)}")
    
    def send_code_snippet(self):
        """Open dialog to send a code snippet"""
        # Create a new window
        code_window = tk.Toplevel(self.root)
        code_window.title("Send Code Snippet")
        code_window.geometry("700x600")
        code_window.minsize(700, 600)
        
        # Main frame with padding
        main_frame = ttk.Frame(code_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_label = ttk.Label(main_frame, text="Send Code Snippet", style='Header.TLabel')
        header_label.pack(anchor="w", pady=(0, 15))
        
        # Store the loaded file path (for attachments)
        loaded_file_path = tk.StringVar(value="")
        
        # Language selection
        lang_frame = ttk.Frame(main_frame)
        lang_frame.pack(fill="x", expand=False, pady=(0, 10))
        
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=(0, 5))
        
        languages = ["Python", "JavaScript", "HTML", "CSS", "Java", "C++", "C#", "PHP", "SQL", "Ruby", "Go", "Swift", "Kotlin", "Bash", "PowerShell", "TypeScript", "Rust", "Other"]
        
        language_var = tk.StringVar(value=languages[0])
        language_combo = ttk.Combobox(lang_frame, textvariable=language_var, values=languages, state='readonly')
        language_combo.pack(side=tk.LEFT, padx=5)
        
        # Code input
        ttk.Label(main_frame, text="Code:").pack(anchor="w", pady=(10, 5))
        
        code_text = scrolledtext.ScrolledText(main_frame, height=15, width=80, wrap=tk.NONE, font=('Courier New', 10))
        code_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add horizontal scrollbar for code
        h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=code_text.xview)
        code_text.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(fill="x", expand=False, before=code_text)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill="x", expand=False, pady=10)
        
        # Checkbox for syntax highlighting
        highlight_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include syntax highlighting", variable=highlight_var).pack(anchor="w")
        
        # Checkbox for including as attachment
        attachment_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include as attachment", variable=attachment_var).pack(anchor="w")
        
        # Filename entry
        filename_frame = ttk.Frame(options_frame)
        filename_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Label(filename_frame, text="Filename:").pack(side=tk.LEFT, padx=(0, 5))
        
        filename_var = tk.StringVar(value="code_snippet.py")
        filename_entry = ttk.Entry(filename_frame, textvariable=filename_var, width=30)
        filename_entry.pack(side=tk.LEFT, fill="x", expand=True)
        
        # Update default extension when language changes
        def update_filename(*args):
            lang = language_var.get().lower()
            
            # Get file extension based on language
            ext = {
                'python': '.py',
                'javascript': '.js',
                'html': '.html',
                'css': '.css', 
                'java': '.java',
                'c++': '.cpp',
                'c#': '.cs',
                'php': '.php',
                'sql': '.sql',
                'ruby': '.rb',
                'go': '.go',
                'swift': '.swift',
                'kotlin': '.kt',
                'bash': '.sh',
                'powershell': '.ps1',
                'typescript': '.ts',
                'rust': '.rs',
                'other': '.txt'
            }.get(lang, '.txt')
            
            # Update filename but keep the name part
            current = filename_var.get()
            if '.' in current:
                name = current.split('.')[0]
                filename_var.set(f"{name}{ext}")
            else:
                filename_var.set(f"{current}{ext}")
        
        language_var.trace('w', update_filename)
        
        # Load from file button
        ttk.Button(
            main_frame,
            text="Load from File",
            command=lambda: self.load_code_from_file(code_text, language_var, filename_var, loaded_file_path)
        ).pack(side=tk.LEFT, pady=10)
        
        # Insert into Email button
        ttk.Button(
            main_frame,
            text="Insert into Email",
            command=lambda: self.insert_code_to_email(
                code_text.get(1.0, tk.END).strip(),
                language_var.get().lower(),
                highlight_var.get(),
                attachment_var.get(),
                filename_var.get(),
                code_window,
                loaded_file_path.get()
            )
        ).pack(side=tk.RIGHT, pady=10)
        
        # Cancel button
        ttk.Button(
            main_frame,
            text="Cancel",
            command=code_window.destroy
        ).pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Center the window
        code_window.update_idletasks()
        width = code_window.winfo_width()
        height = code_window.winfo_height()
        x = (code_window.winfo_screenwidth() // 2) - (width // 2)
        y = (code_window.winfo_screenheight() // 2) - (height // 2)
        code_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Set focus on code text area
        code_text.focus_set()
    
    def load_code_from_file(self, code_text, language_var, filename_var, loaded_file_path_var=None):
        """Load code from a file"""
        file_path = filedialog.askopenfilename(
            title="Select Code File",
            filetypes=[
                ("All Code Files", "*.py *.js *.html *.css *.java *.cpp *.h *.cs *.php *.sql *.rb *.go *.swift *.kt *.sh *.ps1 *.ts *.rs"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("Java Files", "*.java"),
                ("C++ Files", "*.cpp *.h"),
                ("C# Files", "*.cs"),
                ("PHP Files", "*.php"),
                ("SQL Files", "*.sql"),
                ("Ruby Files", "*.rb"),
                ("Go Files", "*.go"),
                ("Swift Files", "*.swift"),
                ("Kotlin Files", "*.kt"),
                ("Shell Scripts", "*.sh"),
                ("PowerShell Scripts", "*.ps1"),
                ("TypeScript Files", "*.ts"),
                ("Rust Files", "*.rs"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Try to guess language from file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            # Map extension to language
            lang_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.html': 'HTML',
                '.css': 'CSS',
                '.java': 'Java',
                '.cpp': 'C++',
                '.h': 'C++',
                '.cs': 'C#',
                '.php': 'PHP',
                '.sql': 'SQL',
                '.rb': 'Ruby',
                '.go': 'Go',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.sh': 'Bash',
                '.ps1': 'PowerShell',
                '.ts': 'TypeScript',
                '.rs': 'Rust'
            }
            
            if ext in lang_map:
                language_var.set(lang_map[ext])
            
            # Set the filename
            filename = os.path.basename(file_path)
            filename_var.set(filename)
            
            # Read file content - try multiple encodings
            code_content = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        code_content = f.read()
                    break  # Success, exit loop
                except (UnicodeDecodeError, UnicodeError):
                    continue  # Try next encoding
            
            # If all encodings failed, try binary mode with error handling
            if code_content is None:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code_content = f.read()
            
            # Insert into text area
            code_text.delete(1.0, tk.END)
            code_text.insert(1.0, code_content)
            
            # Store the file path for attachment
            if loaded_file_path_var is not None:
                loaded_file_path_var.set(file_path)
            
            messagebox.showinfo("Success", f"Loaded {len(code_content)} characters from {filename}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load file: {str(e)}")
    def insert_code_to_email(self, code, language, highlight, as_attachment, filename, window, loaded_file_path=""):
        """Insert code snippet into email compose window"""
        if not code.strip():
            messagebox.showerror("Error", "Please enter some code.")
            return
        
        # Switch to compose view if not already there
        self.show_send_frame()
        
        # If sending as HTML and syntax highlighting is enabled
        if self.html_mode.get() and highlight:
            # Use send_mail's helper function to create HTML with syntax highlighting
            html_code = send_mail.add_syntax_highlighting(code, language)
            
            # Insert at cursor position
            current_pos = self.message_text.index(tk.INSERT)
            self.message_text.insert(current_pos, html_code)
        else:
            # For plain text, just insert the code with simple formatting
            current_pos = self.message_text.index(tk.INSERT)
            
            # Add language info and code block formatting
            formatted_code = f"\n\n--- {language.upper()} CODE ---\n"
            formatted_code += code
            formatted_code += "\n--- END CODE ---\n\n"
            
            self.message_text.insert(current_pos, formatted_code)
        
        # Add as attachment if requested
        if as_attachment:
            try:
                # If file was loaded from disk, use the original file
                if loaded_file_path and os.path.exists(loaded_file_path):
                    file_path = loaded_file_path
                    # Add to attachment list
                    if file_path not in self.attachment_list:
                        self.attachment_list.append(file_path)
                        self.update_attachments_display()
                else:
                    # Create temporary file with the code
                    import tempfile
                    
                    fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[1])
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        f.write(code)
                    
                    # Create a copy with the desired filename in the same directory
                    user_path = os.path.join(os.path.dirname(temp_path), filename)
                    with open(user_path, 'w', encoding='utf-8') as f:
                        f.write(code)
                    
                    # Add to attachment list
                    if user_path not in self.attachment_list:
                        self.attachment_list.append(user_path)
                        self.update_attachments_display()
            except Exception as e:
                messagebox.showerror("Attachment Error", f"Could not create code attachment: {str(e)}")
        
        # Close the code snippet window
        window.destroy()
        
        # Focus on message text
        self.message_text.focus_set()
    #History
    def show_email_history(self):
        """Show email history for current user"""
        # Check if user is logged in and has ID
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showerror("Error", "Please login first to view history.")
            return
        
        # Create a new window
        history_window = tk.Toplevel(self.root)
        history_window.title("Email History")
        history_window.geometry("900x600")
        history_window.minsize(900, 600)
        
        # Main frame with padding
        main_frame = ttk.Frame(history_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_label = ttk.Label(main_frame, text="Email History", style='Header.TLabel')
        header_label.pack(anchor="w", pady=(0, 15))
        
        # Create filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        # Filter by sent/received
        filter_var = tk.StringVar(value="All")
        ttk.Label(filter_frame, text="Show:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(filter_frame, text="All", variable=filter_var, value="All", 
                    command=lambda: self.update_history_list(email_list, filter_var.get())).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Sent", variable=filter_var, value="Sent", 
                    command=lambda: self.update_history_list(email_list, filter_var.get())).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Received", variable=filter_var, value="Received", 
                    command=lambda: self.update_history_list(email_list, filter_var.get())).pack(side=tk.LEFT, padx=5)
        
        # Email list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Create columns
        columns = ("date", "type", "from", "to", "subject", "attachments")
        
        # Create treeview for emails
        email_list = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define column headings
        email_list.heading("date", text="Date")
        email_list.heading("type", text="Type")
        email_list.heading("from", text="From")
        email_list.heading("to", text="To")
        email_list.heading("subject", text="Subject")
        email_list.heading("attachments", text="Attachments")
        
        # Define column widths
        email_list.column("date", width=120)
        email_list.column("type", width=80)
        email_list.column("from", width=150)
        email_list.column("to", width=150)
        email_list.column("subject", width=200)
        email_list.column("attachments", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=email_list.yview)
        email_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack elements
        email_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event to open email details
        email_list.bind("<Double-1>", lambda event: self.show_history_email_details(email_list))
        
        # Status label
        status_var = tk.StringVar()
        status_label = ttk.Label(main_frame, textvariable=status_var)
        status_label.pack(fill="x", pady=(5, 0))
        
        # Buttons at bottom
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="Refresh", 
                command=lambda: self.update_history_list(email_list, filter_var.get())).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Close", command=history_window.destroy).pack(side=tk.RIGHT)
        
        # Load email history initially
        self.update_history_list(email_list, "All", status_var=status_var)
    
    #Update
    def update_history_list(self, treeview, filter_type, status_var=None):
        """Update email history list based on filter"""
        # Clear current items
        for item in treeview.get_children():
            treeview.delete(item)
        
        # Get emails from database
        emails = self.db_manager.get_email_history(self.current_user_id)
        
        if not emails:
            if status_var:
                status_var.set("No email history found for this account.")
            return
        
        # Filter emails if needed
        if filter_type == "Sent":
            emails = [email for email in emails if not email['received']]
        elif filter_type == "Received":
            emails = [email for email in emails if email['received']]
        
        # Add emails to treeview
        for email in emails:
            # Format date
            date_str = email['date'].strftime('%Y-%m-%d %H:%M')
            
            # Determine type
            email_type = "Received" if email['received'] else "Sent"
            
            # Get sender and recipients
            from_str = email['from']
            to_str = email['to']
            
            # Subject
            subject = email['subject'] or "(No Subject)"
            
            # Count attachments
            attachment_count = len(email['attachments'])
            attachment_str = f"{attachment_count} file(s)" if attachment_count > 0 else "None"
            
            # Add to treeview with email ID as the item ID
            treeview.insert("", "end", iid=str(email['id']), values=(
                date_str, email_type, from_str, to_str, subject, attachment_str
            ))
        
        # Update status if provided
        if status_var:
            status_var.set(f"Found {len(emails)} email(s)")

    def show_history_email_details(self, treeview):
        """Show details of selected email from history"""
        # Get selected item
        selection = treeview.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an email to view.")
            return
        
        # Get email ID from selection
        email_id = int(selection[0])
        
        # Fetch email details from database
        email_data = self.db_manager.get_email_details(email_id)
        
        if not email_data:
            messagebox.showerror("Error", "Could not retrieve email details.")
            return
        
        # Create a new window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Email: {email_data['subject']}")
        detail_window.geometry("800x600")
        detail_window.minsize(800, 600)
        
        # Main frame with padding
        main_frame = ttk.Frame(detail_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Email header info section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", expand=False, pady=(0, 15))
        
        # Subject with larger font
        subject_text = email_data.get('subject', 'No Subject')
        subject_label = ttk.Label(header_frame, text=subject_text, font=('Arial', 14, 'bold'))
        subject_label.pack(anchor="w", pady=(0, 10))
        
        # From, To, Date in a grid
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(fill="x", expand=False)
        
        # From
        ttk.Label(info_frame, text="From:", width=10, font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=email_data.get('from', 'Unknown')).grid(row=0, column=1, sticky="w", pady=2)
        
        # To
        ttk.Label(info_frame, text="To:", width=10, font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=email_data.get('to', 'Unknown')).grid(row=1, column=1, sticky="w", pady=2)
        
        # Date
        ttk.Label(info_frame, text="Date:", width=10, font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=2)
        date_str = email_data['date'].strftime('%Y-%m-%d %H:%M:%S') if email_data.get('date') else 'Unknown'
        ttk.Label(info_frame, text=date_str).grid(row=2, column=1, sticky="w", pady=2)
        
        # Type (Sent/Received)
        ttk.Label(info_frame, text="Type:", width=10, font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky="w", pady=2)
        email_type = "Received" if email_data.get('received', False) else "Sent"
        ttk.Label(info_frame, text=email_type).grid(row=3, column=1, sticky="w", pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Create notebook for different content views
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab for message body
        body_frame = ttk.Frame(notebook, padding=10)
        notebook.add(body_frame, text="Message")
        
        # Text widget for body with scrollbar
        body_text = scrolledtext.ScrolledText(body_frame, wrap=tk.WORD)
        body_text.pack(fill="both", expand=True)
        
        # Insert plain text or HTML content
        if email_data.get('html_body'):
            body_text.insert(tk.END, "HTML Content:\n\n")
            body_text.insert(tk.END, email_data['html_body'])
        elif email_data.get('body'):
            body_text.insert(tk.END, email_data['body'])
        else:
            body_text.insert(tk.END, "(No message content)")
        
        body_text.config(state=tk.DISABLED)  # Make read-only
        
        # Tab for attachments if any
        attachments = email_data.get('attachments', [])
        if attachments:
            files_frame = ttk.Frame(notebook, padding=10)
            notebook.add(files_frame, text=f"Attachments ({len(attachments)})")
            
            # Create a list of attachments
            columns = ("name", "type", "size", "is_code")
            attachments_list = ttk.Treeview(files_frame, columns=columns, show="headings")
            
            # Define column headings
            attachments_list.heading("name", text="Filename")
            attachments_list.heading("type", text="Type")
            attachments_list.heading("size", text="Size")
            attachments_list.heading("is_code", text="Code")
            
            # Define column widths
            attachments_list.column("name", width=200)
            attachments_list.column("type", width=100)
            attachments_list.column("size", width=100)
            attachments_list.column("is_code", width=50)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=attachments_list.yview)
            attachments_list.configure(yscrollcommand=scrollbar.set)
            
            # Pack elements
            attachments_list.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add attachments to list
            for i, attachment in enumerate(attachments):
                # Format size
                size_kb = attachment.get('file_size', 0) / 1024
                if size_kb < 1024:
                    size_str = f"{size_kb:.1f} KB"
                else:
                    size_str = f"{size_kb/1024:.1f} MB"
                
                # Format code flag
                is_code = "Yes" if attachment.get('is_code', False) else "No"
                
                # Add to list
                attachments_list.insert("", "end", values=(
                    attachment.get('filename', 'Unknown'),
                    attachment.get('file_type', 'Unknown'),
                    size_str,
                    is_code
                ))
            
            # Button to open selected attachment
            btn_frame = ttk.Frame(files_frame)
            btn_frame.pack(fill="x", pady=10)
            
            ttk.Button(btn_frame, text="Open Selected File", 
                    command=lambda: self.open_attachment_from_history(attachments_list, attachments)).pack(side=tk.LEFT)
        
        # Close button at bottom
        ttk.Button(main_frame, text="Close", command=detail_window.destroy).pack(pady=(10, 0))

    def open_attachment_from_history(self, treeview, attachments):
        """Open selected attachment from history"""
        # Get selected item
        selection = treeview.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a file to open.")
            return
        
        # Get index from selection
        index = treeview.index(selection[0])
        
        # Get attachment info
        attachment = attachments[index]
        
        # Check if filepath exists
        filepath = attachment.get('filepath', '')
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Error", "File not found. It may have been moved or deleted.")
            return
        
        # Open file with default application
        try:
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

def main():
    root = tk.Tk()
    app = EmailClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        