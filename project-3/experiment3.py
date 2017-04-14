#!/usr/bin/python

import os

TCP_Variant = ['Reno', 'SACK']
QUEUE_Variant = ['DropTail', 'RED']

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



def get_throughput():
    granularity = 0.5
    filename="tracefiles/exp3/"+tvar + "_" + qvar + "_output.tr"
    thp1 = thp2 =0
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        clock = 0.0
        sum1 = sum2 = 0
        string=""
        for line in lines:
            record = Record(line)
            if record.flow_id == "0" and record.event == "r" and record.to_node == "5":
                # CBR
                sum1 += record.pkt_size * 8
            if record.flow_id == "1" and record.event == "r":
                # TCP
                sum2 += record.pkt_size * 8

            if record.time - clock <= granularity:
                pass
            else:
                thp1 = sum1 / granularity / (1024 * 1024)
                thp2 = sum2 / granularity / (1024 * 1024)

                string+= str(clock) + "\t" + str(thp1) + "\t" + str(thp2) + "\n"

                clock += granularity
                sum1 = sum2 = 0

        string += str(clock) + "\t" + str(thp1) + "\t" + str(thp2) + "\n"
        return string



def get_latency():
    granularity = 0.5
    filename = "tracefiles/exp3/" + tvar + "_" + qvar + "_output.tr"
    delay1 = delay2 = 0
    if os.path.isfile(filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        start_time1 = {}
        end_time1 = {}
        total_duration1 = total_duration2 = 0.0
        total_packet1 = total_packet2 = 0
        start_time2 = {}
        end_time2 = {}
        clock = 0.0
        string=""
        for line in lines:
            record = Record(line)
            if record.flow_id == "0":
                if record.event == "+" and record.from_node == "4":
                    start_time1.update({record.seq_num: record.time})
                if record.event == "r" and record.to_node == "5":
                    end_time1.update({record.seq_num: record.time})
            if record.flow_id == "1":
                if record.event == "+" and record.from_node == "0":
                    start_time2.update({record.seq_num: record.time})
                if record.event == "r" and record.to_node == "0":
                    end_time2.update({record.seq_num: record.time})

            if record.time - clock <= granularity:
                pass
            else:
                packets = {x for x in start_time1.viewkeys() if x in end_time1.viewkeys()}
                for i in packets:
                    duration = end_time1.get(i) - start_time1.get(i)
                    if duration > 0:
                        total_duration1 += duration
                        total_packet1 += 1

                packets = {x for x in start_time2.viewkeys() if x in end_time2.viewkeys()}
                for i in packets:
                    duration = end_time2.get(i) - start_time2.get(i)
                    if duration > 0:
                        total_duration2 += duration
                        total_packet2 += 1

                delay1 = 0 if total_packet1 == 0 else total_duration1 / total_packet1 * 1000
                delay2 = 0 if total_packet2 == 0 else total_duration2 / total_packet2 * 1000

                string += str(clock) + '\t' + str(delay1) + '\t' + str(delay2) + '\n'

                clock += granularity
                start_time1 = {}
                start_time2 = {}
                end_time1 = {}
                end_time2 = {}
                total_duration1 = total_duration2 = 0.0
                total_packet1 = total_packet2 = 0

        string += str(clock) + '\t' + str(delay1) + '\t' + str(delay2) + '\n'
        return string



# Calculate Throughput and Latency
for tvar in TCP_Variant:
    for qvar in QUEUE_Variant:
        output1 = open('output/exp3/' + tvar + '_' + qvar + '_throughput.dat', 'w')
        output1.write(get_throughput())
        output1.close()

        output2 = open('output/exp3/' + tvar + '_' + qvar + '_delay.dat', 'w')
        output2.write(get_latency())
        output2.close()

