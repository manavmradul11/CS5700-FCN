from SocketServer import BaseRequestHandler, UDPServer
from struct import unpack
import random
import getopt
import struct
import sys
import math
import socket
import threading
import urllib2
#./deployCDN -p 40500 -o 'ec2-54-166-234-74.compute-1.amazonaws.com' -n 'cs5700cdn.example.com' -u 'manu11' -i '/Users/manusaxena/.ssh/id_rsa'

RECORD = {'ec2-54-166-234-74.compute-1.amazonaws.com': '54.166.234.74',
          'ec2-52-90-80-45.compute-1.amazonaws.com': '52.90.80.45',
          'ec2-54-183-23-203.us-west-2.compute.amazonaws.com': '54.183.23.203',
          'ec2-54-70-111-57.us-west-1.compute.amazonaws.com': '54.70.111.57',
          'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com': '52.215.87.82',
          'ec2-52-28-249-79.ap-southeast-1.compute.amazonaws.com': '52.28.249.79',
          'ec2-54-169-10-54.ap-northeast-1.compute.amazonaws.com': '54.169.10.54',
          'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com': '52.62.198.57',
          'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com': '52.192.64.163',
          'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com': '54.233.152.60'}

hostnames = ['ec2-52-90-80-45.compute-1.amazonaws.com',
'ec2-54-183-23-203.us-west-1.compute.amazonaws.com',
'ec2-54-70-111-57.us-west-2.compute.amazonaws.com',
'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com',
'ec2-52-28-249-79.eu-central-1.compute.amazonaws.com',
'ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com',
'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com',
'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com',
'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com']

MAP = {
         '52.90.80.45': (39.04372, -77.48749),
         '54.183.23.203': (37.77493, -122.41942),
         '54.70.111.57': (45.52345, -122.67621),
         '52.215.87.82': (53.34399, -6.26719),
         '52.28.249.79': (50.11552, 8.68417),
         '54.169.10.54': (1.28967, 103.85007),
         '52.62.198.57': (-33.86785, 151.20732),
         '52.192.64.163': (35.689506, 139.6917),
         '54.233.152.60': (-23.5475, 46.63611)}

KEY = '77e206c91186da6b8c7e8a2b2f06936c590b5bce9d6162356a83c58b0dbc96ac'




URL = 'http://api.ipinfodb.com/v3/ip-city/?key=' + KEY + '&ip='



MEASUREMENT_PORT = 60532
dic = {}


class TestThread(threading.Thread):
    def __init__(self, host, target, execute_lock):
        threading.Thread.__init__(self)
        self.host = host
        self.target = target
        self.lock = execute_lock

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = socket.gethostbyname(self.host)
        try:
            sock.connect((ip, MEASUREMENT_PORT))
            sock.sendall(self.target)
            latency = sock.recv(1024)
        except socket.error as e:
            print '[Error]Connect Measurer' + str(e)
            latency = 'inf'
        finally:
            sock.close()

        print '[DEBUG]IP: %s\tLatency:%s' % (ip, latency)
        with self.lock:
            dic.update({ip: float(latency)})


def sort_replica_act(target_ip):

    lock = threading.Lock()
    threads = []

    for i in range(len(hostnames)):
        t = TestThread(hostnames[i], target_ip, lock)
        t.start()
        threads.append(t)


    for t in threads:
        t.join()

    print '[DEBUG]Sorted Replica Server:', dic
    return dic


def sort_replica_geo(target_ip):


    def get_location(_ip):
        res = urllib2.urlopen(URL + _ip)
        loc_info = res.read().split(';')
        return float(loc_info[8]), float(loc_info[9])

    def get_distance(target, src):
        return math.sqrt(reduce(lambda x, y: x + y,
                                map(lambda x, y: math.pow((x - y), 2), target, src), 0))

    distance = {}
    for ip in MAP.keys():
        distance[ip] = 0
    target_address = get_location(target_ip)
    for ip, loc in MAP.iteritems():
        distance[ip] = get_distance(target_address, loc)

    print '[DEBUG]Sorted Replica Server:', distance
    return distance


def is_private(ip):
    f = unpack('!I', socket.inet_pton(socket.AF_INET, ip))[0]
    private = (
        [2130706432, 4278190080],
        [3232235520, 4294901760],
        [2886729728, 4293918720],
        [167772160, 4278190080],
    )
    for net in private:
        if f & net[1] == net[0]:
            return True
    return False


def select_replica(target_ip):
    if is_private(target_ip):
        return '54.166.234.74'
    result = sort_replica_act(target_ip)
    if len(set(result.values())) <= 1:
        result = sort_replica_geo(target_ip)
    sorted_result = sorted(result.items(), key=lambda e: e[1])
    return sorted_result[0][0]




