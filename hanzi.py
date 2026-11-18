import argparse
import math
import os
import sys
from dataclasses import dataclass
from typing import List, Sequence

import requests
from pypinyin import Style, pinyin as to_pinyin
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
#from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from fontTools import ttLib

DATA_SOURCE = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest"
CARD_WIDTH_CM = 8.7
CARD_HEIGHT_CM = 5.8
GRID_COLUMNS = 4
DEFAULT_HANZI_FONT_NAME = "I.Ming"
DEFAULT_PINYIN_FONT_NAME = "STKaiti"
PINYIN_HANZI_GAP_CM = 0.18
MAX_COMMON_PINYIN = 3

def is_cjk_char(char: str) -> bool:
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
        or 0x2CEB0 <= code <= 0x2EBEF
        or 0x30000 <= code <= 0x3134F
    )


def normalize_text(raw_text: str) -> str:
    chars = [ch for ch in raw_text if not ch.isspace()]
    if len(chars) > 8:
        raise ValueError("Please enter no more than 8 Chinese characters (spaces are ignored).")
    if not all(is_cjk_char(ch) for ch in chars):
        raise ValueError("Input contains non-Chinese characters. Please enter only Chinese characters.")
    return "".join(chars)


def _normalize_reading(reading: str) -> str:
    return "".join(reading.strip().split()).lower()


def select_common_readings(readings: Sequence[str], max_count: int = MAX_COMMON_PINYIN) -> List[str]:
    result: List[str] = []
    seen = set()

    for raw in readings:
        reading = raw.strip()
        if not reading:
            continue
        key = _normalize_reading(reading)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(reading)
        if len(result) >= max_count:
            break

    return result


@dataclass
class HanziData:
    character: str
    medians: List[List[List[float]]]
    pinyin: str


class HanziWriterClient:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "hanzi-stroke-card-generator/1.0",
                "Accept": "application/json",
            }
        )

    def fetch(self, character: str) -> HanziData:
        url = f"{DATA_SOURCE}/{character}.json"
        response = self.session.get(url, timeout=self.timeout)

        if response.status_code == 404:
            raise ValueError(f"Stroke data not found for '{character}'.")
        response.raise_for_status()

        payload = response.json()
        medians = payload.get("medians")
        if not isinstance(medians, list) or not medians:
            raise ValueError(f"Invalid data format for '{character}': missing medians.")

        py_list = to_pinyin(character, style=Style.TONE, heteronym=True)
        pinyin_candidates = py_list[0] if py_list and py_list[0] else []

        if not pinyin_candidates:
            pinyin_value = payload.get("pinyin")
            if isinstance(pinyin_value, list):
                pinyin_candidates = [str(item) for item in pinyin_value if item]
            elif isinstance(pinyin_value, str):
                pinyin_candidates = [pinyin_value]

        common_readings = select_common_readings(pinyin_candidates)
        pinyin_text = " / ".join(common_readings)

        return HanziData(character=character, medians=medians, pinyin=pinyin_text)


@dataclass
class CardLayout:
    x: float
    y: float
    width: float
    height: float


