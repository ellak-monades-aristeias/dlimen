import glib
from pyudev import Context, Monitor
import subprocess
import os, os.path
import time
import logging


pseudofilesys = \
    dict(map((lambda x: (x, 1)), ('none', 'shmfs', 'procfs', 'tmpfs', 'devtmpfs')))

gdf_cols = ('filesys', 'blocks', 'used', 'avail', 'use', 'dir')

def mounted():
    '''Get Mounted File Systems'''
    df = os.popen('df 2>/dev/null', 'r')
    df.readline() # skip first line
    mounted = []
    for line in df.readlines():
        line = line.strip()
        rec = dict(zip(gdf_cols, line.split(None, 5)))
        filesys = rec['filesys']
        dir = rec.get('dir')
        if (
            (dir and not (filesys.find(':') >= 0
            or pseudofilesys.get(filesys))
            or 'boot' in dir)
        ): mounted.append(filesys)
    df.close()
    return mounted

def file_counter(path):
    cpt = sum([len(files) for r, d, files in os.walk(path)])
    return cpt

class Storage:
    def __init__(self, cfg, log_file):
        self.logger = logging.getLogger('Storage_module')
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.FileHandler(log_file)
        self.fh.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.ERROR)
        self.formater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        self.fh.setFormatter(self.formater)
        self.ch.setFormatter(self.formater)
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)
        self.cfg = cfg
        self.cfg.get()
        self.log = log_file

    def disk_mnt(self, context):
        self.logger = logging.getLogger('Storage_module.disk_mnt')
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        ext_path = self.cfg.get_option('storage_pool', 'ext_path')
        mount_list = []
        for device in context.list_devices(DEVTYPE = 'partition'):
            if (device.device_type == 'partition'):
                dev_mounted_list = mounted()
                if device.device_node not in dev_mounted_list:
                    mount_list.append("{}".format(device.device_node))
        disk_name = mount_list[-1].split('/')
        disk_name = disk_name[-1]
        self.logger.info("mounting disk: %s" % (disk_name))
        os.makedirs('%s%s' % (ext_path, disk_name))
        disk_mount_point = ext_path + disk_name +'/'
        subprocess.Popen(['mount', mount_list[-1], disk_mount_point, '-o', 'umask=0022,gid=33,uid=33'])
        time.sleep(1)
        in_folder = "storage_pool/"
        for x in pool_subs:
            if not os.path.exists('%s%s/%s/%s' % (ext_path, disk_name, in_folder, x)):
                os.makedirs('%s%s/%s/%s' % (ext_path, disk_name, in_folder, x))
        time.sleep(1)
#	subprocess.Popen(['chown','-R','www-data.www-data',pool_dir])
        for x in pool_subs:
            subprocess.Popen(['sudo', 'mount', '-t', 'aufs', '-o', 'remount,append:%s=rw+nolwh' % (disk_mount_point+in_folder+x),
                           '-o', 'noplink', '-o', 'create=rr', 'none', '%s' % (pool_dir+x)])


    #umounts the usb device that has been unplugged
    def disk_umnt(self, device):
        self.logger = logging.getLogger("Storage_module.disk_umnt")
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        ext_path = self.cfg.get_option("storage_pool", 'ext_path')
        umount_path = device.device_node
        part_name = umount_path.split('/')
        part_name = part_name[-1]
        mount_path = subprocess.check_output(['grep', device.device_node, '/proc/mounts'])
        mount_path = mount_path.split(' ')
        mount_path = mount_path[1]
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        self.logger.info("umounting: %s" % device.device_node)
        disk = device.device_node.split("/")
        disk = disk[2]
