#!/usr/bin/python

import os
import sys

TCP_Variant = ['Reno_Reno', 'NewReno_Reno', 'Vegas_Vegas', 'NewReno_Vegas']
RATE_Variant = [1, 2,3,4,5,6,7,8,9,10]

class Record:
    def __init__(self, line):
        contents = line.split()
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
        self.pkt_type = contents[4]


def calculate_throughput(var, rate):
    filename = "tracefiles/exp2/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        start_time1 = start_time2 = 10.0
        end_time1 = end_time2 = 0.0
        recvdSize1 = recvdSize2 = 0
        for line in lines:
            record = Record(line)
            if record.flow_id == "1":  # TCP stream from 1 to 4
                if record.event == "+" and record.from_node == "0":
                    if (record.time < start_time1):
                        start_time1 = record.time
                if record.event == "r":
                    recvdSize1 += record.pkt_size * 8
                    end_time1 = record.time
            if record.flow_id == "2":  # TCP stream from 5 to 6
                if record.event == "+" and record.from_node == "4":
                    if record.time < start_time2:
                        start_time2 = record.time
                if record.event == "r":
                    recvdSize2 += record.pkt_size * 8
                    end_time2 = record.time
        th1 = recvdSize1 / (end_time1 - start_time1) / (1024 * 1024)
        th2 = recvdSize2 / (end_time2 - start_time2) / (1024 * 1024)
        return str(th1) + '\t' + str(th2)

    return 'no'


def calculate_drop_rate(var, rate):
    filename = "tracefiles/exp2/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        sendNum1 = recvdNum1 = 0
        sendNum2 = recvdNum2 = 0

        for line in lines:
            record = Record(line)
            if record.flow_id == "1":
                if record.event == "+":
                    sendNum1 += 1
                if record.event == "r":
                    recvdNum1 += 1
            if record.flow_id == "2":
                if record.event == "+":
                    sendNum2 += 1
                if record.event == "r":
                    recvdNum2 += 1

        dr1 = 0 if sendNum1 == 0 else float(sendNum1 - recvdNum1) / float(sendNum1)
        dr2 = 0 if sendNum2 == 0 else float(sendNum2 - recvdNum2) / float(sendNum2)
        return str(dr1) + '\t' + str(dr2)
    return 'no'


def calculate_latency(var, rate):
    filename = "tracefiles/exp2/"+var + "_output-" + str(rate) + ".tr"
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        start_time1 = {}
        end_time1 = {}
        start_time2 = {}
        end_time2 = {}
        total_duration1 = total_duration2 = 0.0
        total_packet1 = total_packet2 = 0

        for line in lines:
            record = Record(line)
            if record.flow_id == "1":
                if record.event == "+" and record.from_node == "0":
                    start_time1.update({record.seq_num: record.time})
                if record.event == "r" and record.to_node == "0":
                    end_time1.update({record.seq_num: record.time})
            if record.flow_id == "2":
                if record.event == "+" and record.from_node == "4":
                    start_time2.update({record.seq_num: record.time})
                if record.event == "r" and record.to_node == "4":
                    end_time2.update({record.seq_num: record.time})
        packets = {x for x in start_time1.viewkeys() if x in end_time1.viewkeys()}
        for i in packets:
            start = start_time1[i]
            end = end_time1[i]
            duration = end - start
            if (duration > 0):
                total_duration1 += duration
                total_packet1 += 1
        packets = {x for x in start_time2.viewkeys() if x in end_time2.viewkeys()}
        for i in packets:
            start = start_time2[i]
            end = end_time2[i]
            duration = end - start
            if duration > 0:
                total_duration2 += duration
                total_packet2 += 1

        delay1 = 0 if total_packet1 == 0 else total_duration1 / total_packet1 * 1000
        delay2 = 0 if total_packet2 == 0 else total_duration2 / total_packet2 * 1000

        return str(delay1) + '\t' + str(delay2)
    return 'no'


f1 = open('output/exp2/Reno_Reno_throughput.dat', 'w')
f2 = open('output/exp2/Reno_Reno_droprate.dat', 'w')
f3 = open('output/exp2/Reno_Reno_delay.dat', 'w')
f4 = open('output/exp2/NewReno_Reno_throughput.dat', 'w')
f5 = open('output/exp2/NewReno_Reno_droprate.dat', 'w')
f6 = open('output/exp2/NewReno_Reno_delay.dat', 'w')
f7 = open('output/exp2/Vegas_Vegas_throughput.dat', 'w')
f8 = open('output/exp2/Vegas_Vegas_droprate.dat', 'w')
f9 = open('output/exp2/Vegas_Vegas_delay.dat', 'w')
f10 = open('output/exp2/NewReno_Vegas_throughput.dat', 'w')
f11 = open('output/exp2/NewReno_Vegas_droprate.dat', 'w')
f12 = open('output/exp2/NewReno_Vegas_delay.dat', 'w')

for rate in RATE_Variant:
    for var in TCP_Variant:
        if var == 'NewReno_Reno':
            f4.write(str(rate) + '\t' + calculate_throughput(var, rate) + '\n')
            f5.write(str(rate) + '\t' + calculate_drop_rate(var, rate) + '\n')
            f6.write(str(rate) + '\t' + calculate_latency(var, rate) + '\n')
        if var == 'Vegas_Vegas':
            f7.write(str(rate) + '\t' + calculate_throughput(var, rate) + '\n')
            f8.write(str(rate) + '\t' + calculate_drop_rate(var, rate) + '\n')
            f9.write(str(rate) + '\t' + calculate_latency(var, rate) + '\n')
        if var == 'Reno_Reno':
            f1.write(str(rate) + '\t' + calculate_throughput(var, rate) + '\n')
            f2.write(str(rate) + '\t' + calculate_drop_rate(var, rate) + '\n')
            f3.write(str(rate) + '\t' + calculate_latency(var, rate) + '\n')
        if var == 'NewReno_Vegas':
            f10.write(str(rate) + '\t' + calculate_throughput(var, rate) + '\n')
            f11.write(str(rate) + '\t' + calculate_drop_rate(var, rate) + '\n')
            f12.write(str(rate) + '\t' + calculate_latency(var, rate) + '\n')

f1.close()
f2.close()
f3.close()
f4.close()
f5.close()
f6.close()
f7.close()
f8.close()
f9.close()
f10.close()
f11.close()
f12.close()
