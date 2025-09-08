# generate_curve_cv2.py
import os
import time
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from astropy.io import fits
plt.rcParams['font.family'] = 'DejaVu Sans'

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_BASE_DIR = os.path.join(BASE_DIR, "..", "image_files")
CAMERA_IMG_DIR = os.path.join(IMAGE_BASE_DIR, "spectrum_camera_img/Light")
CURVE_IMG_DIR = os.path.join(IMAGE_BASE_DIR, "spectrum_curve_img")

os.makedirs(CURVE_IMG_DIR, exist_ok=True)

processed_files = set()
VALID_EXTENSIONS = (".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".fits")

# ---- (A) 보정용 시작/끝 파장 (사용자가 직접 입력해야 함) ----
LAMBDA_START = 693.0609   # nm, 예: 0번 픽셀이 400nm
LAMBDA_END   = 415.5012   # nm, 예: 마지막 픽셀이 700nm


def load_image_array(file_path):
    """이미지/ FITS 파일을 불러와 NumPy 배열로 반환"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".fits":
        with fits.open(file_path) as hdul:
            arr = hdul[0].data
            if arr.dtype != np.uint16:
                arr = arr.astype(np.uint16)
    else:
        arr = np.array(Image.open(file_path)).astype(np.uint16)
    return arr


def process_image(file_path, file_name):
    """이미지를 처리하고 스펙트럼 커브를 저장"""
    base_name, _ = os.path.splitext(file_name)
    save_path = os.path.join(CURVE_IMG_DIR, base_name + ".png")
    if os.path.exists(save_path):
        print(f"[SKIP] Curve already exists: {save_path}")
        return

    img_array = load_image_array(file_path)

    # ---- (1) Debayering (RGGB → RGB) ----
    if img_array.ndim == 2:
        rgb = cv2.cvtColor(img_array, cv2.COLOR_BAYER_RG2BGR)
    else:
        rgb = img_array

    # ---- (2) RGB → Grayscale ----
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY).astype(float)

    # ---- (3) 세로 방향 합산 (열 단위) ----
    spectrum = gray.sum(axis=0)
    n_pixels = spectrum.size

    # ---- (4) 픽셀 → nm 선형 보간 ----
    x_pixels = np.arange(n_pixels)
    x_nm = np.linspace(LAMBDA_START, LAMBDA_END, n_pixels)

    print(f"[DEBUG] Pixel range: 0 ~ {n_pixels-1}, "
          f"Wavelength range: {LAMBDA_START:.2f} nm → {LAMBDA_END:.2f} nm")

    # ---- (5) 그래프 그리기 ----
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(x_nm, spectrum, color="black", linewidth=1)
    ax.set_xlabel("Wavelength (nm)", fontsize=12)
    ax.set_ylabel("Intensity (sum over y)", fontsize=12)
    ax.set_title(file_name, fontsize=12)
    ax.invert_xaxis()  # 스펙트럼 보정 방향에 따라 유지/삭제 가능

    xmin, xmax = x_nm.min(), x_nm.max()
    x_ticks = np.linspace(xmin, xmax, 11)
    x_ticks = np.round(x_ticks).astype(int)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_ticks)

    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Saved curve: {save_path}")


def main():
    print("[INFO] Monitoring folder for new images...")
    while True:
        files = sorted(f for f in os.listdir(CAMERA_IMG_DIR) if f.lower().endswith(VALID_EXTENSIONS))
        for f in files:
            if f not in processed_files:
                file_path = os.path.join(CAMERA_IMG_DIR, f)
                process_image(file_path, f)
                processed_files.add(f)
        time.sleep(1)


if __name__ == "__main__":
    main()
