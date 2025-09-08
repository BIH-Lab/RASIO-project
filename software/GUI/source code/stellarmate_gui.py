import tkinter as tk
from tkinter import Tk
import sys
import os
from PIL import Image, ImageTk
from astropy.io import fits
import numpy as np
import re

# 자연 정렬을 위한 함수
def natural_sort_key(s):
    # 파일 이름에서 숫자 부분을 찾아 정렬 키로 사용
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # GUI 폴더
IMAGE_BASE_DIR = os.path.join(BASE_DIR, "..", "image_files")  # image_files 폴더

VALID_EXTENSIONS = (".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".fits")  # 지원 확장자

class SideWindow(tk.Toplevel):
    def __init__(self, root, white_overlay):
        super().__init__(root)
        self.white_overlay = white_overlay

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        print(f"SideWindow - Screen resolution: {screen_width}x{screen_height}")

        # 창 설정
        self.overrideredirect(True)
        self.attributes('-topmost', True)

        bar = 52
        win_width = screen_width // 5
        win_height = screen_height
        self.geometry(f"{win_width}x{win_height-bar}+0+{bar}")
        self.update_idletasks()
        print(f"SideWindow geometry: {win_width}x{win_height-bar}+0+{bar}")

        # 버튼 2개
        btn_height = (screen_height - bar) // 2

        self.btn_top = tk.Button(
            self,
            text="control",
            font=("Arial", 24),
            command=self.show_background,
            borderwidth=0
        )
        self.btn_top.place(x=0, y=0, width=win_width, height=btn_height)

        self.btn_bottom = tk.Button(
            self,
            text="data",
            font=("Arial", 24),
            command=self.show_white,
            borderwidth=0
        )
        self.btn_bottom.place(x=0, y=btn_height, width=win_width, height=btn_height)

    def show_background(self):
        self.white_overlay.withdraw()
        print("WhiteOverlay hidden")

    def show_white(self):
        # 최신 index로 이동
        max_index = self.white_overlay.get_max_index()
        self.white_overlay.current_index = max_index if max_index > 0 else 1
        self.white_overlay.deiconify()
        self.white_overlay.update_images()
        self.white_overlay.update_idletasks()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        bar = 52
        win_width = screen_width * 4 // 5
        win_height = screen_height
        self.white_overlay.geometry(f"{win_width}x{win_height-bar}+{screen_width//5}+{bar}")
        self.white_overlay.lower(self)
        self.lift()
        print(f"WhiteOverlay shown at: {win_width}x{win_height-bar}+{screen_width//5}+{bar}")

    def destroy(self):
        self.white_overlay.destroy()
        super().destroy()
        sys.exit()

class WhiteOverlay(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        print(f"WhiteOverlay - Screen resolution: {self.screen_width}x{self.screen_height}")

        self.overrideredirect(True)
        self.attributes('-topmost', False)

        bar = 52
        win_width = self.screen_width * 4 // 5
        win_height = self.screen_height
        self.geometry(f"{win_width}x{win_height-bar}+{self.screen_width//5}+{bar}")
        self.update_idletasks()
        print(f"WhiteOverlay geometry: {win_width}x{win_height-bar}+{self.screen_width//5}+{bar}")

        # 테두리 프레임
        border_thickness = 2
        self.border_frame = tk.Frame(self, bg="black", highlightthickness=0)
        self.border_frame.place(x=0, y=0, width=win_width, height=win_height-bar)

        # 내부 프레임
        self.inner_frame = tk.Frame(self.border_frame, bg="white", highlightthickness=0)
        self.inner_frame.place(
            x=border_thickness,
            y=border_thickness,
            width=win_width - 2 * border_thickness,
            height=win_height - bar - 2 * border_thickness
        )

        # 폴더
        self.guide_folder = os.path.join(IMAGE_BASE_DIR, "guide_camera_img")
        self.spec_folder = os.path.join(IMAGE_BASE_DIR, "spectrum_camera_img")
        self.curve_folder = os.path.join(IMAGE_BASE_DIR, "spectrum_curve_img")
        self.current_index = 1

        # 이미지 라벨
        self.guide_image_label = tk.Label(self.inner_frame, bg="white")
        self.spec_image_label = tk.Label(self.inner_frame, bg="white")
        self.curve_image_label = tk.Label(self.inner_frame, bg="white")

        # 파일 이름 라벨
        self.filename_label = tk.Label(
            self.inner_frame, font=("Arial", 12), bg="white", anchor="center"
        )
        self.filename_label.place(
            x=100,
            y=self.screen_height * 9 // 10 - bar,
            width=win_width * 4 // 5,
            height=(win_height - bar) // 10
        )

        # 좌우 버튼
        arrow_width = 75
        arrow_height = 75
        self.left_btn = tk.Button(
            self.inner_frame, text="<", font=("Arial", 64), command=self.prev_image
        )
        self.left_btn.place(
            x=10,
            y=(self.screen_height - bar) // 2 - arrow_height // 2,
            width=arrow_width,
            height=arrow_height
        )

        self.right_btn = tk.Button(
            self.inner_frame, text=">", font=("Arial", 64), command=self.next_image
        )
        self.right_btn.place(
            x=win_width - 2 * border_thickness - arrow_width - 10,
            y=(self.screen_height - bar) // 2 - arrow_height // 2,
            width=arrow_width,
            height=arrow_height
        )

        self.update_images()
        self.withdraw()

    def get_file_list(self, folder):
        # 파일 목록을 자연 정렬로 반환
        return sorted(
            [f for f in os.listdir(folder) if f.lower().endswith(VALID_EXTENSIONS)],
            key=natural_sort_key
        )[::-1]  # 최신 파일이 먼저 오도록 역순 정렬

    def get_max_index(self):
        return max(len(self.get_file_list(self.guide_folder)),
                   len(self.get_file_list(self.spec_folder)),
                   len(self.get_file_list(self.curve_folder)))

    def update_images(self):
        guide_files = self.get_file_list(self.guide_folder)
        spec_files = self.get_file_list(self.spec_folder)
        curve_files = self.get_file_list(self.curve_folder)

        # 화면별로 묶음 (앞에서부터 채우고, 부족하면 None)
        frames = []
        for i in range(max(len(guide_files), len(spec_files), len(curve_files))):
            g = guide_files[i] if i < len(guide_files) else None
            s = spec_files[i] if i < len(spec_files) else None
            c = curve_files[i] if i < len(curve_files) else None
            frames.append((g, s, c))

        # 역순으로 화면 배열 
        frames = frames[::-1]

        max_index = len(frames)
        if self.current_index > max_index:
            self.current_index = max_index

        if max_index == 0:
            self.filename_label.config(text="No images available")
            self.guide_image_label.config(image="")
            self.spec_image_label.config(image="")
            self.curve_image_label.config(image="")
            return

        guide_file, spec_file, curve_file = frames[self.current_index - 1]

        guide_file = os.path.join(self.guide_folder, guide_file) if guide_file else None
        spec_file = os.path.join(self.spec_folder, spec_file) if spec_file else None
        curve_file = os.path.join(self.curve_folder, curve_file) if curve_file else None

        # 파일 이름 라벨
        self.filename_label.config(
            text=f"Guide: {os.path.basename(guide_file) if guide_file else '-'} | "
                 f"Spec: {os.path.basename(spec_file) if spec_file else '-'} | "
                 f"Curve: {os.path.basename(curve_file) if curve_file else '-'}"
        )

        # 표시 함수
        def display_image(path, label, width_ratio, height_ratio, x_pos, y_pos):
            if path and os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                if ext == ".fits":
                    # FITS 열기
                    with fits.open(path) as hdul:
                        img_array = hdul[0].data.astype(float)
                        # RGB나 다차원일 경우 합산
                        if img_array.ndim > 2:
                            img_array = img_array.sum(axis=2)
                        # PIL 이미지로 변환
                        img_array = np.nan_to_num(img_array)  # NaN 0으로
                        img_min, img_max = img_array.min(), img_array.max()
                        # 0~255 스케일로 변환
                        img_array = ((img_array - img_min) / max(img_max - img_min, 1e-8) * 255).astype(np.uint8)
                        img = Image.fromarray(img_array)
                else:
                    img = Image.open(path)

                # 크기 조정
                img_width = self.screen_width * width_ratio // 100
                img_height = int(img.height * img_width / img.width)
                img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo)
                label.image = photo
                label.place(x=x_pos, y=y_pos, width=img_width, height=img_height)
            else:
                label.config(image="")

        # 가이드
        display_image(
            guide_file, self.guide_image_label, 39, 25,
            (self.screen_width * 4 // 5) // 4 - (self.screen_width * 39 // 100) // 2,
            (self.screen_height - 52) // 4 - self.screen_height // 5
        )

        # 스펙트럼
        display_image(
            spec_file, self.spec_image_label, 39, 25,
            self.screen_width * 2 // 5 + (self.screen_width * 4 // 5) // 4 - (self.screen_width * 39 // 100) // 2,
            (self.screen_height - 52) // 4 - self.screen_height // 5
        )

        # 커브
        if curve_file and os.path.exists(curve_file):
            img = Image.open(curve_file)
            new_width = self.screen_width * 15 // 25
            new_height = new_width // 3
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.curve_photo = ImageTk.PhotoImage(img)
            self.curve_image_label.config(image=self.curve_photo)
            self.curve_image_label.image = self.curve_photo
            self.curve_image_label.place(
                x=(self.screen_width * 4 // 5) // 2 - new_width // 2,
                y=(self.screen_height - 52) * 3 // 4 - new_height // 2 - 20,
                width=new_width,
                height=new_height
            )
        else:
            self.curve_image_label.config(image="")

    def prev_image(self):
        if self.current_index > 1:
            self.current_index -= 1
            self.update_images()

    def next_image(self):
        max_index = self.get_max_index()
        if self.current_index < max_index:
            self.current_index += 1
            self.update_images()

    def destroy(self):
        self.guide_image_label.destroy()
        self.spec_image_label.destroy()
        self.curve_image_label.destroy()
        super().destroy()

def main():
    root = Tk()
    root.withdraw()

    white_overlay = WhiteOverlay(root)
    win = SideWindow(root, white_overlay)

    root.mainloop()

if __name__ == "__main__":
    main()