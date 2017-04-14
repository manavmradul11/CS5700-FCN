import socket, sys
import re
from struct import *
import commands
import binascii
import subprocess
import time
import array
from random import randint

BUFF = 65535
timeoutVar = 60


# Calculate the checksum for TCP packet
def checksum(s):
    if len(s) & 1:
        s = s + '\0'
    words = array.array('h', s)
    sum = 0
    for word in words:
        sum = sum + (word & 0xffff)
    hi = sum >> 16
    lo = sum & 0xffff
    sum = hi + lo
    sum = sum + (sum >> 16)
    return (~sum) & 0xffff


def _get_local_host():
    # ifconfig file is located in the /sbin/ folder.
    # command module takes the command as string and returns a output generated from command
    get_ip_config = commands.getoutput("/sbin/ifconfig")
    # Regular expressions to extract only the IP address and filter everything else
    ip_address = re.findall("inet addr:(.*?) ", get_ip_config)

    # Error handling for local host IP, if the internet connect does not exist.
    for ip in ip_address:
        if ip != '127.0.0.1':
            return ip


# Select any random port
def _get_port():
    return randint(35000, 65565)


# Default ethernet interface is eth0
NET_INTERFACE = 'eth0'


# Assemble and disassemble Ethernet packet
class EthernetPacket:
    def __init__(self):
        self.src_mac_addr = ''
        self.dest_mac_addr = ''
        self.ethernet_type = 0
        self.data = ''

    def disassemble(self, packet):
        [self.dest_mac_addr, self.src_mac_addr, self.ethernet_type] = unpack('!6s6sH', packet[:14])
        self.dest_mac_addr = binascii.hexlify(self.dest_mac_addr)
        self.src_mac_addr = binascii.hexlify(self.src_mac_addr)
        self.data = packet[14:]

    def assemble(self, ether_type=0x800):
        # Ethernet type for IP is 0x800
        src = binascii.unhexlify(self.src_mac_addr)
        dest = binascii.unhexlify(self.dest_mac_addr)
        header = pack('!6s6sH', dest, src, ether_type)
        return header + self.data


# ARP to find MAC address of destination
class ARPPacket:
    def __init__(self):
        self.hw_type = 1
        self.proto_type = 0x800  # IP protocol
        self.hw_addr_len = 6
        self.proto_addr_len = 4
        self.op = 0
        self.send_hw_addr = ''
        self.send_proto_addr = ''
        self.recv_hw_addr = ''
        self.recv_proto_addr = ''

    def disassemble(self, raw_packet):
        [self.hw_type, self.proto_type, self.hw_addr_len, self.proto_addr_len, self.op, binary_SHA, binary_SPA, \
         binary_RHA, binary_RPA] = unpack("!HHBBH6s4s6s4s", raw_packet)
        self.send_hw_addr = binascii.hexlify(binary_SHA)
        self.recv_hw_addr = binascii.hexlify(binary_RHA)
        self.send_proto_addr = socket.inet_ntoa(binary_SPA)
        self.recv_proto_addr = socket.inet_ntoa(binary_RPA)

    def assemble(self, operation=1):
        binary_SHA = binascii.unhexlify(self.send_hw_addr)
        binary_RHA = binascii.unhexlify(self.recv_hw_addr)
        binary_SPA = socket.inet_aton(self.send_proto_addr)
        binary_RPA = socket.inet_aton(self.recv_proto_addr)
        return pack("!HHBBH6s4s6s4s", self.hw_type, self.proto_type, self.hw_addr_len, self.proto_addr_len, \
                    operation, binary_SHA, binary_SPA, binary_RHA, binary_RPA)


