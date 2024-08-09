# **RPL Attack Implementations for Contiki-NG and COOJA**

This project implements the RPL (Routing Protocol for Low-power and Lossy Networks) attacks discussed in the paper:

- **Reference:** "[A Reference Implementation for RPL Attacks Using Contiki-NG and COOJA](https://ieeexplore.ieee.org/document/9600057)"

## **Project Structure:**

- **`build` folder:** Contains compiled code or intermediate build artifacts.
- **`node.c` file:** Main source C code for the node.
- **`Makefile`:** Instructions for building the project.
- **`sim_script.js` file:** JavaScript script for running simulations.
- **`adel` folder:**
  - **Data Analysis Scripts:** Python scripts for aggregating and analyzing control messages for each node.
  - **`PCAP` folder:** PCAP files captured for each attack scenario (including a baseline without attacks) and node 7.
  - **`sim` folder:** COOJA simulation files for easy replication of the work.
  - **`logs` folder:** contains output logfiles from Contiki-NG simulations and there corresponding analysis.

  
## **Running the Simulations:**

1. **Enable an Attack:**
   - Uncomment the corresponding `#define` line in `project-conf.h`.
   - Add the attack name to the JavaScript array.

2. **Adjust Logging Path:**
   - Edit the logging path in the code and remove any trailing slashes (`/`).

3. **Run COOJA in Non-GUI Mode:**
   ```bash
   java -jar /path/to/contiki-ng-attacks/tools/cooja/dist/cooja.jar -nogui=sim.csc
   ```
   (Replace `/path/to/contiki-ng-attacks` with the actual path).

4. **Environment Setup:**
   - **Java 8 (amd64):** Ensure you have Java 8 with amd64 architecture installed.
   - **Makefile CFLAGS:** Add the following lines to `Makefile.include`:
     ```makefile
     CFLAGS += -I/usr/lib/jvm/java-8-openjdk-amd64/include -I/usr/lib/jvm/java-8-openjdk-amd64/include/linux
     ```

## **Implemented Attacks:**

This section provides summaries and implementation details for each attack, enhancing understanding:

- **Selective Forwarding Attack (SFA):**
  - **Description:** Disrupts communication by selectively dropping packets (except control packets) at a compromised node.
  - **Implementation:** Modifies `uip6.c` to drop non-ICMPv6 packets when the attack is active.
  
- **Sinkhole Attack (SHA):**
  - **Description:** A malicious node attracts traffic by advertising a seemingly ideal path, enabling eavesdropping or disruption.
  - **Implementation:** Modifies `rpl-icmp6.c` to set the rank in DIO messages to the root rank, making the node appear as the best choice.
  
- **Version Number Attack (VNA):**
  - **Description:** Causes excessive control message overhead and instability by forcing routing table resets through frequent version number increments in DIO messages.
  - **Implementation:** Modifies `rpl-icmp6.c` to increment the DODAG version number.
  
- **DIS Flooding Attack (DFA):**
  - **Description:** Depletes network resources by sending frequent DIS messages, causing neighbors to reset DIO trickle timers and flood the network with DIOs.
  - **Implementation:** Modifies `rpl-timers.c` and `rpl-dag.c` to reduce the DIS transmission period and ensure its continuation even after joining the DODAG.
  
- **Sybil Attack (SYA):**
  - **Description:** Misleads or overwhelms routing tables with bogus routes by assuming multiple fake identities.
  - **Implementation:** Modifies `uip-icmp6.c` to change the link-layer and link-local addresses using `linkaddr_set_node_addr` and `uip_ds6_set_addr_iid` functions.

## **Additional Notes:**

Feel free to reach out if you have any questions or encounter issues replicating this work. Consider contributing to the project by extending it with further attacks or functionalities.
