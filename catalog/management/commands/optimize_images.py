from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image
import os

class Command(BaseCommand):
    help = 'Optimize images and create WebP versions'

    def handle(self, *args, **options):
        media_dir = os.path.join(settings.BASE_DIR, 'media/products')
        
        if not os.path.exists(media_dir):
            self.stdout.write('Media directory not found')
            return
        
        sizes = {
            'small': (360, 270),
            'medium': (480, 360),
            'large': (800, 600),
        }
        
        for filename in os.listdir(media_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(media_dir, filename)
                base_path = os.path.splitext(filepath)[0]
                
                try:
                    img = Image.open(filepath)
                    
                    # Convert to RGB
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    
                    # Create multiple sizes
                    for size_name, size in sizes.items():
                        # JPEG version
                        img_copy = img.copy()
                        img_copy.thumbnail(size, Image.Resampling.LANCZOS)
                        jpeg_path = f"{base_path}_{size_name}.jpg"
                        img_copy.save(jpeg_path, 'JPEG', quality=80, optimize=True)
                        self.stdout.write(f'✓ Created {os.path.basename(jpeg_path)}')
                        
                        # WebP version
                        webp_path = f"{base_path}_{size_name}.webp"
                        img_copy.save(webp_path, 'WEBP', quality=80)
                        self.stdout.write(f'✓ Created {os.path.basename(webp_path)}')
                    
                except Exception as e:
                    self.stdout.write(f'✗ Error processing {filename}: {e}')