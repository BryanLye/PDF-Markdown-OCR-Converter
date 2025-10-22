"""
Image extraction and processing utilities
"""

import base64
import io
from pathlib import Path
from PIL import Image


class ImageHandler:
    """Handle image extraction, cleaning, and conversion from OCR results"""
    
    def __init__(self, output_format='original', jpeg_quality=95):
        """Initialize ImageHandler
        
        Args:
            output_format: 'original', 'jpg', or 'png'
            jpeg_quality: JPEG quality (1-100) if converting to JPG
        """
        self.output_format = output_format.lower()
        self.jpeg_quality = jpeg_quality
        
        if self.output_format not in ['original', 'jpg', 'png']:
            raise ValueError("output_format must be 'original', 'jpg', or 'png'")
        
        if not 1 <= jpeg_quality <= 100:
            raise ValueError("jpeg_quality must be between 1 and 100")
    
    def find_image_start(self, data):
        """Find the actual start of image data by looking for format markers.
        
        Args:
            data: Raw image bytes
            
        Returns:
            tuple: (start_position, format) or (None, None) if not found
        """
        # JPEG: FF D8 FF
        jpeg_start = None
        for i in range(len(data) - 2):
            if data[i:i+3] == b'\xff\xd8\xff':
                jpeg_start = i
                break
        
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        png_start = data.find(b'\x89PNG\r\n\x1a\n')
        
        # GIF: GIF8
        gif_start = data.find(b'GIF8')
        
        # Return the earliest valid start position
        valid_starts = [(pos, fmt) for pos, fmt in [
            (jpeg_start, 'jpg'),
            (png_start, 'png'),
            (gif_start, 'gif')
        ] if pos is not None and pos >= 0]
        
        if valid_starts:
            pos, fmt = min(valid_starts, key=lambda x: x[0])
            return pos, fmt
        
        return None, None
    
    def process_image(self, image_base64, output_path, page_index, image_index):
        """Process and save an image from base64 data
        
        Args:
            image_base64: Base64 encoded image string
            output_path: Directory to save the image
            page_index: Page number
            image_index: Image number on the page
            
        Returns:
            dict: Result with 'success', 'path', 'size', and optional 'error'
        """
        try:
            # Decode base64
            img_data = base64.b64decode(image_base64)
            
            # Find actual image start
            img_start, img_format = self.find_image_start(img_data)
            
            if img_start is None:
                # Save as binary for manual inspection
                img_path = output_path / f"page_{page_index}_figure_{image_index}.bin"
                with open(img_path, "wb") as f:
                    f.write(img_data)
                return {
                    'success': False,
                    'path': img_path,
                    'error': 'Could not identify image format'
                }
            
            # Clean image data
            clean_data = img_data[img_start:]
            
            # Open with Pillow
            pil_img = Image.open(io.BytesIO(clean_data))
            
            # Determine output format
            if self.output_format == 'original':
                final_format = img_format
            elif self.output_format == 'jpg':
                final_format = 'jpg'
                if pil_img.mode in ('RGBA', 'LA', 'P'):
                    pil_img = pil_img.convert('RGB')
            else:  # png
                final_format = 'png'
            
            # Generate output path
            img_path = output_path / f"page_{page_index}_figure_{image_index}.{final_format}"
            
            # Save image
            if final_format == 'jpg':
                pil_img.save(img_path, "JPEG", quality=self.jpeg_quality)
            elif final_format == 'png':
                pil_img.save(img_path, "PNG")
            else:
                pil_img.save(img_path, img_format.upper())
            
            return {
                'success': True,
                'path': img_path,
                'size': pil_img.size,
                'format': final_format
            }
            
        except Exception as e:
            # Fallback: save raw cleaned data if available
            try:
                if img_start is not None:
                    img_path = output_path / f"page_{page_index}_figure_{image_index}_raw.{img_format}"
                    with open(img_path, "wb") as f:
                        f.write(clean_data)
                    return {
                        'success': False,
                        'path': img_path,
                        'error': f'Pillow processing failed: {str(e)}, saved raw data'
                    }
            except:
                pass
            
            return {
                'success': False,
                'path': None,
                'error': str(e)
            }