# class defining the format for DataLink layer
class DataLinkLayer:
    def __init__(self):
        self.src_mac = ""
        self.dest_mac = ""
        self.gateway_mac = ""
        self.send_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.recv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))

    def connect(self):
        self.send_sock.bind((NET_INTERFACE, 0))

    def get_mac_addr_by_arp(self, dest_ip):
        send_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        receive_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        src_mac = self.get_mac_addr()
        src_ip = self.get_ip_addr()
        self.src_mac = src_mac
        ARP_Request_Packet = ARPPacket()
        ARP_Request_Packet.send_hw_addr = src_mac
        ARP_Request_Packet.send_proto_addr = src_ip

        ARP_Request_Packet.recv_hw_addr = "000000000000"
        ARP_Request_Packet.recv_proto_addr = dest_ip

        Ethernet_packet = EthernetPacket()
        Ethernet_packet.src_mac_addr = src_mac
        Ethernet_packet.dest_mac_addr = "FFFFFFFFFFFF"

        Ethernet_packet.data = ARP_Request_Packet.assemble(1)
        send_socket.sendto(Ethernet_packet.assemble(0x0806), (NET_INTERFACE, 0))

        ARP_res_packet = ARPPacket()
        while True:

            recv_raw_packet = receive_socket.recvfrom(4096)[0]
            Ethernet_packet.disassemble(recv_raw_packet)
            if self.src_mac == Ethernet_packet.dest_mac_addr:
                ARP_res_packet.disassemble(Ethernet_packet.data[:28])
                if ARP_res_packet.recv_proto_addr == src_ip and ARP_res_packet.send_proto_addr == dest_ip:
                    break

        send_socket.close()
        receive_socket.close()

        return ARP_res_packet.send_hw_addr

    def get_gateway_ip(self):
        out = subprocess.check_output(['route', '-n']).split('\n')
        data = []
        res = []

        for line in out:

            if line[:7] == '0.0.0.0':
                data = line.split(' ')
                break

        for i in range(len(data)):
            if data[i] != '':
                res.append(data[i])

        return res[1]

    def get_ip_addr(self):
        # ifconfig file is located in the /sbin/ folder.
        # command module takes the command as string and returns a output generated from command
        get_ip_config = commands.getoutput("/sbin/ifconfig")
        # Regular expressions to extract only the IP address and filter everything else
        ip_address = re.findall("inet addr:(.*?) ", get_ip_config)
        for ip in ip_address:

            if ip != '127.0.0.1':
                return ip

    def get_mac_addr(self):

        get_ip_config = commands.getoutput("/sbin/ifconfig")
        # Regular expressions to extract only the MAC address and filter everything else
        mac_address = re.findall("HWaddr (.*?) ", get_ip_config)

        return mac_address[0].replace(":", "")

    def send(self, raw_packet):
        self.connect()

        if self.gateway_mac == '':
            try:
                self.gateway_mac = self.get_mac_addr_by_arp(self.get_gateway_ip())
            except:

                sys.exit(0)

        Ethernet_Packet = EthernetPacket()
        Ethernet_Packet.src_mac_addr = self.src_mac

        Ethernet_Packet.dest_mac_addr = self.gateway_mac
        self.dest_mac = Ethernet_Packet.dest_mac_addr
        Ethernet_Packet.data = raw_packet

        self.send_sock.send(Ethernet_Packet.assemble())

    def receive(self):

        Ethernet_Packet = EthernetPacket()

        while True:

            try:
                packet_recv = self.recv_sock.recvfrom(4096)[0]
            except socket.error:
                print "display error"
            Ethernet_Packet.disassemble(packet_recv)

            if Ethernet_Packet.dest_mac_addr == self.src_mac and Ethernet_Packet.src_mac_addr == self.dest_mac:
                return Ethernet_Packet.data


'''

0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Version|  IHL  |Type of Service|          Total Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Identification        |Flags|      Fragment Offset    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Time to Live |    Protocol   |         Header Checksum       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Source Address                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Destination Address                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

'''


