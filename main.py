from cameras import Cameras
from web import WebServer
from watcher_thread import Watcher
import time
import yaml


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
            time.sleep(10)  # Keep the main thread alive while the cameras are recording
            print("Healthy!")
    except KeyboardInterrupt:
        print("Stopping services...")
        print("Stopping recording and processing!")
        recorder.stop_recording()
        print("Stopping all plugins!")
        watcher.stopWatching()
        exit()

if __name__ == '__main__':
    main()