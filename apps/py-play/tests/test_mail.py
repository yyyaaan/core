from email import message_from_bytes
from email.header import decode_header, make_header

from play.mail import build_mime


def test_build_mime_encodes_non_ascii():
    msg = message_from_bytes(
        build_mime("bot@x.dev", ["a@x.dev", "b@x.dev"], "2 Süper Lig", "<p>Ä</p>")
    )
    assert msg["To"] == "a@x.dev, b@x.dev"
    assert str(make_header(decode_header(msg["Subject"]))) == "2 Süper Lig"
    assert msg.get_content_type() == "text/html"
    assert msg.get_payload(decode=True).decode() == "<p>Ä</p>\n"
