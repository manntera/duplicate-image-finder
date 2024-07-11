import os
import shutil
import threading
from typing import Tuple
import tkinter as tk
import psutil
import signal

from model import DuplicateImageFinder
from view import UIComponents
from config import Config

class DuplicateImagePresenter:
    def __init__(self, root: tk.Tk, finder: DuplicateImageFinder, view: UIComponents):
        self.root = root
        self.finder = finder
        self.view = view
        self.current_image_paths = [None, None]
        self._shutdown_requested = False

        self._setup_event_listeners()
        self._setup_bindings()
        self._setup_threads()

    def _setup_event_listeners(self):
        self.finder.on_progress_update.add_listener(self._update_progress)
        self.finder.on_duplicate_found.add_listener(self._handle_duplicate_found)
        self.finder.on_processing_complete.add_listener(self._handle_processing_complete)

    def _setup_bindings(self):
        self.root.bind('<Key>', self._handle_keypress)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_threads(self):
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.finder_thread = None

    def start(self):
        self._update_pending_count()
        self.finder_thread = threading.Thread(target=self.finder.find_duplicates)
        self.finder_thread.start()
        self.monitor_thread.start()
        self._next_image()

    def _next_image(self):
        if self._shutdown_requested:
            return

        item = self.finder.get_next_duplicate()
        if item is None:
            if self.finder.is_processing_complete():
                self._handle_processing_complete()
            else:
                self.view.set_status_text("待機中...")
                self.root.after(Config.UI_UPDATE_INTERVAL, self._next_image)
        else:
            self._display_image_pair(item)

    def _display_image_pair(self, item: Tuple[str, str]):
        filepath1, filepath2 = item
        self.view.set_frame_image_a(filepath1)
        self.view.set_frame_image_b(filepath2)
        self.view.set_frame_text_a(os.path.basename(filepath1))
        self.view.set_frame_text_b(os.path.basename(filepath2))
        self.view.set_status_text("重複画像が検出されました")
        self.current_image_paths = [filepath1, filepath2]
        self._update_pending_count()
        self.root.update_idletasks()

    def _handle_processing_complete(self):
        self.view.set_status_text("処理完了")
        self.root.after(2000, self._on_closing)

    def _handle_keypress(self, event: tk.Event):
        if event.keysym in ['Left', 'Right']:
            index = 0 if event.keysym == 'Left' else 1
            filepath = self.current_image_paths[index]
            if filepath and os.path.exists(filepath):
                self._move_to_trash(filepath)
                self.finder.add_to_delete_list(filepath)
        self._next_image()

    def _move_to_trash(self, file_path: str):
        trash_folder = self.finder.get_trash_folder()
        os.makedirs(trash_folder, exist_ok=True)
        shutil.move(file_path, os.path.join(trash_folder, os.path.basename(file_path)))

    def _on_closing(self):
        self.finder.stop()
        self._shutdown_requested = True
        self.root.quit()
        self.root.destroy()

    def _update_progress(self, value: float):
        self.view.set_progress(100, value)
        self.root.update_idletasks()

    def _update_pending_count(self):
        pending_count = self.finder.get_pending_count()
        self.view.set_wait_list(pending_count)
        self.root.update_idletasks()

    def _handle_duplicate_found(self, filepath1: str, filepath2: str):
        self._update_pending_count()

    def _monitor_resources(self):
        while not self.finder.is_processing_complete() and not self._shutdown_requested:
            cpu_usage = psutil.cpu_percent(interval=Config.RESOURCE_CHECK_INTERVAL)
            mem_usage = psutil.virtual_memory().percent
            print(f"CPU Usage: {cpu_usage}% | Memory Usage: {mem_usage}%")
            if cpu_usage > Config.HIGH_RESOURCE_THRESHOLD or mem_usage > Config.HIGH_RESOURCE_THRESHOLD:
                print("High resource usage detected.")

    def _signal_handler(self, signum, frame):
        self._shutdown_requested = True
        print("\nShutdown requested. Cleaning up...")
        self._on_closing()