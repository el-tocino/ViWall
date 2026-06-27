# Set the video file (supports spaces in the name)
echo "filename /path/to/local_video.mp4" | nc -u -w0 127.0.0.1 5005

# Start playback
echo "start" | nc -u -w0 127.0.0.1 5005

# Reconfigure the crop on the fly (x, y, width, height)
echo "reconfigure node_1 100 100 640 480" | nc -u -w0 127.0.0.1 5005

# Stop playback (goes to black screen)
echo "stop" | nc -u -w0 127.0.0.1 5005
