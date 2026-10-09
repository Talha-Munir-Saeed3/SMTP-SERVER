import smtplib
import ssl
import os
import math
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders

# Email credentials (will be set by main.py when importing)
username = ""
password = ""
name = ""


def get_mime_type(file_path):
    """Get the appropriate MIME type for a file based on extension"""
    # Custom MIME types for coding files
    extension_to_mime = {
        '.py': 'text/x-python',
        '.java': 'text/x-java',
        '.c': 'text/x-c',
        '.cpp': 'text/x-cpp',
        '.h': 'text/x-c',
        '.hpp': 'text/x-cpp',
        '.cs': 'text/x-csharp',
        '.js': 'application/javascript',
        '.ts': 'text/x-typescript',
        '.json': 'application/json',
        '.css': 'text/css',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.xml': 'text/xml',
        '.md': 'text/markdown',
        '.rb': 'text/x-ruby',
        '.php': 'text/x-php',
        '.go': 'text/x-go',
        '.rs': 'text/x-rust',
        '.swift': 'text/x-swift',
        '.kt': 'text/x-kotlin',
        '.dart': 'text/x-dart',
        '.scala': 'text/x-scala',
        '.pl': 'text/x-perl',
        '.lua': 'text/x-lua',
        '.r': 'text/x-r',
        '.sh': 'text/x-shellscript',
        '.sql': 'text/x-sql'
    }
    
    # Get file extension
    _, ext = os.path.splitext(file_path.lower())
    
    # Check our custom mapping first
    if ext in extension_to_mime:
        return extension_to_mime[ext]
    
    # Fall back to system's MIME type detection
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    # Default fallbacks based on general categories
    if ext in ['.txt', '.log', '.ini', '.conf', '.cfg']:
        return 'text/plain'
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        return 'image/' + ext[1:]
    elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
        return 'audio/' + ext[1:]
    elif ext in ['.mp4', '.avi', '.mov', '.webm']:
        return 'video/' + ext[1:]
    elif ext in ['.pdf']:
        return 'application/pdf'
    elif ext in ['.doc', '.docx']:
        return 'application/msword'
    elif ext in ['.xls', '.xlsx']:
        return 'application/vnd.ms-excel'
    elif ext in ['.ppt', '.pptx']:
        return 'application/vnd.ms-powerpoint'
    
    # Last resort
    return 'application/octet-stream'

def create_code_part(file_path, filename=None):
    """Create a properly formatted MIME part for code files"""
    if filename is None:
        filename = os.path.basename(file_path)
    
    # Get MIME type
    mime_type = get_mime_type(file_path)
    main_type, sub_type = mime_type.split('/', 1)
    
    # Read file content
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    # For text-based files, use MIMEText with proper encoding
    if main_type == 'text':
        try:
            # Try to decode as text
            text_content = file_content.decode('utf-8')
            part = MIMEText(text_content, _subtype=sub_type, _charset='utf-8')
        except UnicodeDecodeError:
            # If decoding fails, treat as binary
            part = MIMEBase(main_type, sub_type)
            part.set_payload(file_content)
            encoders.encode_base64(part)
    else:
        # Handle as binary file
        if mime_type == 'application/pdf':
            part = MIMEApplication(file_content, _subtype='pdf')
        elif mime_type.startswith('image/'):
            part = MIMEImage(file_content, _subtype=sub_type)
        else:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(file_content)
            encoders.encode_base64(part)
    
    # Add header
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    
    # Add additional headers for code files to improve handling
    if main_type == 'text' and sub_type.startswith('x-'):
        part.add_header('Content-Description', f'Source code ({sub_type[2:]})')
    
    return part