def get_card_layouts(page_width: float, page_height: float) -> List[CardLayout]:
    card_width = CARD_WIDTH_CM * cm
    card_height = CARD_HEIGHT_CM * cm

    side_margin = 1.0 * cm
    top_bottom_margin = 1.0 * cm
    h_gap = 0.5 * cm
    v_gap = 0.5 * cm

    layouts: List[CardLayout] = []

    columns = int((page_width - 2 * side_margin + h_gap) // (card_width + h_gap))
    rows = int((page_height - 2 * top_bottom_margin + v_gap) // (card_height + v_gap))

    if columns <= 0 or rows <= 0:
        raise RuntimeError("Page size is too small to place cards.")

    used_width = columns * card_width + (columns - 1) * h_gap
    used_height = rows * card_height + (rows - 1) * v_gap

    start_x = (page_width - used_width) / 2
    start_y = (page_height - used_height) / 2

    for row in range(rows):
        for col in range(columns):
            x = start_x + col * (card_width + h_gap)
            y = page_height - start_y - (row + 1) * card_height - row * v_gap
            layouts.append(CardLayout(x=x, y=y, width=card_width, height=card_height))

    return layouts


def _map_point(x: float, y: float, box_x: float, box_y: float, box_size: float) -> tuple[float, float]:
    mapped_x = box_x + (x / 1024.0) * box_size
    mapped_y = box_y + (y / 1024.0) * box_size
    return mapped_x, mapped_y


def _extract_polyline_segment(
    points: Sequence[tuple[float, float]], start_distance: float, end_distance: float
) -> List[tuple[float, float]]:
    if len(points) < 2:
        return []

    cumulative = [0.0]
    for index in range(1, len(points)):
        x0, y0 = points[index - 1]
        x1, y1 = points[index]
        cumulative.append(cumulative[-1] + math.hypot(x1 - x0, y1 - y0))

    total = cumulative[-1]
    if total <= 0:
        return []

    start = max(0.0, min(start_distance, total))
    end = max(0.0, min(end_distance, total))
    if end <= start:
        return []

    result: List[tuple[float, float]] = []

    for seg_index in range(len(points) - 1):
        seg_start = cumulative[seg_index]
        seg_end = cumulative[seg_index + 1]
        seg_len = seg_end - seg_start
        if seg_len <= 1e-9:
            continue
        if seg_end < start or seg_start > end:
            continue

        local_start = max(start, seg_start)
        local_end = min(end, seg_end)
        if local_end <= local_start:
            continue

        x0, y0 = points[seg_index]
        x1, y1 = points[seg_index + 1]
        t0 = (local_start - seg_start) / seg_len
        t1 = (local_end - seg_start) / seg_len

        p_start = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
        p_end = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)

        if not result or math.hypot(result[-1][0] - p_start[0], result[-1][1] - p_start[1]) > 1e-6:
            result.append(p_start)
        result.append(p_end)

    return result


def draw_grid(c: canvas.Canvas, x: float, y: float, size: float) -> None:
    c.saveState()
    c.setStrokeColor(colors.HexColor("#D9D9D9"))
    c.setLineWidth(0.6)

    c.rect(x, y, size, size)
    c.line(x, y + size / 2, x + size, y + size / 2)
    c.line(x + size / 2, y, x + size / 2, y + size)
    c.line(x, y, x + size, y + size)
    c.line(x + size, y, x, y + size)

    c.restoreState()


def draw_median_stroke(
    c: canvas.Canvas,
    points: Sequence[Sequence[float]],
    x: float,
    y: float,
    size: float,
    stroke_color,
    line_width: float,
    draw_arrow: bool = False,
) -> None:
    if len(points) < 2:
        return

    mapped_points = [_map_point(float(point[0]), float(point[1]), x, y, size) for point in points]

    c.saveState()
    c.setStrokeColor(stroke_color)
    c.setLineWidth(line_width)
    c.setLineJoin(1)
    c.setLineCap(1)

    path = c.beginPath()
    start_x, start_y = mapped_points[0]
    path.moveTo(start_x, start_y)

    for px, py in mapped_points[1:]:
        path.lineTo(px, py)

    c.drawPath(path)

    inner_width = max(line_width * 0.45, 0.6)
    if inner_width < line_width:
        c.setStrokeColor(colors.white)
        c.setLineWidth(inner_width)
        c.drawPath(path)

    if draw_arrow:
        cumulative = [0.0]
        for index in range(1, len(mapped_points)):
            x0, y0 = mapped_points[index - 1]
            x1, y1 = mapped_points[index]
            cumulative.append(cumulative[-1] + math.hypot(x1 - x0, y1 - y0))

        total_len = cumulative[-1]
        if total_len >= 0.01:
            tip_inset = max(line_width * 0.55, 0.8)
            tip_distance = min(tip_inset, max(total_len - 0.01, 0.0))

            min_shaft_len = max(size * 0.11, line_width * 4.2)
            max_shaft_len = max(size * 0.34, line_width * 8.0)
            shaft_len = min(max_shaft_len, max(min_shaft_len, total_len * 0.72))

            shaft_start_from_end = min(total_len - 0.005, tip_distance + shaft_len)
            shaft_start_distance = max(0.0, total_len - shaft_start_from_end)
            shaft_end_distance = max(0.0, total_len - tip_distance)

            shaft_points = _extract_polyline_segment(mapped_points, shaft_start_distance, shaft_end_distance)

            if len(shaft_points) >= 2:
                c.setStrokeColor(stroke_color)
                c.setLineWidth(max(line_width * 0.22, 0.55))
                c.setLineJoin(1)
                c.setLineCap(1)

                shaft_path = c.beginPath()
                shaft_path.moveTo(shaft_points[0][0], shaft_points[0][1])
                for px, py in shaft_points[1:]:
                    shaft_path.lineTo(px, py)
                c.drawPath(shaft_path)

                tip_x, tip_y = shaft_points[-1]
                prev_x, prev_y = shaft_points[-2]
                dx = tip_x - prev_x
                dy = tip_y - prev_y
                direction_len = math.hypot(dx, dy)

                if direction_len >= 0.01:
                    ux = dx / direction_len
                    uy = dy / direction_len
                    perp_x = -uy
                    perp_y = ux

                    head_len = max(line_width * 1.05, 0.95)
                    head_half_width = max(line_width * 0.28, 0.46)

                    base_x = tip_x - ux * head_len
                    base_y = tip_y - uy * head_len

                    left_x = base_x + perp_x * head_half_width
                    left_y = base_y + perp_y * head_half_width
                    right_x = base_x - perp_x * head_half_width
                    right_y = base_y - perp_y * head_half_width

                    c.setStrokeColor(stroke_color)
                    c.setLineWidth(max(line_width * 0.14, 0.42))
                    c.line(tip_x, tip_y, left_x, left_y)
                    c.line(tip_x, tip_y, right_x, right_y)

    c.restoreState()


def draw_stroke_frame(
    c: canvas.Canvas,
    medians: Sequence[Sequence[Sequence[float]]],
    step_index: int,
    frame_x: float,
    frame_y: float,
    frame_size: float,
) -> None:
    draw_grid(c, frame_x, frame_y, frame_size)

    normal_width = max(frame_size * 0.06, 1.2)
    current_width = max(frame_size * 0.07, 1.5)

    for index in range(step_index + 1):
        color = colors.HexColor("#111111") if index < step_index else colors.HexColor("#C1121F")
        width = normal_width if index < step_index else current_width
        draw_median_stroke(
            c,
            medians[index],
            frame_x,
            frame_y,
            frame_size,
            color,
            width,
            draw_arrow=(index == step_index),
        )


def draw_card(c: canvas.Canvas, data: HanziData, layout: CardLayout, hanzi_font_family: str, pinyin_font_family: str) -> None:
    c.saveState()

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(layout.x, layout.y, layout.width, layout.height)

    inner_padding = 0.24 * cm
    title_h = 0.9 * cm
    title_y = layout.y + layout.height - inner_padding - title_h
    center_x = layout.x + layout.width / 2

    pinyin_font_size = 12
    hanzi_font_size = 18
    group_gap = PINYIN_HANZI_GAP_CM * cm if data.pinyin else 0.0

    c.setFont(pinyin_font_family, pinyin_font_size)
    pinyin_width = c.stringWidth(data.pinyin, pinyin_font_family, pinyin_font_size) if data.pinyin else 0.0

    c.setFont(hanzi_font_family, hanzi_font_size)
    hanzi_width = c.stringWidth(data.character, hanzi_font_family, hanzi_font_size)

    total_width = pinyin_width + group_gap + hanzi_width
    group_start_x = center_x - total_width / 2

    if data.pinyin:
        c.setFont(pinyin_font_family, pinyin_font_size)
        c.setFillColor(colors.HexColor("#333333"))
        c.drawString(group_start_x, title_y + 0.31 * cm, data.pinyin)
        c.setFillColor(colors.black)

    c.setFont(hanzi_font_family, hanzi_font_size)
    c.drawString(group_start_x + pinyin_width + group_gap, title_y + 0.28 * cm, data.character)

    area_x = layout.x + inner_padding
    area_y = layout.y + inner_padding
    area_w = layout.width - 2 * inner_padding
    area_h = layout.height - (title_h + 2 * inner_padding + 0.15 * cm)

    stroke_count = len(data.medians)
    cols = GRID_COLUMNS
    rows = max(1, math.ceil(stroke_count / cols))

    cell_gap = 0.12 * cm
    cell_size_by_w = (area_w - cell_gap * (cols - 1)) / cols
    cell_size_by_h = (area_h - cell_gap * (rows - 1)) / rows
    cell_size = max(min(cell_size_by_w, cell_size_by_h), 0.45 * cm)

    total_w = cols * cell_size + (cols - 1) * cell_gap
    total_h = rows * cell_size + (rows - 1) * cell_gap

    origin_x = area_x + (area_w - total_w) / 2
    origin_y = area_y + (area_h - total_h) / 2

    for step in range(stroke_count):
        row = step // cols
        col = step % cols

        frame_x = origin_x + col * (cell_size + cell_gap)
        frame_y = origin_y + (rows - 1 - row) * (cell_size + cell_gap)

        draw_stroke_frame(c, data.medians, step, frame_x, frame_y, cell_size)

    c.restoreState()


def generate_pdf(chars: str, output_path: str, hanzi_font_family: str, pinyin_font_family: str) -> None:
    
    client = HanziWriterClient()
    items = [client.fetch(ch) for ch in chars]

    c = canvas.Canvas(output_path, pagesize=A4)
    page_w, page_h = A4
    card_layouts = get_card_layouts(page_w, page_h)

    for index, item in enumerate(items):
        slot = index % len(card_layouts)
        if slot == 0 and index > 0:
            c.showPage()
        draw_card(c, item, card_layouts[slot], hanzi_font_family, pinyin_font_family)

    c.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enter a sequence of Chinese characters, download stroke order data, and generate 8.7x5.8 cm landscape card PDF."
    )
    parser.add_argument("--text", help="A sequence of Chinese characters, e.g. 你好世界学习成长")
    parser.add_argument("--output", default="hanzi_cards.pdf", help="Output PDF filename")
    parser.add_argument("--hanzi_font_family", default="I.Ming", help="Hanzi font family name")
    parser.add_argument("--pinyin_font_family", default="STKaiti", help="Pinyin font family name")
    parser.add_argument("--font_file_paths", default="./Fonts/I.Ming/I.Ming-8.10.ttf;./Fonts/Stkaiti/stkaiti.ttf", help="Semicolon-separated list of font file paths.")
    return parser.parse_args()


