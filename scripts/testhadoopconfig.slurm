#!/bin/bash
#SBATCH --job-name=TextMining_Pipeline
#SBATCH --nodes=4
#SBATCH --exclusive
#SBATCH --time=01:00:00
#SBATCH --output=pipeline_%j.log

echo "=== 1. Setup Environment ==="
NODES=($(scontrol show hostnames $SLURM_JOB_NODELIST))
MASTER_NODE=${NODES[0]}

USER_SCRATCH="/tmp/hadoop-${USER}-${SLURM_JOB_ID}"
CONF_DIR="${HOME}/hadoop_conf_${SLURM_JOB_ID}"
IMAGE="${HOME}/singularity_env.sif"

mkdir -p $CONF_DIR $USER_SCRATCH

echo "=== 2. Generate Configuration ==="
cat <<EOF > $CONF_DIR/core-site.xml
<configuration>
    <property><name>fs.defaultFS</name><value>hdfs://${MASTER_NODE}:9000</value></property>
    <property><name>hadoop.tmp.dir</name><value>${USER_SCRATCH}</value></property>
</configuration>
EOF

cat <<EOF > $CONF_DIR/hdfs-site.xml
<configuration>
    <property><name>dfs.replication</name><value>1</value></property>
    <property><name>dfs.permissions.enabled</name><value>false</value></property>
</configuration>
EOF

cat <<EOF > $CONF_DIR/yarn-site.xml
<configuration>
    <property><name>yarn.resourcemanager.hostname</name><value>${MASTER_NODE}</value></property>
    <property><name>yarn.nodemanager.aux-services</name><value>mapreduce_shuffle</value></property>
</configuration>
EOF

cat <<EOF > $CONF_DIR/mapred-site.xml
<configuration>
    <property><name>mapreduce.framework.name</name><value>yarn</value></property>
</configuration>
EOF

for node in "${NODES[@]}"; do echo $node >> $CONF_DIR/workers; done

echo "=== 3. Start Cluster ==="
BIND="--bind ${CONF_DIR}:/opt/hadoop/etc/hadoop --bind ${USER_SCRATCH}:${USER_SCRATCH} --bind ${HOME}/.ssh:/home/user/.ssh"

singularity exec $BIND $IMAGE hdfs namenode -format -force -nonInteractive
singularity exec $BIND $IMAGE start-dfs.sh
singularity exec $BIND $IMAGE start-yarn.sh

sleep 10 

echo "=== 4. Run Pipeline ==="
START_TIME=$(date +%s)

singularity exec $BIND $IMAGE hdfs dfs -mkdir -p /input
singularity exec $BIND $IMAGE hdfs dfs -put /path/to/public/novels/* /input/
singularity exec $BIND $IMAGE hadoop jar /path/to/TextMining.jar com.pipeline.Main /input /output
singularity exec $BIND $IMAGE hdfs dfs -get /output /path/to/permanent/results/output_${SLURM_JOB_ID}

END_TIME=$(date +%s)
echo "Pipeline Execution Time: $((END_TIME - START_TIME)) seconds"

echo "=== 5. Teardown ==="
singularity exec $BIND $IMAGE stop-yarn.sh
singularity exec $BIND $IMAGE stop-dfs.sh

srun rm -rf $USER_SCRATCH
rm -rf $CONF_DIR

echo "Job Complete."
