# --- editor.py (텍스트 위치 미세 조정) ---

import io
import json
import base64
import os
import sys
from typing import List, Dict, Any
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter
from PIL import Image
import tempfile
from pathlib import Path
import fitz

# --- Enhanced font setup based on addWatermark.py ---
DEFAULT_FONT_NAME = "Helvetica"
REGULAR_FONT_NAME = "NotoSansKR-Regular"
BOLD_FONT_NAME = "NotoSansKR-Bold"
REGULAR_FONT_FILE = "NotoSansKR-Regular.ttf"
BOLD_FONT_FILE = "NotoSansKR-Bold.ttf"


def resolve_font_dir() -> Path | None:
    candidates: List[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)

    if meipass:
        meipass_path = Path(meipass)
        candidates.extend(
            [
                meipass_path / "pdf_processor" / "fonts",
                meipass_path / "fonts",
            ]
        )

    module_dir = Path(__file__).resolve().parent
    candidates.extend(
        [
            module_dir.parent / "fonts",
            module_dir.parent.parent / "fonts",
        ]
    )

    for candidate in candidates:
        regular_font_path = candidate / REGULAR_FONT_FILE
        bold_font_path = candidate / BOLD_FONT_FILE
        if regular_font_path.exists() and bold_font_path.exists():
            return candidate

    return None


try:
    resolved_font_dir = resolve_font_dir()

    if resolved_font_dir:
        regular_font_path = resolved_font_dir / REGULAR_FONT_FILE
        bold_font_path = resolved_font_dir / BOLD_FONT_FILE
        pdfmetrics.registerFont(TTFont(REGULAR_FONT_NAME, str(regular_font_path)))
        pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, str(bold_font_path)))
        DEFAULT_FONT_NAME = REGULAR_FONT_NAME
        print(
            f"SUCCESS: Fonts '{REGULAR_FONT_NAME}' and '{BOLD_FONT_NAME}' loaded successfully."
        )
    else:
        print(f"ERROR: Font files not found: {REGULAR_FONT_FILE}, {BOLD_FONT_FILE}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load fonts. Error: {e}")
# --- End of font setup ---


def hex_to_color(hex_color: str):
    return HexColor(hex_color)


def resolve_text_font(element: Dict[str, Any]) -> str:
    font_family = element.get("fontFamily", "Helvetica")
    font_bold = element.get("fontBold", False)

    if font_family == "Times-Roman":
        return "Times-Bold" if font_bold else "Times-Roman"
    if font_family == "Courier":
        return "Courier-Bold" if font_bold else "Courier"
    if font_family == "NotoSansKR":
        return BOLD_FONT_NAME if font_bold else REGULAR_FONT_NAME
    return "Helvetica-Bold" if font_bold else "Helvetica"


def text_width_with_spacing(text: str, font_name: str, font_size: float, char_spacing: float) -> float:
    if not text:
        return 0

    return pdfmetrics.stringWidth(text, font_name, font_size) + max(len(text) - 1, 0) * char_spacing


def hex_to_rgb_tuple(hex_color: str):
    color = hex_color.lstrip("#")
    if len(color) != 6:
        return (0, 0, 0)
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


def int_color_to_hex(color: int) -> str:
    return f"#{(color >> 16) & 255:02x}{(color >> 8) & 255:02x}{color & 255:02x}"


def map_pdf_font(font_name: str):
    normalized = font_name.lower()
    font_bold = any(token in normalized for token in ["bold", "black", "heavy", "semibold", "demi"])

    if "times" in normalized:
        font_family = "Times-Roman"
    elif "courier" in normalized or "mono" in normalized:
        font_family = "Courier"
    elif "noto" in normalized:
        font_family = "NotoSansKR"
    else:
        font_family = "Helvetica"

    return font_family, font_bold


