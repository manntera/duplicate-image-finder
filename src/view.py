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
        """UIのセットアップ"""
        self._root.title(Config.WINDOW_TITLE)
        self._style = ttk.Style()
        self._style.theme_use("clam")

        self._frame_images = ttk.Frame(self._root, padding="10 10 10 10")
        self._frame1 = ttk.Frame(self._frame_images, padding="10 10 10 10", relief="sunken")
        self._frame2 = ttk.Frame(self._frame_images, padding="10 10 10 10", relief="sunken")
        self._label1 = ttk.Label(self._root, font=Config.FONT)
        self._label2 = ttk.Label(self._root, font=Config.FONT)
        self._panel1 = ttk.Label(self._frame1, anchor="center")
        self._panel2 = ttk.Label(self._frame2, anchor="center")
        self._status_label = ttk.Label(self._root, font=Config.FONT)
        self._progress_frame = ttk.Frame(self._root, padding="10 10 10 10")
        self._progress_description_label = ttk.Label(self._progress_frame, text="画像の読み込み進捗：", font=Config.FONT, justify="center")
        self._progress = ttk.Progressbar(self._progress_frame)
        self._progress_label = ttk.Label(self._progress_frame, font=Config.FONT, justify="center")
        self._instruction_label = ttk.Label(self._root, text=Config.INSTRUCTION_TEXT, font=Config.FONT, justify="left")
        self._pending_count_label = ttk.Label(self._root, font=Config.FONT, justify="left")

        self._layout_ui()

    def _layout_ui(self):
        """UIのレイアウトを設定"""
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
        self._progress.config(orient="horizontal", length=Config.PROGRESS_BAR_LENGTH, mode="determinate")
        self._progress_label.grid(row=0, column=2, padx=(10, 0), sticky="w")
        self._pending_count_label.grid(row=5, column=0, pady=(0, 10), columnspan=2)

        self._configure_grid()

    def _configure_grid(self):
        """Gridの列幅を調整"""
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_columnconfigure(1, weight=1)
        self._root.grid_rowconfigure(1, weight=1)
        self._frame_images.grid_columnconfigure(0, weight=1)
        self._frame_images.grid_columnconfigure(1, weight=1)
        self._frame_images.grid_rowconfigure(0, weight=1)
        self._progress_frame.grid_columnconfigure(0, weight=1)
        self._progress_frame.grid_columnconfigure(1, weight=3)
        self._progress_frame.grid_columnconfigure(2, weight=1)

    def _resize_image(self, image_path: str, frame_size: Tuple[int, int]):
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

    def setInstructionText(self, text: str):
        """操作方法のUIを更新"""
        self._instruction_label.config(text=text)

    def setFrameImageA(self, image_path: str):
        """左枠の画像を更新"""
        frame_size = (self._frame1.winfo_width(), self._frame1.winfo_height())
        image_data = self._resize_image(image_path, frame_size)
        self._panel1.config(image=image_data)
        self._panel1.image = image_data

    def setFrameTextA(self, text: str):
        """左枠の文字表示を更新"""
        self._label1.config(text=text)

    def setFrameImageB(self, image_path: str):
        """右枠の画像を更新"""
        frame_size = (self._frame2.winfo_width(), self._frame2.winfo_height())
        image_data = self._resize_image(image_path, frame_size)
        self._panel2.config(image=image_data)
        self._panel2.image = image_data

    def setFrameTextB(self, text: str):
        """右枠の文字表示を更新"""
        self._label2.config(text=text)

    def setStatusText(self, text: str):
        """status_labelの文字列を更新"""
        self._status_label.config(text=text)

    def setProgress(self, max_value: int, current_value: int):
        """プログレスバーとパーセント表記を更新"""
        self._progress["maximum"] = max_value
        self._progress["value"] = current_value
        percent = (current_value / max_value) * 100
        self._progress_label.config(text=f"{percent:.2f}%")

    def setWaitList(self, count: int):
        """待機中の重複画像数を更新"""
        self._pending_count_label.config(text=f"待機中の重複画像数: {count}")
