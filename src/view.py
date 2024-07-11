import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from config import Config
from typing import Tuple


class UIComponents:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_ui()

    def setup_ui(self):
        """UIのセットアップ"""
        self.root.title(Config.WINDOW_TITLE)
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.frame_images = ttk.Frame(self.root, padding="10 10 10 10")
        self.frame1 = ttk.Frame(self.frame_images, padding="10 10 10 10", relief="sunken")
        self.frame2 = ttk.Frame(self.frame_images, padding="10 10 10 10", relief="sunken")
        self.label1 = ttk.Label(self.frame1, font=Config.FONT)
        self.label2 = ttk.Label(self.frame2, font=Config.FONT)
        self.panel1 = ttk.Label(self.frame1)
        self.panel2 = ttk.Label(self.frame2)
        self.status_label = ttk.Label(self.root, font=Config.FONT)
        self.progress_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.progress_description_label = ttk.Label(self.progress_frame, text="画像の読み込み進捗：", font=Config.FONT, justify="center")
        self.progress = ttk.Progressbar(self.progress_frame)
        self.progress_label = ttk.Label(self.progress_frame, font=Config.FONT, justify="center")
        self.instruction_label = ttk.Label(self.root, text=Config.INSTRUCTION_TEXT, font=Config.FONT, justify="left")
        self.pending_count_label = ttk.Label(self.root, font=Config.FONT, justify="left")

        self.layout_ui()

    def layout_ui(self):
        """UIのレイアウトを設定"""
        self.instruction_label.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w", columnspan=2)
        self.frame_images.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        self.frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.panel1.grid(row=0, column=0, sticky="nsew")
        self.panel2.grid(row=0, column=0, sticky="nsew")
        self.label1.grid(row=1, column=0, pady=5)
        self.label2.grid(row=1, column=0, pady=5)
        self.status_label.grid(row=2, column=0, pady=(0, 5), columnspan=2)
        self.progress_frame.grid(row=3, column=0, pady=(0, 10), padx=10, columnspan=2, sticky="ew")
        self.progress_description_label.grid(row=0, column=0, sticky="e")
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress.config(orient="horizontal", length=Config.PROGRESS_BAR_LENGTH, mode="determinate")
        self.progress_label.grid(row=0, column=2, padx=(10, 0), sticky="w")
        self.pending_count_label.grid(row=4, column=0, pady=(0, 10), columnspan=2)

        self.configure_grid()

    def configure_grid(self):
        """Gridの列幅を調整"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.frame_images.grid_columnconfigure(0, weight=1)
        self.frame_images.grid_columnconfigure(1, weight=1)
        self.frame_images.grid_rowconfigure(0, weight=1)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_columnconfigure(1, weight=3)
        self.progress_frame.grid_columnconfigure(2, weight=1)

    def resize_image(self, image_path: str, frame_size: Tuple[int, int], event: tk.Event = None):
        """画像のリサイズ"""
        if image_path:
            with Image.open(image_path) as img:
                img_ratio = img.width / img.height
                frame_ratio = frame_size[0] / frame_size[1]
                if img_ratio > frame_ratio:
                    new_width = frame_size[0]
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = frame_size[1]
                    new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