def resolve_fitz_font(element: Dict[str, Any]) -> str:
    font_family = element.get("fontFamily", "Helvetica")
    font_bold = element.get("fontBold", False)

    if font_family == "Times-Roman":
        return "tibo" if font_bold else "tiro"
    if font_family == "Courier":
        return "cobo" if font_bold else "cour"
    return "hebo" if font_bold else "helv"


def resolve_fitz_font_file(element: Dict[str, Any], text: str = "") -> Path | None:
    font_family = element.get("fontFamily", "Helvetica")
    needs_unicode_font = font_family == "NotoSansKR" or any(ord(char) > 127 for char in text)
    if not needs_unicode_font:
        return None

    font_dir = resolve_font_dir()
    if not font_dir:
        return None

    font_file = BOLD_FONT_FILE if element.get("fontBold", False) else REGULAR_FONT_FILE
    font_path = font_dir / font_file
    return font_path if font_path.exists() else None


def get_fitz_font_name(element: Dict[str, Any], text: str = "") -> str:
    font_file = resolve_fitz_font_file(element, text)
    if font_file:
        return "notosanskr-bold" if element.get("fontBold", False) else "notosanskr"

    return resolve_fitz_font(element)


def get_text_length(text: str, font_name: str, font_size: float, font_file: Path | None = None) -> float:
    if font_file:
        return fitz.Font(fontfile=str(font_file)).text_length(text, fontsize=font_size)

    return fitz.get_text_length(text, fontname=font_name, fontsize=font_size)


def get_centered_text_origin(
    rect: fitz.Rect,
    text: str,
    font_name: str,
    font_size: float,
    align: str,
    y_offset: float = 0,
    font_file: Path | None = None,
) -> fitz.Point:
    font = fitz.Font(fontfile=str(font_file)) if font_file else fitz.Font(fontname=font_name)
    text_width = get_text_length(text, font_name, font_size, font_file)

    if align == "right":
        text_x = rect.x1 - text_width
    elif align == "left":
        text_x = rect.x0
    else:
        text_x = rect.x0 + (rect.width - text_width) / 2

    text_height = font_size * (font.ascender - font.descender)
    text_y = rect.y0 + (rect.height - text_height) / 2 + font_size * font.ascender + y_offset
    return fitz.Point(text_x, text_y)


def intersection_area(a: fitz.Rect, b: fitz.Rect) -> float:
    intersection = a & b
    if intersection.is_empty:
        return 0
    return intersection.width * intersection.height


def detect_text_style_from_area(
    pdf_file_stream: io.BytesIO,
    page_number: int,
    x: float,
    y: float,
    width: float,
    height: float,
) -> Dict[str, Any]:
    doc = fitz.open(stream=pdf_file_stream.read(), filetype="pdf")
    page_index = page_number - 1
    if page_index < 0 or page_index >= len(doc):
        raise ValueError("Page number is out of range")

    page = doc[page_index]
    target_rect = fitz.Rect(x, y, x + width, y + height)
    target_center = target_rect.tl + (target_rect.br - target_rect.tl) * 0.5
    best_span = None
    best_rect = None
    best_score = -1.0

    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                span_rect = fitz.Rect(span.get("bbox"))
                overlap = intersection_area(target_rect, span_rect)
                if overlap <= 0:
                    continue

                span_center = span_rect.tl + (span_rect.br - span_rect.tl) * 0.5
                distance = ((span_center.x - target_center.x) ** 2 + (span_center.y - target_center.y) ** 2) ** 0.5
                score = overlap - distance * 0.01
                if score > best_score:
                    best_score = score
                    best_span = span
                    best_rect = span_rect

    if not best_span or not best_rect:
        raise ValueError("No text found in the selected area")

    font_family, font_bold = map_pdf_font(best_span.get("font", ""))
    detected_font_element = {"fontFamily": font_family, "fontBold": font_bold}
    font_name = get_fitz_font_name(detected_font_element, best_span.get("text", "").strip())
    font_file = resolve_fitz_font_file(detected_font_element, best_span.get("text", "").strip())
    centered_origin = get_centered_text_origin(
        best_rect,
        best_span.get("text", "").strip(),
        font_name,
        float(best_span.get("size", 12)),
        "center",
        font_file=font_file,
    )
    span_origin = best_span.get("origin")
    y_offset = 0
    if span_origin and len(span_origin) >= 2:
        y_offset = float(span_origin[1]) - centered_origin.y

    return {
        "detectedText": best_span.get("text", "").strip(),
        "x": best_rect.x0,
        "y": best_rect.y0,
        "width": best_rect.width,
        "height": best_rect.height,
        "fontSize": best_span.get("size", 12),
        "color": int_color_to_hex(best_span.get("color", 0)),
        "fontFamily": font_family,
        "fontBold": font_bold,
        "align": "center",
        "yOffset": y_offset,
    }


