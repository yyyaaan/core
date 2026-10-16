from io import BytesIO

from PIL import Image

from play.energy.water import crop_meter


def test_crop_meter_crops_top_left_and_rotates_ccw():
    img = Image.new("RGB", (1000, 500), "white")
    img.paste((255, 0, 0), (0, 0, 10, 10))  # top-left marker
    src = BytesIO()
    img.save(src, "JPEG")
    out = Image.open(BytesIO(crop_meter(src.getvalue())))
    assert out.size == (300, 310)
    assert (
        out.getpixel((2, 307))[0] > 200
    )  # top-left ends up bottom-left after CCW rotation
