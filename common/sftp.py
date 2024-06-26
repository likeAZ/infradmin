import pysftp
import os
import common.infradmin_logs


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
        self.o_logger.info(f"delting {s_file_path} on {self.s_hostname}")
        self.o_connection.remove(s_file_path)
