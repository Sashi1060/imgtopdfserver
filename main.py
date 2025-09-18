import io
from typing import List
from PIL import Image
from fpdf import FPDF
import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
load_dotenv()
# Initialize the FastAPI app
app = FastAPI()

# --- Configure CORS ---
# This allows your front-end (running on a different port/domain)
# to communicate with your backend.
origins = [
   "https://image-to-pdf-converter-teal.vercel.app"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------


@app.post("/convert/")
async def convert_images_to_pdf(
    files: List[UploadFile] = File(...),
    pageSize: str = Form("A4"),
    orientation: str = Form("portrait"),
):
    # Validate orientation input, defaulting to portrait
    valid_orientation = (
        orientation.lower()
        if orientation.lower() in ("portrait", "landscape")
        else "portrait"
    )

    # 1. FIX: Pass the validated orientation string directly.
    # The fpdf2 library is smart enough to accept 'portrait' or 'landscape'.
    pdf = FPDF(orientation=valid_orientation, unit="pt", format=pageSize)  # type: ignore

    for uploaded_file in files:
        # ... (rest of the loop is the same)
        image_bytes = await uploaded_file.read()
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_width, img_height = img.size
        except Exception:
            continue

        pdf.add_page()
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        page_height = pdf.h - pdf.t_margin - pdf.b_margin

        ratio = min(page_width / img_width, page_height / img_height)
        pdf_img_width = img_width * ratio
        pdf_img_height = img_height * ratio

        pos_x = (page_width - pdf_img_width) / 2
        pos_y = (page_height - pdf_img_height) / 2

        pdf.image(
            io.BytesIO(image_bytes), x=pos_x, y=pos_y, w=pdf_img_width, h=pdf_img_height
        )

    # 2. FIX: Remove the unnecessary .encode('latin-1')
    # The pdf.output() method already returns bytes.
    pdf_output_bytes = pdf.output()

    return StreamingResponse(
        io.BytesIO(pdf_output_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=converted.pdf"},
    )
