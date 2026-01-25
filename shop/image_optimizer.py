from PIL import Image
import os
from django.conf import settings

class ImageOptimizer:
    """Optimize images to specific sizes"""
    
    SIZES = {
        'thumbnail': (200, 150),
        'small': (360, 270),
        'medium': (480, 360),
        'large': (800, 600),
    }
    
    @staticmethod
    def optimize_image(image_path, size='medium', quality=80):
        """
        Optimize an image to specific size
        Returns optimized image path
        """
        if not os.path.exists(image_path):
            return image_path
        
        try:
            img = Image.open(image_path)
            
            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Resize with aspect ratio preservation
            img.thumbnail(ImageOptimizer.SIZES.get(size, ImageOptimizer.SIZES['medium']), Image.Resampling.LANCZOS)
            
            # Save optimized version
            base_path = os.path.splitext(image_path)[0]
            optimized_path = f"{base_path}_{size}.jpg"
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
            
            # Create WebP version
            webp_path = f"{base_path}_{size}.webp"
            img.save(webp_path, 'WEBP', quality=quality)
            
            return optimized_path
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")
            return image_path