import imaplib
import email
import os 
from datetime import datetime
from email.header import decode_header
import mimetypes

# Email credentials (will be set by main.py when importing)
username = ""
password = ""
host = "imap.gmail.com"


def clean_filename(filename):
    #Clean filename to ensure it's valid for the filesystem
    if not filename:
        return "unnamed_attachment"
    #File cleaning Proper Format
    # Replace invalid characters with underscore
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def get_download_path():
    #Get the default downloads path for the operating system
    # Default to current directory if downloads can't be found
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # Create a folder for email attachments if it doesn't exist
    email_attachments_folder = os.path.join(downloads_path, "Email_Attachments")
    if not os.path.exists(email_attachments_folder):
        os.makedirs(email_attachments_folder)
    
    return email_attachments_folder

def create_email_folder(base_path, email_data, x):
    """Create a unique folder for each email based on sender and subject"""
    # Get sender email from the 'from' field
    sender = email_data.get('from', 'unknown_sender')
    # Extract just the email address if possible
    if '<' in sender and '>' in sender:
        sender = sender.split('<')[1].split('>')[0]
    sender = clean_filename(sender.split('@')[0])  # Use just the username part
    
    # Get subject, default to timestamp if not available
    subject = email_data.get('subject', 'no_subject')
    subject = clean_filename(subject)
    
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #Email Number
    x = x.decode('utf-8')
    a = int(x)
    # Create folder name from sender and subject (limited length)
    folder_name = f"{sender}_{subject[:20]}_email_{a}_{timestamp}"
    
    # Create the directory
    email_folder = os.path.join(base_path, folder_name)
    os.makedirs(email_folder, exist_ok=True)
    
    return email_folder

def decode_attachment_filename(encoded_filename):
    #Decode the filename from email headers
    if not encoded_filename:
        return "unnamed_attachment"
        
    # Decode the header
    decoded_parts = decode_header(encoded_filename)
    filename_parts = []
    
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            # If it's bytes and we know the encoding
            if encoding:
                try:
                    filename_parts.append(part.decode(encoding))
                except:
                    filename_parts.append(part.decode('utf-8', errors='replace'))
            else:
                # Try utf-8 if no encoding specified
                try:
                    filename_parts.append(part.decode('utf-8'))
                except:
                    filename_parts.append(part.decode('utf-8', errors='replace'))
        else:
            # If it's already a string
            filename_parts.append(part)
            
    return ''.join(filename_parts)

def get_file_extension(content_type, filename=None):
    """Get appropriate file extension based on content type"""
    if filename and '.' in filename:
        return os.path.splitext(filename)[1]
    
    # Common coding file types
    extension_map = {
        'text/x-python': '.py',
        'text/x-java': '.java',
        'text/x-c': '.c',
        'text/x-cpp': '.cpp',
        'text/x-csharp': '.cs',
        'application/javascript': '.js',
        'application/json': '.json',
        'text/css': '.css',
        'text/html': '.html',
        'text/xml': '.xml',
        'text/markdown': '.md',
        'text/x-ruby': '.rb',
        'text/x-php': '.php',
        'text/x-go': '.go',
        'text/x-rust': '.rs',
        'text/x-swift': '.swift',
        'text/x-typescript': '.ts',
        'text/x-kotlin': '.kt',
        'text/x-dart': '.dart',
        'text/x-scala': '.scala',
        'text/x-perl': '.pl',
        'text/x-lua': '.lua',
        'text/x-r': '.r'
    }
    
    if content_type in extension_map:
        return extension_map[content_type]
    
    # Use mimetypes module as fallback
    ext = mimetypes.guess_extension(content_type)
    if ext:
        return ext
    
    # Default extensions for common base types
    if content_type.startswith('text/'):
        return '.txt'
    elif content_type.startswith('image/'):
        return '.img'
    elif content_type.startswith('audio/'):
        return '.audio'
    elif content_type.startswith('video/'):
        return '.video'
    else:
        return '.bin'  # Binary file default

def detect_code_content(content, content_type):
    """Detect if the content is likely code based on content and type"""
    # Already identified as code by content type
    code_types = ['text/x-python', 'text/x-java', 'text/x-c', 'application/javascript',
                 'text/css', 'text/x-cpp', 'text/x-csharp', 'application/json']
    
    if content_type in code_types:
        return True
    
    # Check for coding indicators in plain text
    if content_type == 'text/plain':
        # Common code indicators
        code_indicators = [
            'def ', 'class ', 'function ', 'import ', 'from ', '#include',
            'public class', 'int main', 'package ', 'using namespace',
            'function(', '=>', '{', '};', 'var ', 'let ', 'const ',
            '#!/usr/bin', '<html', '<script', '<style', '<?php',
            'SELECT ', 'CREATE TABLE', '@import'
        ]
        
        for indicator in code_indicators:
            if indicator in content:
                return True
    
    return False

