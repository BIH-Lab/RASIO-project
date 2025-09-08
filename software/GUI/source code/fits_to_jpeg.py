# fits_to_rgb_jpeg.py
import os
import time
import numpy as np
from astropy.io import fits
from PIL import Image

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_BASE_DIR = os.path.join(BASE_DIR, "..", "image_files")
LIGHT_DIR = os.path.join(IMAGE_BASE_DIR, "spectrum_camera_img", "Light")
OUTPUT_DIR = os.path.join(IMAGE_BASE_DIR, "spectrum_camera_img")

processed_files = set()


def demosaic_bayer(raw):
    """
    간단한 RGGB Bayer → RGB 변환 (해상도 절반)
    raw: 2D numpy array
    """
    h, w = raw.shape
    rgb = np.zeros((h//2, w//2, 3), dtype=np.float32)

    # R 채널
    rgb[:, :, 0] = raw[0::2, 0::2]
    # G 채널 (두 개 평균)
    rgb[:, :, 1] = (raw[0::2, 1::2] + raw[1::2, 0::2]) / 2
    # B 채널
    rgb[:, :, 2] = raw[1::2, 1::2]

    return rgb


def stretch_asinh(data, scale=1000):
    """
    asinh stretch: 천문학 이미지에서 자주 사용
    """
    data = np.nan_to_num(data)
    data = data - np.min(data)
    if np.max(data) > 0:
        data = data / np.max(data)
    return np.arcsinh(scale * data) / np.arcsinh(scale)


def stretch_rgb(rgb, scale=500):
    """
    RGB 전체 강도를 기준으로 asinh stretch 적용
    (채널 간 색 비율 유지 → 색 보존)
    """
    # 채널 합으로 밝기(intensity) 계산
    intensity = np.mean(rgb, axis=2)

    # 스트레치된 밝기
    stretched_intensity = stretch_asinh(intensity, scale=scale)

    # 원래 채널 비율 계산
    total = np.sum(rgb, axis=2, keepdims=True) + 1e-6  # 0 나눗셈 방지
    ratio = rgb / total

    # 색 비율은 유지하고 밝기만 조정
    rgb_stretched = ratio * stretched_intensity[:, :, None]

    return rgb_stretched


def convert_fits_to_jpeg(file_path, file_name):
    base_name, _ = os.path.splitext(file_name)
    save_path = os.path.join(OUTPUT_DIR, base_name + ".jpg")

    if os.path.exists(save_path):
        print(f"[SKIP] JPEG already exists: {save_path}")
        return

    with fits.open(file_path) as hdul:
        raw_data = hdul[0].data.astype(np.float32)

    if raw_data is None:
        print(f"[ERROR] FITS has no data: {file_name}")
        return

    # NaN 처리
    raw_data = np.nan_to_num(raw_data)

    # Bayer → RGB 변환
    rgb_image = demosaic_bayer(raw_data)

    # 전체 강도를 기준으로 스트레치 (색 보존)
    rgb_image = stretch_rgb(rgb_image, scale=500)

    # 0~255 변환
    rgb_image = (rgb_image * 255).astype(np.uint8)

    # 상하 반전 (원래 코드 유지)
    rgb_image = np.flipud(rgb_image)

    # JPEG 저장
    img = Image.fromarray(rgb_image, mode="RGB")
    img.save(save_path, "JPEG", quality=95)
    print(f"[INFO] Saved JPEG: {save_path}")


def main():
    print("[INFO] Monitoring folder for new FITS files...")
    while True:
        try:
            fits_files = sorted(f for f in os.listdir(LIGHT_DIR) if f.lower().endswith(".fits"))
        except FileNotFoundError:
            print(f"[ERROR] Directory not found: {LIGHT_DIR}")
            time.sleep(5)
            continue

        for f in fits_files:
            if f not in processed_files:
                file_path = os.path.join(LIGHT_DIR, f)
                try:
                    convert_fits_to_jpeg(file_path, f)
                    processed_files.add(f)
                except Exception as e:
                    print(f"[ERROR] Failed to process {f}: {e}")

        time.sleep(2)


if __name__ == "__main__":
    main()
