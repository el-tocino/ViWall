import cv2
import socket
import threading
import json
import os
import numpy as np

class VideoTilePlayer:
    def __init__(self, config_path="config.json", host="0.0.0.0", port=5005):
        self.config_path = config_path
        self.host = host
        self.port = port
        
        # Thread-safe state
        self.lock = threading.Lock()
        self.playing = False
        self.setup_mode = False  # New setup state
        self.filename = None
        self.machine_id = "node_1" 
        self.crop = {"x": 0, "y": 0, "w": 800, "h": 600} 
        
        self.sync_frame = None
        self.cap = None
        self.load_config()
        
        # Start UDP listener as a daemon thread
        self.udp_thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.udp_thread.start()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.machine_id = config.get("machine_id", self.machine_id)
                    self.crop = config.get("crop", self.crop)
                    self.filename = config.get("filename", self.filename)
                print(f"Loaded config for {self.machine_id}: {self.crop}")
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump({
                    "machine_id": self.machine_id,
                    "crop": self.crop,
                    "filename": self.filename
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        print(f"[{self.machine_id}] Listening for UDP commands on {self.host}:{self.port}")
        
        while True:
            data, addr = sock.recvfrom(1024)
            msg = data.decode('utf-8').strip()
            print(f"Received: {msg}")
            self._handle_command(msg)

    def _handle_command(self, msg):
        parts = msg.split()
        if not parts: return
        
        cmd = parts[0].lower()
        
        with self.lock:
            if cmd == "start":
                self.playing = True
                self.setup_mode = False
            
            elif cmd == "stop":
                self.playing = False
                self.setup_mode = False
                
            elif cmd == "setup":
                self.setup_mode = True
                self.playing = False
            
            elif cmd == "sync" and len(parts) == 2:
                try:
                    self.sync_frame = int(parts[1])
                except ValueError:
                    print("Invalid sync parameter. Expected integer.")

            elif cmd == "filename" and len(parts) > 1:
                self.filename = " ".join(parts[1:])
                if self.cap:
                    self.cap.release()
                    self.cap = None
                self.save_config()
            
            elif cmd == "reconfigure" and len(parts) == 6:
                target_id = parts[1]
                if target_id == self.machine_id:
                    try:
                        self.crop = {
                            "x": int(parts[2]),
                            "y": int(parts[3]),
                            "w": int(parts[4]),
                            "h": int(parts[5])
                        }
                        self.save_config()
                        print(f"[{self.machine_id}] Reconfigured crop to {self.crop}")
                    except ValueError:
                        print("Invalid reconfigure parameters. Expected 4 integers.")

    def run(self):
        window_name = f"Tile Player - {self.machine_id}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Uncomment the line below to force the application to take over the entire physical monitor
        # cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        while True:
            # 1. Safely read current state
            with self.lock:
                playing = self.playing
                setup_mode = self.setup_mode
                filename = self.filename
                crop = self.crop.copy()
                sync_target = self.sync_frame
                
                if self.sync_frame is not None:
                    self.sync_frame = None

            # 2. Handle Setup Mode
            if setup_mode:
                # Create a solid white background (255, 255, 255)
                white_frame = np.ones((crop["h"], crop["w"], 3), dtype=np.uint8) * 255
                
                # Dynamic font scaling based on window width
                text = self.machine_id
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = max(1.0, crop["w"] / 400.0) 
                thickness = max(2, int(font_scale * 2))
                
                # Calculate text size and center coordinates
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                text_x = (crop["w"] - text_size[0]) // 2
                text_y = (crop["h"] + text_size[1]) // 2
                
                # Draw black text
                cv2.putText(white_frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)
                cv2.imshow(window_name, white_frame)
                
                if cv2.waitKey(100) & 0xFF == 27:
                    break
                    
            # 3. Handle Playback
            elif playing and filename and os.path.exists(filename):
                if self.cap is None or not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(filename)
                
                if sync_target is not None:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, sync_target)
                    
                ret, frame = self.cap.read()
                
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                    
                h, w = frame.shape[:2]
                
                x1, y1 = max(0, crop["x"]), max(0, crop["y"])
                x2, y2 = min(w, x1 + crop["w"]), min(h, y1 + crop["h"])
                
                cropped = frame[y1:y2, x1:x2]
                
                if cropped.size > 0:
                    cv2.imshow(window_name, cropped)
                    
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                delay = int(1000 / fps) if fps > 0 else 30
                
                if cv2.waitKey(delay) & 0xFF == 27: 
                    break
                    
            # 4. Handle Idle State
            else:
                black_frame = np.zeros((crop["h"], crop["w"], 3), dtype=np.uint8)
                cv2.imshow(window_name, black_frame)
                
                if cv2.waitKey(100) & 0xFF == 27:
                    break

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    player = VideoTilePlayer()
    player.run()
