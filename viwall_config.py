import cv2
import numpy as np
import pytesseract
import json

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

def analyze_wall_photo(image_path, target_w, target_h):
    # 1. Load the setup photograph
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    img_h, img_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Threshold to find the bright white screens
    # Adjust thresholds if your photo has varying room glare
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Find outer bounds of the screens
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_screens = []
    
    print(f"Processing photo and extracting machine IDs...")
    for idx, cnt in enumerate(contours):
        # Filter out minor light reflections or small artifacts
        area = cv2.contourArea(cnt)
        if area < (img_w * img_h * 0.01): 
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Crop the single screen matrix out of the photo to run OCR
        screen_roi = gray[y:y+h, x:x+w]
        
        # Clean up the ROI image for OCR (invert so text is black on white if thresholded)
        _, roi_thresh = cv2.threshold(screen_roi, 100, 255, cv2.THRESH_BINARY_INV)
        
        # OCR Configuration: Assume a single uniform block of text
        custom_config = r'--psm 6'
        machine_id = pytesseract.image_to_string(screen_roi, config=custom_config).strip()
        
        # Fallback if OCR is messy due to photo angle
        if not machine_id:
            machine_id = f"unknown_node_{idx}"
        
        # Clean alphanumeric characters and underscores only
        machine_id = "".join(c for c in machine_id if c.isalnum() or c in "外部-_").strip()
        
        detected_screens.append({
            "id": machine_id,
            "photo_x": x,
            "photo_y": y,
            "photo_w": w,
            "photo_h": h
        })

    if not detected_screens:
        print("No screens detected. Ensure the screens are bright white in the photograph.")
        return

    # 3. Find the global bounding envelope of the whole video wall in the picture
    min_x = min(s["photo_x"] for s in detected_screens)
    max_x = max(s["photo_x"] + s["photo_w"] for s in detected_screens)
    min_y = min(s["photo_y"] for s in detected_screens)
    max_y = max(s["photo_y"] + s["photo_h"] for s in detected_screens)
    
    wall_photo_w = max_x - min_x
    wall_photo_h = max_y - min_y

    print(f"\nDetected {len(detected_screens)} screens. Remapping to {target_w}x{target_h}...")

    # 4. Calculate relative normalization scales and build config layout map
    configs = {}
    for s in detected_screens:
        # Calculate relative position within the total wall grid bounds [0.0 to 1.0]
        rel_x = (s["photo_x"] - min_x) / wall_photo_w
        rel_y = (s["photo_y"] - min_y) / wall_photo_h
        rel_w = s["photo_w"] / wall_photo_w
        rel_h = s["photo_h"] / wall_photo_h
        
        # Map normalized boundaries directly to pixel targets inside the master video dimensions
        crop_x = int(round(rel_x * target_w))
        crop_y = int(round(rel_y * target_h))
        crop_w = int(round(rel_w * target_w))
        crop_h = int(round(rel_h * target_h))
        
        configs[s["id"]] = {
            "machine_id": s["id"],
            "crop": {
                "x": crop_x,
                "y": crop_y,
                "w": crop_w,
                "h": crop_h
            },
            "filename": "video.mp4" # Placeholder
        }

    # Output structural configuration blocks
    print("\n--- Generated Client Configurations ---")
    for mid, cfg in configs.items():
        filename = f"config_{mid}.json"
        with open(filename, 'w') as f:
            json.dump(cfg, f, indent=4)
        print(f"Saved: {filename}")
        print(json.dumps(cfg, indent=2))

if __name__ == "__main__":
    # Prompt user for reference resolution calculations
    target_w, target_h = get_target_resolution()
    
    image_path = input("Enter path to the setup photo (e.g., wall.jpg): ").strip()
    analyze_wall_photo(image_path, target_w, target_h)
