from pathlib import Path


def count_words_and_lines(file_path: str) -> dict[str, int]:
    """Read a text file and return its word and line counts."""
    text: str = Path(file_path).read_text(encoding="utf-8")
    lines: list[str] = text.splitlines()
    words: list[str] = text.split()

    return {
        "lines": len(lines),
        "words": len(words),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python word_count.py <file_path>")
        sys.exit(1)

    result = count_words_and_lines(sys.argv[1])
    print(f"Lines: {result['lines']}")
    print(f"Words: {result['words']}")