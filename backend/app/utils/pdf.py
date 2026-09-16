import struct
from typing import List, Tuple


class SimplePDFBuilder:
    """
    A lightweight, enterprise-ready pure Python PDF builder.
    Compiles text, titles, lists, and formatting into standard-compliant multi-page PDF binaries.
    No third-party library dependencies (such as reportlab or fpdf) are required.
    """

    def __init__(self, page_width: float = 612.0, page_height: float = 792.0):
        self.width = page_width
        self.height = page_height
        self.objects = []
        self.pages = []
        self.font_obj_id = None
        self.bold_font_obj_id = None

    def _add_object(self, content: bytes) -> int:
        obj_id = len(self.objects) + 1
        self.objects.append((obj_id, content))
        return obj_id

    @staticmethod
    def _wrap_text(text: str, max_chars: int = 85) -> List[str]:
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            # handle newline characters
            if "\n" in word:
                parts = word.split("\n")
                for idx, part in enumerate(parts):
                    if idx > 0:
                        lines.append(" ".join(current_line))
                        current_line = []
                        current_length = 0
                    if part:
                        if current_length + len(part) + 1 > max_chars:
                            lines.append(" ".join(current_line))
                            current_line = [part]
                            current_length = len(part)
                        else:
                            current_line.append(part)
                            current_length += len(part) + 1
                continue

            if current_length + len(word) + 1 > max_chars:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1

        if current_line:
            lines.append(" ".join(current_line))

        return [line for line in lines if line.strip() or line == ""]

    def build_report_pdf(self, title: str, sections: List[Tuple[str, List[str]]]) -> bytes:
        """
        Creates a PDF document binary by wrapping and placing headings and paragraphs.
        """
        # Register standard catalog/pages structures as dummy placeholders to be filled later
        catalog_id = 1
        pages_id = 2

        # Add Fonts (Helvetica & Helvetica-Bold)
        self.font_obj_id = self._add_object(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /MacRomanEncoding >>"
        )
        self.bold_font_obj_id = self._add_object(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /MacRomanEncoding >>"
        )

        # Lay out text and calculate pages
        # Letter size top-bottom margins: 50pt margin -> y from 50 to 742 (height is 792)
        margin_x = 50.0
        margin_y = 50.0
        max_y = self.height - margin_y
        min_y = margin_y
        line_height = 14.0

        current_page_lines = []
        pages_content_streams = []

        # Title
        title_lines = self._wrap_text(title, max_chars=50)
        current_page_lines.append(("bold", 18.0, title_lines))
        current_page_lines.append(("regular", 10.0, ["Generated on: " + str(bytes(struct.pack('b', 0))[:0], 'utf-8')])) # empty line spacer

        for sec_title, sec_paragraphs in sections:
            # We want to fit section title and at least one paragraph on same page
            # Reserve space (title + space = ~2 lines)
            sec_lines = [("bold", 12.0, [sec_title])]
            for para in sec_paragraphs:
                p_lines = self._wrap_text(para, max_chars=80)
                sec_lines.append(("regular", 10.0, p_lines))
                sec_lines.append(("regular", 10.0, [""]))  # empty line spacing between paragraphs

            current_page_lines.extend(sec_lines)

        # Now group page lines into separate pages based on vertical height
        pages_data: List[List[Tuple[str, float, str]]] = []
        page_items = []
        y_cursor = max_y - 20.0  # leave some room for top spacing

        for font_type, size, lines in current_page_lines:
            for line in lines:
                needed_height = size + 4.0
                if y_cursor - needed_height < min_y:
                    pages_data.append(page_items)
                    page_items = []
                    y_cursor = max_y - 20.0

                page_items.append((font_type, size, line))
                y_cursor -= needed_height

        if page_items:
            pages_data.append(page_items)

        # Build page stream contents
        contents_ids = []
        page_ids = []

        for p_idx, p_items in enumerate(pages_data):
            # Compile text commands
            stream_commands = []
            
            # Draw header border and footer page numbers
            stream_commands.append(f"0.8 0.8 0.8 RG 1 w 50 750 m 562 750 l s".encode("utf-8")) # top border line
            stream_commands.append(f"0.5 0.5 0.5 rg BT /F1 8 Tf 50 35 Td (JobCatalyst AI - Confidential ATS Evaluation Report) Tj ET".encode("utf-8"))
            stream_commands.append(f"BT /F1 8 Tf 530 35 Td (Page {p_idx+1} of {len(pages_data)}) Tj ET".encode("utf-8"))

            y_pos = 730.0
            for font_type, size, line in p_items:
                if not line:
                    y_pos -= 8.0
                    continue
                
                # PDF escaped string
                escaped_line = line.replace("(", "\\(").replace(")", "\\)")
                font_name = "F2" if font_type == "bold" else "F1"
                
                # Dark gray for body, deep slate for bold headers
                color = "0.15 0.2 0.3 rg" if font_type == "bold" else "0.25 0.25 0.25 rg"
                
                cmd = f"BT {color} /{font_name} {size} Tf 50 {y_pos} Td ({escaped_line}) Tj ET"
                stream_commands.append(cmd.encode("utf-8"))
                y_pos -= (size + 4.0)

            stream_data = b"\n".join(stream_commands)
            stream_obj = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream_data), stream_data)
            stream_id = self._add_object(stream_obj)
            contents_ids.append(stream_id)

        # Build Page and Pages objects
        # We need to preserve Catalog and Pages root IDs as 1 and 2
        for s_id in contents_ids:
            p_obj = b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /MediaBox [0 0 612 792] /Contents %d 0 R >>" % (
                self.font_obj_id, self.bold_font_obj_id, s_id
            )
            p_id = self._add_object(p_obj)
            page_ids.append(p_id)

        # Setup Catalog and Pages dictionary payload
        kids_str = " ".join([f"{pid} 0 R" for pid in page_ids])
        pages_content = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids_str.encode("utf-8"), len(page_ids))
        catalog_content = b"<< /Type /Catalog /Pages 2 0 R >>"

        # Overwrite/Insert the first two objects at their fixed slots
        # To maintain index 1 and 2, we just insert them at the front of objects array
        # Let's rebuild the objects array cleanly
        final_objects = []
        final_objects.append((1, catalog_content))
        final_objects.append((2, pages_content))
        
        # Shift other object IDs appropriately
        # To make it simple: catalog is id 1, pages root is id 2.
        # Let's adjust all references!
        # The fonts are created first (ids 3, 4), stream contents next (ids 5...), page objects last.
        # Let's do a complete, deterministic offset rebuild to avoid any reference issue:
        
        # We will reset and do a clean multi-pass object allocation:
        self.objects = []
        # Index 1: Catalog
        # Index 2: Pages Root
        # Index 3: Regular Font
        # Index 4: Bold Font
        catalog_idx = 1
        pages_idx = 2
        font_idx = 3
        bold_font_idx = 4
        
        # Streams and Pages start from index 5
        curr_idx = 5
        streams_list = []
        for p_idx, p_items in enumerate(pages_data):
            stream_commands = []
            stream_commands.append(b"0.8 0.8 0.8 RG 1 w 50 750 m 562 750 l s") # top divider
            stream_commands.append(f"0.4 0.4 0.4 rg BT /F1 8 Tf 50 35 Td (JobCatalyst AI - ATS Performance Report) Tj ET".encode("utf-8"))
            stream_commands.append(f"BT /F1 8 Tf 530 35 Td (Page {p_idx+1} of {len(pages_data)}) Tj ET".encode("utf-8"))

            y_pos = 725.0
            for font_type, size, line in p_items:
                if not line:
                    y_pos -= 10.0
                    continue
                escaped_line = line.replace("(", "\\(").replace(")", "\\)")
                font_name = "F2" if font_type == "bold" else "F1"
                color = "0.15 0.2 0.35 rg" if font_type == "bold" else "0.2 0.2 0.2 rg"
                cmd = f"BT {color} /{font_name} {size} Tf 50 {y_pos} Td ({escaped_line}) Tj ET"
                stream_commands.append(cmd.encode("utf-8"))
                y_pos -= (size + 4.0)

            s_data = b"\n".join(stream_commands)
            s_payload = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(s_data), s_data)
            streams_list.append((curr_idx, s_payload))
            curr_idx += 1

        pages_list = []
        for i, (s_idx, _) in enumerate(streams_list):
            p_payload = b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /MediaBox [0 0 612 792] /Contents %d 0 R >>" % s_idx
            pages_list.append((curr_idx, p_payload))
            curr_idx += 1

        # Re-compile absolute catalog/pages contents
        kids_repr = " ".join([f"{p_id} 0 R" for p_id, _ in pages_list])
        pages_payload = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids_repr.encode("utf-8"), len(pages_list))
        catalog_payload = b"<< /Type /Catalog /Pages 2 0 R >>"
        font_payload = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /MacRomanEncoding >>"
        bold_font_payload = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /MacRomanEncoding >>"

        # Final objects map
        self.objects = [
            (1, catalog_payload),
            (2, pages_payload),
            (3, font_payload),
            (4, bold_font_payload)
        ] + streams_list + pages_list

        # Write PDF binary structure
        pdf_bytes = bytearray()
        pdf_bytes.extend(b"%PDF-1.4\n")

        offsets = {}
        for obj_id, obj_content in self.objects:
            offsets[obj_id] = len(pdf_bytes)
            pdf_bytes.extend(f"{obj_id} 0 obj\n".encode("utf-8"))
            pdf_bytes.extend(obj_content)
            pdf_bytes.extend(b"\nendobj\n")

        # Cross-reference table
        xref_start = len(pdf_bytes)
        pdf_bytes.extend(b"xref\n")
        pdf_bytes.extend(f"0 {len(self.objects) + 1}\n".encode("utf-8"))
        pdf_bytes.extend(b"0000000000 65535 f \n")
        
        for obj_id in sorted(offsets.keys()):
            offset_str = f"{offsets[obj_id]:010d} 00000 n \n"
            pdf_bytes.extend(offset_str.encode("utf-8"))

        pdf_bytes.extend(b"trailer\n")
        pdf_bytes.extend(f"<< /Size {len(self.objects) + 1} /Root 1 0 R >>\n".encode("utf-8"))
        pdf_bytes.extend(b"startxref\n")
        pdf_bytes.extend(f"{xref_start}\n".encode("utf-8"))
        pdf_bytes.extend(b"%%EOF\n")

        return bytes(pdf_bytes)
