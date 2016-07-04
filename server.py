import socket
import json

sock = socket.socket()
sock.bind(('', 50140))
sock.listen(0)
sc, addr = sock.accept()

json_str = '{"RiderName":"'+ 'Daniel' + '","Company":"' + 'Pycom' + '","BadgeNumber":' + '123456' + \
            ',"EventID":"' + 'EVENT_0' + ',"BikeID":' + '1' + ',"RideStatus":"' + 'initialized' + '}]}'
json_d = json.dumps(json_str)
sc.send(bytes(json_d, 'ascii'))
