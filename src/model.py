import os
import queue
import threading
from typing import Callable, List, Tuple, Dict
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
import cupy as cp
import numpy as np
from config import Config

class Event:
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def notify(self, *args, **kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)

class DuplicateImageFinder:
    def __init__(self, image_folder: str, trash_folder: str, similarity_threshold: int):
        self._image_folder = image_folder
        self._trash_folder = trash_folder
        self._similarity_threshold = similarity_threshold
        self._result_queue: queue.Queue = queue.Queue()
        self._to_delete: List[str] = []
        self._stop_event = threading.Event()
        self._total_files = 0
        self._processing_complete = False
        self._lock = threading.Lock()

        # イベント
        self.on_progress_update = Event()
        self.on_duplicate_found = Event()
        self.on_processing_complete = Event()

    def find_duplicates(self):
        """重複画像を探す"""
        image_hashes = {}
        count = 0

        def process_image(filepath: str):
            nonlocal count
            if self._stop_event.is_set() or count >= Config.MAX_IMAGES:
                return
            try:
                with Image.open(filepath) as image:
                    image.thumbnail((500, 500))
                    image_array = np.array(image)
                    image_gpu = cp.asarray(image_array)
                    image_hash = imagehash.phash(Image.fromarray(cp.asnumpy(image_gpu)))
                duplicate_found = False
                with self._lock:
                    if filepath in image_hashes.values():
                        return

                    for existing_hash, existing_path in image_hashes.items():
                        if abs(image_hash - existing_hash) <= self._similarity_threshold:
                            self._result_queue.put((filepath, existing_path))
                            self.on_duplicate_found.notify(filepath, existing_path)
                            duplicate_found = True
                            break

                    if not duplicate_found:
                        image_hashes[image_hash] = filepath
                count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
            if count % 100 == 0:
                self.on_progress_update.notify(min(count / self._total_files * 100, 100))

        all_files = self._get_all_image_files()
        self._total_files = len(all_files)

        with ThreadPoolExecutor(max_workers=Config.INITIAL_NUM_THREADS) as executor:
            for i in range(0, self._total_files, Config.INITIAL_BATCH_SIZE):
                if self._stop_event.is_set():
                    break
                batch = all_files[i:i + Config.INITIAL_BATCH_SIZE]
                futures = [executor.submit(process_image, filepath) for filepath in batch]
                for future in as_completed(futures):
                    future.result()
                    self.on_progress_update.notify(min(count / self._total_files * 100, 100))

        self._processing_complete = True
        self._result_queue.put(None)
        self.on_processing_complete.notify()

    def _get_all_image_files(self) -> List[str]:
        """すべての画像ファイルのリストを取得"""
        all_files = []
        for root, _, files in os.walk(self._image_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    all_files.append(os.path.join(root, file))
        return all_files

    def stop(self):
        """処理を停止"""
        self._stop_event.set()

    def get_next_duplicate(self) -> Tuple[str, str] | None:
        """次の重複画像ペアを取得"""
        if not self._result_queue.empty():
            return self._result_queue.get()
        return None

    def add_to_delete_list(self, filepath: str):
        """削除リストにファイルを追加"""
        self._to_delete.append(filepath)

    def is_processing_complete(self) -> bool:
        """処理が完了したかどうかを返す"""
        return self._processing_complete

    def get_trash_folder(self) -> str:
        """ゴミ箱フォルダのパスを返す"""
        return self._trash_folder

    def get_pending_count(self) -> int:
        """待機中の重複画像ペアの数を返す"""
        return self._result_queue.qsize()