def send_mail(text="BODY", subject="Heading", from_email=name+'<'+username+'>', to_emails=None, html=None, files=None, size_limit=20, code_highlight=True):
    #Check to see the reciever type is form of list (Can Be Multiple Reciptents)
    assert isinstance(to_emails, list)
    #For holding multpile content types
    msg = MIMEMultipart('alternative')
    #.split() and .join() functions for seperating recipetnants with ,
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = subject
    #Creating versions of the contents
    txt_part = MIMEText(text, 'plain')
    msg.attach(txt_part)
    #Priority if HTML and Text then HTML Version
    #HTML
    if html is not None:
        html_part = MIMEText(html, "html")
        msg.attach(html_part)
    # Handle file attachments
    if files is not None:
        # Convert single file path to list if necessary
        if isinstance(files, str):
            files = [files]
        
        # Check total size of all attachments
        total_size_bytes = 0
        valid_files = []
        size_warnings = []
        code_files = []
        
        for file_path in files:
            # Skip if file doesn't exist
            if not os.path.isfile(file_path):
                print(f"Warning: File '{file_path}' not found and will be skipped.")
                continue
            
            # Detect if it's a code file
            mime_type = get_mime_type(file_path)
            is_code_file = mime_type.startswith('text/x-') or mime_type in [
                'application/javascript', 'text/css', 'text/html', 'text/xml', 
                'application/json', 'text/markdown'
            ]
            
            if is_code_file:
                code_files.append(file_path)
            
            # Get file size
            file_size_bytes = os.path.getsize(file_path)
            # Estimate base64 encoded size (33% increase)
            encoded_size_bytes = file_size_bytes * 1.33
            
            # Convert to MB for user-friendly messages
            file_size_mb = file_size_bytes / (1024 * 1024)
            encoded_size_mb = encoded_size_bytes / (1024 * 1024)
            
            # Check individual file size
            if encoded_size_mb > size_limit:
                size_warnings.append(f"Warning: File '{os.path.basename(file_path)}' is {file_size_mb:.2f}MB " +
                                    f"({encoded_size_mb:.2f}MB when encoded), which exceeds the {size_limit}MB limit and will be skipped.")
                continue
                
            # Add to running total and valid files list
            total_size_bytes += encoded_size_bytes
            valid_files.append(file_path)
        
        # Report on code files detected
        if code_files:
            print(f"Detected {len(code_files)} code file(s):")
            for code_file in code_files:
                filename = os.path.basename(code_file)
                mime_type = get_mime_type(code_file)
                print(f" - {filename} ({mime_type})")
        
        # Check if total size exceeds limit
        total_size_mb = total_size_bytes / (1024 * 1024)
        if total_size_mb > size_limit:
            print(f"Warning: Total attachment size {total_size_mb:.2f}MB exceeds the {size_limit}MB limit.")
            print(f"Consider sending files separately or using a file sharing service.")
            #Greedy appaorach Quantity over Quality
            # Sort files by size and try to include as many as possible
            if valid_files:
                valid_files.sort(key=lambda f: os.path.getsize(f))
                included_files = []
                cumulative_size = 0
                
                for file_path in valid_files:
                    file_size = os.path.getsize(file_path) * 1.33  # Encoded size
                    if cumulative_size + file_size <= size_limit * 1024 * 1024:
                        included_files.append(file_path)
                        cumulative_size += file_size
                    else:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        print(f"Skipping '{os.path.basename(file_path)}' ({size_mb:.2f}MB) to stay under the size limit.")
                
                valid_files = included_files
                print(f"Including {len(valid_files)} of {len(files)} files to stay under the {size_limit}MB limit.")
        
        # Display any size warnings
        for warning in size_warnings:
            print(warning)
        
        # Process and attach valid files
        for file_path in valid_files:
            # Get the filename from the path
            filename = os.path.basename(file_path)
            
            # Determine if this is a code file that needs special handling
            mime_type = get_mime_type(file_path)
            is_code_file = mime_type.startswith('text/x-') or mime_type in [
                'application/javascript', 'text/css', 'text/html', 'text/xml',
                'application/json', 'text/markdown'
            ]
            
            if is_code_file and code_highlight:
                # Special handling for code files
                part = create_code_part(file_path, filename)
            else:
                # Determine content type based on file extension
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Read the file in binary mode
                with open(file_path, 'rb') as attachment:
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        # Handle images
                        part = MIMEImage(attachment.read())
                    elif file_ext in ['.pdf']:
                        # Handle PDFs
                        part = MIMEApplication(attachment.read(), _subtype='pdf')
                    elif file_ext in ['.doc', '.docx']:
                        # Handle Word documents
                        part = MIMEApplication(attachment.read(), _subtype='msword')
                    elif file_ext in ['.xls', '.xlsx', '.csv']:
                        # Handle Excel spreadsheets and CSV files
                        part = MIMEApplication(attachment.read(), _subtype='excel')
                    elif file_ext in ['.ppt', '.pptx']:
                        # Handle PowerPoint presentations
                        part = MIMEApplication(attachment.read(), _subtype='powerpoint')
                    else:
                        # Handle other file types as generic attachments
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                    
                    # Add header to part to make it an attachment
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            
            msg.attach(part)
        
    msg1 = msg.as_string()

    #Logging into the server
    #Opening Server
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    #Basic protocol used when sending email extended Hello to server server responds (TLS etc)
    #Intial Gretting
    server.ehlo()
    #For setting up encryption rules
    simple_mail_context = ssl.create_default_context()
    #Ofcourse Now we want a secure connection
    server.starttls(context=simple_mail_context)
    #Login Using mail and app secured password
    server.login(username, password)
    #Send mail
    server.sendmail(from_email, to_emails, msg1)
    #Log Out Of server QUIT
    server.quit()

