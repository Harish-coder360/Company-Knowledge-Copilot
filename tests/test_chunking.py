from app.rag.chunking import recursive_character_split


def test_recursive_split_respects_overlap():
    text = """This is a long policy document. """ * 50
    chunks = recursive_character_split(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 1
    # Ensure overlap by checking prefix equality between consecutive chunks
    for i in range(len(chunks) - 1):
        assert chunks[i+1][:10] == chunks[i][40:50]


def test_empty_text_returns_empty_list():
    assert recursive_character_split("   ") == []
