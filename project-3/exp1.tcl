#Command line input -> Reno 1  

#Create a simulator object
set ns [new Simulator]
 
# TCP variant
set variant [lindex $argv 0]
# CBR rate
set rate [lindex $argv 1]

# Open the trace file
set tf [open ${variant}_output-${rate}.tr w]
$ns trace-all $tf
 
#Define a 'finish' procedure
proc finish {} {
        global ns nf
        $ns flush-trace
        exit 0
}
 
#Create four nodes
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node] 
 
#Create links between the nodes
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n5 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n4 $n3 10Mb 10ms DropTail
$ns duplex-link $n6 $n3 10Mb 10ms DropTail

# set link queue size
$ns queue-limit $n2 $n3 10

#Setup a TCP conncection
if {$variant eq "Tahoe"} {
	set tcp [new Agent/TCP]
} elseif {$variant eq "Reno"} {
	set tcp [new Agent/TCP/Reno]
} elseif {$variant eq "NewReno"} {
	set tcp [new Agent/TCP/Newreno]
} elseif {$variant eq "Vegas"} {
	set tcp [new Agent/TCP/Vegas]
}

$tcp set class_ 1
$ns attach-agent $n1 $tcp
set sink [new Agent/TCPSink]
$ns attach-agent $n4 $sink
$ns connect $tcp $sink

#setup a FTP Application
set ftp [new Application/FTP]
$ftp attach-agent $tcp
 
#Setup a UDP connection
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
set null [new Agent/Null]
$ns attach-agent $n3 $null
$ns connect $udp $null
 
#Setup a CBR over UDP connection
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set rate_ ${rate}mb
$cbr set packet_size_ 1500 

#Schedule events for the CBR and FTP agents
$ns at 0.0 "$cbr start"
$ns at 1.0 "$ftp start"
$ns at 9.0 "$ftp stop"
$ns at 10.0 "$cbr stop"
 
#Call the finish procedure after 5 seconds of simulation time
$ns at 10.0 "finish"
 
#Run the simulation
$ns run
