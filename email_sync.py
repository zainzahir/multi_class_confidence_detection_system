import imaplib
import email
from email.header import decode_header
import re


def fetch_and_classify_emails(app, db, User, ResponseHistory, predict_confidence_fn):
    """
    Connect to the teacher's email inbox via IMAP, fetch unread emails,
    match senders to registered students, classify the email body text,
    and save results to the database.
    
    Returns a dict with sync results.
    """
    imap_server = app.config.get('IMAP_SERVER', 'imap.gmail.com')
    teacher_email = app.config.get('TEACHER_EMAIL', '')
    teacher_password = app.config.get('TEACHER_EMAIL_PASSWORD', '')
    
    if not teacher_email or not teacher_password:
        return {
            'success': False,
            'message': 'Teacher email credentials not configured. Please set TEACHER_EMAIL and TEACHER_EMAIL_PASSWORD in .env file.',
            'processed': 0,
            'classified': 0,
            'errors': 0
        }
    
    results = {
        'success': True,
        'message': '',
        'processed': 0,
        'classified': 0,
        'errors': 0,
        'details': []
    }
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(teacher_email, teacher_password)
        mail.select('INBOX')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK' or not messages[0]:
            results['message'] = 'No new unread emails found.'
            mail.logout()
            return results
        
        email_ids = messages[0].split()
        results['processed'] = len(email_ids)
        
        for email_id in email_ids:
            try:
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    results['errors'] += 1
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Get sender email
                sender = msg.get('From', '')
                sender_email = extract_email(sender)
                
                if not sender_email:
                    results['errors'] += 1
                    results['details'].append(f'Could not extract email from sender: {sender}')
                    continue
                
                # Get subject
                subject = decode_email_header(msg.get('Subject', 'No Subject'))
                
                # Get email body text
                body = get_email_body(msg)
                
                if not body or len(body.strip()) < 10:
                    results['details'].append(f'Email from {sender_email} has no/short body text. Skipped.')
                    continue
                
                # Check if sender is a registered student
                with app.app_context():
                    student = User.query.filter_by(email=sender_email.lower(), role='student').first()
                    
                    if not student:
                        results['details'].append(f'Email from {sender_email} - not a registered student. Skipped.')
                        continue
                    
                    # Run prediction on the email body
                    prediction = predict_confidence_fn(body)
                    
                    # Save to database
                    history = ResponseHistory(
                        user_id=student.id,
                        input_text=body[:2000],  # Limit text length
                        predicted_label=prediction['label'],
                        confidence_score=prediction['confidence'],
                        source='Email',
                        email_subject=subject[:200]
                    )
                    db.session.add(history)
                    db.session.commit()
                    
                    results['classified'] += 1
                    results['details'].append(
                        f'Email from {student.name} ({sender_email}): {prediction["label"]} ({prediction["confidence"]}%)'
                    )
                    
            except Exception as e:
                results['errors'] += 1
                results['details'].append(f'Error processing email: {str(e)}')
        
        mail.logout()
        results['message'] = (
            f'Sync complete. Processed: {results["processed"]}, '
            f'Classified: {results["classified"]}, '
            f'Errors: {results["errors"]}'
        )
        
    except imaplib.IMAP4.error as e:
        results['success'] = False
        results['message'] = f'IMAP connection error: {str(e)}. Check your email credentials.'
    except Exception as e:
        results['success'] = False
        results['message'] = f'Email sync error: {str(e)}'
    
    # Map keys to match the frontend expectations
    results['emails_processed'] = results.get('processed', 0)
    results['emails_classified'] = results.get('classified', 0)
    
    return results


def extract_email(sender_string):
    """Extract email address from a sender string like 'Name <email@example.com>'."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', sender_string)
    return match.group(0).lower() if match else None


def decode_email_header(header):
    """Decode an email header that might be encoded."""
    if header is None:
        return 'No Subject'
    decoded_parts = decode_header(header)
    parts = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(encoding or 'utf-8', errors='replace'))
        else:
            parts.append(part)
    return ' '.join(parts)


def get_email_body(msg):
    """Extract plain text body from an email message."""
    body = ''
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
            
            if content_type == 'text/plain':
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
                except Exception:
                    continue
            elif content_type == 'text/html' and not body:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                    # Strip HTML tags for a basic text extraction
                    body = re.sub(r'<[^>]+>', ' ', html_body)
                    body = re.sub(r'\s+', ' ', body).strip()
                except Exception:
                    continue
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                pass
        elif content_type == 'text/html':
            try:
                charset = msg.get_content_charset() or 'utf-8'
                html_body = msg.get_payload(decode=True).decode(charset, errors='replace')
                body = re.sub(r'<[^>]+>', ' ', html_body)
                body = re.sub(r'\s+', ' ', body).strip()
            except Exception:
                pass
    
    return body.strip()
