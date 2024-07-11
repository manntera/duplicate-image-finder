import os
import queue
import threading
from typing import Callable, List, Tuple
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
import cupy as cp
import numpy as np
from config import Config


class DuplicateImageFinder:
    def __init__(self, image_folder: str, trash_folder: str, similarity_threshold: int):
        self.image_folder = image_folder
        self.trash_folder = trash_folder
        self.similarity_threshold = similarity_threshold
        self.result_queue: queue.Queue = queue.Queue()
        self.to_delete: List[str] = []
        self.stop_event = threading.Event()
        self.total_files = 0
        self.processing_complete = False
        self.lock = threading.Lock()

    def find_duplicates(self, progress_callback: Callable[[float], None]):
        """重複画像を探す"""
        image_hashes = {}
        count = 0

        def process_image(filepath: str):
            nonlocal count
            if self.stop_event.is_set() or count >= Config.MAX_IMAGES:
                return
            try:
                with Image.open(filepath) as image:
                    image.thumbnail((500, 500))
                    image_array = np.array(image)
                    image_gpu = cp.asarray(image_array)
                    image_hash = imagehash.phash(Image.fromarray(cp.asnumpy(image_gpu)))
                duplicate_found = False
                with self.lock:
                    if filepath in image_hashes.values():
                        return

                    for existing_hash, existing_path in image_hashes.items():
                        if abs(image_hash - existing_hash) <= self.similarity_threshold:
                            self.result_queue.put((filepath, existing_path))
                            duplicate_found = True
                            break

                    if not duplicate_found:
                        image_hashes[image_hash] = filepath
                count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
            if count % 100 == 0:
                progress_callback(min(count / self.total_files * 100, 100))

        all_files = self._get_all_image_files()
        self.total_files = len(all_files)

        with ThreadPoolExecutor(max_workers=Config.INITIAL_NUM_THREADS) as executor:
            for i in range(0, self.total_files, Config.INITIAL_BATCH_SIZE):
                if self.stop_event.is_set():
                    break
                batch = all_files[i:i + Config.INITIAL_BATCH_SIZE]
                futures = [executor.submit(process_image, filepath) for filepath in batch]
                for future in as_completed(futures):
                    future.result()
                    progress_callback(min(count / self.total_files * 100, 100))

        self.processing_complete = True
        self.result_queue.put(None)

    def _get_all_image_files(self) -> List[str]:
        """すべての画像ファイルのリストを取得"""
        all_files = []
        for root, _, files in os.walk(self.image_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    all_files.append(os.path.join(root, file))
        return all_files

    def stop(self):
        """処理を停止"""
        self.stop_event.set()
