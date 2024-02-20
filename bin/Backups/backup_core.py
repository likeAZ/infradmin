import json

class IncrementalBackup:

    def __init__(self, name="backup", server=None, keep=90, store=None,
                 config_file=None, user="root"):
        with open("/usr/src/app/infradmin/conf", 'r') as fp:
            self.d_json_conf = json.load(fp)
        #self.server = server
        #self.keep = keep
        #self.config_file = config_file
        #self.store = store
        #self.user = user

    def run_command(self, command=None, shell=False, ignore_errors=False,
                    ignore_codes=None):
        result = subprocess.call(command, shell=False)
        if result and not ignore_errors and (not ignore_codes or result in set(ignore_codes)):
            raise BaseException(str(command) + " " + str(result))

    def backup(self):

        # rotate the backups
        rotater = rotatebackups.RotateBackups(self.keep, self.store)
        rotated_names = rotater.rotate_backups()

        rsync_to = None
        if not rotated_names:
            # get the current date and timestamp and the zero backup name
            now = datetime.datetime.now()
            padding = len(str(self.keep))
            tstamp = now.strftime("%Y%m%d%H%M%S")
            zbackup_name = string.join(["".zfill(padding), tstamp, self.name], ".")
            rsync_to = self.store + os.sep + zbackup_name
        else:
            rsync_to = rotated_names[0]

        # create the base rsync command with excludes
        rsync_base = ["rsync", "-avR", "--ignore-errors", "--delete", "--delete-excluded"]

        # get the paths to backup either from the command line or from a paths file
        bpaths = []
        expaths = []
        if self.config_file:

            pf = open(self.config_file, "r")
            config = json.load(pf)
            pf.close()

            # add the paths to backup
            bpaths.extend(config["backup"])

            # add and filter/exclude options
            if "exclude" in config:
                for exclude in config["exclude"]:
                    rsync_base.extend(["--exclude", exclude])

            if "port" in config:
                for thePort in config["port"]:
                    rsync_base.extend(["-e", thePort])

        # one rsync command per path, ignore files vanished errors
        for bpath in bpaths:
            bpath = bpath.strip()
            rsync_cmd = rsync_base[:]
            if self.server:
                bpath = self.user + "@" + self.server + ":" + bpath
            rsync_cmd.append(bpath)
            rsync_cmd.append(rsync_to)
            logging.debug(rsync_cmd)
            self.run_command(command=rsync_cmd, ignore_errors=True)


"""
Prints out the usage for the command line.
"""


def usage():
    usage = ["incrbackup.py [-hnksctu]\n"]
    usage.append("  [-h | --help] prints this help and usage message\n")
    usage.append("  [-n | --name] backup namespace\n")
    usage.append("  [-k | --keep] number of backups to keep before deleting\n")
    usage.append("  [-s | --server] the server to backup, if remote\n")
    usage.append("  [-c | --config] configuration file with backup paths\n")
    usage.append("  [-t | --store] directory locally to store the backups\n")
    usage.append("  [-u | --user] the remote username used to ssh for backups\n")
    message = string.join(usage)
    print
    message


"""
Main method that starts up the backup.  
"""


def main(argv):
    # set the default values
    pid_file = tempfile.gettempdir() + os.sep + "incrbackup.pid"
    name = "backup"
    keep = 90
    server = None
    config_file = None
    store = None
    user = "backup"

    try:

        # process the command line options
        opts, args = getopt.getopt(argv, "hn:k:s:c:t:u:", ["help", "name=",
                                                           "keep=", "server=", "config=", "store=", "user="])

        # if no arguments print usage
        if len(argv) == 0:
            usage()
            sys.exit()

            # loop through all of the command line options and set the appropriate
        # values, overriding defaults
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-n", "--name"):
                name = arg
            elif opt in ("-k", "--keep"):
                keep = int(arg)
            elif opt in ("-s", "--server"):
                server = arg
            elif opt in ("-c", "--config"):
                config_file = arg
            elif opt in ("-t", "--store"):
                store = arg
            elif opt in ("-u", "--user"):
                user = arg

    except getopt.GetoptError, msg:
        # if an error happens print the usage and exit with an error
        usage()
        sys.exit(errno.EIO)

    # check options are set correctly
    if config_file == None or store == None:
        usage()
        sys.exit(errno.EPERM)

    # process backup, catch any errors, and perform cleanup
    try:

        # another backup can't already be running, if pid file doesn't exist, then
        # create it
        if os.path.exists(pid_file):
            logging.warning("Backup running, %s pid exists, exiting." % pid_file)
            sys.exit(errno.EBUSY)
        else:
            pid = str(os.getpid())
            f = open(pid_file, "w")
            f.write("%s\n" % pid)
            f.close()

        # create the backup object and call its backup method
        ibackup = IncrementalBackup(name, server, keep, store, config_file, user)
        ibackup.backup()

    except(Exception):
        logging.exception("Incremental backup failed.")
    finally:
        os.remove(pid_file)


# if we are running the script from the command line, run the main function
if __name__ == "__main__":
    main(sys.argv[1:])