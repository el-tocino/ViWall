import cv2
import numpy as np
import pytesseract
import json
import socket
import time

def get_target_resolution():
    print("--- Video Wall Resolution Configuration ---")
    print("1: 1080p (1920x1080)")
    print("2: 4K UHD (3840x2160)")
    print("3: Custom Resolution")
    choice = input("Select the target video resolution layout [1-3]: ").strip()
    
    if choice == "1":
        return 1920, 1080
    elif choice == "2":
        return 3840, 2160
    elif choice == "3":
        try:
            w = int(input("Enter video width (pixels): "))
            h = int(input("Enter video height (pixels): "))
            return w, h
        except ValueError:
            print("Invalid input. Defaulting to 1080p.")
            return 1920, 1080
    else:
        print("Invalid choice. Defaulting to 1080p.")
        return 1920, 1080

def transmit_config(machine_id, crop, broadcast_ip="255.255.255.255", port=5005):
    """Formats and transmits a standard UDP reconfigure packet to the clients."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Matches client format: reconfigure {target_id} {x} {y} {w} {h}
    cmd = f"reconfigure {machine_id} {crop['x']} {crop['y']} {crop['w']} {crop['h']}"
    
    try:
        sock.sendto(cmd.encode('utf-8'), (broadcast_ip, port))
        print(f"📡 Broadcasted network update to [{machine_id}] -> {cmd}")
    except Exception as e:
        print(f"❌ Failed to transmit packet for {machine_id}: {e}")
    finally:
        sock.close()

def analyze_and_push_wall(image_path, target_w, target_h, broadcast_ip, port):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    img_h, img_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_screens = []
    
    print(f"\nProcessing photo and extracting machine IDs via OCR...")
    for idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < (img_w * img_h * 0.01): 
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        screen_roi = gray[y:y+h, x:x+w]
        
        custom_config = r'--psm 6'
        machine_id = pytesseract.image_to_string(screen_roi, config=custom_config).strip()
        
        if not machine_id:
            machine_id = f"unknown_node_{idx}"
        
        machine_id = "".join(c for c in machine_id if c.isalnum() or c in "外部-_").strip()
        
        detected_screens.append({
            "id": machine_id,
            "photo_x": x,
            "photo_y": y,
            "photo_w": w,
            "photo_h": h
        })

    if not detected_screens:
        print("No screens detected. Ensure your video wall is actively running the 'setup' command.")
        return

    # Establish global outer boundaries of the video wall display area
    min_x = min(s["photo_x"] for s in detected_screens)
    max_x = max(s["photo_x"] + s["photo_w"] for s in detected_screens)
    min_y = min(s["photo_y"] for s in detected_screens)
    max_y = max(s["photo_y"] + s["photo_h"] for s in detected_screens)
    
    wall_photo_w = max_x - min_x
    wall_photo_h = max_y - min_y

    print(f"Detected {len(detected_screens)} screens. Remapping grid matrices to target canvas...")

    # Calculate layouts and push live network configurations
    print("\n--- Deploying Network Configurations ---")
    for s in detected_screens:
        rel_x = (s["photo_x"] - min_x) / wall_photo_w
        rel_y = (s["photo_y"] - min_y) / wall_photo_h
        rel_w = s["photo_w"] / wall_photo_w
        rel_h = s["photo_h"] / wall_photo_h
        
        crop_x = int(round(rel_x * target_w))
        crop_y = int(round(rel_y * target_h))
        crop_w = int(round(rel_w * target_w))
        crop_h = int(round(rel_h * target_h))
        
        crop_data = {
            "x": crop_x,
            "y": crop_y,
            "w": crop_w,
            "h": crop_h
        }
        
        # Save local structural file copy for auditing
        cfg_backup = {"machine_id": s["id"], "crop": crop_data, "filename": "video.mp4"}
        with open(f"config_{s['id']}.json", 'w') as f:
            json.dump(cfg_backup, f, indent=4)
            
        # Push dynamic reconfiguration payload out over the network topology
        transmit_config(s["id"], crop_data, broadcast_ip, port)
        time.sleep(0.05) # Small buffer delay to keep UDP queues clean

    print("\nConfiguration sequence complete. Send a 'start' packet to test the layout synchronization.")

if __name__ == "__main__":
    target_w, target_h = get_target_resolution()
    
    img_filename = input("Enter path to the setup photo (e.g., wall.jpg): ").strip()
    
    # Configure your network specifics
    b_ip = input("Enter UDP broadcast address [Default: 255.255.255.255]: ").strip() or "255.255.255.255"
    b_port = input("Enter target
