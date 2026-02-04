import cv2
import numpy as np
from PIL import Image

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    レシート画像を前処理してOCR精度を向上させる
    
    処理内容:
    1. グレースケール化
    2. ノイズ除去
    3. 適応的二値化
    4. コントラスト強調
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
    
    # ノイズ除去（ガウシアンブラー）
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 適応的二値化（レシートの照明ムラに対応）
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # コントラスト強調（CLAHE）
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(binary)
    
    # PIL Imageに戻す
    result = Image.fromarray(enhanced)
    
    return result


def resize_image(image: Image.Image, max_width: int = 1000) -> Image.Image:
    """
    画像を適切なサイズにリサイズ（OCR精度向上のため）
    """
    width, height = image.size
    
    if width > max_width:
        ratio = max_width / width
        new_height = int(height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    return image
