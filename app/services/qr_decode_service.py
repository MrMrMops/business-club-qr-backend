from typing import Optional

import cv2
import numpy as np


def decode_qr_image(image_bytes: bytes) -> Optional[str]:
    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        return None

    detector = cv2.QRCodeDetector()

    data, _, _ = detector.detectAndDecode(image)

    if not data:
        return None

    return data