Methodology for running experiments:


Given:
                         N1                      N4
                           \                    /
                            \                  /
                             N2--------------N3
                            /                  \
                           /                    \
                         N5                      N6

Bandwidth of each link: 10Mbps


Factors we considered:

Average Throughput
packet drop rate
Latency
properties associated with each TCP variant



Experiment 1:


Sarvesh created the TCL script using the above topology. He put one CBR source at N2 with sink at N3, and  then tested the results
for each TCP stream variant(Tahoe, Reno, NewReno, and Vegas)from N1 to a sink at N4.

  a. Incremented the CBR(from 1 to 10 Mbps) to plot the results
  
  b. Varied the  the packet size to determine the best settings for plotting results

After trace file results were generated, I(Manu) created the parsing script for experiment-1 in Python to compute the output -
i.e. throughput,packet drop rate, and latency (three of them on Y axis )as a function of CBR bandwidth(on X axis)



Me(Manu) and Sarvesh then plotted the output results in Excel sheets for each TCP Variant
   	


Experiment 2:


Sarvesh created the TCL script  by using  one CBR, and two TCP.He then added CBR source at N2 and a sink at N3,
then he added two TCP streams(from the below pairs) from N1 to N4 and N5 to N6, respectively.

* Reno/Reno
* NewReno/Reno
* Vegas/Vegas
* NewReno/Vegas

   a.Incremented the CBR(from 1 to 10 Mbps) to plot the results
   b.Varied the  the packet size to determine the best settings for plotting results


After trace file results were generated, I(Manu) created the parsing script for experiment-2 in Python to compute the output -
i.e. throughput, packet loss rate, and latency(three of them on Y axis) vs CBR bandwidth(on X axis) and
also analyzed how the protocols are implemented and why the different choices in different TCP variants can impact fairness

Me(Manu) and Sarvesh then plotted the output results in Excel sheets for each TCP Variant pairs.


Experiment 3: 18 graphs (6 graphs if we have both TCP variants and CBR source in one graph)

Sarvesh created the TCL script by adding one TCP flow (N1-N4) and one CBR/UDP (N5-N6) flow to the same topology as in
experiment-1 and then tested the influence of each queuing discipline(DropTail and Random Early Drop-RED) for each TCP
stream variant(TCP Reno and SACK) and CBR flow.

   a.Changed the size of the queue for best settings to plot the result

   b.Started CBR before the TCP stream or vice versa, to validate change in the results


After trace file results were generated, I(Manu) created the parsing script for experiment-3 in Python to compute the output -
throughput, and latency(both on y axis), vs time(on X axis).


Me(Manu) and Sarvesh then plotted the output results in Excel sheets for each queing algorithm.


Me(Manu) and Sarvesh created the report by using the above results and performing T-tests on the data sets for throughput to
come to a conclusion.

