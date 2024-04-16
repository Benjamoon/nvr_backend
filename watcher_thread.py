import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor

class Handler(FileSystemEventHandler):
    def __init__(self, handlers, max_workers=5):
        self.handlers = handlers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_files = set()  # Track files currently being processed
        self.lock = threading.Lock()  # Lock for managing access to the set

    def on_modified(self, event):
        if not event.is_directory:
            with self.lock:  # Ensure thread-safe manipulation of the set
                if event.src_path not in self.processing_files:
                    self.processing_files.add(event.src_path)
                    for handler in self.handlers:
                        # Wrap the handler to include pre and post-processing steps
                        wrapped_handler = lambda p=event.src_path: self.process_file(p, handler)
                        self.executor.submit(wrapped_handler)

    def process_file(self, path, handler):
        try:
            handler(path)
        finally:
            with self.lock:
                self.processing_files.remove(path)

    def shutdown(self):
        print("Force shutdown all handlers!")
        self.executor.shutdown(wait=False)  # Force shutdown without waiting for tasks to complete

class Watcher:
    def __init__(self, directory_to_watch, handlers):
        self.directory_to_watch = directory_to_watch
        self.observer = Observer()
        self.handler = Handler(handlers)
        self.running = False
        self.thread = None

    def run(self):
        self.observer.schedule(self.handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while self.running:
                time.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()

    def startWatching(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def stopWatching(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.handler.shutdown()  # Shutdown the handler's thread pool
            self.observer.stop()
            self.thread.join()