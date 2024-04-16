# Certi

To access this from a https frontend (such as the one hosted at nvr.h0st.uk) you will need a certificate.
A self signed one will usually work well enough.
```openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365```

You can use any other one though from an authority :)