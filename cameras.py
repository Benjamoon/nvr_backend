import subprocess
import threading
from datetime import datetime
import os
import time

class Cameras:
    def __init__(self, config):
        self.config = config
        self.threads = []
        self.processes = []  # Keep track of subprocesses
        self.running = True
        self.output_logs = {}  # Dictionary to store output logs

    def create_directory(self):
        current_date = datetime.now()
        base_directory_path = f"recordings/{current_date.strftime('%Y')}/{current_date.strftime('%m')}/{current_date.strftime('%d')}"
        os.makedirs("live", exist_ok=True)
        for camera in self.config['cameras']:
            camera_directory = os.path.join(base_directory_path, camera['name'])
            os.makedirs(camera_directory, exist_ok=True)

    def generate_ffmpeg_command(self, camera):
        address = camera["rtsp_address"]
        name = camera["name"]
        fontfile_path = self.config['font_file']
        text_filters = f"drawtext=fontfile={fontfile_path}:text='%{{localtime}}':x=(w-tw)-10:y=h-th-10:fontsize=24:fontcolor=white@0.8, drawtext=fontfile={fontfile_path}:text='{name}':x=10:y=h-th-10:fontsize=24:fontcolor=white@0.8"
        
        return [
            "ffmpeg",
            "-y",
            "-hwaccel", "cuda",
            "-rtsp_transport", "tcp",
            "-re",
            "-i", address,
            "-timeout", "5000000",
            "-analyzeduration", "1000000",
            "-probesize", "5000000",
            "-r", "25",
            "-an",
            "-c:v", "h264_nvenc",
            "-preset", "medium",
            "-f", "segment",
            "-segment_time", str(self.config["segment_length"]),
            "-reset_timestamps", "1",
            "-segment_format", "mp4",
            "-strftime", "1",
            "-pix_fmt", "yuv420p",
            "-vf", text_filters,
            f"recordings/%Y/%m/%d/{name}/{name}_%H_%M_%S.mp4",
            "-update", "1",
            "-q:v", "3",
            "-vf", f"fps=1,{text_filters}",  # Apply the text filter and update fps for the JPEG output
            f"live/{name}.jpg",
        ]

    def start_recording(self):
        for camera in self.config["cameras"]:
            thread = threading.Thread(target=self.run_ffmpeg, args=(camera,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def run_ffmpeg(self, camera):
        name = camera['name']
        print(f"Staring FFMPEG Process for {name}")
        self.output_logs[name] = []
        while self.running:
            try:
                self.create_directory()
                proc = subprocess.Popen(self.generate_ffmpeg_command(camera), stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
                self.processes.append(proc)
                for line in proc.stderr:  # Read the output line by line
                    self.output_logs[name].append(line)
                    # Limit log size
                    self.output_logs[name] = self.output_logs[name][-self.config["log_lines"]:]
                proc.wait()
            except Exception as e:
                print(f"Error with camera {name}: {e}")

    def get_logs(self):
        return self.output_logs  # Provide a method to access the logs

    def stop_recording(self):
        self.running = False  # Set running to False to stop loops

        # Request FFmpeg to gracefully close
        for proc in self.processes:
            if proc.poll() is None:  # Check if the process is still running
                try:
                    print("Sending quit command to proc!")
                    proc.stdin.write('q')  # Send 'q' to FFmpeg's stdin
                    proc.stdin.flush()
                except Exception as e:
                    print(f"Failed to send quit command: {e}")
                    proc.terminate()  # Fallback if writing to stdin fails

        # Wait a bit for processes to terminate gracefully
        still_running = True
        waited_for = 0
        
        while still_running and waited_for < 10:
            still_running = False
            count = 0
            
            for proc in self.processes:
                if proc.poll() is None:
                    count += 1
                    still_running = True
                    proc.stdin.write('q')  # Send 'q' to FFmpeg's stdin
                    proc.stdin.flush()


            print(f"{count} process(s) still running, waiting (max = {10 - waited_for} seconds)")
            time.sleep(1)
            waited_for += 1

        # Forcefully terminate if still running
        for proc in self.processes:
            if proc.poll() is None:  # If process is still running
                print("proc is still running. Forcefully killing.")
                proc.kill()  # Force kill the process

        # Ensure all threads are finished
        for thread in self.threads:
            thread.join()

        print("All FFmpeg processes have been stopped.")