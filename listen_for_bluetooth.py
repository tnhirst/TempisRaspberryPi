from bluetooth import *

server = BluetoothSocket(RFCOMM)
server.bind(("", PORT_ANY))
server.listen(1)

port = server.getsockname()[1]

uuid = "e1f520d6-a6b7-40c2-984b-b0c7cef24ad0"

#advertise_service(
#	server, 
#	"Tempis",
#	service_id=uuid,
#	service_classes=[uuid, SERIAL_PORT_CLASS],
#	profiles=[SERIAL_PORT_PROFILE]
#)

print("Waiting for connection on RFCOMM channel %d" % port)

client, info = server.accept()
print(info)
print(client)


while True:
	data = client.recv(16)
	if data:
		print(data)

	
