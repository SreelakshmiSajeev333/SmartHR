import fitz


def extract_text_from_pdf(file_path):

    """
    Extract text from an uploaded PDF document.
    """

    extracted_text = []

    try:

        document = fitz.open(file_path)

        for page_number, page in enumerate(document):

            page_text = page.get_text("text")

            if page_text.strip():

                extracted_text.append(page_text)

        document.close()

        full_text = "\n".join(extracted_text).strip()

        if not full_text:
            raise ValueError(
                "No readable text found in the PDF document."
            )

        return full_text

    except Exception as error:

        raise ValueError(
            f"Unable to process PDF: {error}"
        ) from error


def split_text_into_chunks(text, chunk_size=1000, overlap=150):

    """
    Divide extracted document text into smaller sections.
    """

    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks