import os
from typing import List
from ocr_library import OCR  # Assuming there's an OCR library to import

class PDFProcessor:
    def __init__(self):
        self.ocr = OCR()

    def process_single_pdf(self, pdf_path: str) -> str:
        """
        Process a single PDF file to extract text and images.
        
        Args:
            pdf_path (str): The path to the PDF file.
        
        Returns:
            str: Extracted markdown content.
        """
        text = self.ocr.extract_text(pdf_path)
        images = self.ocr.extract_images(pdf_path)
        
        markdown_content = self.convert_to_markdown(text, images)
        return markdown_content

    def process_batch_pdfs(self, pdf_paths: List[str]) -> List[str]:
        """
        Process a batch of PDF files.
        
        Args:
            pdf_paths (List[str]): A list of paths to PDF files.
        
        Returns:
            List[str]: A list of extracted markdown contents for each PDF.
        """
        return [self.process_single_pdf(pdf_path) for pdf_path in pdf_paths]

    def convert_to_markdown(self, text: str, images: List[str]) -> str:
        """
        Convert the extracted text and images to markdown format.
        
        Args:
            text (str): The extracted text from the PDF.
            images (List[str]): List of image paths extracted from the PDF.
        
        Returns:
            str: The markdown formatted string.
        """
        markdown = text
        for image in images:
            markdown += f"\n\n![Image]({image})"
        return markdown