def apply_replace_elements(pdf_bytes: bytes, elements: List[Dict[str, Any]]) -> bytes:
    replace_elements = [el for el in elements if el.get("type") == "replace"]
    if not replace_elements:
        return pdf_bytes

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for el in replace_elements:
        page_index = int(el.get("page", 1)) - 1
        if page_index < 0 or page_index >= len(doc):
            continue

        page = doc[page_index]
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        width = max(float(el.get("width", 1)), 1)
        height = max(float(el.get("height", 1)), 1)
        padding = float(el.get("padding", 0))

        redact_rect = fitz.Rect(
            x + padding,
            y + padding,
            x + width - padding,
            y + height - padding,
        )
        if redact_rect.is_empty or redact_rect.width <= 0 or redact_rect.height <= 0:
            redact_rect = fitz.Rect(x, y, x + width, y + height)

        fill_color = hex_to_rgb_tuple(el.get("fillColor", "#ffffff"))
        page.add_redact_annot(redact_rect, fill=fill_color)
        page.apply_redactions()

        text = el.get("text", "")
        if not text:
            continue

        insert_rect = fitz.Rect(x, y, x + width, y + height)
        font_name = get_fitz_font_name(el, text)
        font_file = resolve_fitz_font_file(el, text)
        font_size = float(el.get("fontSize", 12))
        text_color = hex_to_rgb_tuple(el.get("color", "#000000"))
        align = el.get("align", "center")
        insert_kwargs = {
            "fontname": font_name,
            "fontsize": font_size,
            "color": text_color,
        }
        if font_file:
            insert_kwargs["fontfile"] = str(font_file)

        page.insert_text(
            get_centered_text_origin(insert_rect, text, font_name, font_size, align, float(el.get("yOffset", 0)), font_file),
            text,
            **insert_kwargs,
        )

    return doc.tobytes(garbage=4, deflate=True)


