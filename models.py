from datetime import datetime


class HttpLog:

    def __init__(self, remotehost, rfc931, authuser, timestamp, request, status, bytes):
        self.remotehost = remotehost
        self.rfc931 = rfc931
        self.authuser = authuser
        self.timestamp = int(timestamp)
        self.request = request
        self.section = request.split('/')[1].split(' ')[0]
        self.status = status
        self.bytes = bytes
