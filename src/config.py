import configparser
from typing import Tuple


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
    CACHE_SAVE_INTERVAL = 50
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