class IPPacket:
    def __init__(self, saddr_='', daddr_='', data_=''):
        self.ip_ihl = 5  # IP Header Length
        self.ip_ver = 4  # IPV4
        self.ip_tos = 0  # Type of service
        self.ip_ecn = 0
        self.ip_tot_len = 0  # Total length of the packet
        self.ip_id = 0  # Identification bit
        self.ip_flag_df = 1  # Do not fragment bit
        self.ip_flag_mf = 0
        self.ip_frag_off = 0
        self.ip_ttl = 255  # Time to live
        self.ip_proto = socket.IPPROTO_TCP  # TCP protocol (6)
        self.ip_check = 0  # IP checksum
        self.ip_saddr = saddr_  # Source address
        self.ip_daddr = daddr_  # Destination address
        self.ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl
        self.ip_tos_ecn = (self.ip_tos << 2) + self.ip_ecn
        self.ip_flag_frag = (((self.ip_flag_df << 1) + self.ip_flag_mf) << 13) + self.ip_frag_off
        self.data = data_

    def AssemblePacket(self):
        self.id = randint(0, 65535)

        self.ip_tot_len = self.ip_ihl * 4 + len(self.data)

        src_addr = socket.inet_aton(self.ip_saddr)
        dest_addr = socket.inet_aton(self.ip_daddr)

        fake_ip_header = pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, \
                              self.ip_id, self.ip_flag_frag, self.ip_ttl, self.ip_proto, self.ip_check, src_addr,
                              dest_addr)

        self.ip_check = network_chksum(fake_ip_header)
        # Pack the IP Header according to format shown above
        ip_header = pack('!BBHHHBB', self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, \
                         self.ip_id, self.ip_flag_frag, self.ip_ttl, self.ip_proto) + \
                    pack('H', self.ip_check) + pack('!4s4s', src_addr, dest_addr)

        packet = ip_header + self.data
        return packet

    def disAssemble(self, packet_raw):
        # Unpack the IP Header according to format shown above
        [self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, self.ip_id, self.ip_flag_frag, \
         self.ip_ttl, self.ip_proto] = unpack('!BBHHHBB', packet_raw[0:10])
        [self.ip_check] = unpack('H', packet_raw[10:12])
        [src_addr, dest_addr] = unpack('!4s4s', packet_raw[12:20])

        self.ip_ihl = self.ip_ihl_ver & 0x0f
        self.ip_ver = (self.ip_ihl_ver & 0xf0) >> 4
        self.ip_tos = (self.ip_tos_ecn & 0xfc) >> 2
        self.ip_ecn = self.ip_tos_ecn & 0x03
        self.ip_flag_df = (self.ip_flag_frag & 0x40) >> 14
        self.ip_flag_mf = (self.ip_flag_frag & 0x20) >> 13
        self.ip_frag_off = self.ip_flag_frag & 0x1f

        self.ip_saddr = socket.inet_ntoa(src_addr)
        self.ip_daddr = socket.inet_ntoa(dest_addr)

        self.data = packet_raw[self.ip_ihl * 4:self.ip_tot_len]

        fake_ip_header = packet_raw[0:10] + pack('H', 0) + packet_raw[12:20]
        new_chksum = network_chksum(fake_ip_header)
        if self.ip_check != new_chksum:
            raise ValueError


class IPLayer:
    def __init__(self, saddr_='', daddr_=''):
        self.sock = DataLinkLayer()

        self.src_addr = saddr_
        self.dest_addr = daddr_

    def send(self, saddr_, daddr_, data):
        self.src_addr = saddr_
        self.dest_addr = daddr_
        send_ip_packets = IPPacket(self.src_addr, self.dest_addr, data)
        try:
            self.sock.send(send_ip_packets.AssemblePacket())
        except:
            raise ValueError

    def recv(self, packet_type=socket.IPPROTO_TCP):
        while True:
            ip_packet_received = IPPacket()
            packet_raw = self.sock.receive()

            try:
                ip_packet_received.disAssemble(packet_raw)
            except:

                continue

            if ip_packet_received.ip_proto == packet_type and \
                            ip_packet_received.ip_saddr == self.dest_addr and \
                            ip_packet_received.ip_daddr == self.src_addr:
                return ip_packet_received.data


