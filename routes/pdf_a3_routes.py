import io
import base64
from flask import request, jsonify, send_file
from pypdf import PdfReader, PdfWriter
from util.utility import validate_and_decode_base64, apply_pdfa3_compliance, file_to_base64
from flask_openapi3 import APIBlueprint, Tag
from schemas import ErrorResponse, GeneratePDFA3Response, GeneratePDFA3Form, DownloadPDFA3Request

# Tag groups the endpoints in Swagger UI
pdf_a3_tag = Tag(name="PDF-A3", description="PDF/A-3 compliance and management")
pdf_a3  = APIBlueprint("pdf_a3", __name__, url_prefix="/pdf-a3")

# ---------------------------------------------------------
# API Endpoint 
# ---------------------------------------------------------

# Generate PDF/A-3 compliant file with attachments
@pdf_a3.post("/generate", tags=[pdf_a3_tag], summary="Generate PDF/A-3 compliant file with attachments", responses={
        200: GeneratePDFA3Response,
        400: ErrorResponse,
        401: ErrorResponse,
        403: ErrorResponse,
        500: ErrorResponse
    })
def generate_pdfa3(form: GeneratePDFA3Form):

    pdf_file = request.files.get("pdf")
    xml_file = request.files.get("xml")
    attachments = request.files.getlist("attachments")

    # 1. Validate required fields
    if not pdf_file or not xml_file:
        return jsonify({"detail": "Missing pdf or xml field"}), 400

    payload = {
        "pdf": {
            "content": file_to_base64(pdf_file)
        },
        "xml": {
            "content": file_to_base64(xml_file)
        },
        "xml_filename": xml_file.filename or "factur-x.xml",
        "attachments": []
    }

    for attach in attachments:
        payload["attachments"].append({
            "filename": attach.filename,
            "content": file_to_base64(attach)
        })
    

    xml_filename = payload.get("xml_filename", "factur-x.xml")
    attachments = payload.get("attachments", [])

    try:
        # 2. Secure decoding of main files
        pdf_bytes = validate_and_decode_base64(payload["pdf"]["content"], "pdf.content")
        xml_bytes = validate_and_decode_base64(payload["xml"]["content"], "xml.content")
        
        # 3. Load and write the PDF
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        writer.append(reader)
        
        # 4. Attach the main XML file
        writer.add_attachment(
            filename=xml_filename,
            data=xml_bytes
        )
        
        # 5. Process and attach optional secondary files
        for i, attach in enumerate(attachments):
            content = attach.get("content")
            fname = attach.get("filename", f"attachment_{i}")
            
            if content:
                attach_bytes = validate_and_decode_base64(content, f"attachments[{i}].content")
                writer.add_attachment(
                    filename=fname,
                    data=attach_bytes
                )
        
        # 6. Apply compliance metadata
        apply_pdfa3_compliance(writer)
        
        # 7. Write final output to memory (RAM)
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        # 8. Return the generated file as a binary stream
        pdf_bytes = output_buffer.getvalue()
        encoded_pdf = base64.b64encode(pdf_bytes).decode()

        return {
            "successful": True,
            "pdfa3": {
                "content": encoded_pdf
            }
        }

    except ValueError as ve:
        # Handle Base64 validation and data type errors
        return jsonify({"detail": str(ve)}), 400
    except Exception as e:
        # Handle PDF corruption or internal processing errors
        return jsonify({"detail": f"Internal processing error: {str(e)}"}), 500
    

# Download endpoint to return the PDF/A-3 file as an attachment
@pdf_a3.post("/download", tags=[pdf_a3_tag], summary="Download a base64 PDF as a file", responses={
        400: ErrorResponse,
})
def download_pdfa3(body: DownloadPDFA3Request):
    try:
        pdf_bytes = base64.b64decode(body.content)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="output_pdfa3.pdf"
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to decode: {str(e)}"}), 400