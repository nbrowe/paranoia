"""Tests for masking and per-recipient rendering."""
from paranoia.messages import Message, mask, render

MSG = Message(7, 1.5, "pikachu", "meet at  noon", frozenset({"gengar", "abra"}))


def test_mask_preserves_whitespace_and_length():
    """Only non-whitespace is replaced; layout is untouched."""
    out = mask("a b\t cd\n")
    assert out == "* *\t **\n"
    assert len(mask(MSG.text)) == len(MSG.text)


def test_omitted_recipient_gets_mask_without_omitted_field():
    """Omitted users see stars, masked=True, and no omitted key."""
    out = render(MSG, "gengar")
    assert out["text"] == "**** **  ****"
    assert out["masked"] is True
    assert "omitted" not in out
    assert "meet" not in str(out)


def test_sender_gets_real_text_and_sorted_omitted():
    """The sender sees the original and the sorted omit list."""
    out = render(MSG, "pikachu")
    assert out["text"] == MSG.text
    assert out["masked"] is False
    assert out["omitted"] == ["abra", "gengar"]


def test_third_party_gets_real_text_and_no_omitted():
    """Uninvolved users read the message and learn nothing about omits."""
    out = render(MSG, "eevee")
    assert out == {
        "id": 7, "ts": 1.5, "sender": "pikachu",
        "text": MSG.text, "masked": False,
    }
