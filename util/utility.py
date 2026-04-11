import base64
from pypdf.generic import DictionaryObject, NameObject, BooleanObject
from pypdf import PdfWriter

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

def validate_and_decode_base64(base64_str: str, field_name: str) -> bytes:
    """
    Checks if a string is valid Base64 and decodes it into bytes.
    """
    if not isinstance(base64_str, str):
        raise ValueError(f"The field '{field_name}' must be a string.")
        
    # Valid Base64 must have a length that is a multiple of 4
    if len(base64_str) % 4 != 0:
        raise ValueError(f"The field '{field_name}' is not a properly formatted Base64 string (invalid length).")
        
    try:
        return base64.b64decode(base64_str)
    except Exception:
        raise ValueError(f"Failed to decode Base64 for field '{field_name}'.")


def apply_pdfa3_compliance(writer: PdfWriter):
    """
    Injects required markers into the catalog to simulate
    PDF/A-3 compliance and force opening the attachments panel.
    """
    mark_info = DictionaryObject()
    mark_info[NameObject("/Marked")] = BooleanObject(True)
    
    catalog = writer._root_object
    catalog[NameObject("/MarkInfo")] = mark_info
    catalog[NameObject("/PageMode")] = NameObject("/UseAttachments")


def file_to_base64(file_storage):
    file_storage.seek(0)
    return base64.b64encode(file_storage.read()).decode()