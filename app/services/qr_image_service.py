from io import BytesIO

import qrcode


def generate_qr_image(link: str) -> BytesIO:
    qr = qrcode.make(link)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer