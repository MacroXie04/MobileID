import re


class TransferBarcodeParser:
    def __init__(self):
        self.name_pattern = re.compile(
            r'<h4\s+class="white-h4"[^>]*margin-top[^>]*>\s*([^<]+?)\s*</h4>',
            re.IGNORECASE,
        )
        self.student_id_pattern = re.compile(
            r'<h4\s+id="student-id"[^>]*>\s*([^<]+?)\s*</h4>',
            re.IGNORECASE,
        )
        self.img_base64_pattern = re.compile(
            r'<img[^>]+src="data:image/jpeg;base64,([^"]+)"',
            re.IGNORECASE,
        )
        self.magstrip_pattern = re.compile(
            r'formattedTimestamp\s*\+\s*"(\d+)"',
        )

    def parse(self, html):
        name_match = self.name_pattern.search(html)
        student_id_match = self.student_id_pattern.search(html)
        img_base64_match = self.img_base64_pattern.search(html)
        magstrip_match = self.magstrip_pattern.search(html)

        name = name_match.group(1).strip() if name_match else None
        information_id = student_id_match.group(1).strip() if student_id_match else None
        img_base64 = img_base64_match.group(1).strip() if img_base64_match else None
        magstrip_suffix = magstrip_match.group(1).strip() if magstrip_match else None

        return {
            "name": name,
            "information_id": information_id,
            "img_base64": img_base64,
            "barcode": magstrip_suffix,
        }


# only for testing
if __name__ == "__main__":

    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(BASE_DIR, "test.html")

    parser = TransferBarcodeParser()

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    parser.parse(html)

    print("Done")
