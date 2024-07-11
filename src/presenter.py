import os
import shutil
import threading
import tkinter as tk
from typing import Tuple
from model import DuplicateImageFinder
from view import UIComponents
import psutil
from config import Config
import signal


class DuplicateImagePresenter:
    def __init__(self, root: tk.Tk, finder: DuplicateImageFinder, view: UIComponents):
        self.root = root
        self.finder = finder
        self.view = view
        self.current_image_paths = [None, None]
        self.setup_bindings()
        self.monitor_thread = threading.Thread(target=self.monitor_resources)
        self.finder_thread = None
        self._shutdown_requested = False

        self.finder.on_progress_update.add_listener(self.update_progress)
        self.finder.on_duplicate_found.add_listener(self.handle_duplicate_found)
        self.finder.on_processing_complete.add_listener(self.handle_processing_complete)

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self._shutdown_requested = True
        print("\nShutdown requested. Cleaning up...")
        self.on_closing()

    def setup_bindings(self):
        """キーバインディングとウィンドウクローズイベントの設定"""
        self.root.bind('<Key>', self.handle_keypress)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start(self):
        """アプリの起動"""
        self.update_pending_count()
        self.finder_thread = threading.Thread(target=self.finder.find_duplicates)
        self.finder_thread.start()
        self.monitor_thread.start()
        self.next_image()

    def next_image(self):
        """次の画像を表示"""
        if self._shutdown_requested:
            return
        item = self.finder.get_next_duplicate()
        if item is None:
            if self.finder.is_processing_complete():
                self.handle_processing_complete()
            else:
                self.view.set_status_text("待機中...")
                self.root.after(Config.UI_UPDATE_INTERVAL, self.next_image)
        else:
            self.display_image_pair(item)

    def display_image_pair(self, item: Tuple[str, str]):
        """画像のペアを表示"""
        filepath1, filepath2 = item
        self.view.set_frame_image_a(filepath1)
        self.view.set_frame_image_b(filepath2)
        self.view.set_frame_text_a(os.path.basename(filepath1))
        self.view.set_frame_text_b(os.path.basename(filepath2))
        self.view.set_status_text("重複画像が検出されました")
        self.current_image_paths = [filepath1, filepath2]
        self.update_pending_count()
        self.root.update_idletasks()

    def handle_processing_complete(self):
        """処理完了時のハンドリング"""
        self.view.set_status_text("処理完了")
        self.root.after(2000, self.on_closing)

    def handle_keypress(self, event: tk.Event):
        """キープレスのハンドリング"""
        if event.keysym == 'Left':
            if self.current_image_paths[0] and os.path.exists(self.current_image_paths[0]):
                self.move_to_trash(self.current_image_paths[0])
                self.finder.add_to_delete_list(self.current_image_paths[0])
        elif event.keysym == 'Right':
            if self.current_image_paths[1] and os.path.exists(self.current_image_paths[1]):
                self.move_to_trash(self.current_image_paths[1])
                self.finder.add_to_delete_list(self.current_image_paths[1])
        self.next_image()

    def move_to_trash(self, file_path: str):
        """ファイルをゴミ箱に移動"""
        trash_folder = self.finder.get_trash_folder()
        if not os.path.exists(trash_folder):
            os.makedirs(trash_folder)
        shutil.move(file_path, os.path.join(trash_folder, os.path.basename(file_path)))

    def on_closing(self):
        """ウィンドウクローズ時のハンドリング"""
        self.finder.stop()
        self._shutdown_requested = True
        self.root.quit()
        self.root.destroy()

    def update_progress(self, value: float):
        """進捗の更新"""
        self.view.set_progress(100, value)
        self.root.update_idletasks()

    def update_pending_count(self):
        """待機中の画像数を更新"""
        pending_count = self.finder.get_pending_count()
        self.view.set_wait_list(pending_count)
        self.root.update_idletasks()

    def handle_duplicate_found(self, filepath1: str, filepath2: str):
        """重複が見つかった時のハンドリング"""
        self.update_pending_count()

    def monitor_resources(self):
        """リソースの監視"""
        while not self.finder.is_processing_complete() and not self._shutdown_requested:
            cpu_usage = psutil.cpu_percent(interval=Config.RESOURCE_CHECK_INTERVAL)
            mem_usage = psutil.virtual_memory().percent
            print(f"CPU Usage: {cpu_usage}% | Memory Usage: {mem_usage}%")
            if cpu_usage > Config.HIGH_RESOURCE_THRESHOLD or mem_usage > Config.HIGH_RESOURCE_THRESHOLD:
                print("High resource usage detected.")