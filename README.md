## Playback
ViWall presumes you have local video files to the client player host for playback.  
You'll want to select a video of sufficient size and quality to playback that it can be cut into tiles and still have a reasonably good look.  Additionally, the quality/bit rate and frame rate will have a good deal to do with the playback being steady.  The sync command can be used to try and keep things in agreement between hosts.  

This runs over UDP, so it's both insecure and not recommended to be used on an open network. Don't use this if you don't know what you're doing.  Using this means you gladly  accept the risks.  If you make fixes, please let me know, I'd love to see them.

Each client player should have a unique machine_id. This isn't enforced or checked, so you can have all of them playing one segment, if you copy the same config over and over again.  

Was usable for 1080p source files on a couple of n100 machines.

## Set the video file (supports spaces in the name)
echo "filename /path/to/local_video.mp4" | nc -u -w0 127.0.0.1 5005

## Start playback
echo "start" | nc -u -w0 127.0.0.1 5005

## Reconfigure the crop on the fly (x, y, width, height)
echo "reconfigure node_1 100 100 640 480" | nc -u -w0 127.0.0.1 5005

## Stop playback (goes to black screen)
echo "stop" | nc -u -w0 127.0.0.1 5005

## Sync all listening players to frame 300
echo "sync 300" | nc -u -w0 127.0.0.1 5005

## Setup tool (stops playback if running)
echo "setup" | nc -u -w0 127.0.0.1 5005

### requirements
Do a "pip install opencv-python numpy" and you should be good to go.  For the controller, pytesseract is also useful to generate configs from the setup. Take a picture of your screens running the setup screen, and feed it to the viwall_config.py, it will build configs for each one it detects.  


### Setup
<blockquote>
$ python viwall_config.py
  
  --- Video Wall Resolution Configuration ---

1: 1080p (1920x1080)

2: 4K UHD (3840x2160)

3: Custom Resolution

Select the target video resolution layout [1-3]: 2

Enter path to the setup photo (e.g., wall.jpg): wall.jpg


Processing photo and extracting machine IDs...

Detected 4 screens. Remapping to 3840x2160...


--- Generated Client Configurations ---

Saved: config_node_1.json

{

  "machine_id": "node_1",
  
  "crop": { "x": 0, "y": 0, "w": 1920, "h": 1080 },
  
  "filename": "video.mp4"

}


Saved: config_node_2.json

{

  "machine_id": "node_2",
  
  "crop": { "x": 1920, "y": 0, "w": 1920, "h": 1080 }

}
</blockquote>