def save_content_to_file(content, folder_path, filename, content_type):
    """Save content to file with appropriate extension"""
    # Determine if content is likely code
    is_code = detect_code_content(content, content_type)
    
    # Get appropriate extension if filename doesn't have one
    if '.' not in filename:
        extension = get_file_extension(content_type, filename)
        filename = f"{filename}{extension}"
    
    # Save content to file
    filepath = os.path.join(folder_path, filename)
    
    # Handle duplicate filenames
    counter = 1
    original_filename = filename
    while os.path.exists(filepath):
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}_{counter}{ext}"
        filepath = os.path.join(folder_path, filename)
        counter += 1
    
    # Write mode depends on content type
    mode = 'wb' if isinstance(content, bytes) else 'w'
    with open(filepath, mode) as f:
        f.write(content)
    
    return {
        'filename': filename,
        'path': filepath,
        'type': content_type,
        'is_code': is_code
    }

def recieve_mail(save_attachments=True, save_content=True):
    #Create server 
    mail = imaplib.IMAP4_SSL(host)
    #Login 
    mail.login(username, password)
    #Informing to read messages
    mail.select("inbox")
    #Either all mails or unseen ones
    #Unpacking the tuple and no using a return value
    _, search_data = mail.search(None, 'UNSEEN')
    my_msg = []
    # Get base attachments directory if saving is enabled
    base_attachments_dir = get_download_path() if (save_attachments or save_content) else None
    #Now search data has 3 items we have to seperate them using .split()
    for num in search_data[0].split():
        email_data = {}
        attachments_info = []
        content_info = []
        #num is really the email number
        #Data is the whole contents like encoding version body subject everything
        _, data = mail.fetch(num, '(RFC822)')
        #Parasing for the relevant stuff
        _, b = data[0]
        #Bytes to readable objects
        email_message = email.message_from_bytes(b)

        print("="*50)
        print("Email:", len(my_msg) + 1)
        print("="*50)

        for header in ['subject', 'to', 'from', 'date']:
            print("{}: {}".format(header, email_message[header]))
            email_data[header] = email_message[header]
        
        # Create a separate folder for this email's attachments and content
        email_specific_folder = None
        
        # Process email parts
        has_attachments = False
        has_content = False
        
        for part in email_message.walk():
            content_type = part.get_content_type()
            
            # Handle attachments
            if part.get_content_disposition() == 'attachment':
                has_attachments = True
                # Get filename
                filename = part.get_filename()
                if filename:
                    # Decode the filename if needed
                    filename = decode_attachment_filename(filename)
                    # Clean the filename to ensure it's valid
                    filename = clean_filename(filename)
                    
                    # Save attachment if enabled
                    if save_attachments and base_attachments_dir:
                        # Create email-specific folder on demand (only when needed)
                        if email_specific_folder is None:
                            email_specific_folder = create_email_folder(base_attachments_dir, email_data, num)
                            print(f"\nCreated folder for this email: {os.path.basename(email_specific_folder)}")
                        
                        filepath = os.path.join(email_specific_folder, filename)
                        
                        # Handle duplicate filenames by adding a counter
                        counter = 1
                        original_filename = filename
                        while os.path.exists(filepath):
                            name, ext = os.path.splitext(original_filename)
                            filename = f"{name}_{counter}{ext}"
                            filepath = os.path.join(email_specific_folder, filename)
                            counter += 1
                            
                        # Save the file
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        print(f"Attachment saved: {filename}")
                        
                        # Add to attachments info
                        attachments_info.append({
                            'filename': filename,
                            'path': filepath,
                            'type': content_type,
                            'is_code': detect_code_content(part.get_payload(decode=True), content_type)
                        })
            
            # Handle email content
            elif content_type in ["text/plain", "text/html"] or content_type.startswith("text/x-"):
                has_content = True
                content = part.get_payload(decode=True)
                
                if content:
                    # Decode content if it's bytes
                    if isinstance(content, bytes):
                        try:
                            decoded_content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                decoded_content = content.decode('latin-1')
                            except:
                                decoded_content = content.decode('utf-8', errors='replace')
                    else:
                        decoded_content = content
                    
                    # Store in email_data
                    if content_type == "text/plain":
                        email_data['body'] = decoded_content
                        print(f"\nBody: {decoded_content[:150]}...")
                    elif content_type == "text/html":
                        email_data['html_body'] = decoded_content
                        print(f"\nHTML body: {len(decoded_content)} characters")
                    else:
                        # Likely code content
                        email_data[f'{content_type}_content'] = decoded_content
                        print(f"\n{content_type} content: {len(decoded_content)} characters")
                    
                    # Save to file if enabled
                    if save_content and base_attachments_dir:
                        # Create folder if not already done
                        if email_specific_folder is None:
                            email_specific_folder = create_email_folder(base_attachments_dir, email_data, num)
                            print(f"\nCreated folder for this email: {os.path.basename(email_specific_folder)}")
                        
                        # Generate appropriate filename
                        if content_type == "text/plain":
                            base_filename = "message"
                        elif content_type == "text/html":
                            base_filename = "message_html"
                        else:
                            # Use content type as basis for filename
                            base_filename = content_type.replace('/', '_').replace('text_', '')
                        
                        # Save content to file
                        content_file_info = save_content_to_file(
                            decoded_content, 
                            email_specific_folder,
                            base_filename,
                            content_type
                        )
                        
                        print(f"{content_type} content saved as: {content_file_info['filename']}")
                        content_info.append(content_file_info)
        
        # Add attachments and content info to email data
        if attachments_info:
            email_data['attachments'] = attachments_info
        if content_info:
            email_data['content_files'] = content_info
        if email_specific_folder:
            email_data['email_folder'] = email_specific_folder
        
        my_msg.append(email_data)
    
    # If items were saved, provide summary
    if (save_attachments or save_content) and base_attachments_dir:
        has_saved_items = any('attachments' in email or 'content_files' in email for email in my_msg)
        if has_saved_items:
            print("\n" + "="*50)
            folders_created = sum(1 for email in my_msg if 'email_folder' in email)
            if folders_created > 0:
                print(f"Created {folders_created} folder(s) for emails with attachments/content")
                print(f"Base directory: {base_attachments_dir}")
                
                # Count by type
                attachment_count = sum(len(email.get('attachments', [])) for email in my_msg)
                content_count = sum(len(email.get('content_files', [])) for email in my_msg)
                code_count = sum(1 for email in my_msg 
                               for attachment in email.get('attachments', []) 
                               if attachment.get('is_code', False))
                code_count += sum(1 for email in my_msg 
                                for content in email.get('content_files', []) 
                                if content.get('is_code', False))
                html_count = sum(1 for email in my_msg 
                               for content in email.get('content_files', []) 
                               if content.get('type') == 'text/html')
                
                if attachment_count > 0:
                    print(f"Downloaded {attachment_count} attachment(s)")
                if content_count > 0:
                    print(f"Saved {content_count} content file(s)")
                if code_count > 0:
                    print(f"Detected {code_count} code file(s)")
                if html_count > 0:
                    print(f"Saved {html_count} HTML file(s)")
            else:
                print("No attachments or content saved from the new emails")
            print("="*50)
    
    return my_msg


