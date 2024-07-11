import os
import shutil
import threading
import queue
from typing import Callable, Tuple, List
from PIL import Image, ImageTk
import imagehash
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import ttk
import psutil
import configparser


class Config:
    MAX_IMAGES = 50000
    INITIAL_NUM_THREADS = 4
    INITIAL_BATCH_SIZE = 100
    WINDOW_TITLE = "Duplicate Image Finder"
    IMAGE_DISPLAY_SIZE = (250, 250)
    PROGRESS_BAR_LENGTH = 200
    RESOURCE_CHECK_INTERVAL = 1
    HIGH_RESOURCE_THRESHOLD = 90
    UI_UPDATE_INTERVAL = 100
    FONT = ("Noto Sans CJK JP", 12)
    INSTRUCTION_TEXT = (
        "操作方法:\n"
        "1. 重複画像が表示されます。\n"
        "2-1. 左右キーを押すと重複した画像がtrash_folderに指定したフォルダに移動します。\n"
        "2-2. 左右キー以外のボタンを押すと移動処理がされません\n"
        "3. 自動的に次の重複画像が表示されます。\n"
        "4. 全ての画像が処理されるとウィンドウが閉じます。"
    )
    SIMILARITY_THRESHOLD = 10  # 初期値


def load_config(config_file: str = "config.ini") -> Tuple[str, str, int]:
    """設定ファイルを読み込む"""
    config = configparser.ConfigParser()
    config.read(config_file)
    image_folder = config.get("Paths", "image_folder", fallback="")
    trash_folder = config.get("Paths", "trash_folder", fallback="")
    similarity_threshold = config.getint("Settings", "similarity_threshold", fallback=Config.SIMILARITY_THRESHOLD)
    return image_folder, trash_folder, similarity_threshold


