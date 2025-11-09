"""
HEIC to JPG Converter
Converts HEIC images to JPG format with quality preservation
"""
import sys
import os
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF opener with Pillow
register_heif_opener()

def convert_heic_to_jpg(input_path, output_path=None, quality=95):
    """
    Convert a HEIC file to JPG
    
    Args:
        input_path: Path to input HEIC file
        output_path: Path to output JPG file (optional, defaults to same name with .jpg)
        quality: JPG quality (1-100, default 95)
    """
    try:
        input_path = Path(input_path)
        
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            return False
            
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.with_suffix('.jpg')
        else:
            output_path = Path(output_path)
        
        # Open and convert
        print(f"Converting: {input_path.name}")
        image = Image.open(input_path)
        
        # Convert to RGB if necessary (HEIC can have alpha channel)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save as JPG
        image.save(output_path, 'JPEG', quality=quality, optimize=True)
        print(f"✓ Saved: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error converting {input_path.name}: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("HEIC to JPG Converter")
        print("\nUsage:")
        print("  python heic_converter.py <file1.heic> [file2.heic] [file3.heic] ...")
        print("  python heic_converter.py <folder>")
        print("\nOptions:")
        print("  Drag and drop HEIC files onto this script")
        print("  Or provide file paths as arguments")
        sys.exit(1)
    
    files_to_convert = []
    
    # Process arguments
    for arg in sys.argv[1:]:
        path = Path(arg)
        
        if path.is_file() and path.suffix.lower() in ['.heic', '.heif']:
            files_to_convert.append(path)
        elif path.is_dir():
            # Find all HEIC files in directory
            heic_files = list(path.glob('*.heic')) + list(path.glob('*.HEIC')) + \
                        list(path.glob('*.heif')) + list(path.glob('*.HEIF'))
            files_to_convert.extend(heic_files)
        else:
            print(f"Skipping: {arg} (not a HEIC file or directory)")
    
    if not files_to_convert:
        print("No HEIC files found to convert!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Convert all files
    print(f"\nFound {len(files_to_convert)} file(s) to convert\n")
    
    success_count = 0
    for file_path in files_to_convert:
        if convert_heic_to_jpg(file_path):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Conversion complete: {success_count}/{len(files_to_convert)} successful")
    print(f"{'='*50}")
    
    # Pause so user can see results
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
