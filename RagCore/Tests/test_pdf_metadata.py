import pymupdf4llm

def test_real_pdf_metadata():
    result = pymupdf4llm.to_markdown(
        "RagCore/Tests/Fixtures/Pdf_samples/sample_with_blank_page.pdf",
        page_chunks=True,
    )

    print(result)

    for page in result:
        print(page["metadata"])