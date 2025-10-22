"""
Main PDF processing module using Mistral AI OCR
"""

import base64
import time
from pathlib import Path
from datetime import datetime
from mistralai import Mistral

from .image_handler import ImageHandler
from .utils import sanitize_filename


class PDFProcessor:
    """Process PDFs using Mistral AI OCR and extract markdown with images"""
    
    def __init__(self, api_key, output_format='original', jpeg_quality=95):
        """Initialize PDF Processor
        
        Args:
            api_key: Mistral AI API key
            output_format: Image format - 'original', 'jpg', or 'png'
            jpeg_quality: JPEG quality (1-100) if using JPG format
        """
        self.client = Mistral(api_key=api_key)
        self.image_handler = ImageHandler(output_format=output_format, jpeg_quality=jpeg_quality)
    
    def process_pdf(self, pdf_path, output_dir):
        """Process a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save outputs
            
        Returns:
            dict: Processing results summary
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        print(f"Processing: {pdf_path.name}")
        print(f"File size: {pdf_path.stat().st_size:,} bytes")
        
        # Create output directory for this PDF
        safe_name = sanitize_filename(pdf_path.name)
        pdf_output_dir = output_dir / safe_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Encode PDF to Base64
            print("Encoding PDF to base64...")
            with open(pdf_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
            data_uri = f"data:application/pdf;base64,{pdf_b64}"
            
            # Call Mistral OCR
            print("Running Mistral OCR...")
            start_time = time.time()
            
            result = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": data_uri},
                include_image_base64=True
            )
            
            processing_time = time.time() - start_time
            print(f"OCR completed in {processing_time:.1f} seconds")
            
            # Process results
            markdown_pages = []
            total_images = 0
            successful_images = 0
            failed_images = 0
            
            for page in result.pages:
                md = page.markdown or ""
                page_images = 0
                
                print(f"Processing page {page.index}...")
                
                for i, img in enumerate(page.images):
                    if not img.image_base64:
                        continue
                    
                    result_info = self.image_handler.process_image(
                        img.image_base64,
                        pdf_output_dir,
                        page.index,
                        i + 1
                    )
                    
                    total_images += 1
                    
                    if result_info['success']:
                        successful_images += 1
                        size_info = f"{result_info['size'][0]}x{result_info['size'][1]}"
                        print(f"  Saved: {result_info['path'].name} ({size_info})")
                    else:
                        failed_images += 1
                        print(f"  Failed: {result_info.get('error', 'Unknown error')}")
                    
                    # Add image reference to markdown
                    if result_info['path']:
                        md += f"\n\n![Figure page {page.index} image {i+1}]({result_info['path'].name})\n"
                    
                    page_images += 1
                
                if page_images > 0:
                    print(f"  Page {page.index}: {page_images} images processed")
                
                markdown_pages.append(f"## Page {page.index}\n\n{md}")
            
            # Save combined markdown
            full_markdown_path = pdf_output_dir / f"{safe_name}_extracted.md"
            with open(full_markdown_path, "w", encoding="utf-8") as wf:
                # Add document header
                header = f"# {pdf_path.name}\n\n"
                header += f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                header += f"**Pages:** {len(result.pages)} | **Images:** {successful_images} extracted\n\n"
                header += "---\n\n"
                
                wf.write(header + "\n\n".join(markdown_pages))
            
            # Create summary
            summary = {
                'pdf_name': pdf_path.name,
                'pages': len(result.pages),
                'total_images': total_images,
                'successful_images': successful_images,
                'failed_images': failed_images,
                'processing_time': processing_time,
                'output_dir': pdf_output_dir,
                'success': True,
                'error': None
            }
            
            print(f"Completed: {pdf_path.name} - {len(result.pages)} pages, {successful_images} images extracted")
            return summary
            
        except Exception as e:
            error_summary = {
                'pdf_name': pdf_path.name,
                'pages': 0,
                'total_images': 0,
                'successful_images': 0,
                'failed_images': 0,
                'processing_time': 0,
                'output_dir': pdf_output_dir,
                'success': False,
                'error': str(e)
            }
            print(f"Failed to process {pdf_path.name}: {e}")
            return error_summary
    
    def process_batch(self, pdf_files, output_dir, delay=2):
        """Process multiple PDF files
        
        Args:
            pdf_files: List of PDF file paths
            output_dir: Base output directory
            delay: Delay in seconds between processing files
            
        Returns:
            dict: Batch processing summary
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Batch Processing {len(pdf_files)} PDF files")
        print(f"Output directory: {output_dir}")
        
        results = []
        total_start_time = time.time()
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\nProgress: {i}/{len(pdf_files)}")
            
            result = self.process_pdf(pdf_path, output_dir)
            results.append(result)
            
            # Delay between files (API rate limiting)
            if i < len(pdf_files):
                time.sleep(delay)
        
        # Generate batch summary
        total_time = time.time() - total_start_time
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        total_pages = sum(r['pages'] for r in successful)
        total_images = sum(r['successful_images'] for r in successful)
        
        # Save batch summary file
        summary_path = output_dir / "BATCH_SUMMARY.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# Batch OCR Processing Summary\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Time:** {total_time:.1f} seconds\n")
            f.write(f"**Files Processed:** {len(successful)}/{len(results)}\n")
            f.write(f"**Total Pages:** {total_pages}\n")
            f.write(f"**Total Images:** {total_images}\n\n")
            
            f.write("## Successful Extractions\n\n")
            for r in successful:
                f.write(f"- **{r['pdf_name']}**: {r['pages']} pages, {r['successful_images']} images ({r['processing_time']:.1f}s)\n")
            
            if failed:
                f.write("\n## Failed Extractions\n\n")
                for r in failed:
                    f.write(f"- **{r['pdf_name']}**: {r['error']}\n")
        
        print(f"\n{'='*60}")
        print("BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Files processed: {len(successful)}/{len(results)}")
        print(f"Total pages: {total_pages}")
        print(f"Total images extracted: {total_images}")
        print(f"\nAll results saved in: {output_dir}")
        print(f"Summary saved: {summary_path}")
        
        return {
            'total_files': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'total_pages': total_pages,
            'total_images': total_images,
            'total_time': total_time,
            'results': results
        }