class DuplicateImageFinder:
    def __init__(self, image_folder: str, trash_folder: str, similarity_threshold: int, update_pending_callback: Callable[[int], None]):
        self.image_folder = image_folder
        self.trash_folder = trash_folder
        self.similarity_threshold = similarity_threshold
        self.result_queue: queue.Queue = queue.Queue()
        self.to_delete: List[str] = []
        self.stop_event = threading.Event()
        self.total_files = 0
        self.processing_complete = False
        self.update_pending_callback = update_pending_callback
        self.lock = threading.Lock()
        self.num_threads = Config.INITIAL_NUM_THREADS
        self.batch_size = Config.INITIAL_BATCH_SIZE

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
                    image_hash = imagehash.phash(image)
                duplicate_found = False
                with self.lock:
                    if filepath in image_hashes.values():
                        return

                    for existing_hash, existing_path in image_hashes.items():
                        if abs(image_hash - existing_hash) <= self.similarity_threshold:
                            self.result_queue.put((filepath, existing_path))
                            self.update_pending_callback(self.result_queue.qsize())
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

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            for i in range(0, self.total_files, self.batch_size):
                if self.stop_event.is_set():
                    break
                batch = all_files[i:i + self.batch_size]
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

    def adjust_resources(self):
        """リソースの調整"""
        cpu_usage = psutil.cpu_percent(interval=Config.RESOURCE_CHECK_INTERVAL)
        mem_usage = psutil.virtual_memory().percent

        if cpu_usage > Config.HIGH_RESOURCE_THRESHOLD or mem_usage > Config.HIGH_RESOURCE_THRESHOLD:
            self.num_threads = max(1, self.num_threads - 1)
            self.batch_size = max(10, self.batch_size // 2)
        else:
            self.num_threads = min(32, self.num_threads + 1)
            self.batch_size = min(1000, self.batch_size * 2)

        print(f"Adjusted resources: Threads={self.num_threads}, Batch size={self.batch_size}")

    def stop(self):
        """処理を停止"""
        self.stop_event.set()


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


class DuplicateImageApp:
    def __init__(self, root: tk.Tk, finder: DuplicateImageFinder):
        self.root = root
        self.finder = finder
        self.ui = UIComponents(root)
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
            self.ui.status_label.config(text="待機中...")
            self.root.after(Config.UI_UPDATE_INTERVAL, self.next_image)

    def display_image_pair(self, item: Tuple[str, str]):
        """画像のペアを表示"""
        filepath1, filepath2 = item
        frame1_size = (self.ui.frame1.winfo_width(), self.ui.frame1.winfo_height())
        frame2_size = (self.ui.frame2.winfo_width(), self.ui.frame2.winfo_height())
        img1 = self.ui.resize_image(filepath1, frame1_size)
        img2 = self.ui.resize_image(filepath2, frame2_size)
        self.ui.panel1.config(image=img1)
        self.ui.panel1.image = img1
        self.ui.panel2.config(image=img2)
        self.ui.panel2.image = img2
        self.ui.label1.config(text=os.path.basename(filepath1))
        self.ui.label2.config(text=os.path.basename(filepath2))
        self.ui.status_label.config(text="重複画像が検出されました")
        self.ui.panel1.image_path = filepath1
        self.ui.panel2.image_path = filepath2
        self.update_pending_count()
        self.root.update_idletasks()

    def handle_processing_complete(self):
        """処理完了時のハンドリング"""
        if self.finder.processing_complete:
            self.ui.status_label.config(text="処理完了")
            self.root.after(2000, self.on_closing)
        else:
            self.root.after(Config.UI_UPDATE_INTERVAL, self.next_image)

    def handle_keypress(self, event: tk.Event):
        """キープレスのハンドリング"""
        if event.keysym == 'Left':
            if os.path.exists(self.ui.panel1.image_path):
                self.move_to_trash(self.ui.panel1.image_path)
                self.finder.to_delete.append(self.ui.panel1.image_path)
        elif event.keysym == 'Right':
            if os.path.exists(self.ui.panel2.image_path):
                self.move_to_trash(self.ui.panel2.image_path)
                self.finder.to_delete.append(self.ui.panel2.image_path)
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
        self.ui.progress["value"] = value
        self.ui.progress_label.config(text=f"{value:.3f}%")
        self.root.update_idletasks()

    def update_pending_count(self):
        """待機中の画像数を更新"""
        pending_count = self.finder.result_queue.qsize()
        self.ui.pending_count_label.config(text=f"待機中の重複画像数: {pending_count}")
        self.root.update_idletasks()

    def monitor_resources(self):
        """リソースの監視"""
        while not self.finder.stop_event.is_set():
            self.finder.adjust_resources()
            cpu_usage = psutil.cpu_percent(interval=Config.RESOURCE_CHECK_INTERVAL)
            mem_usage = psutil.virtual_memory().percent
            print(f"CPU Usage: {cpu_usage}% | Memory Usage: {mem_usage}%")
            if cpu_usage > Config.HIGH_RESOURCE_THRESHOLD or mem_usage > Config.HIGH_RESOURCE_THRESHOLD:
                print("High resource usage detected.")


def main():
    """メイン関数"""
    image_folder, trash_folder, similarity_threshold = load_config()
    Config.SIMILARITY_THRESHOLD = similarity_threshold  # 設定ファイルから読み込んだ値を設定

    root = tk.Tk()
    root.title(Config.WINDOW_TITLE)

    def update_pending_count_ui(count: int):
        app.update_pending_count()

    finder = DuplicateImageFinder(image_folder, trash_folder, Config.SIMILARITY_THRESHOLD, update_pending_count_ui)
    app = DuplicateImageApp(root, finder)

    finder_thread = threading.Thread(target=finder.find_duplicates, args=(app.update_progress,))
    finder_thread.start()

    app.start()
    root.mainloop()

    finder_thread.join()
    app.monitor_thread.join()

    print("Processing complete.")


if __name__ == "__main__":
    main()