def network_chksum(msg):
    if len(msg) & 1:
        msg = msg + '\0'
    words = array.array('h', msg)
    sum = 0
    for word in words:
        sum = sum + (word & 0xffff)
    high = sum >> 16
    low = sum & 0xffff
    sum = high + low
    sum = sum + (sum >> 16)
    return (~sum) & 0xffff


# The structure of TCP packet is as follows

'''

0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Source Port          |       Destination Port        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Sequence Number                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Acknowledgment Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Data |           |U|A|P|R|S|F|                               |
   | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
   |       |           |G|K|H|T|N|N|                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum            |         Urgent Pointer        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                             data                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

'''


class TCPPacket:
    def __init__(self, src_port_=0, dest_port_=0, src_ip_='', dest_ip_='', data_=''):
        self.src_port = src_port_
        self.dest_port = dest_port_
        self.seq_num = 0
        self.ack_num = 0
        self.data_off = 5
        self.fin = 0
        self.syn = 0
        self.rst = 0
        self.psh = 0
        self.ack = 0
        self.urg = 0
        self.window = 65535
        self.checksum = 0
        self.urg_ptr = 0
        self.data = data_
        self.src_ip = src_ip_
        self.dest_ip = dest_ip_
        self.MSS = 536

    # createPacket function creates a TCP packet. It inserts header data like Source and Destination IP and Flags

    def createPacket(self):
        # Get src and dest ip in dotted format
        src_ip = socket.inet_aton(self.src_ip)
        dest_ip = socket.inet_aton(self.dest_ip)
        self.checksum = 0
        offset_res = (self.data_off << 4) + 0
        tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)
        # returns packed binary data.
        tcp_header = pack('!HHLLBBHHH', self.src_port, self.dest_port, self.seq_num,
                          self.ack_num, offset_res, tcp_flags, self.window, self.checksum, self.urg_ptr)

        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(self.data)

        pesudo_header = pack('!4s4sBBH', src_ip, dest_ip, placeholder, protocol, tcp_length)
        temp = pesudo_header + tcp_header + self.data
        # calculate checksum
        if len(temp) % 2 != 0:
            temp = temp + pack('B', 0)
        self.checksum = checksum(temp)

        # return a binary package representing the tcp header
        tcp_header_new = pack('!HHLLBBH', self.src_port, self.dest_port, self.seq_num, self.ack_num,
                              offset_res, tcp_flags, self.window) + pack('H', self.checksum) + pack('!H', self.urg_ptr)

        return tcp_header_new + self.data

    # disAssemble : decode the received TCP packet

    def disAssemble(self, packet_raw):
        # disassemble the packet
        [self.src_port, self.dest_port, self.seq_num, self.ack_num, offset_res, tcp_flags,
         self.window] = unpack('!HHLLBBH', packet_raw[0:16])
        [self.checksum] = unpack('H', packet_raw[16:18])
        [self.urg_ptr] = unpack('!H', packet_raw[18:20])

        len_header = offset_res >> 4
        self.fin = tcp_flags & 0x01
        self.syn = (tcp_flags & 0x02) >> 1
        self.rst = (tcp_flags & 0x04) >> 2
        self.psh = (tcp_flags & 0x08) >> 3
        self.ack = (tcp_flags & 0x16) >> 4
        self.urg = (tcp_flags & 0x32) >> 5
        self.data = packet_raw[len_header * 4:]
        # calculate the checksum for received packet. This makes sure received packet is not corrupted in transit

        src_ip = socket.inet_aton(self.src_ip)
        dest_ip = socket.inet_aton(self.dest_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        # tcp_length should be the length inside the header * 4 and plust the length of the data
        tcp_length = len_header * 4 + len(self.data)

        pesudo_header = pack('!4s4sBBH', src_ip, dest_ip, placeholder, protocol, tcp_length)
        tcp_header_and_data = packet_raw[:16] + pack('H', 0) + packet_raw[18:]
        temp = pesudo_header + tcp_header_and_data
        new_checksum = checksum(temp)

        if self.checksum != new_checksum:
            raise ValueError


class TCPLayer:
    def __init__(self, src_ip_='', dest_ip_='', data_=''):
        self.src_ip = src_ip_
        self.dest_ip = dest_ip_
        self.src_port = 0
        self.dest_port = 0
        self.seq_num = 0
        self.ack_num = 0

        self.sock = IPLayer()
        self.pre_seq = 0  # to store the packet seq and ack number for retransmission
        self.pre_ack = 0
        self.cwnd = 1  # initial congestion window size
        self.MSS = 536

    def connect(self, hostname, dest_port=80):

        self.dest_port = dest_port
        src_ip_ = _get_local_host()
        dest_ip_ = socket.gethostbyname(hostname)
        self.dest_ip = dest_ip_
        self.src_ip = src_ip_
        # random selection of source port
        self.src_port = _get_port()

        # 3 way handshake process
        self.data = ''
        tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, self.data)
        tcp_packet.syn = 1

        self.seq_num = randint(0, 65535)

        tcp_packet.seq_num = self.seq_num
        count = 0
        while True:
            if count >= 2:
                sys.exit(0)
            self.sendPacket(tcp_packet.createPacket())
            tcp_packet = self._recv_until_timeout()

            if tcp_packet == '' and count < 2:
                count += 1

                continue
            if tcp_packet.rst == 1:

                sys.exit(0)
            else:

                if tcp_packet.syn == 1 and tcp_packet.ack == 1 and tcp_packet.ack_num == self.seq_num + 1:
                    self.seq_num = tcp_packet.ack_num
                    self.ack_num = tcp_packet.seq_num
                    break
                else:
                    count += 1

                    continue

        tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, self.data)
        tcp_packet.ack = 1
        tcp_packet.seq_num = self.seq_num
        tcp_packet.ack_num = self.ack_num + 1
        self.ack_num = self.ack_num + 1
        self.sendPacket(tcp_packet.createPacket())

    def send(self, data):
        # build a new tcp packet and send it to the dest ip, then wait for the ack.
        # If the wait time exceeds the timeout, retransmit this packet
        self.cwnd = self.MSS
        while len(data) > 0:
            send_data = data[:self.cwnd]
            data = data[self.cwnd:]
            tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, data)
            tcp_packet.seq_num = self.seq_num
            tcp_packet.ack_num = self.ack_num
            tcp_packet.ack = 1
            tcp_packet.psh = 1
            tcp_packet.data = send_data

            self.sendPacket(tcp_packet.createPacket())

            while True:
                get_tcp_packet = self._recv_until_timeout()
                if get_tcp_packet == '':

                    retransmit_tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, data)
                    retransmit_tcp_packet.seq_num = self.seq_num
                    retransmit_tcp_packet.ack_num = self.ack_num
                    retransmit_tcp_packet.ack = 1
                    retransmit_tcp_packet.psh = 1
                    # If ACK is not received then decrease the cwnd
                    if self.cwnd > 1:
                        self.cwnd -= 1
                    else:
                        self.cwnd = self.MSS
                    retransmit_tcp_packet.data = send_data
                    try:
                        self.sendPacket(retransmit_tcp_packet.createPacket())
                    except:
                        continue

                else:

                    if get_tcp_packet.rst == 1:
                        sys.exit(0)
                    if get_tcp_packet.ack == 1 and get_tcp_packet.ack_num == (
                                self.seq_num + min(self.cwnd, len(send_data))):

                        # Implement a basic congestion window, start with 1 and increase till 1000
                        if self.cwnd < 1000:
                            self.cwnd += 1
                        else:
                            self.cwnd = 1000

                        self.pre_ack = self.ack_num
                        self.pre_seq = self.seq_num
                        self.seq_num = get_tcp_packet.ack_num
                        self.ack_num = get_tcp_packet.seq_num
                        break
                    else:
                        continue

    def recvPackets(self):
        result_data = []

        while True:
            tcp_packet = self._recv_until_timeout()

            if tcp_packet == '':
                sys.exit(0)

            if tcp_packet.rst == 1:
                sys.exit(0)
            else:

                if tcp_packet.seq_num == self.pre_ack:

                    if tcp_packet.fin == 1:
                        self.ack_num = tcp_packet.seq_num + len(tcp_packet.data) + 1
                        self.seq_num = tcp_packet.ack_num
                        ack_fin_tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
                        ack_fin_tcp_packet.ack = 1
                        ack_fin_tcp_packet.ack_num = self.ack_num
                        ack_fin_tcp_packet.seq_num = self.seq_num
                        self.sendPacket(ack_fin_tcp_packet.createPacket())
                        self.pre_ack = self.ack_num
                        self.pre_seq = self.seq_num
                        break

                    else:
                        result_data.append(tcp_packet.data)
                        self.seq_num = tcp_packet.ack_num
                        self.ack_num = tcp_packet.seq_num + len(tcp_packet.data)
                        ack_next_tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip,
                                                        '')
                        ack_next_tcp_packet.ack = 1
                        ack_next_tcp_packet.seq_num = self.seq_num
                        ack_next_tcp_packet.ack_num = self.ack_num
                        self.sendPacket(ack_next_tcp_packet.createPacket())
                        self.pre_seq = self.seq_num
                        self.pre_ack = self.ack_num

                elif tcp_packet.seq_num != self.pre_ack:
                    ack_loss_tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
                    ack_loss_tcp_packet.ack_num = self.pre_ack
                    ack_loss_tcp_packet.seq_num = self.pre_seq
                    ack_loss_tcp_packet.ack = 1
                    self.sendPacket(ack_loss_tcp_packet.createPacket())

        return ''.join(result_data)

    def close(self):
        # Close a connection by sending fin and ack flags
        fin_flag_tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
        fin_flag_tcp_packet.fin = 1
        fin_flag_tcp_packet.ack = 1
        fin_flag_tcp_packet.ack_num = self.ack_num
        fin_flag_tcp_packet.seq_num = self.seq_num
        self.sendPacket(fin_flag_tcp_packet.createPacket())
        tcp_packet = self._recv_until_timeout()
        # Acknowledgment flag not received
        if tcp_packet == '':
            sys.exit(0)
        # Server sends a reset RST flag
        if tcp_packet.rst == 1:

            sys.exit(0)
        else:
            # fin and ack flag is received
            if self.ack_num == tcp_packet.seq_num and self.seq_num + 1 == tcp_packet.ack_num and tcp_packet.fin == 1 and tcp_packet.ack == 1:

                self.ack_num = tcp_packet.seq_num + 1
                self.seq_num = tcp_packet.ack_num
                tcp_packet = TCPPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
                tcp_packet.ack_num = self.ack_num
                tcp_packet.seq_num = self.seq_num
                tcp_packet.fin = 1
                self.sendPacket(tcp_packet.createPacket())
                return

            elif self.ack_num == tcp_packet.seq_num and self.seq_num + 1 == tcp_packet.ack_num and tcp_packet.ack == 1 and tcp_packet.fin == 0:

                return
            else:
                sys.exit(0)

    def sendPacket(self, tcp_packet):
        count = 0
        while True:
            try:
                self.sock.send(self.src_ip, self.dest_ip, tcp_packet)
                break
            except:
                if count > 6:
                    sys.exit(0)
                count += 1
                continue

    def _recv_until_timeout(self):
        start = time.time()
        tcp_packet = TCPPacket()
        while time.time() - start < timeoutVar:

            try:
                raw_packet = self.sock.recv(socket.IPPROTO_TCP)
            except:
                continue

            tcp_packet.src_ip = self.dest_ip
            tcp_packet.dest_ip = self.src_ip
            try:
                tcp_packet.disAssemble(raw_packet)
            except ValueError:
                continue

            if tcp_packet.src_port == self.dest_port and tcp_packet.dest_port == self.src_port:
                return tcp_packet
            else:
                continue
        return ''