#	subprocess.Popen(['chown','-R','www-data.www-data',pool_dir])
        for x in pool_subs:
            try:
                subprocess.Popen(['sudo', 'mount', '-t', 'aufs', '-o', 'remount,del:%s/storage_pool/%s' % (mount_path,
                                                            x), 'none', '%s%s' % (pool_dir, x)])
            except:
                pass
        time.sleep(1)
        p = subprocess.Popen(['umount',"-l", umount_path])
        self.logger.info("removing: %s" % part_name)
	p.communicate()
	if file_counter(ext_path + part_name) == 0:
            subprocess.Popen(['rm', '-r', '%s%s' % (ext_path, part_name)])
        else:
            self.logger.info("could not remove %s" % ext_path+part_name)
    #umounts all the branches from the pool directory
	
    def umnt_all(self):    # on server close
        self.logger = logging.getLogger("Storage_module.umnt_all")
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        for x in pool_subs:
            try:
                p = subprocess.Popen(['sudo', 'umount', "-l", pool_dir+x], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                self.logger.info("umounting %s" % x)
                p.communicate()
            except:
                pass
				
    #mounts a specific path
    def mount_path(self, path):
        self.logger = logging.getLogger("Storage_module.umnt_path")
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
#	subprocess.Popen(['chown','-R','www-data.www-data',pool_dir])
        for x in pool_subs:
            subprocess.Popen(['sudo', 'mount', '-t', 'aufs', '-o', 'remount,append:%s=rw+nolwh' % (path+x),
                          '-o', 'noplink', '-o', 'create=rr', 'none', '%s' % (pool_dir+x)])
 
 #umounts pool folders from targeted path
    def umnt_path(self, path):
        self.logger = logging.getLogger("Storage_module.umnt_path")
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        for x in pool_subs:
            p = subprocess.Popen(['sudo', 'umount', "-l", path+x])
            self.logger.info("umounting %s" % x)
            p.communicate()

#deletes pool folders and the folder from the targeted path
    def del_path(self, path):
        self.logger = logging.getLogger("Storage_module.del_path")
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        for x in pool_subs:
            if file_counter(path + x) == 0:
            
                self.logger.info("removing %s" % x)
                subprocess.Popen(['sudo', 'rm', '-r', path+x])
            else:
                self.logger.info("could not remove %s directory of the pool" % x)
        time.sleep(1)
        self.logger.info("removing %s" % path)
        if file_counter(path) == 0:
            subprocess.Popen(['sudo', 'rm', '-r', path])

    def disk_src(self):
        try:
            from pyudev.glib import MonitorObserver

            def device_event(observer, device):
                print 'event {0} on device {1}'.format(device.action, device)
                if device.action == "add":
                    manager.disk_mnt(context)
                elif device.action == "remove":
                    manager.disk_umnt(device)
        except:
            from pyudev.glib import GUDevMonitorObserver as MonitorObserver

            def device_event(observer, action, device):
                print 'event {0} on device {1}'.format(action, device)
                if action == "add":
                    manager.disk_mnt(context)
                elif action == "remove":
                    manager.disk_umnt(device)
        context = Context()
        manager = Storage(self.cfg, self.log)
        monitor = Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block', device_type='partition')
        observer = MonitorObserver(monitor)
        observer.connect('device-event', device_event)
        monitor.start()
        glib.MainLoop().run()

    def init_pool(self):
        self.logger = logging.getLogger("Storage_module.init_pool")
        self.logger.info("creating pool directory and subdirectories")
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        local_path = self.cfg.get_option('storage_pool', 'local_path')
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        ext_path = self.cfg.get_option('storage_pool', 'ext_path')
        storage_path = self.cfg.get_option('storage_pool', 'storage_path')
        if os.path.isdir(pool_dir) is True:
            self.umnt_all()
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        if not os.path.exists(pool_dir):
            os.makedirs(pool_dir)
        if not os.path.exists(local_path):
            os.makedirs(local_path)
            for x in pool_subs:
                os.makedirs(local_path+x)
        if not os.path.exists(ext_path):
            os.makedirs(ext_path)
        pool_dir = self.cfg.get_option('storage_pool', 'pool_path')
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        for x in pool_subs:
            if not os.path.exists(pool_dir + x):
                os.makedirs(pool_dir + x)
	subprocess.Popen(['chown','-R','www-data.www-data',local_path])
	subprocess.Popen(['chown','-R','www-data.www-data',pool_dir]) ################################

        self.logger.info("created pool directory and subdirectories")
        self.logger.info("mounting disks with subdirectories using aufs")
#	subprocess.Popen(['chown','-R','www-data.www-data',pool_dir])
        for x in pool_subs: # local mounter
            subprocess.Popen(['sudo', 'mount', '-t', 'aufs', '-o', 'br=%s%s=rw+nolwh' % (local_path, x),
                              '-o', 'noplink','-o', 'create=rr', 'none', '%s%s' % (pool_dir, x)])
        time.sleep(1)
        self.on_server_start()
        time.sleep(1)
        disks = []
        disks = Storage.path_init(self)
        if len(disks) >= 1:
            for disk in disks:
                disk_name = disk.split("/")
                disk_name = disk_name[-2]
                for x in pool_subs:
                    try:
                        subprocess.Popen(['sudo', 'mount', '-t', 'aufs', '-o', 'remount,append:%sstorage_pool/%s=rw+nolwh' % (disk, x),
                                      '-o', 'noplink', '-o', 'create=rr', 'none', '%s%s' % (pool_dir, x)])
                    except:
                        pass
                    time.sleep(1)
					
    #paths initialization
    def path_init(self):
        ext_path = self.cfg.get_option("storage_pool", "ext_path")
        self.logger = logging.getLogger("Storage_module.path_init")
        self.logger.info("scanning ext folder for disks")
        disks = []
        temp_list = os.listdir(ext_path)
        for item in temp_list:
            if os.path.isdir(ext_path+item):
                disks.append(ext_path+item+"/")
        self.logger.info("scanning completed")
        return disks
		
    def rnm_file(self):
        while True:
            local = self.cfg.get_option('storage_pool', 'local_path')
            ext = self.cfg.get_option("storage_pool", "ext_path")
            list = self.ext_list_creator()
            half_list = []
            for item in list:
                half_item = item.split("/")
                disk = half_item[-3]
                if "storage_pool" in disk:
                    disk = disk.split("_")
                    disk = disk[-1]
                half_item = half_item[-2::]
                half_item = "/" + "/".join(half_item)
                half_list.append([disk, half_item])
            to_change_list = []
            for i in range(len(half_list)):
                count = 0
                for j in range(len(half_list)):
                    if half_list[i][1] == half_list[j][1] and count > 0:
                        to_change_list.append(half_list[j])
                    elif half_list[i][1] == half_list[j][1]:
                        count += 1
                count = 0
                for num in range(len(to_change_list)):
                    item_to_rename = to_change_list[num][1].split(".")
                    count += 1
                    if item_to_rename[0][-2] == "_":
                        integer = int(item_to_rename[0][-1])
                        integer += 1
                        integer = str(integer)
                        item_to_rename[0] = str(item_to_rename[0])
                        item_to_rename[0] = item_to_rename[0][:-1:]
                        item_to_rename[0] = item_to_rename[0] + integer
                    else:
                        item_to_rename[0] = item_to_rename[0] + "_" + str(1)
                    item_to_rename = ".".join(item_to_rename)
                    if to_change_list[num][0] == "local":
                        try:
                            os.rename(local+to_change_list[num][1], local+item_to_rename)
                        except:
                            pass
                    else:
                        try:
                            os.rename(ext+to_change_list[num][0]+"/" + "storage_pool/" + to_change_list[num][1],
                                  ext+to_change_list[num][0]+"/"+ "storage_pool/" + item_to_rename)
                        except:
                            pass
            time.sleep(3)


    def on_server_start(self):
        #part 1
        ext_path = self.cfg.get_option("storage_pool", "ext_path")
        pool_subs = self.cfg.get_option("storage_pool", "pool_folders")
        pool_subs = pool_subs.split(",")
        ext_disks = os.listdir(ext_path)
        pool_dir = self.cfg.get_option("storage_pool", "pool_path")
        for disk_name in ext_disks:
            disk = ext_path+disk_name+"/"
            disk_dir = os.listdir(disk)
            if disk_dir == []:
                p = subprocess.Popen(["sudo", "umount", disk])
                p.communicate()
                p = subprocess.Popen(["sudo", "rmdir", disk])
                p.communicate()
        dev = os.listdir("/dev/")
        sds = []
        dev_mounted_list = mounted()
        for i in dev:
            #if "sd" in i and "sda" not in i:
            if "sd" in i and i not in dev_mounted_list:
                sds.append(i)
        for i in sds:
            try:
                tmp = int(i[-1])
            except:
                sds.remove(i)
        for i in sds:
            if os.path.exists(ext_path+i):
                sds.remove(i)
        for i in sds:
            if os.path.exists(ext_path+i) == False:
                subprocess.Popen(["sudo", "mkdir", ext_path+i])
                time.sleep(1)
                subprocess.Popen(["sudo", "mount", "/dev/"+i, ext_path+i])
            if os.path.exists(ext_path + i + "/" + "storage_pool/") is False:
                subprocess.Popen(["sudo", "mkdir", ext_path+ i + "/" + "storage_pool/"])

    def ext_list_creator(self):
        ext_path = self.cfg.get_option("storage_pool", "ext_path")
        local_path = self.cfg.get_option('storage_pool', 'local_path')
        ext = os.listdir(ext_path)
        pool_subs = self.cfg.get_option('storage_pool', 'pool_folders')
        pool_subs = pool_subs.split(',')
        ffl = []
        for i in ext:
            for sub in pool_subs:
                ext_disk = os.listdir(ext_path+i+"/storage_pool/"+sub)
                for item in ext_disk:
                    if item == ".wh..wh.orph":
                        ext_disk.remove(".wh..wh.orph")
                for item in ext_disk:
                    ffl.append(ext_path + i + "/" + "storage_pool/" + sub +"/" + item)
        local = os.listdir(local_path)
        for i in local:
            items = os.listdir(local_path+i)
            for j in items:
                if j == ".wh..wh.orph":
                    items.remove(j)
            for j in items:
                ffl.append(local_path+i+"/"+j)
        return ffl
