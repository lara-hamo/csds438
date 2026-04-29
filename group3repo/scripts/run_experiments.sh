#!/bin/bash

PROJECT_DIR="${HOME}/csds438/project438"

echo "Nodes,Execution_Time_Seconds" > ${PROJECT_DIR}/scaling_results.csv

for NODE_COUNT in 1 2 4 8; do
    sbatch --nodes=$NODE_COUNT hadoopconfig.sh
    sleep 2
done