def create_overlay(
    page_width_pt: float, page_height_pt: float, elements: List[Dict[str, Any]]
) -> bytes:
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width_pt, page_height_pt))
    PADDING = 2

    for el in elements:
        el_type = el.get("type")
        x_px, y_px = el.get("x", 0), el.get("y", 0)
        py_top = page_height_pt - y_px
        px = x_px

        if el_type == "text":
            font_size_px = el.get("fontSize", 12)
            font_name = resolve_text_font(el)
            letter_spacing = el.get("letterSpacing", 0)
            text_content = el.get("text", "")
            lines = text_content.splitlines() if text_content else []

            line_height = font_size_px * 1.2
            block_height = len(lines) * line_height
            max_width = 0
            if lines:
                max_width = max(
                    text_width_with_spacing(line, font_name, font_size_px, letter_spacing)
                    for line in lines
                )

            if el.get("hasBackground", False):
                bg_color = el.get("backgroundColor", "#FFFFFF")
                c.setFillColor(hex_to_color(bg_color))
                bg_bottom_y = py_top - block_height

                c.rect(
                    px - PADDING,
                    bg_bottom_y - PADDING,
                    max_width + (2 * PADDING),
                    block_height + (2 * PADDING),
                    stroke=0,
                    fill=1,
                )

            if lines:
                text_object = c.beginText()
                text_object.setFont(font_name, font_size_px)
                text_object.setCharSpace(letter_spacing)
                text_object.setFillColor(hex_to_color(el.get("color", "#000000")))
                text_object.setLeading(line_height)

                start_x = px
                start_y = py_top - font_size_px

                text_object.setTextOrigin(start_x, start_y)

                for line in lines:
                    text_object.textLine(line)
                c.drawText(text_object)

        elif el_type == "signature":
            width_px, height_px = el.get("width", 100), el.get("height", 50)
            py_bottom = py_top - height_px

            if el.get("hasBackground", False):
                bg_color = el.get("backgroundColor", "#FFFFFF")
                c.setFillColor(hex_to_color(bg_color))
                c.rect(px, py_bottom, width_px, height_px, stroke=0, fill=1)

            try:
                img_bytes = base64.b64decode(el.get("imageData", ""))
                img = Image.open(io.BytesIO(img_bytes))

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_f:
                    img.save(temp_f, format="PNG")
                    temp_path = temp_f.name

                c.drawImage(
                    temp_path,
                    px,
                    py_bottom,
                    width=width_px,
                    height=height_px,
                    mask="auto",
                )
                os.remove(temp_path)
            except Exception as e:
                print(f"Error processing signature image: {e}")

        elif el_type == "checkbox":
            size_px = el.get("size", 18)
            py_bottom = py_top - size_px
            is_transparent = el.get("isTransparent", False)
            has_border = el.get("hasBorder", True)

            # 위치 보정을 위한 조정된 좌표
            adj_px = px + 1.3
            adj_py_bottom = py_bottom - 1.3

            if has_border or not is_transparent:
                c.setStrokeColor(hex_to_color(el.get("borderColor", "#000000")))
                c.setFillColor(hex_to_color(el.get("color", "#FFFFFF")))
                # 두께를 1.0으로 줄여서 프론트엔드와 시각적으로 맞춤
                c.setLineWidth(1.0)
                c.rect(
                    adj_px,
                    adj_py_bottom,
                    size_px,
                    size_px,
                    stroke=(1 if has_border else 0),
                    fill=(0 if is_transparent else 1),
                )

            if el.get("checked", False):
                c.setStrokeColor(HexColor("#000000"))
                c.setLineWidth(size_px / 8)
                c.setLineCap(1)
                c.setLineJoin(1)
                p = c.beginPath()
                p.moveTo(px + size_px * 0.2, py_bottom + size_px * 0.5)
                p.lineTo(px + size_px * 0.45, py_bottom + size_px * 0.25)
                p.lineTo(px + size_px * 0.8, py_bottom + size_px * 0.75)
                c.drawPath(p)

    c.save()
    packet.seek(0)
    return packet.read()


def apply_edits_to_pdf(pdf_file_stream: io.BytesIO, elements_json: str) -> bytes:
    # ... (이 함수는 변경 없음)
    elements_by_page = {}
    try:
        all_elements = json.loads(elements_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format for elements")

    original_pdf_bytes = pdf_file_stream.read()
    pdf_bytes = apply_replace_elements(original_pdf_bytes, all_elements)
    overlay_elements = [el for el in all_elements if el.get("type") != "replace"]

    for el in overlay_elements:
        page_str = str(el.get("page"))
        if page_str not in elements_by_page:
            elements_by_page[page_str] = []
        elements_by_page[page_str].append(el)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num_str = str(i + 1)
        if page_num_str in elements_by_page:
            page_width_pt = float(page.mediabox.width)
            page_height_pt = float(page.mediabox.height)

            overlay_bytes = create_overlay(
                page_width_pt, page_height_pt, elements_by_page[page_num_str]
            )
            overlay_pdf = PdfReader(io.BytesIO(overlay_bytes))

            page.merge_page(overlay_pdf.pages[0])

        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue()
