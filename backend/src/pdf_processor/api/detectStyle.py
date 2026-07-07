import io

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from pdf_processor import editor

router = APIRouter()


@router.post("/detect-text-style")
async def detect_text_style_api(
    file: UploadFile = File(...),
    page: int = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    width: float = Form(...),
    height: float = Form(...),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be uploaded.")

    try:
        pdf_bytes = await file.read()
        return editor.detect_text_style_from_area(
            pdf_file_stream=io.BytesIO(pdf_bytes),
            page_number=page,
            x=x,
            y=y,
            width=width,
            height=height,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
