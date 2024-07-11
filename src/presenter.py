import os
import shutil
import threading
import tkinter as tk
from typing import Tuple
from model import DuplicateImageFinder
from view import UIComponents
import psutil
from config import Config


class DuplicateImagePresenter:
    def __init__(self, root: tk.Tk, finder: DuplicateImageFinder, view: UIComponents):
        self.root = root
        self.finder = finder
        self.view = view
        self.setup_bindings()
        self.monitor_thread = threading.Thread(target=self.monitor_resources)

    def setup_bindings(self):
        """キーバインディングとウィンドウクローズイベントの設定"""
        self.root.bind('<Key>', self.handle_keypress)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start(self):
        """アプリの起動"""
        self.update_pending_count()
        self.next_image()
        self.monitor_thread.start()

    def next_image(self):
        """次の画像を表示"""
        if not self.finder.result_queue.empty():
            item = self.finder.result_queue.get()
            if item is None:
                self.handle_processing_complete()
                return
            self.display_image_pair(item)
        else:
            self.view.status_label.config(text="待機中...")
            self.root.after(Config.UI_UPDATE_INTERVAL, self.next_image)

    def display_image_pair(self, item: Tuple[str, str]):
        """画像のペアを表示"""
        filepath1, filepath2 = item
        frame1_size = (self.view.frame1.winfo_width(), self.view.frame1.winfo_height())
        frame2_size = (self.view.frame2.winfo_width(), self.view.frame2.winfo_height())
        img1 = self.view.resize_image(filepath1, frame1_size)
        img2 = self.view.resize_image(filepath2, frame2_size)
        self.view.panel1.config(image=img1)
        self.view.panel1.image = img1
        self.view.panel2.config(image=img2)
        self.view.panel2.image = img2
        self.view.label1.config(text=os.path.basename(filepath1))
        self.view.label2.config(text=os.path.basename(filepath2))
        self.view.status_label.config(text="重複画像が検出されました")
        self.view.panel1.image_path = filepath1
        self.view.panel2.image_path = filepath2
        self.update_pending_count()
        self.root.update_idletasks()

    def handle_processing_complete(self):
        """処理完了時のハンドリング"""
        if self.finder.processing_complete:
            self.view.status_label.config(text="処理完了")
            self.root.after(2000, self.on_closing)
        else:
            self.root.after(Config.UI_UPDATE_INTERVAL, self.next_image)

    def handle_keypress(self, event: tk.Event):
        """キープレスのハンドリング"""
        if event.keysym == 'Left':
            if os.path.exists(self.view.panel1.image_path):
                self.move_to_trash(self.view.panel1.image_path)
                self.finder.to_delete.append(self.view.panel1.image_path)
        elif event.keysym == 'Right':
            if os.path.exists(self.view.panel2.image_path):
                self.move_to_trash(self.view.panel2.image_path)
                self.finder.to_delete.append(self.view.panel2.image_path)
        self.next_image()

    def move_to_trash(self, file_path: str):
        """ファイルをゴミ箱に移動"""
        if not os.path.exists(self.finder.trash_folder):
            os.makedirs(self.finder.trash_folder)
        shutil.move(file_path, os.path.join(self.finder.trash_folder, os.path.basename(file_path)))

    def on_closing(self):
        """ウィンドウクローズ時のハンドリング"""
        self.finder.stop()
        self.root.quit()
        self.root.destroy()

    def update_progress(self, value: float):
        """進捗の更新"""
        self.view.progress["value"] = value
        self.view.progress_label.config(text=f"{value:.3f}%")
        self.root.update_idletasks()

    def update_pending_count(self):
        """待機中の画像数を更新"""
        pending_count = self.finder.result_queue.qsize()
        self.view.pending_count_label.config(text=f"待機中の重複画像数: {pending_count}")
        self.root.update_idletasks()

    def monitor_resources(self):
        """リソースの監視"""
        while not self.finder.stop_event.is_set():
            cpu_usage = psutil.cpu_percent(interval=Config.RESOURCE_CHECK_INTERVAL)
            mem_usage = psutil.virtual_memory().percent
            print(f"CPU Usage: {cpu_usage}% | Memory Usage: {mem_usage}%")
            if cpu_usage > Config.HIGH_RESOURCE_THRESHOLD or mem_usage > Config.HIGH_RESOURCE_THRESHOLD:
                print("High resource usage detected.")
