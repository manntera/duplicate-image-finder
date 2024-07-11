from config import load_config, Config
from model import DuplicateImageFinder
from view import UIComponents
from presenter import DuplicateImagePresenter
import tkinter as tk
import threading


def main():
    """メイン関数"""
    image_folder, trash_folder, similarity_threshold = load_config()
    Config.SIMILARITY_THRESHOLD = similarity_threshold  # 設定ファイルから読み込んだ値を設定

    root = tk.Tk()
    root.title(Config.WINDOW_TITLE)

    finder = DuplicateImageFinder(image_folder, trash_folder, Config.SIMILARITY_THRESHOLD)
    view = UIComponents(root)
    presenter = DuplicateImagePresenter(root, finder, view)

    finder_thread = threading.Thread(target=finder.find_duplicates, args=(presenter.update_progress,))
    finder_thread.start()

    presenter.start()
    root.mainloop()

    finder_thread.join()
    presenter.monitor_thread.join()

    print("Processing complete.")


if __name__ == "__main__":
    main()