if __name__ == "__main__":
    print("Checking for new emails and downloading attachments and content...")
    my_inbox = recieve_mail(save_attachments=True, save_content=True)
    
    # Print summary
    if not my_inbox:
        print("No new emails found.")
    else:
        print(f"\nProcessed {len(my_inbox)} new email(s).")
        
        # Count attachments and content files
        attachment_count = sum(len(email.get('attachments', [])) for email in my_inbox)
        content_count = sum(len(email.get('content_files', [])) for email in my_inbox)
        
        if attachment_count > 0 or content_count > 0:
            if attachment_count > 0:
                print(f"Downloaded {attachment_count} attachment(s).")
            if content_count > 0:
                print(f"Saved {content_count} content file(s).")
                
            # Count code files
            code_count = sum(1 for email in my_inbox 
                           for attachment in email.get('attachments', []) 
                           if attachment.get('is_code', False))
            code_count += sum(1 for email in my_inbox 
                            for content in email.get('content_files', []) 
                            if content.get('is_code', False))
            
            if code_count > 0:
                print(f"Detected {code_count} code file(s) among the attachments and content.")



#Testing
"""
Object created for reciving mails
OK, Success for logging in
OK
"""

"""
print(mail)
print(mail.login(username,password))
print(mail.select("inbox"))
#"""