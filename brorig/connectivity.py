#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import subprocess

import os
import pymysql
import paramiko
import uuid

import brorig.log as log
import brorig.config as config


def db_connect_start():
    dbconn = pymysql.connect(host=config.config['db']['host'],
                             port=3306,
                             user=config.config['db']['user'],
                             passwd=config.config['db']['passwd'],
                             db='smp')
    log.info("DB connection started with %s" % config.config['db']['host'])
    return dbconn


def db_connect_stop(dbconn):
    dbconn.close()
    log.info("DB connction stopped")


class Connection:
    def __init__(self, host, username=None, passwd=None, pkey_path=None):
        self.host = host
        self.username = username
        self.passwd = passwd
        self.pkey = None
        if pkey_path:
            self.pkey = paramiko.RSAKey.from_private_key_file(pkey_path)

    def open_ssh_connexion(self):
        self.connection = paramiko.SSHClient()
        self.connection.load_system_host_keys()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connection.connect(self.host, port=22, username=self.username, password=self.passwd, pkey=self.pkey, timeout=10)
        self.connect_trans = paramiko.Transport((self.host, 22))
        self.connect_trans.connect(username=self.username, password=self.passwd, pkey=self.pkey)
        self.transport = paramiko.SFTPClient.from_transport(self.connect_trans)
        log.debug("SSH connection established with %s" % self.host)

    def close_ssh_connexion(self):
        self.connect_trans.close()
        self.connection.close()
        del self.connection
        del self.connect_trans
        del self.transport
        log.debug("Remote connection (%s) closed" % self.host)


class Transfer:
    def __init__(self, conn):
        self.sftp = conn

    def get(self, remote_path, local_path):
        log.debug("Download file from server %s to local %s" % (remote_path, local_path))
        self.sftp.get(remote_path, local_path)

    def put(self, local_path, remote_path):
        self.sftp.put(local_path, remote_path)


class Script:
    def __init__(self, connection, exe_remote=True, code="", interpret="bash", sudo=False,
                 ignore_error=False):
        self.connection = connection
        self.interpret = interpret
        self.exe_remote = exe_remote
        self.code = code
        self.args = {}
        self.file_name = None
        self.sudo = sudo
        self.ignore_error = ignore_error

    def __iadd__(self, other):
        self.code += other + "\n"
        return self

    def file(self, path):
        self.file_name = path

    def exe(self):
        # TODO fast remote execution (one line). Don't use remote transfer in tmp script

        # Define script name
        path_script = '/tmp/brorig_{0!s}'.format(base64.b32encode(uuid.uuid4().bytes)[:26])

        # Create local script file
        if not self.file_name:
            f = open(path_script, 'w')
            f.write(self.code)
            f.close()

        # Transfer script to remote server if needed
        if self.exe_remote:
            self.connection.open_ssh_connexion()
            t = Transfer(self.connection.transport)
            t.put(self.file_name if self.file_name else path_script, path_script)

        # Script execution
        cmd = '{sudo}{interpret} {script} {args}'.format(
            sudo=("sudo " if self.sudo else ""),
            interpret=self.interpret,
            script=path_script,
            args=" ".join([("-" if len(str(arg)) == 1 else "--") + str(arg) + " " + str(val) for arg, val in
                            self.args.iteritems()]))

        log.info("{1} code execution: {0:.100}".format(self.code, "Remote" if self.exe_remote else "Local"))
        log.debug("Launch {1} command: {0}".format(cmd, "remote" if self.exe_remote else "local"))

        if self.exe_remote:
            # Remote execution
            _, stdout, stderr = self.connection.connection.exec_command(cmd)
            err = stderr.read()
            out = stdout.read()
            return_code = self.connection.connection.recv_exit_status()
        else:
            # Local execution
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            return_code = p.returncode

        # Remove script
        os.remove(path_script)
        if self.exe_remote:
            self.connection.connection.exec_command("rm -rf {}".format(path_script))

        # Close remote connection
        if self.exe_remote:
            self.connection.close_ssh_connexion()

        # Error handler
        if return_code != 0 and not self.ignore_error:
            raise Exception('{1} script execution error: {0}'.format(err, "Remote" if self.exe_remote else "Local"))

        # End script execution
        self.connection.close_ssh_connexion()
        return out

    @staticmethod
    def remote_exe(connect, cmd=None, filename=None):
        script = Script(connect, code=cmd, exe_remote=True)
        if filename:
            script.file(filename)
        return script.exe()
