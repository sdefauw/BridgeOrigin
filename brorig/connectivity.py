#!/usr/bin/env python
# coding: utf-8
import subprocess

import pymysql
import log
import config
import paramiko


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
    def __init__(self, host, username=None, passwd=None):
        self.host = host
        self.username = username
        self.passwd = passwd

    def open_ssh_connexion(self):
        self.connection = paramiko.SSHClient()
        self.connection.load_system_host_keys()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connection.connect(self.host, port=22, username=self.username, password=self.passwd, timeout=10)
        self.connect_trans = paramiko.Transport((self.host, 22))
        self.connect_trans.connect(username=self.username, password=self.passwd)
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
    def __init__(self, connection, exe_remote=True, code="", interpret="sh", sudo=False,
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
        # Open SSH connection
        self.connection.open_ssh_connexion()
        # Write file script
        path_script = '/tmp/script'
        if not self.file_name:
            f = open(path_script, 'w')
            f.write(self.code)
            f.close()
        # Transfer if needed
        if self.exe_remote:
            t = Transfer(self.connection.transport)
            t.put(self.file_name if self.file_name else path_script, path_script)
        # Execute script
        starter_script = self.interpret
        if self.sudo:
            starter_script = "sudo " + starter_script
        cmd = starter_script + ' ' + path_script
        cmd += ((" " + (
            " ".join(["--" + str(arg) + " " + str(val) for arg, val in
                      self.args.iteritems()]))) if self.args != {} else "")
        if self.exe_remote:
            log.info("Remote command execution: %s" % cmd)
            _, stdout, stderr = self.connection.connection.exec_command(cmd)
            err = stderr.read()
            out = stdout.read()
            if err and not self.ignore_error:
                self.connection.close_ssh_connexion()
                raise Exception('Remote script execution: ' + err)
        else:
            log.info("Local command execution: %s" % cmd)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            if err and not self.ignore_error:
                self.connection.close_ssh_connexion()
                raise Exception('Local script execution: ' + err)
        self.connection.close_ssh_connexion()
        return out

    @staticmethod
    def remote_exe(connect, cmd=None, filename=None):
        script = Script(connect, code=cmd, exe_remote=True)
        if filename:
            script.file(filename)
        return script.exe()
