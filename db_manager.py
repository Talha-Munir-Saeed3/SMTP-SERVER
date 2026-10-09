import mysql.connector
import os
import datetime

#Interface between application and database
class DatabaseManager:
    def __init__(self, host="localhost", user="root", password="", database="email_client"):
        """Initialize database connection"""
        self.connection_params = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        self.connection = None
        self.cursor = None
    #Connection
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.connection_params)
            self.cursor = self.connection.cursor()
            return True
        except mysql.connector.Error as err:
            print(f"Database connection error: {err}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    #Created already
    def create_tables(self):
        """Create required tables if they don't exist"""
        if not self.connect():
            return False
        
        try:
            # Users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    display_name VARCHAR(255),
                    provider VARCHAR(50),
                    last_login DATETIME
                )
            """)
            
            # Emails table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    msg_id VARCHAR(255),
                    subject VARCHAR(255),
                    from_email VARCHAR(255),
                    to_email TEXT,
                    date DATETIME,
                    body TEXT,
                    html_body LONGTEXT,
                    received BOOLEAN,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Attachments table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email_id INT,
                    filename VARCHAR(255),
                    filepath VARCHAR(512),
                    file_type VARCHAR(100),
                    file_size INT,
                    is_code BOOLEAN,
                    FOREIGN KEY (email_id) REFERENCES emails(id)
                )
            """)
            
            # Recipients table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS recipients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email_id INT,
                    recipient_email VARCHAR(255),
                    recipient_type ENUM('to', 'cc', 'bcc'),
                    FOREIGN KEY (email_id) REFERENCES emails(id)
                )
            """)
            
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")
            return False
        finally:
            self.disconnect()
    #User management add update
    def add_user(self, email, display_name, provider):
        """Add or update user in database"""
        if not self.connect():
            return None
        
        try:
            # Check if user exists
            self.cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = self.cursor.fetchone()
            
            if result:
                # Update existing user
                user_id = result[0]
                self.cursor.execute("""
                    UPDATE users 
                    SET display_name = %s, provider = %s, last_login = NOW() 
                    WHERE id = %s
                """, (display_name, provider, user_id))
            else:
                # Insert new user
                self.cursor.execute("""
                    INSERT INTO users (email, display_name, provider, last_login)
                    VALUES (%s, %s, %s, NOW())
                """, (email, display_name, provider))
                user_id = self.cursor.lastrowid
                
            self.connection.commit()
            return user_id
        except mysql.connector.Error as err:
            print(f"Error adding user: {err}")
            return None
        finally:
            self.disconnect()
            
    #Saving emails which are send or recieved
    def save_sent_email(self, user_id, subject, from_email, to_emails, body, html_body=None, attachments=None):
        """Save sent email to database"""
        if not self.connect():
            return None
        
        try:
            # Insert email
            self.cursor.execute("""
                INSERT INTO emails (user_id, subject, from_email, to_email, date, body, html_body, received)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s, FALSE)
            """, (user_id, subject, from_email, ', '.join(to_emails), body, html_body))
            
            email_id = self.cursor.lastrowid
            
            # Insert recipients
            for recipient in to_emails:
                self.cursor.execute("""
                    INSERT INTO recipients (email_id, recipient_email, recipient_type)
                    VALUES (%s, %s, 'to')
                """, (email_id, recipient))
            
            # Insert attachments if any
            if attachments:
                for attachment in attachments:
                    filename = os.path.basename(attachment)
                    file_size = os.path.getsize(attachment)
                    file_type = os.path.splitext(filename)[1]
                    
                    self.cursor.execute("""
                        INSERT INTO attachments (email_id, filename, filepath, file_type, file_size, is_code)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (email_id, filename, attachment, file_type, file_size, self._is_code_file(file_type)))
            
            self.connection.commit()
            return email_id
        except mysql.connector.Error as err:
            print(f"Error saving sent email: {err}")
            return None
        finally:
            self.disconnect()
    
    def save_received_emails(self, user_id, emails):
        """Save received emails to database"""
        if not self.connect() or not emails:
            return []
        
        saved_ids = []
        try:
            for email_data in emails:
                # Convert date string to datetime object
                date_str = email_data.get('date', '')
                try:
                    # This is a simplified approach - in a real app you'd need more robust date parsing
                    date_obj = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    date_obj = datetime.datetime.now()
                
                # Insert email
                self.cursor.execute("""
                    INSERT INTO emails (user_id, subject, from_email, to_email, date, body, html_body, received)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """, (
                    user_id, 
                    email_data.get('subject', ''), 
                    email_data.get('from', ''),
                    email_data.get('to', ''),
                    date_obj,
                    email_data.get('body', ''),
                    email_data.get('html_body', '')
                ))
                
                email_id = self.cursor.lastrowid
                saved_ids.append(email_id)
                
                # Insert attachments if any
                attachments = email_data.get('attachments', [])
                for attachment in attachments:
                    filename = attachment.get('filename', '')
                    filepath = attachment.get('path', '')
                    file_type = attachment.get('type', '')
                    is_code = attachment.get('is_code', False)
                    
                    # Get file size if path exists
                    file_size = 0
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                    
                    self.cursor.execute("""
                        INSERT INTO attachments (email_id, filename, filepath, file_type, file_size, is_code)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (email_id, filename, filepath, file_type, file_size, is_code))
                
                # Insert content files (specially saved email content)
                content_files = email_data.get('content_files', [])
                for content_file in content_files:
                    filename = content_file.get('filename', '')
                    filepath = content_file.get('path', '')
                    file_type = content_file.get('type', '')
                    is_code = content_file.get('is_code', False)
                    
                    # Get file size if path exists
                    file_size = 0
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                    
                    self.cursor.execute("""
                        INSERT INTO attachments (email_id, filename, filepath, file_type, file_size, is_code)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (email_id, filename, filepath, file_type, file_size, is_code))
            
            self.connection.commit()
            return saved_ids
        except mysql.connector.Error as err:
            print(f"Error saving received emails: {err}")
            return []
        finally:
            self.disconnect()

    #Emails for a specifc user with email address
    def get_email_history(self, user_id, limit=50, offset=0):
        """Get email history for a user"""
        if not self.connect():
            return []
        
        try:
            self.cursor.execute("""
                SELECT id, subject, from_email, to_email, date, received
                FROM emails
                WHERE user_id = %s
                ORDER BY date DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            
            emails = []
            for row in self.cursor.fetchall():
                email_id, subject, from_email, to_email, date, received = row
                
                # Get attachments for this email
                self.cursor.execute("""
                    SELECT id, filename, file_type, file_size, is_code
                    FROM attachments
                    WHERE email_id = %s
                """, (email_id,))
                
                attachments = []
                for att_row in self.cursor.fetchall():
                    att_id, filename, file_type, file_size, is_code = att_row
                    attachments.append({
                        'id': att_id,
                        'filename': filename,
                        'file_type': file_type,
                        'file_size': file_size,
                        'is_code': bool(is_code)
                    })
                
                emails.append({
                    'id': email_id,
                    'subject': subject,
                    'from': from_email,
                    'to': to_email,
                    'date': date,
                    'received': bool(received),
                    'attachments': attachments
                })
            
            return emails
        except mysql.connector.Error as err:
            print(f"Error fetching email history: {err}")
            return []
        finally:
            self.disconnect()
    #Complete Email info
    def get_email_details(self, email_id):
        """Get full details of a specific email"""
        if not self.connect():
            return None
        
        try:
            self.cursor.execute("""
                SELECT id, user_id, subject, from_email, to_email, date, body, html_body, received
                FROM emails
                WHERE id = %s
            """, (email_id,))
            
            row = self.cursor.fetchone()
            if not row:
                return None
                
            email_id, user_id, subject, from_email, to_email, date, body, html_body, received = row
            
            # Get attachments
            self.cursor.execute("""
                SELECT id, filename, filepath, file_type, file_size, is_code
                FROM attachments
                WHERE email_id = %s
            """, (email_id,))
            
            attachments = []
            for att_row in self.cursor.fetchall():
                att_id, filename, filepath, file_type, file_size, is_code = att_row
                attachments.append({
                    'id': att_id,
                    'filename': filename,
                    'filepath': filepath,
                    'file_type': file_type,
                    'file_size': file_size,
                    'is_code': bool(is_code)
                })
            
            return {
                'id': email_id,
                'user_id': user_id,
                'subject': subject,
                'from': from_email,
                'to': to_email,
                'date': date,
                'body': body,
                'html_body': html_body,
                'received': bool(received),
                'attachments': attachments
            }
        except mysql.connector.Error as err:
            print(f"Error fetching email details: {err}")
            return None
        finally:
            self.disconnect()
    #A basic helper function to increament code files count
    def _is_code_file(self, file_type):
        """Determine if a file is likely code based on extension"""
        code_extensions = [
            '.py', '.java', '.js', '.html', '.css', '.c', '.cpp', '.cs', 
            '.php', '.rb', '.go', '.swift', '.ts', '.json', '.xml', '.sh',
            '.sql', '.rs', '.kt', '.scala', '.pl', '.lua'
        ]
        
        return any(file_type.lower().endswith(ext) for ext in code_extensions)