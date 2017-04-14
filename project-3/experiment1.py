#!/usr/bin/python

import os

class Record:
    def __init__(self, line):
        contents = line.split()
        self.pkt_type = contents[4]
        self.pkt_size = int(contents[5])
        self.flow_id = contents[7]
        self.src_addr = contents[8]
        self.dst_addr = contents[9]
        self.seq_num = contents[10]
        self.pkt_id = contents[11]
        self.event = contents[0]
        self.time = float(contents[1])
        self.from_node = contents[2]
        self.to_node = contents[3]



TCP_Variant = ['Tahoe', 'Reno', 'NewReno', 'Vegas']
RATE_Variant = [1, 3, 5,7,8,8.5,9,9.2,9.4,9.6]

MEGA = 1024*1024





def calculate_throughput(var, rate):
    filename = "tracefiles/exp1/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        start_time = 10.0
        end_time = 0.0
        recvdSize = 0
        for line in lines:
            record = Record(line)
            if record.flow_id == "1":
                if record.event == "+" and record.from_node == "0":
                    if record.time < start_time:
                        start_time = record.time
                if record.event == "r":
                    recvdSize += record.pkt_size * 8
                    end_time = record.time
        return recvdSize / (end_time - start_time) / MEGA
    return 0


def calculate_drop_rate(var, rate):
    filename = "tracefiles/exp1/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        sendNum = recvdNum = 0
        for line in lines:
            record = Record(line)
            if record.flow_id == "1":
                if record.event == "+":
                    sendNum += 1
                if record.event == "r":
                    recvdNum += 1
        if sendNum == 0:
            return 0
        else:
            return float(sendNum - recvdNum) / float(sendNum)
    return 0


def calculate_latency(var, rate):
    filename = "tracefiles/exp1/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        end_time = {}
        start_time = {}
        total_duration = 0.0
        total_packet = 0
        for line in lines:
            record = Record(line)
            if record.flow_id == "1":
                if record.event == "+" and record.from_node == "0":
                    start_time.update({record.seq_num: record.time})
                if record.event == "r" and record.to_node == "0":
                    end_time.update({record.seq_num: record.time})
        packets = {x for x in start_time.viewkeys() if x in end_time.viewkeys()}
        for i in packets:
            start = start_time[i]
            end = end_time[i]
            duration = end - start
            if duration > 0:
                total_duration += duration
                total_packet += 1
        if total_packet == 0:
            return 0
        return total_duration / total_packet * 1000
    return 0


f1 = open('output/exp1/throughput.dat', 'w')
f2 = open('output/exp1/droprate.dat', 'w')
f3 = open('output/exp1/delay.dat', 'w')
for rate in RATE_Variant:
    str_throughput = ''
    str_droprate = ''
    str_latency = ''
    for var in TCP_Variant:
        str_throughput = str_throughput + '\t' + str(calculate_throughput(var, rate))
        str_droprate = str_droprate + '\t' + str(calculate_drop_rate(var, rate))
        str_latency = str_latency + '\t' + str(calculate_latency(var, rate))
    f1.write(str(rate) + str_throughput + '\n')
    f2.write(str(rate) + str_droprate + '\n')
    f3.write(str(rate) + str_latency + '\n')
f1.close()
f2.close()
f3.close()