def add_syntax_highlighting(code, language=''):
    """Create HTML with syntax highlighting for code using a simple approach"""
    # Base CSS for code highlighting
    highlight_css = """
    <style>
        .code-container {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 14px;
            line-height: 1.45;
            color: #24292e;
            margin-bottom: 16px;
        }
        .code-header {
            background-color: #e1e4e8;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            color: #24292e;
        }
        .code-content {
            padding: 16px;
        }
        .keyword { color: #d73a49; }
        .string { color: #032f62; }
        .comment { color: #6a737d; font-style: italic; }
        .number { color: #005cc5; }
        .function { color: #6f42c1; }
        .class { color: #22863a; }
        .tag { color: #22863a; }
        .attr { color: #6f42c1; }
    </style>
    """
    
    # Escape HTML special characters
    code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Language-specific simple highlighting (just a basic implementation)
    language = language.lower()
    
    # Apply basic syntax highlighting based on language
    # In a real implementation, you'd use a proper syntax highlighting library
    # This is just a simple version for demonstration
    if language in ['python', 'py']:
        # Python keywords
        keywords = ['def', 'class', 'import', 'from', 'if', 'elif', 'else', 'for', 'while', 
                    'return', 'yield', 'try', 'except', 'finally', 'with', 'as', 'lambda',
                    'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is']
        
        for keyword in keywords:
            code = code.replace(f' {keyword} ', f' <span class="keyword">{keyword}</span> ')
            code = code.replace(f'^{keyword} ', f'<span class="keyword">{keyword}</span> ')
            code = code.replace(f' {keyword}:', f' <span class="keyword">{keyword}</span>:')
        
        # Simple string highlighting (very basic)
        # This is a simplistic approach and won't work for all cases
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Handle comments
            if '#' in line:
                comment_pos = line.find('#')
                lines[i] = line[:comment_pos] + f'<span class="comment">{line[comment_pos:]}</span>'
        
        code = '\n'.join(lines)
    
    elif language in ['javascript', 'js', 'typescript', 'ts']:
        # JS/TS keywords
        keywords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
                   'try', 'catch', 'finally', 'switch', 'case', 'break', 'class', 'export',
                   'import', 'from', 'true', 'false', 'null', 'undefined']
        
        for keyword in keywords:
            code = code.replace(f' {keyword} ', f' <span class="keyword">{keyword}</span> ')
            code = code.replace(f'^{keyword} ', f'<span class="keyword">{keyword}</span> ')
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Handle comments
            if '//' in line:
                comment_pos = line.find('//')
                lines[i] = line[:comment_pos] + f'<span class="comment">{line[comment_pos:]}</span>'
        
        code = '\n'.join(lines)
    
    elif language in ['html', 'xml']:
        # Very basic tag highlighting
        import re
        # Match opening and closing tags
        code = re.sub(r'&lt;/?([a-zA-Z0-9_-]+)', r'&lt;<span class="tag">\1</span>', code)
        # Match attributes
        code = re.sub(r'([a-zA-Z0-9_-]+)=', r'<span class="attr">\1</span>=', code)
    
    # Wrap the code in HTML container
    language_name = language if language else "code"
    html = f"""
    {highlight_css}
    <div class="code-container">
        <div class="code-header">{language_name.upper()} Code</div>
        <div class="code-content"><pre>{code}</pre></div>
    </div>
    """
    
    return html

