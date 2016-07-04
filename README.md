# Instructions to get this working on the bikes and the Gateway

The gateways need the following files:
    - gateway.py

The bikes need:
    - rider.py
    - config.py
    - Adafruit_LCD

Before putting the config.py into the bike, make sure to edit the id. Use id = '1' for the first bike
and id = '2' for the second bike.

Upload the files inside '/flash/' using the FTP server.

Make sure that all 3 LoPy's are updated with the latest firmware.

Don't touch the boot.py files on the LoPy's or upload the boot.py contained in this repo.

To get the code running, access the LoPy using the serial terminal. So, for the bikes do:

```python
>>> import rider
>>> rider.main()
```

And for the gateway do:

```python
>>> import gateway
>>> gateway.main()
```

The gateway.py file needs to be edited in order to supply the correct WLAN credentials, socket IP and PORT.

That's it!
