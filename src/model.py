import os
import queue
import threading
import json
from typing import List, Tuple
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
import cupy as cp
import numpy as np
from config import Config

class Event:
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners.remove(listener)

    def notify(self, *args, **kwargs):
        for listener in self._listeners:
            listener(*args, **kwargs)

class DuplicateImageFinder:
    def __init__(self, image_folder: str, trash_folder: str, similarity_threshold: int, cache_file: str = 'image_hash_cache.json'):
        self._image_folder = image_folder
        self._trash_folder = trash_folder
        self._similarity_threshold = similarity_threshold
        self._cache_file = cache_file
        self._result_queue: queue.Queue = queue.Queue()
        self._to_delete: List[str] = []
        self._stop_event = threading.Event()
        self._total_files = 0
        self._processing_complete = False
        self._lock = threading.Lock()

        self.on_progress_update = Event()
        self.on_duplicate_found = Event()
        self.on_processing_complete = Event()

        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self._cache_file):
            with open(self._cache_file, 'r') as f:
                self._image_hash_cache = json.load(f)
        else:
            self._image_hash_cache = {}

    def _save_cache(self):
        with open(self._cache_file, 'w') as f:
            json.dump(self._image_hash_cache, f)

    def find_duplicates(self):
        image_hashes = {}
        count = 0

        def process_image(filepath: str):
            nonlocal count
            if self._stop_event.is_set() or count >= Config.MAX_IMAGES:
                return
            try:
                image_hash = self._calculate_image_hash(filepath)
                self._check_for_duplicate(filepath, image_hash, image_hashes)
                count += 1
                self._update_progress(count)
                if count % Config.CACHE_SAVE_INTERVAL == 0:  # 定期的にキャッシュを保存
                    self._save_cache()
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

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

        self._processing_complete = True
        self._result_queue.put(None)
        self.on_processing_complete.notify()
        self._save_cache()

    def _calculate_image_hash(self, filepath: str):
        file_mod_time = os.path.getmtime(filepath)
        cache_key = f"{filepath}:{file_mod_time}"

        if cache_key in self._image_hash_cache:
            return imagehash.hex_to_hash(self._image_hash_cache[cache_key])

        with Image.open(filepath) as image:
            image.thumbnail((500, 500))
            image_array = np.array(image)
            image_gpu = cp.asarray(image_array)
            image_hash = imagehash.phash(Image.fromarray(cp.asnumpy(image_gpu)))

        self._image_hash_cache[cache_key] = str(image_hash)
        return image_hash

    def _check_for_duplicate(self, filepath: str, image_hash, image_hashes: dict):
        with self._lock:
            if filepath in image_hashes.values():
                return

            for existing_hash, existing_path in image_hashes.items():
                if abs(image_hash - existing_hash) <= self._similarity_threshold:
                    self._result_queue.put((filepath, existing_path))
                    self.on_duplicate_found.notify(filepath, existing_path)
                    return

            image_hashes[image_hash] = filepath

    def _update_progress(self, count: int):
        progress = (count / self._total_files) * 100
        self.on_progress_update.notify(progress)

    def _get_all_image_files(self) -> List[str]:
        all_files = []
        for root, _, files in os.walk(self._image_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    all_files.append(os.path.join(root, file))
        return all_files

    def stop(self):
        self._stop_event.set()
        self._save_cache()  # 停止時にキャッシュを保存

    def get_next_duplicate(self) -> Tuple[str, str] | None:
        return self._result_queue.get() if not self._result_queue.empty() else None

    def add_to_delete_list(self, filepath: str):
        self._to_delete.append(filepath)

    def is_processing_complete(self) -> bool:
        return self._processing_complete

    def get_trash_folder(self) -> str:
        return self._trash_folder

    def get_pending_count(self) -> int:
        return self._result_queue.qsize()
