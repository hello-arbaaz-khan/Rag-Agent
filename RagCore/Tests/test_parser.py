import textwrap

from RagCore.Chunking.parser import MarkdownParser


def test_empty_content():
    # Empty content se empty result milna chahiye.

    parser = MarkdownParser()

    assert parser.parse("") == []


def test_whitespace_only_content():
    # Sirf spaces/newlines bhi empty treat hone chahiye.

    parser = MarkdownParser()

    assert parser.parse("   \n\n   ") == []


def test_paragraph():
    # Normal paragraph correctly detect hona chahiye.

    parser = MarkdownParser()

    units = parser.parse("This is a paragraph.")

    assert len(units) == 1
    assert units[0].unit_type == "paragraph"
    assert units[0].content == "This is a paragraph."


def test_multiple_paragraphs():
    # Multiple paragraphs separate structural units honi chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            First paragraph.

            Second paragraph.

            Third paragraph.
            """
        )
    )

    assert len(units) == 3

    assert [unit.unit_type for unit in units] == [
        "paragraph",
        "paragraph",
        "paragraph",
    ]


def test_heading():
    # Heading detect aur level preserve hona chahiye.

    parser = MarkdownParser()

    units = parser.parse("# Introduction")

    assert len(units) == 1
    assert units[0].unit_type == "heading"
    assert units[0].content == "Introduction"
    assert units[0].level == 1


def test_multiple_heading_levels():
    # H1/H2/H3 ke levels correctly preserve hone chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            # Main

            ## Section

            ### Subsection
            """
        )
    )

    assert [unit.level for unit in units] == [1, 2, 3]


def test_heading_with_inline_markdown():
    # Heading ke andar bold/italic Markdown hone par text preserve hona chahiye.

    parser = MarkdownParser()

    units = parser.parse("# **Important** Section")

    assert len(units) == 1
    assert units[0].unit_type == "heading"
    assert "Important" in units[0].content
    assert "Section" in units[0].content


def test_bullet_list():
    # Bullet list ko ek list structural unit banana chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            - First item
            - Second item
            - Third item
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "list"
    assert "First item" in units[0].content
    assert "Second item" in units[0].content
    assert "Third item" in units[0].content


def test_ordered_list():
    # Numbered list bhi list structural unit honi chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            1. First
            2. Second
            3. Third
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "list"
    assert "First" in units[0].content
    assert "Second" in units[0].content


def test_nested_list():
    # Nested list completely lose nahi honi chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            - Parent
              - Child
              - Another child
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "list"
    assert "Parent" in units[0].content
    assert "Child" in units[0].content


def test_fenced_code():
    # Fenced code ko code unit banana chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            ```python
            def hello():
                return "world"
            ```
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "code"
    assert "def hello()" in units[0].content
    assert units[0].language == "python"


def test_code_without_language():
    # Language missing ho to parser crash nahi hona chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            ```
            print("hello")
            ```
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "code"
    assert units[0].language is None


def test_indented_code():
    # Indented code block bhi detect hona chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        "    print(\"hello\")\n    print(\"world\")"
    )

    assert any(unit.unit_type == "code" for unit in units)


def test_table():
    # Markdown table ko table unit banana chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            | Name | Age |
            | --- | --- |
            | Ali | 20 |
            | Ahmed | 25 |
            """
        )
    )

    assert len(units) == 1
    assert units[0].unit_type == "table"
    assert "Name" in units[0].content
    assert "Ali" in units[0].content
    assert "Ahmed" in units[0].content


def test_mixed_document():
    # Realistic document mein different structures preserve honi chahiye.

    parser = MarkdownParser()

    units = parser.parse(
        textwrap.dedent(
            """
            # Introduction

            This is a paragraph.

            - First
            - Second

            | A | B |
            | --- | --- |
            | 1 | 2 |

            ```python
            print("hello")
            ```
            """
        )
    )

    assert [unit.unit_type for unit in units] == [
        "heading",
        "paragraph",
        "list",
        "table",
        "code",
    ]


def test_deterministic_parser_output():
    # Same input ko baar baar parse karne par same result hona chahiye.

    parser = MarkdownParser()

    content = textwrap.dedent(
        """
        # Test

        Some paragraph.

        - Item
        """
    )

    first = parser.parse(content)
    second = parser.parse(content)

    assert first == second