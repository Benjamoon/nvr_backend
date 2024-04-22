from cameras import Cameras
from web import WebServer
from watcher_thread import Watcher
import time
import yaml
import os

def get_dir_size_in_gb(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)  # Convert bytes to gigabytes

def delete_oldest_files_until_limit(directory, limit_gb):
    files = []
    # Traverse directory and collect all files with their paths and stats
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filepath.endswith(".mp4"):  # Ensure it's an MP4 file
                file_stat = os.stat(filepath)
                files.append((filepath, file_stat.st_mtime))

    # Sort files by their modification time (oldest first)
    files.sort(key=lambda x: x[1])

    current_size = get_dir_size_in_gb(directory)

    # Delete files until the current size is under the limit
    for file, _ in files:
        if current_size <= limit_gb:
            break
        try:
            file_size = os.path.getsize(file) / (1024 ** 3)  # Get size in GB before deleting
            os.remove(file)
            current_size -= file_size
            print(f"Deleted {file}, freed {file_size:.3f} GB, remaining size {current_size:.3f} GB")
        except Exception as e:
            print(f"Failed to delete {file}: {str(e)}")

    # After deleting files, check and remove empty directories recursively
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):  # Check if directory is empty
                try:
                    os.rmdir(dir_path)
                    print(f"Deleted empty directory: {dir_path}")
                except Exception as e:
                    print(f"Failed to delete directory {dir_path}: {str(e)}")

    return current_size



def main():
    with open("config.yaml", 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    # Initialize camera recorder and web server
    recorder = Cameras(config)
    web_server = WebServer(config, recorder)
    
    # Plugins that act on the live directory. (snapshot processing)
    plugins = []
    watcher = Watcher("live/", plugins)
    
    # Start camera recording and web server
    recorder.start_recording()
    web_server.start()
    watcher.startWatching()
    print("Cameras are now recording!")
    try:
        while True:
            print("Healthy!")
            
            # Check the size of the recordings directory
            dir_size = get_dir_size_in_gb("recordings/")
            print("Recordings Size is", dir_size, "GB")
            
            if dir_size > config["max_size"]:
                print("Greater than maximum size!")
                delete_oldest_files_until_limit("recordings/", config["max_size"])
            
            time.sleep(10)  # Keep the main thread alive while the cameras are recording
            
    except KeyboardInterrupt:
        print("Stopping services...")
        print("Stopping recording and processing!")
        recorder.stop_recording()
        print("Stopping all plugins!")
        watcher.stopWatching()
        exit()

if __name__ == '__main__':
    main()