import cv2
import numpy as np
from PIL import Image

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    レシート画像を前処理してOCR精度を向上させる
    
    処理内容:
    1. グレースケール化
    2. リサイズ（高解像度化）
    3. ノイズ除去
    4. コントラスト強調
    5. Otsu二値化
    """
    # PIL ImageをOpenCV形式に変換
    img_array = np.array(image)
    
    # RGBからBGRに変換（OpenCVはBGR形式）
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # グレースケール化
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array
    
    # 高解像度化（幅2000pxにリサイズ）
    height, width = gray.shape
    if width < 2000:
        scale = 2000 / width
        new_width = 2000
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # ノイズ除去（Non-local Means Denoising）
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # コントラスト強調（CLAHE）
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Otsu二値化（自動閾値）
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # PIL Imageに戻す
    result = Image.fromarray(binary)
    
    return result


def resize_image(image: Image.Image, max_width: int = 2000) -> Image.Image:
    """
    画像を適切なサイズにリサイズ（OCR精度向上のため）
    """
    width, height = image.size
    
    if width > max_width:
        ratio = max_width / width
        new_height = int(height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    elif width < 1500:
        # 小さすぎる画像は拡大
        ratio = 1500 / width
        new_height = int(height * ratio)
        image = image.resize((1500, new_height), Image.Resampling.LANCZOS)
    
    return image
