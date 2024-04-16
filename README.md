# What is this

A super simple NVR setup that takes in rtsp streams, records and outputs a live snapshot for them.
Also overlays a timestamp and the camera name on the stream

# Future?

Theres a simple plugin system that acts on the live snapshots. I would like some sort of human detection system in the future.

# Certi

To access this from a https frontend (such as the one hosted at nvr.h0st.uk) you will need a certificate.
A self signed one will usually work well enough.
```openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365```

You can use any other one though from an authority :)

# Install
```pip install -r requirements.txt```

Also FFMPEG

## Linux
```sudo apt install ffmpeg```

## Windows

Why are you running this on windows?? Download the installer i guess...

# Run

```python main.py```

# Use

Either host the frontend too, or use nvr.h0st.uk

Enter the creds from config.yaml and it should connect :)

# API

API is accessible at port 5000.

Might work on some docs for this at somepoint, but its pretty simple

/cameras - returns cameras
/cameras/{cam_name} - returns the data for that camera

/cameras/{cam_name}/live - returns refreshing snapshot

/recordings/* - Returns the recordins directory (if mp4 is requested, will return the clip)