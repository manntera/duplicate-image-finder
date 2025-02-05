import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Tuple
from config import Config

class UIComponents:
    def __init__(self, root: tk.Tk):
        self._root = root
        self._setup_ui()

    def _setup_ui(self):
        self._root.title(Config.WINDOW_TITLE)
        self._style = ttk.Style()
        self._style.theme_use("clam")

        self._create_widgets()
        self._layout_widgets()
        self._configure_grid()

    def _create_widgets(self):
        self._frame_images = ttk.Frame(self._root, padding="10")
        self._frame1 = ttk.Frame(self._frame_images, padding="10", relief="sunken")
        self._frame2 = ttk.Frame(self._frame_images, padding="10", relief="sunken")
        self._label1 = ttk.Label(self._root, font=Config.FONT)
        self._label2 = ttk.Label(self._root, font=Config.FONT)
        self._panel1 = ttk.Label(self._frame1, anchor="center")
        self._panel2 = ttk.Label(self._frame2, anchor="center")
        self._status_label = ttk.Label(self._root, font=Config.FONT)
        self._progress_frame = ttk.Frame(self._root, padding="10")
        self._progress_description_label = ttk.Label(self._progress_frame, text="画像の読み込み進捗：", font=Config.FONT, justify="center")
        self._progress = ttk.Progressbar(self._progress_frame, orient="horizontal", length=Config.PROGRESS_BAR_LENGTH, mode="determinate")
        self._progress_label = ttk.Label(self._progress_frame, font=Config.FONT, justify="center")
        self._instruction_label = ttk.Label(self._root, text=Config.INSTRUCTION_TEXT, font=Config.FONT, justify="left")
        self._pending_count_label = ttk.Label(self._root, font=Config.FONT, justify="left")

    def _layout_widgets(self):
        self._instruction_label.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w", columnspan=2)
        self._frame_images.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        self._frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._frame2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self._panel1.grid(row=0, column=0, sticky="nsew")
        self._panel2.grid(row=0, column=0, sticky="nsew")
        self._label1.grid(row=2, column=0, pady=5, padx=10, sticky="n")
        self._label2.grid(row=2, column=1, pady=5, padx=10, sticky="n")
        self._status_label.grid(row=3, column=0, pady=(0, 5), columnspan=2)
        self._progress_frame.grid(row=4, column=0, pady=(0, 10), padx=10, columnspan=2, sticky="ew")
        self._progress_description_label.grid(row=0, column=0, sticky="e")
        self._progress.grid(row=0, column=1, sticky="ew")
        self._progress_label.grid(row=0, column=2, padx=(10, 0), sticky="w")
        self._pending_count_label.grid(row=5, column=0, pady=(0, 10), columnspan=2)

    def _configure_grid(self):
        self._root.grid_columnconfigure((0, 1), weight=1)
        self._root.grid_rowconfigure(1, weight=1)
        self._frame_images.grid_columnconfigure((0, 1), weight=1)
        self._frame_images.grid_rowconfigure(0, weight=1)
        self._progress_frame.grid_columnconfigure(1, weight=3)

    def _resize_image(self, image_path: str, frame_size: Tuple[int, int]):
        if not image_path:
            return None
        
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

    def clear_images(self):
        for panel in (self._panel1, self._panel2):
            panel.config(image='')
            panel.image = None
        for label in (self._label1, self._label2):
            label.config(text='')
    
    def set_instruction_text(self, text: str):
        self._instruction_label.config(text=text)

    def set_frame_image(self, panel: ttk.Label, frame: ttk.Frame, image_path: str):
        frame_size = (frame.winfo_width(), frame.winfo_height())
        image_data = self._resize_image(image_path, frame_size)
        panel.config(image=image_data)
        panel.image = image_data

    def set_frame_image_a(self, image_path: str):
        self.set_frame_image(self._panel1, self._frame1, image_path)

    def set_frame_image_b(self, image_path: str):
        self.set_frame_image(self._panel2, self._frame2, image_path)

    def set_frame_text_a(self, text: str):
        self._label1.config(text=text)

    def set_frame_text_b(self, text: str):
        self._label2.config(text=text)

    def set_status_text(self, text: str):
        self._status_label.config(text=text)

    def set_progress(self, max_value: int, current_value: float):
        self._progress["maximum"] = max_value
        self._progress["value"] = current_value
        percent = (current_value / max_value) * 100
        self._progress_label.config(text=f"{percent:.2f}%")

    def set_wait_list(self, count: int):
        self._pending_count_label.config(text=f"待機中の重複画像数: {count}")