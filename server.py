import base64
from binascii import hexlify
import os
import socket
import sys
import threading
import traceback

import paramiko
from paramiko.py3compat import b, u, decodebytes

host_key = paramiko.RSAKey(filename='test_rsa.key')

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_auth_none(self, username):
        return False

# now connect
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 2200))
except Exception as e:
    print('*** Bind failed: ' + str(e))
    traceback.print_exc()
    sys.exit(1)

try:
    sock.listen(100)
    print('Listening for connection ...')
    client, addr = sock.accept()
except Exception as e:
    print('*** Listen/accept failed: ' + str(e))
    traceback.print_exc()
    sys.exit(1)

print('Got a connection!')

try:
    t = paramiko.Transport(client)
    t.set_gss_host(socket.getfqdn(""))
    try:
        t.load_server_moduli()
    except:
        print('(Failed to load moduli -- gex will be unsupported.)')
        raise
    t.add_server_key(host_key)
    server = Server()

    try:
        t.start_server(server=server)
    except paramiko.SSHException:
        print('*** SSH negotiation failed.')
        sys.exit(1)

    # wait for auth
    chan = t.accept(20)
    if chan is None:
        print('*** No channel.')
        sys.exit(1)
    print('Authenticated!')

    server.event.wait(10)
    if not server.event.is_set():
        print('*** Client never asked for a shell.')
        sys.exit(1)

    chan.send('\r\n\r\nWelcome to my dorky little BBS!\r\n\r\n')
    chan.send('We are on fire all the time!  Hooray!  Candy corn for everyone!\r\n')
    chan.send('Happy birthday to Robot Dave!\r\n\r\n')

    while True:
        chan.send('Username: ')
        f = chan.makefile('rU')
        username = f.readline().strip('\r\n')
        chan.send('\r\nI don\'t like you, ' + username + '.\r\n')

except Exception as e:
    print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)
