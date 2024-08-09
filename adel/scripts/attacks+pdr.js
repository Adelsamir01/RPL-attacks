//sim.setSpeedLimit(1.0); // set simulation speed to real time (1x)
TIMEOUT(600000, log.log("Total PRR " + totalPRR + "\n")); // 10 mintue simulation
path = "/home/adel/contiki-ng-attacks/examples/benchmarks/faya/no-attack_log.txt";// path to log file
log.writeFile(path, "");

timeout_function = function my_fun() {
  log.log("Script timed out.\n");
  log.testOK();
}
my_log_func = function(path,time,idx,msgx){
  log.append(path, (time / 1000000) + "\tID:" + idx + "	" + msgx + "\n");
}
// class Attack
function Attack(name,target,startTime,endTime){
    this.name = name; // name of variable used in contiki-ng core to turn on/off attack
    this.target = sim.getMoteWithID(target); // target mote in which attack variable is changed
    this.startTime = startTime*1000; // attack start time in usec  
    this.endTime = endTime*1000; // attack stop time in usec
    this.ON = false; // state of the attack ON
    this.OFF = false; // state of the attack OFF
    this.valuesList = new Array();
    this.timesList = new Array();
    this.vName = "";
    // function to access mote's memory and update its ithbyte with byteValue
    this.memAccess = function (varName,ithByte,byteValue) {
        mem = this.target.getMemory();
        exists = mem.getSymbolMap().containsKey(varName);
        if (exists) {
            sym = mem.getSymbolMap().get(varName);
            mem_seg = mem.getMemorySegment(sym.addr, sym.size);
            mem_seg[ithByte] = byteValue;
            mem.setMemorySegment(sym.addr, mem_seg);
            return true;
        }
        return false;
    }
    this.timeVarUpdate = function (time) {
        if (this.ON && time > this.startTime && time <  this.endTime) {
            for(i=0;i<this.valuesList.length;i++){
                if(1000*this.timesList[i] > time)
                    break;
                else
                   this.memAccess(this.vName,0,this.valuesList[i]); 
            }
        }
    } 
    // function to activate/deactivate an attack
    this.flipSwitch = function (time) {
        if (!this.ON && time > this.startTime) {
            this.ON = this.memAccess(this.name,0,0xff);
            if(this.ON)
                log.log("[WARN: "+this.name+" ] attack has stopped")
                my_log_func(path,time,this.target.getID(),"[WARN: "+this.name+" ] attack has started");
        }
        this.timeVarUpdate(time);
        if (!this.OFF && time > this.endTime) {
            this.OFF = this.memAccess(this.name,0,0x00);
            if(this.OFF)
                log.log("[WARN: "+this.name+" ] attack has stopped")
                my_log_func(path,time,this.target.getID(),"[WARN: "+this.name+" ] attack has stopped");
        }
    }
}

attacks = new Array();
// SFA 
// attacks.push(new Attack("SFA_on", 7, 0, 600000));
// attacks.push(new Attack("SFA_on", 8, 300000, 600000));

// SHA 
attacks.push(new Attack("SHA_on", 7, 300000, 1200000));
// attacks.push(new Attack("SHA_on", 8, 0, 600000));

// VNA
// attacks.push(new Attack("VNA_on", 8, 300000, 600000));

// DFA
// attacks.push(new Attack("DFA_on", 16, 300000, 600000));

// SYA
// sya = new Attack("SYA_on", 7, 200000, 600000);
// sya.vName="fake_id";
// sya.valuesList.push(0x09); sya.timesList.push(200000);
// sya.valuesList.push(0x26); sya.timesList.push(400000);
// attacks.push(sya);

// randx = new java.util.Random(sim.getRandomSeed())
// rand_node = randx.nextInt(16);
// while(rand_node < 2 || rand_node == 7)
//       rand_node = randx.nextInt(16);

// my_log_func(path,time,-1,"rand = "+rand_node);
// attacks.push(new Attack("sfa_on", rand_node, 300000, 500000));

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
while (true) { 
	//for(j=0;j<attacks.length;j++)
	//attacks[j].flipSwitch(time);
    YIELD();

    var position = msg.indexOf(']');
    var result = msg.slice(position + 1).trim();
    var msgArray = result.split(' ');

    my_log_func(path, time, id, msg);

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

         log.log(
            "\nTotal Received: " + totalSent +
            ", Total Sent: " + totalReceived + "\n"
        ); 

        PDR = (totalSent / totalReceived ) * 100;
        t_total = totalPRR * 100;

        log.log(
            "\n Total Delay: " + totaldelay +
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
