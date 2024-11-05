import pysftp
import os
import common.infradmin_logs
import re


class Sftp:
    def __init__(self, s_hostname, s_username, s_password, i_port=22):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.o_connection = None
        self.s_hostname = s_hostname
        self.s_username = s_username
        self.s_password = s_password
        self.i_port = i_port
        self.o_logger = common.infradmin_logs.O_LOGGER

    def connect(self):
        """
        Connects to the sftp server and returns the sftp connection object
        """
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            # Get the sftp connection object
            self.o_connection = pysftp.Connection(
                host=self.s_hostname,
                username=self.s_username,
                password=self.s_password,
                port=self.i_port,
                cnopts=cnopts
            )
        except Exception as err:
            raise Exception(err)
        finally:
            self.o_logger.info(f"Connected to {self.s_hostname} as {self.s_username}.")

    def disconnect(self):
        """
        Closes the sftp connection
        """
        self.o_connection.close()
        self.o_logger.info(f"Disconnected from host {self.s_hostname}")

    def listdir(self, s_remote_path: str) -> list:
        """
        lists all the files and directories in the specified path and returns them
        :return: A list of dirs
        """
        return self.o_connection.listdir(s_remote_path)

    def download(self, s_remote_path: str, s_target_local_path: str):
        """
        Downloads the file from remote sftp server to local.
        Also, by default extracts the file to the specified target_local_path
        """

        try:
            self.o_logger.info(
                f"downloading from {self.s_hostname} as {self.s_username} [(remote path : {s_remote_path});(local path: {s_target_local_path})]"
            )

            # Create the target directory if it does not exist
            path, _ = os.path.split(s_target_local_path)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception as err:
                    raise Exception(err)

            # Download from remote sftp server to local
            self.o_connection.get(s_remote_path, s_target_local_path)
            self.o_logger.info("download completed")

        except Exception as err:
            raise Exception(err)

    def upload(self, s_source_local_path: str, s_remote_path: str):
        """
        Uploads the source files from local to the sftp server.
        """

        try:
            self.o_logger.info(
                f"uploading to {self.s_hostname} as {self.s_username} [(remote path: {s_remote_path});(source local path: {s_source_local_path})]"
            )

            # Download file from SFTP
            self.o_connection.put(s_source_local_path, s_remote_path)
            self.o_logger.info("upload completed")

        except Exception as err:
            raise Exception(err)

    def delete(self, s_file_path):
        try:
            self.o_logger.info(f"delting {s_file_path} on {self.s_hostname}")
            self.o_connection.remove(s_file_path)
        except Exception as err:
            raise Exception(err)

    def execute_command(self, s_command: str):
        try:
            self.o_logger.info(f"executing command {s_command} on {self.s_hostname}")
            l_result = self.o_connection.execute(s_command)
        except Exception as err:
            raise Exception(err)
        return l_result

    def size_available(self, i_required_space_gb: int, s_file_path: str) -> bool:
        b_ret = False
        s_dir_path = os.path.dirname(s_file_path)
        l_result = self.execute_command(f'df -h {s_dir_path}')
        self.o_logger.info(f"Checking available space on {self.s_hostname} : {l_result}")
        for s_ligne in l_result:
            s_ligne = s_ligne.decode('utf-8').strip()  # Decode bytes to string and strip whitespace
            self.o_logger.info(f"Checking available space on line : {s_ligne}")
            match = re.search(r'(\S+)\s+(\d+)([KMGTP])\s+(\d+)([KMGTP])\s+(\d+)([KMGTP])\s+(\d+)%\s+(\S+)', s_ligne)
            if match:
                size, size_unit, used, used_unit, avail, avail_unit, root, root_unit, capacity = match.groups()
                self.o_logger.info(f"Checking if {i_required_space_gb} is lower than {avail}{avail_unit}")
                self.o_logger.info(f"debug: size is {size}{size_unit}, used is {used}{used_unit}, avail is {avail}{avail_unit}, root is {root}{root_unit}, capacity is {capacity}")
                if avail_unit == 'G' and int(avail) >= i_required_space_gb:
                    b_ret = True
                elif avail_unit == 'T' and int(avail) * 1024 >= i_required_space_gb:
                    b_ret = True
                # Add more unit conversions if needed
                break

        return b_ret
