import sys
import subprocess

try:
    from PIL import Image, ImageDraw
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw

def remove_background(img_path):
    img = Image.open(img_path).convert("RGBA")
    
    # Get top-left pixel color as the background to remove
    bg_color = img.getpixel((0, 0))
    
    # Use floodfill to make background transparent
    # thresh=30 allows for slight compression artifacts in the black background
    ImageDraw.floodfill(img, (0, 0), (255, 255, 255, 0), thresh=30)
    ImageDraw.floodfill(img, (img.width-1, 0), (255, 255, 255, 0), thresh=30)
    ImageDraw.floodfill(img, (0, img.height-1), (255, 255, 255, 0), thresh=30)
    ImageDraw.floodfill(img, (img.width-1, img.height-1), (255, 255, 255, 0), thresh=30)
    
    img.save(img_path)
    print("Background removed successfully.")

if __name__ == "__main__":
    remove_background(r"c:\Users\VICTUS\OneDrive\Attachments\Desktop\igrris\frontend-web\public\logo_red_eyes.png")
