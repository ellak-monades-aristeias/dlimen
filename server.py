import socket
import os
import os.path
import lib.config
from lib.storagepool import Storage
from multiprocessing import Process, Queue
import logging
import time
from  hurry.filesize import size
import subprocess
#logger initialization
logger = logging.getLogger('Server_log')
logger.setLevel(logging.DEBUG)
log_file = '/var/log/dlimen.log'
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formater)
ch.setFormatter(formater)
logger.addHandler(fh)
logger.addHandler(ch)


cfg = lib.config.Config('/usr/local/bin/dlimen/config.conf', 1)
cfg_conf = cfg.get()
pool_subs = cfg.get_option('storage_pool', 'pool_folders')
pool_subs = pool_subs.split(',')
pool_dir = cfg.get_option('storage_pool', 'pool_path')


logger.info("checking for unix socket")
if os.path.exists("/tmp/python_unix_socket"):
    logger.info("removing unix socket")
    os.remove("/tmp/python_unix_socket")



server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
logger.info("binding unix socket")
server.bind("/tmp/python_unix_socket")
server.listen(1)

logger.info("initializing storage instance")
diskmanager = Storage(cfg, log_file)

logger.info("calling init_pool function")
diskmanager.init_pool()
logger.info("starting disk searching process")
p = Process(target=diskmanager.disk_src)
f = Process(target=diskmanager.rnm_file)
f.daemon = True
f.start()
p.daemon = True
p.start()
logger.info("starting data receiving loop")
conn, addr = server.accept()



while True:
    try:
        data = conn.recv(1024)
        received = data.split()
        if not data:
            if os.path.exists("/tmp/python_unix_socket"):
                logger.info("removing unix socket")
                os.remove("/tmp/python_unix_socket")
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            logger.info("binding unix socket")
            server.bind("/tmp/python_unix_socket")
            server.listen(1)
            conn, addr = server.accept()
        else:
            print "-" * 20
            print data
            if "done" == data.lower():
                break
            elif "get_pool_path" == data:  #gives the pool's path
                conn.send(pool_dir)
            elif "change_pool_path" == data:  #changes the pool's path
                prv_path = pool_dir
                pool_dir = conn.recv(1024)
                if os.path.exists(pool_dir):
                    pool_dir = pool_dir + '/pool/'
                    cfg.set('storage_pool', 'pool_path', pool_dir)
                    cfg.write()
                    time.sleep(1)
                    diskmanager.init_pool()
                    diskmanager.umnt_path(prv_path)
                    try:
                        diskmanager.umnt_path(prv_path)
                    except:
                        pass
                    time.sleep(1)
                    diskmanager.del_path(prv_path)
                else:
                    path_error = "You have entered an incorrect path"
                    pool_dir = prv_path
                    conn.send(path_error)
            elif "get_pool_space" == data:  #gives the space of the pool
                device_list = diskmanager.path_init()
                device_list.append(pool_dir)
                table = []
                for disk in device_list:
                    data = [subprocess.Popen(["df", "--output=size,used,avail,pcent",
                                                         "-x", "tmpfs", "-x", "devtmpfs", disk], stdout=subprocess.PIPE,
                                                stdin=subprocess.PIPE).communicate()[0]]
                    disk_list = data[0]
                    disk_list = disk_list.split("\n")
                    disk_list = disk_list[1]
                    disk_list = disk_list.strip()
                    disk_list = disk_list.split(" ")
                    for i in disk_list:
                        try:
                            disk_list.remove('')
                        except:
                            pass
                    for i in range(len(disk_list)):
                        if i != 3:
                            disk_list[i] = int(disk_list[i])
                    table.append(disk_list)
                pool_disk = [0, 0, 0, "0%"]
                for disk in table:
                    pool_disk[0] += int(disk[0])
                    pool_disk[1] += int(disk[1])
                    pool_disk[2] += int(disk[2])
                total_pcent = (pool_disk[1] / float(pool_disk[0]))*100
                total_pcent = str(total_pcent)
                total_pcent = total_pcent[0:4]
                pool_disk[0] = pool_disk[0]/1024
                pool_disk[1] = pool_disk[1]/1024
                pool_disk[2] = pool_disk[2]/1024
                pool_disk[3] = total_pcent+"%"
                pool_disk[0] = "Total Space: " + str(pool_disk[0]) + " MB"
                pool_disk[1] = "Used Space: " + str(pool_disk[1]) + " MB"
                pool_disk[2] = "Availiable Space: " + str(pool_disk[2]) + " MB"
                pool_disk[3] = "Percentage Use: " + pool_disk[3]
                data = str(pool_disk)
                conn.send(data)
            elif "device_list" == data:    #gives you the list of devices mounted
                ext_path = cfg.get_option("storage_pool", "ext_path")
                cfg.get()
                device_dict = []
                tmp = os.listdir(ext_path)
                device_dict = [{"id": 0, "name": "local", "status": "mounted"}]
                try:
                    for i in range(len(tmp)):
                        status = "mounted"
                        if os.path.isdir(ext_path + tmp[i]):
                            device_dict.append({"id": i+1, "name": tmp[i], "status": status})
                except:
                    pass
                device_dict = str(device_dict)
                conn.send(device_dict)
            elif "get_disk_space" == received[0]: #gives the space of the device entered by the user
                ext_path = cfg.get_option("storage_pool", "ext_path")
                local_path = cfg.get_option("storage_pool", "local_path")
                cfg.get()
                try:
                    disk_num = received[1]
                    disk_num = int(disk_num)
                    device_dict = [{"id": 0, "name": local_path, "status": "mounted"}]
                    tmp = os.listdir(ext_path)
                    if tmp != []:
                        for i in range(len(tmp)):
                            status = "mounted"
                            if os.path.isdir(ext_path + tmp[i]):
                                device_dict.append({"id": i+1, "name": tmp[i], "status": status})
                    print device_dict
                    for i in range(len(device_dict)):
                        if device_dict[i]["id"] == disk_num:
                            if disk_num == 0:
                                data = subprocess.Popen(["df", "-h", "--output=source,fstype,size,used,avail,pcent,target",
                                                         "-x", "tmpfs", "-x", "devtmpfs", device_dict[i]["name"]], stdout=subprocess.PIPE,
                                                        stdin=subprocess.PIPE).communicate()[0]
                                break
                            elif disk_num  <= len(device_dict) and disk_num > 0:
                                data = subprocess.Popen(["df", "-h", "--output=source,fstype,size,used,avail,pcent,target",
                                                         "-x", "tmpfs", "-x", "devtmpfs", "/dev/"+device_dict[i]["name"]], stdout=subprocess.PIPE,
                                                        stdin=subprocess.PIPE).communicate()[0]
                                break
                        else:
                            data = "device don't exist"
                    conn.send(data)
                except:
                    conn.send("device don't exist")
    except KeyboardInterrupt, k:
        break
print "-" * 20

logger.info("data receiving loop terminated")
logger.info("closing server...")
conn.close()
logger.info("terminating disk searching process")
p.terminate()
logger.info("removing unix socket")
os.remove("/tmp/python_unix_socket")
logger.info("starting umounting sequence")
diskmanager.umnt_all()
logger.info("starting folder deleting sequence")
diskmanager.del_path(pool_dir)