def send_code(code_text, language="", subject="Code Snippet", to_emails=None, 
             message="Here's the code you requested:", include_as_attachment=True,
             attachment_name=None):
    """Send code with optional syntax highlighting"""
    assert isinstance(to_emails, list)
    
    # Default attachment name based on language if not provided
    if include_as_attachment and attachment_name is None:
        if language:
            ext = {
                'python': '.py', 'py': '.py',
                'javascript': '.js', 'js': '.js',
                'typescript': '.ts', 'ts': '.ts',
                'html': '.html', 'css': '.css',
                'java': '.java', 'c': '.c', 'cpp': '.cpp',
                'csharp': '.cs', 'cs': '.cs',
                'go': '.go', 'rust': '.rs', 'ruby': '.rb',
                'php': '.php', 'swift': '.swift',
                'kotlin': '.kt', 'scala': '.scala'
            }.get(language.lower(), '.txt')
            attachment_name = f"code_snippet{ext}"
        else:
            attachment_name = "code_snippet.txt"
    
    # Create HTML version with syntax highlighting
    html_body = f"""
    <html>
    <body>
        <p>{message}</p>
        {add_syntax_highlighting(code_text, language)}
        <p>Regards,<br>Code Sender</p>
    </body>
    </html>
    """
    
    # Plain text version
    plain_text = f"{message}\n\n{code_text}\n\nRegards,\nCode Sender"
    
    # Create temporary file for attachment if needed
    temp_file_path = None
    files_to_send = []
    
    if include_as_attachment:
        import tempfile
        
        # Create temporary file
        fd, temp_file_path = tempfile.mkstemp(suffix="." + attachment_name.split('.')[-1])
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(code_text)
            
            files_to_send.append(temp_file_path)
        except Exception as e:
            print(f"Error creating temporary file: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            temp_file_path = None
    
    try:
        # Send email
        send_mail(
            text=plain_text,
            subject=subject,
            to_emails=to_emails,
            html=html_body,
            files=files_to_send if files_to_send else None
        )
        print(f"Code sent successfully to {', '.join(to_emails)}")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


#TESTING

if __name__ == "__main__":
    name = 'NcProb'
    email = os.getenv('GMAIL_USERNAME', '')
    t = "Hello is it working?"
    file = [r"C:\Users\Talha\Desktop\CODES\6th Sem\CN\PROJECT\recieve.py"]
    #send_mail(text=t, to_emails=[email], html=None, files=file, size_limit=10)


"""
(standard reply codes)
server created object created
Extended hello at service 250

start tls 220
password and username correct 235 accepted
close connection 221
"""

"""
server=smtplib.SMTP(host='smtp.gmail.com',port=587)
print(server)
print(server.ehlo())
simple_mail_context=ssl.create_default_context()
print(simple_mail_context)
print(server.starttls(context=simple_mail_context))
print(server.login(username,password))
print(server.quit())
#"""