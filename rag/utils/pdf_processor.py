import re
import fitz
import docx

from rag.models import DocumemtsChunks,UploadedDocument
from rag.utils.vector_store import store_document_chunks
 

def extract_text_from_pdf(file_path):
    """This function is used to extract text from pdf file."""
 
    page_text = []
    pfd_document = fitz.open(file_path)

    for page_num in range(len(pfd_document)):
        page = pfd_document[page_num]
        text = page.get_text()

        if text.split():
            page_text.append((page_num + 1, text))
    pfd_document.close()
    return page_text


def extract_text_from_txt(file_path):
    """
    TXT file se text nikalo
    Return: List of tuples [(1, text)]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    return [(1, text)]



def extract_text_from_docx(file_path):
    """
    This function is used to extract text from docx file.
    """
    doc = docx.Document(file_path)
    full_text = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            full_text.append(paragraph.text)

    return [(1, '\n'.join(full_text))]


def clean_text(text):
    """
    cleaning the text from pdf file
    """
    # Multiple to single space
    text = re.sub(r' +', ' ', text)
    
    # Muliple to single new line
    text = re.sub(r'\n+', '\n', text)

    # Remove special characters
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\"]', ' ', text)

    # Remove leading and trailing spaces
    text = text.strip()

    return text


def create_chunks(page_texts, chunk_size=500, chunk_overlap=50):
    """This function is used to create chunks of text."""
    chunk = []

    chunk_index = 0

    for page_num, text in page_texts:

        text = clean_text(text)
        word = text.split()

        if not word:
            continue
        
        start = 0
        while start < len(word):
            end = start + chunk_size
            chunk_word = word[start:end]

            chunk_text = ' '.join(chunk_word)

            chunk.append({
                "chunk_text":chunk_text,
                "page_number":page_num,
                "chunk_index":chunk_index,
                "size":len(chunk_word)
            })

            chunk_index += 1
            start = end - chunk_overlap
    return chunk


def get_extractor(file_type):

    extractors = {
        "pdf": extract_text_from_pdf,
        "docx": extract_text_from_docx,
        "doc": extract_text_from_docx,
        "txt": extract_text_from_txt
    }
    return extractors.get(file_type)


def process_document(document):
    """Process full document.
    1. Extract text
    2. Clean text
    3. Chunk it
    4. Save chunks to DB
    5. Create embeddings and store in ChromaDB
    6. Mark document as processed
    """
    extractor = get_extractor(document.file_type)
    if not extractor:
        raise ValueError(f"File type {document.file_type} is not supported")

    file_path = document.file.path
    pages_text = extractor(file_path)
    if not pages_text:
        raise ValueError("File is empty")

    chunks = create_chunks(pages_text, chunk_size=100, chunk_overlap=50)
    if not chunks:
        raise ValueError("Chunks creation failed")

    DocumemtsChunks.objects.filter(document=document).delete()

    chunks_obj = [
        DocumemtsChunks(
            document=document,
            chunk_text=chunk['chunk_text'],
            chunk_index=chunk['chunk_index'],
            page_number=chunk['page_number'],
            chunk_size=chunk['size']
        )
        for chunk in chunks
    ]
    DocumemtsChunks.objects.bulk_create(chunks_obj)
    
    store_document_chunks(document.id)
    
    document.is_processed = True
    document.processing_error = None
    document.save()

    print(f"{document.name}: {len(chunks)} chunks created.")
    return len(chunks)
