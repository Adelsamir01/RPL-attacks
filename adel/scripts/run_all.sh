#!/bin/bash

# Path to Cooja JAR file
COOJA_JAR="/home/adel/contiki-ng-attacks/tools/cooja/dist/cooja.jar"

# Path to Cooja simulation configuration file
SIM_CONFIG="sim.csc"

# Directory containing JavaScript files
JS_DIR="/home/adel/contiki-ng-attacks/examples/benchmarks/faya/adel/scripts/sim_scripts"

# Output directory for logs
LOG_DIR="/home/adel/contiki-ng-attacks/examples/benchmarks/faya/adel/logs"
mkdir -p "$LOG_DIR"

# Path to Contiki directory
CONTIKI_DIR="/home/adel/contiki-ng-attacks"

# Path to Python analysis script
PYTHON_ANALYSIS_SCRIPT="/home/adel/contiki-ng-attacks/examples/benchmarks/faya/adel/scripts/metrics_scripts/network_node_metrics_calculator.py"

# Loop through each JavaScript file in the directory
for JS_FILE in "$JS_DIR"/*.js; do
  # Extract the base name of the JavaScript file (without extension)
  JS_BASE=$(basename "$JS_FILE" .js)

  # Run the Cooja simulation with the current JavaScript file
  echo "Running simulation with $JS_FILE"
  LOG_FILE="$LOG_DIR/${JS_BASE}_log.txt"

  # Example of redirecting standard output and error to log file
  java -jar "$COOJA_JAR" -nogui="$SIM_CONFIG" -contiki="$CONTIKI_DIR" -script="$JS_FILE" &> "$LOG_FILE"

  echo "Simulation completed for $JS_FILE. Log saved to $LOG_FILE"

  # Run the Python analysis script on the generated log file
  echo "Analyzing log file $LOG_FILE"
  python3 "$PYTHON_ANALYSIS_SCRIPT" "$LOG_FILE"
  echo "Analysis completed for $LOG_FILE"
done

echo "All simulations and analyses completed."

