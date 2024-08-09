// Set a timeout to log the total PRR every 900,000 ms (15 minutes)
TIMEOUT(900000, log.log("Total PRR " + totalPRR + "\n"));

// Initialize arrays and variables
packetsReceived = new Array();
packetsSent = new Array();
serverID = 1;
nodeCount = 16;
totalPRR = 0;
t_total = 0;
throughput = 0;
PDR = 0;
data_length = 100;
Average_delay = 0;
timeReceived = new Array();
timeSent = new Array();
delay = new Array();

// Initialize arrays to zero for each node
for (i = 0; i < (nodeCount - 1); i++) {
    packetsReceived[i] = 0;
    packetsSent[i] = 0;
    timeReceived[i] = 0.0;
    timeSent[i] = 0.0;
    delay[i] = 0.0;
}

// Main loop to handle messages
while (1) {
    YIELD();

    var position = msg.indexOf(']');
    var result = msg.slice(position + 1).trim();
    var msgArray = result.split(' ');

    

    if (msgArray[1].equals("received") && msgArray.length == 6) {
        
        // Received packet
        var senderPart = msgArray[3]
        //var receiverPart = msgArray[5];
        var senderID = parseInt(senderPart.slice(-3));
        //var receiverID = parseInt(receiverPart.slice(-3));
            
         //log.log("ReceiverID: " + receiverID+"\n"); // Output: ReceiverID: 9
        //senderID = mote.getID();
        //log.log("Message from: "+ senderID + " is " + msg + "\n");
        packetsReceived[senderID]++;
        timeReceived[senderID] = time;
        //log.log("SenderID: " + senderID+"\n"); // Output: SenderID: 1

        /*log.log(
            "\nSenderID: " + senderID +
            ", PRR: " + (packetsReceived[senderID] / packetsSent[senderID]) +
            ", timeReceived[senderID]: " + timeReceived[senderID]/ 10000000 +
            ", timeSent[senderID]: " + timeSent[senderID]/ 10000000 + "\n"
        );*/

        totalReceived = totalSent = 0;
        totaldelay = 0;
        count1 = 0;

        for (i = 0; i < (nodeCount - 1); i++) {
            totalReceived += packetsReceived[i];
            totalSent += packetsSent[i];

            if (timeReceived[i] > 0) {
                delay[i] = timeReceived[i] - timeSent[i];
                delay[i] = delay[i] / 10000000;

                if (delay[i] > 0) {
                    totaldelay = totaldelay + delay[i];
                    count1++;
                }
            }
        }

        totalPRR = totalReceived / totalSent;
        total_simulation_time = time;

        //log.log("\nTotal simulation time: " + total_simulation_time / 10000000 + "(Sec) \n");

        throughput = (totalReceived * data_length * 8 * 1000) / total_simulation_time;

        /* log.log(
            "\nTotal Received: " + totalReceived +
            ", Total Sent: " + totalSent + "\n"
        ); */

        PDR = (totalReceived / totalSent) * 100;
        t_total = totalPRR * 100;

        log.log(
            "\nTotal Packet Reception Rate: " + totalPRR +
            ", Total Delay: " + totaldelay +
            ", Packet Delivery Ratio: " + PDR + "\n"
        );

        //log.log("\nThroughput: " + throughput + "\n");

    } else if (msgArray[0].equals("Sending") && msgArray.length == 6) {
        
        // Sent packet
        receiverID = mote.getID();
        //log.log("Message from: "+ receiverID + " is " + msg + "\n");
        packetsSent[receiverID]++;
        timeSent[receiverID] = time;

        /*log.log(
            "\nPackets Sent[receiverID]: " + packetsSent[receiverID] +
            ", Time Sent[receiverID]: " + timeSent[receiverID]/ 10000000 +
            ", Receiver ID: " + receiverID + "\n"
        );*/
    }
}

