from PIL import Image
import glob

for f in glob.glob(r'c:\Users\VICTUS\OneDrive\Attachments\Desktop\igrris\frontend-web\public\*.png'):
    try:
        img = Image.open(f)
        print(f, img.size, img.mode)
    except Exception as e:
        print(f, e)
