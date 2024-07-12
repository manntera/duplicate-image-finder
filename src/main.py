import signal
import sys
import tkinter as tk

from config import load_config, Config
from model import DuplicateImageFinder
from view import UIComponents
from presenter import DuplicateImagePresenter

def signal_handler(signum, frame):
    print("\nShutdown requested. Cleaning up...")
    if 'presenter' in globals():
        presenter.on_closing()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    image_folder, trash_folder, similarity_threshold = load_config()
    Config.SIMILARITY_THRESHOLD = similarity_threshold

    root = tk.Tk()
    root.title(Config.WINDOW_TITLE)

    finder = DuplicateImageFinder(image_folder, trash_folder, Config.SIMILARITY_THRESHOLD)
    view = UIComponents(root)
    presenter = DuplicateImagePresenter(root, finder, view)

    presenter.start()
    root.mainloop()

    presenter.wait_for_threads()
    print("Processing complete.")

if __name__ == "__main__":
    main()