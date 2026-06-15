from cat_api.services.segmentation import segment_text


def test_segment_text_by_sentence() -> None:
    segments = segment_text("Save the file. Close the window!\n\nRestart the app?")

    assert segments == [
        "Save the file.",
        "Close the window!",
        "Restart the app?",
    ]


def test_segment_text_by_paragraph() -> None:
    segments = segment_text(
        "First paragraph wraps\nacross lines.\n\nSecond paragraph.",
        strategy="paragraph",
    )

    assert segments == [
        "First paragraph wraps across lines.",
        "Second paragraph.",
    ]
