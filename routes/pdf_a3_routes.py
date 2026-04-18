import io
import base64
from flask import request, jsonify, send_file
from pypdf import PdfReader, PdfWriter
from util.utility import validate_and_decode_base64, apply_pdfa3_compliance, file_to_base64
from flask_openapi3 import APIBlueprint, Tag
from schemas import ErrorResponse, GeneratePDFA3Response, GeneratePDFA3Form, DownloadPDFA3Request
from middleware.auth_middleware import verify_token
from pydantic import BaseModel 

# 1. Define Tags and Blueprint
pdf_a3_tag = Tag(name="PDF-A3", description="PDF/A-3 compliance, management, and extraction")
pdf_a3 = APIBlueprint("pdf_a3", __name__, url_prefix="/pdf-a3")

# 2. Define Request Model for Extraction
class ExtractRequest(BaseModel):
    content: str

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

# 1. Generate PDF/A-3
@pdf_a3.post("/generate", 
             tags=[pdf_a3_tag], 
             summary="Generate PDF/A-3 compliant file with attachments", 
             responses={200: GeneratePDFA3Response, 400: ErrorResponse, 500: ErrorResponse},
             security=[{"BearerAuth": []}])
# @verify_token
def generate_pdfa3(form: GeneratePDFA3Form):
    pdf_file = request.files.get("pdf")
    xml_file = request.files.get("xml")
    attachments = request.files.getlist("attachments")

    if not pdf_file or not xml_file:
        return jsonify({"detail": "Missing pdf or xml field"}), 400

    try:
        # Convert files to base64 then decode to bytes for processing
        pdf_bytes = base64.b64decode(file_to_base64(pdf_file))
        xml_bytes = base64.b64decode(file_to_base64(xml_file))
        
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        writer.append(reader)
        
        # Attach main XML
        writer.add_attachment(filename=xml_file.filename or "factur-x.xml", data=xml_bytes)
        
        # Attach additional files
        for attach in attachments:
            content_bytes = base64.b64decode(file_to_base64(attach))
            writer.add_attachment(filename=attach.filename, data=content_bytes)
        
        apply_pdfa3_compliance(writer)
        
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        encoded_pdf = base64.b64encode(output_buffer.getvalue()).decode()

        return {
            "successful": True,
            "pdfa3": {"content": encoded_pdf}
        }
    except Exception as e:
        return jsonify({"detail": f"Internal processing error: {str(e)}"}), 500

# 2. Download PDF/A-3
@pdf_a3.post("/download", 
             tags=[pdf_a3_tag], 
             summary="Download a base64 PDF as a file",
             security=[{"BearerAuth": []}])
# @verify_token
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

# 3. Extract from PDF/A-3 Developed by Hamoud Rabany 
# Warning : 
@pdf_a3.post("/extract", 
             tags=[pdf_a3_tag], 
             summary="Extract embedded files from PDF/A-3",
             security=[{"BearerAuth": []}])
# @verify_token
def extract_pdfa3(body: ExtractRequest):
    try:
        content = body.content
        # Auto-fix base64 padding
        missing_padding = len(content) % 4
        if missing_padding:
            content += '=' * (4 - missing_padding)

        pdf_bytes = base64.b64decode(content)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        response_data = {"xml_metadata": None, "other_attachments": []}

        if reader.attachments:
            for filename, data_list in reader.attachments.items():
                file_raw_data = data_list[0] if isinstance(data_list, list) else data_list
                encoded_file = base64.b64encode(file_raw_data).decode('utf-8')

                if filename.lower().endswith(".xml"):
                    response_data["xml_metadata"] = {"filename": filename, "content": encoded_file}
                else:
                    response_data["other_attachments"].append({"filename": filename, "content": encoded_file})

        return {
            "successful": True,
            "message": "Files extracted successfully",
            "data": response_data
        }, 200
    except Exception as e:
        return {"successful": False, "error": f"Failed to extract: {str(e)}"}, 500