class DNSPacket:
    def __init__(self):
        self.id = random.randint(0, 65535)
        self.flags = 0
        self.qcount = 0
        self.acount = 0
        self.nscount = 0
        self.arcount = 0
        self.query = DNSQuery()
        self.answer = DNSAnswer()

    def build_query(self, domain_name):
        packet = struct.pack('>HHHHHH', self.id, self.flags,
                             self.qcount, self.acount,
                             self.nscount, self.arcount)
        packet += self.query.create(domain_name)
        return packet

    def build_answer(self, domain_name, ip):
        self.answer = DNSAnswer()
        self.acount = 1
        self.flags = 0x8180
        packet = self.build_query(domain_name)
        packet += self.answer.create(ip)
        return packet

    def rebuild(self, raw_packet):
        [self.id,
         self.flags,
         self.qcount,
         self.acount,
         self.nscount,
         self.arcount] = struct.unpack('>HHHHHH', raw_packet[:12])
        self.query = DNSQuery()
        self.query.rebuild(raw_packet[12:])
        self.answer = None

    def debug_print(self):
        print 'ID: %X\tFlags:%.4X' % (self.id, self.flags)
        print 'Query Count:%d\tAnswer Count:%d' % (self.qcount, self.acount)
        if self.qcount > 0:
            self.query.debug_print()
        if self.acount > 0:
            self.answer.debug_print()


class DNSQuery:
    def __init__(self):
        self.qname = ''
        self.qtype = 0
        self.qclass = 0

    def create(self, domain_name):
        self.qname = domain_name
        query = ''.join(chr(len(x)) + x for x in domain_name.split('.'))
        query += '\x00'
        return query + struct.pack('>HH', self.qtype, self.qclass)

    def rebuild(self, raw_data):
        [self.qtype, self.qclass] = struct.unpack('>HH', raw_data[-4:])
        s = raw_data[:-4]
        ptr = 0
        temp = []
        while True:
            count = ord(s[ptr])
            if count == 0:
                break
            ptr += 1
            temp.append(s[ptr:ptr + count])
            ptr += count
        self.qname = '.'.join(temp)

    def debug_print(self):
        print '[DEBUG]DNS QUERY'
        print 'Request:', self.qname
        print 'Type: %d\tClass: %d' % (self.qtype, self.qclass)


class DNSAnswer:
    def __init__(self):
        self.aname = 0
        self.atype = 0
        self.aclass = 0
        self.ttl = 0
        self.data = ''
        self.len = 0

    def create(self, ip):
        self.aname = 0xC00C
        self.atype = 0x0001
        self.aclass = 0x0001
        self.ttl = 60
        self.data = ip
        self.len = 4
        ans = struct.pack('>HHHLH4s', self.aname, self.atype, self.aclass,
                          self.ttl, self.len, socket.inet_aton(self.data))
        return ans

    def debug_print(self):
        print '[DEBUG]DNS ANSWER'
        print 'Query: %X' % self.aname
        print 'Type: %d\tClass: %d' % (self.atype, self.aclass)
        print 'TTL: %d\tLength: %d' % (self.ttl, self.len)
        print 'IP: %s' % self.data


class DNSUDPHandler(BaseRequestHandler):
    def handle(self):
        print '[DEBUG]CDN Name: %s' % self.server.name
        data = self.request[0].strip()
        sock = self.request[1]
        packet = DNSPacket()
        packet.rebuild(data)
        print '[DEBUG]From client IP:', self.client_address[0]
        print '[DEBUG]Receive DNS Request:'
        packet.debug_print()

        if packet.query.qtype == 1:
            domain = packet.query.qname
            if domain == self.server.name:
                ip = select_replica(self.client_address[0])

                print '[DEBUG]Select replica server: %s' % ip
                data = packet.build_answer(domain, ip)
                sock.sendto(data, self.client_address)
                print '[DEBUG]Send DNS Answer:'
                packet.debug_print()
            else:
                sock.sendto(data, self.client_address)
        else:
            sock.sendto(data, self.client_address)


class SimpleDNSServer(UDPServer):
    def __init__(self, cdn_name, port, server_address, handler_class=DNSUDPHandler):
        self.name = cdn_name
        UDPServer.__init__(self, server_address, handler_class)
        return


def parse(argvs):
    (port, name) = (0, '')
    opts, args = getopt.getopt(argvs[1:], 'p:n:')
    for o, a in opts:
        if o == '-p':
            port = int(a)
        elif o == '-n':
            name = a
        else:
            sys.exit('Usage: %s -p <port> -o <origin>' % argvs[0])
    return port, name


if __name__ == '__main__':
    (port_number, cdn_name) = parse(sys.argv)
    dns_server = SimpleDNSServer(cdn_name, 40500, ('', port_number))
    dns_server.serve_forever()


