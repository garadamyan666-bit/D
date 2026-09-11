import base64

import pytest

from app.services.chart_vision import validate_image


def test_chart_image_validation_accepts_supported_image_data():
    payload = base64.b64encode(b"x" * 1200).decode()
    assert validate_image("data:image/png;base64," + payload).startswith("data:image/png")


def test_chart_image_validation_rejects_bad_type_and_small_file():
    with pytest.raises(ValueError):
        validate_image("data:text/plain;base64," + base64.b64encode(b"x" * 1200).decode())
    with pytest.raises(ValueError):
        validate_image("data:image/jpeg;base64," + base64.b64encode(b"tiny").decode())
