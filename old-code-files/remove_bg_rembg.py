import sys
import subprocess
import os

try:
    import rembg
    from PIL import Image
except ImportError:
    print("Installing rembg...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg", "Pillow"])
    import rembg
    from PIL import Image

def remove_background(img_path):
    print(f"Removing background for {img_path}...")
    with open(img_path, 'rb') as i:
        with open(img_path, 'wb') as o:
            input_img = i.read()
            output_img = rembg.remove(input_img)
            o.write(output_img)
    print("Background removed successfully.")

if __name__ == "__main__":
    img_path = r"c:\Users\VICTUS\OneDrive\Attachments\Desktop\igrris\frontend-web\public\logo_red_eyes_transparent.png"
    if os.path.exists(img_path):
        remove_background(img_path)
    else:
        print("File not found!")
