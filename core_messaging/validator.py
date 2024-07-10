import magic
import pyclamd
from django.core.exceptions import ValidationError


def validate_file_type(file):
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_buffer(file.read(1024))
    
    allowed_mime_types = [
        'image/jpeg',
        'image/png',
        'application/pdf',
        # add more allowed MIME types here
    ]
    
    if file_mime_type not in allowed_mime_types:
        raise ValidationError('Unsupported file type.')

def validate_file_size(file):
    max_file_size = 25 * 1024 * 1024  # 25 MB
    if file.size > max_file_size:
        raise ValidationError('File size exceeds limit of 25MB.')

def scan_file_for_viruses(file):
    cd = pyclamd.ClamdAgnostic()
    if not cd.ping():  # Ensure ClamAV is running
        raise ValidationError('ClamAV is not running.')

    file.seek(0)  # Reset file pointer to the beginning
    result = cd.instream(file)
    if result and result['stream'][0] == 'FOUND':
        raise ValidationError('File contains a virus.')