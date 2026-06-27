## Playback
ViWall presumes you have local video files to the client player host for playback.  
You'll want to select a video of sufficient size and quality to playback that it can be cut into tiles and still have a reasonably good look.  Additionally, the quality/bit rate and frame rate will have a good deal to do with the playback being steady.  The sync command can be used to try and keep things in agreement between hosts.  

This runs over UDP, so it's both insecure and not recommended to be used on an open network. Don't use this if you don't know what you're doing, or you blindly accept the risks.  

Each client player should have a unique machine_id. This isn't enforced or checked, so you can have all of them playing one segment, if you copy the same config over and over again.  

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



### requirements
Do a "pip install opencv-python numpy" and you should be good to go.  
