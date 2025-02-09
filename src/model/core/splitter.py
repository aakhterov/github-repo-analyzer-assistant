import os
from typing import Dict, List
import nbformat

from langchain_core.documents import Document
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

EXT_LANG_MAPPING = {
    ".cpp": Language.CPP,
    ".go": Language.GO,
    ".kt": Language.KOTLIN,
    ".js": Language.JS,
    ".ts": Language.TS,
    ".php": Language.PHP,
    ".py": Language.PYTHON,
    ".ipynb": Language.PYTHON,
    ".proto": Language.PROTO,
    ".rst": Language.RST,
    ".rb": Language.RUBY,
    ".rs": Language.RUST,
    ".scala": Language.SCALA,
    ".swift": Language.SWIFT,
    ".html": Language.HTML,
    ".tex": Language.LATEX,
    ".cs": Language.CSHARP,
    ".c": Language.C,
    ".pl": Language.PERL,
}
DEFAULT_CODE_CHUNK_SIZE = 400
DEFAULT_CODE_CHUNK_OVERLAP = 0
DEFAULT_NOCODE_CHUNK_SIZE = 1500
DEFAULT_NOCODE_CHUNK_OVERLAP = 400

def smart_splitter(text: str, metadata: Dict, **kwargs) -> List[Document]:
    """
    Splits text content into documents based on file type and specified parameters.

    Args:
        text (str): The text content to split
        metadata (Dict): Metadata dictionary containing filename and other properties
        **kwargs: Additional keyword arguments
            code (Dict): Parameters for code file splitting
                chunk_size (int): Size of code chunks (default: 400)
                chunk_overlap (int): Overlap between code chunks (default: 0)
            nocode (Dict): Parameters for non-code file splitting
                chunk_size (int): Size of non-code chunks (default: 1500)
                chunk_overlap (int): Overlap between non-code chunks (default: 400)

    Returns:
        List[Document]: List of Document objects containing the split content with metadata

    The function determines the appropriate splitting strategy based on file extension:
    - For code files (matched via EXT_LANG_MAPPING), uses language-specific splitting
    - For Jupyter notebooks, extracts and combines code/markdown cells before splitting
    - For other files, uses tiktoken-based splitting
    Each resulting document includes the filename in its content.
    """
    filename = metadata.get("filename")
    file_extension = os.path.splitext(filename)[1]

    if file_extension in EXT_LANG_MAPPING:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=EXT_LANG_MAPPING[file_extension],
            chunk_size=kwargs.get("code", {}).get("chunk_size", DEFAULT_CODE_CHUNK_SIZE),
            chunk_overlap=kwargs.get("code", {}).get("chunk_size", DEFAULT_CODE_CHUNK_OVERLAP)
        )
    else:
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4o",
            chunk_size=kwargs.get("nocode", {}).get("chunk_size", DEFAULT_NOCODE_CHUNK_SIZE),
            chunk_overlap=kwargs.get("nocode", {}).get("chunk_size", DEFAULT_NOCODE_CHUNK_OVERLAP)
        )

    if file_extension == ".ipynb":
        notebook = nbformat.reads(text, as_version=4)
        cells = [cell['source'] for cell in notebook['cells'] if cell['cell_type'] in ['code', 'markdown']]
        text = "\n".join(cells)

    docs = splitter.create_documents(texts=[text], metadatas=[metadata])

    for doc in docs:
        doc.page_content = f"filename: {filename}\n{doc.page_content}"

    return docs