def register_fonts(hanzi_font_family: str, pinyin_font_family: str, font_paths: list[str]) -> None:
    
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    
    for font_path in font_paths:
        
        if not os.path.exists(font_path):
            print(f"Font file not found: {font_path}")
            continue
        
        font = ttLib.TTFont(font_path)
        font_name = font["name"]
        font_family_name = font_name.getBestFamilyName()
    
        if font_family_name in registered_fonts:
            print(f"Font already registered: {font_family_name}")
            continue
        
        if not font_family_name in [hanzi_font_family, pinyin_font_family]:
            print(f"Skipping font: {font_name.getBestFullName()} (family name: {font_family_name})")
            continue
        
        print(f"Registering font: {font_name.getBestFullName()} (family name: {font_family_name})")
        pdfmetrics.registerFont(TTFont(font_family_name, font_path))
        registered_fonts.append(font_family_name)
        

def main() -> int:
    args = parse_args()
    try:
        if not args.text:
            print(f"No text provided; please use the --text argument to specify the Chinese characters.")
            return 1

        if not args.output:
            print(f"No output filename provided; please use the --output argument to specify the output PDF filename.")
            return 1

        hanzi_font_family = DEFAULT_HANZI_FONT_NAME
        if args.hanzi_font_family:
            hanzi_font_family = args.hanzi_font_family
            print(f"Using {hanzi_font_family} for Hanzi characters")
        else:
            print(f"No Hanzi font provided: using {hanzi_font_family}")

        pinyin_font_family = DEFAULT_PINYIN_FONT_NAME
        if args.pinyin_font_family:
            pinyin_font_family = args.pinyin_font_family
            print(f"Using {pinyin_font_family} for Pinyin characters")
        else:
            print(f"No Pinyin font provided: using {pinyin_font_family}")
        
        font_file_paths = [
                        r"./Fonts/I.Ming/I.Ming-8.10.ttf",
                        r"./Fonts/Stkaiti/stkaiti.ttf"
                    ]
        
        if args.font_file_paths:
            font_file_paths = args.font_file_paths.split(";")
        
        raw = args.text
        
        register_fonts(
            hanzi_font_family,
            pinyin_font_family,
            font_file_paths)
        
        chars = normalize_text(raw)
        generate_pdf(chars, args.output, hanzi_font_family, pinyin_font_family)
        print(f"PDF generated: {args.output}")
        print(f"Data source: {DATA_SOURCE}")
        return 0
    
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    

if __name__ == "__main__":
    raise SystemExit(main())
