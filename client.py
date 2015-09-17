import socket
import os
import os.path
import logging



print "Connecting..."
if os.path.exists("/tmp/python_unix_socket"):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("/tmp/python_unix_socket")
    print "Ready"
    print "Press CTRL + C or Done to exit the server."
    while True:
        try:
            x = raw_input("> ")
            x = x.lstrip(" ")
            if "" != x:
                print "Client Send:", x
                client.send(x)
                x = x.split()
                if x[0].lower() == "done":       # terminates the processes and umounts and deletes pool folder
                    print "Shutting down..."
                    break
                elif x[0] == "get_pool_path":  # gives the pool's path
                    data = client.recv(1024)
                    print data
                elif x[0] == "change_pool_path":  # changes the pool's path
                    pool_dir = raw_input("Enter new pool path: ")
                    client.send(pool_dir)
                    if os.path.exists(pool_dir):
                        pass
                    else:
                        data = client.recv(1024)
                        print data
                elif x[0] == "get_pool_space":    # gives the space of the pool
                    data = client.recv(1024)
                    data = data.strip("[]'")
                    data = data.split(",")
                    for i in data:
                        i = i.strip(" ")
                        i = i.strip("'")
                        print i
                elif x[0] == "device_list":    # gives you the list of devices mounted
                    data = client.recv(1024)
                    print data
                elif x[0] == "get_disk_space": # gives the space of the device entered by the user
                    data = client.recv(1024)
                    print data
        except KeyboardInterrupt, k:
            print "Shutting down."
            break
    client.close()
else:
    logging.error("couldn't connect")
    print "Couldn't Connect!"
print "Done"
