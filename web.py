# web.py
import os
from flask import Flask, send_from_directory, make_response, request
from flask_cors import CORS, cross_origin
import threading
import json
import copy

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


class WebServer:
    def __init__(self, config, recorder, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self.config = config
        self.auth = HTTPBasicAuth()
        self.app = Flask(__name__)
        self.cors = CORS(self.app)
        self.server_thread = None
        self.recorder = recorder
        self.running = threading.Event()
        
        self.app.config["CORS_HEADERS"] = 'Content-Type'
        
        @self.auth.verify_password
        def verify_user_and_password(username, password):
            for user in self.config["users"]:
                if str(user["username"]).lower() == str(username).lower():
                    return check_password_hash(str(user["password_hashed"]), str(password))
                
            return False
        

        @self.app.route('/')
        @self.auth.login_required
        @cross_origin()
        def index():
            return send_from_directory('.', 'index.html')

        # Get all the cameras registered!
        @self.app.route('/cameras')
        @self.auth.login_required
        @cross_origin()
        def cameras():
            logs = self.recorder.get_logs()
            base_response = copy.copy(self.config["cameras"])
            
            for cam in base_response:
                cam["logs"] = logs[cam["name"]]
            
            return json.dumps(base_response)
        
        # Individual registered camera data
        @self.app.route('/cameras/<path:camera_name>')
        @self.auth.login_required
        @cross_origin()
        def cameras_individual(camera_name):
            logs = self.recorder.get_logs()
            
            for cam in self.config["cameras"]:
                if cam["name"] == camera_name:
                    cam_data = copy.copy(cam)
                    cam_data["logs"] = logs[cam["name"]]
                    return json.dumps(cam_data)
            
            return f"Camera {camera_name} not found", 404
        
        # The latest snapshot (for basic live view impemtatnion)
        @self.app.route('/cameras/<path:camera_name>/live')
        @self.auth.login_required
        @cross_origin()
        def get_live_file(camera_name):
            res = make_response(send_from_directory('live', f"{camera_name}.jpg"))
            res.headers["Refresh"] = 0.5
            return res

        # Get all the recordings!
        @self.app.route('/recordings')
        @self.auth.login_required
        @cross_origin()
        def recordings():
            files = os.listdir("recordings")
            return json.dumps(files), 200
        
        # Get recordings decendents
        @self.app.route('/recordings/<path:recordings_path>')
        @self.auth.login_required
        @cross_origin()
        def recordings_path(recordings_path):
            path = os.path.join("recordings", recordings_path)
        
            
            if path.endswith(".mp4"):
                return send_from_directory("recordings", recordings_path)
            
            files = os.listdir(path)
            return json.dumps(files), 200

    def start(self):
        """Start the web server."""
        self.running.set()
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Web server started at http://{self.host}:{self.port}")

    def _run_server(self):
        while self.running.is_set():
            self.app.run(host=self.host, port=self.port, threaded=True, use_reloader=False, ssl_context=('cert.pem', 'key.pem'))