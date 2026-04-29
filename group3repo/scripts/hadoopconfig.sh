#!/bin/bash
#SBATCH --job-name=CSDS438_Pipeline
#SBATCH --exclusive
#SBATCH --time=03:00:00
#SBATCH --output=pipeline_%j.log

pkill -u $USER -f java
sleep 3

NODES=($(scontrol show hostnames $SLURM_JOB_NODELIST))
MASTER_NODE=${NODES[0]}
NODE_COUNT=${#NODES[@]}

PROJECT_DIR="${HOME}/csds438/project438"
USER_SCRATCH="/tmp/hadoop-${USER}-${SLURM_JOB_ID}"
CONF_DIR="${HOME}/hadoop_conf_${SLURM_JOB_ID}"

mkdir -p $CONF_DIR $USER_SCRATCH ${PROJECT_DIR}/logs

module purge
module load Python/3.10.8-GCCcore-12.2.0 Java

REAL_JAVA=$(readlink -f $(which java))
ACTUAL_JAVA_HOME=$(dirname $(dirname $REAL_JAVA))

export HADOOP_HOME="${PROJECT_DIR}/hadoop-3.3.6"
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH
export HADOOP_CONF_DIR=$CONF_DIR

cp -r $HADOOP_HOME/etc/hadoop/* $CONF_DIR/

echo "export JAVA_HOME=$ACTUAL_JAVA_HOME" >> $CONF_DIR/hadoop-env.sh
echo "export HADOOP_CONF_DIR=$CONF_DIR" >> $CONF_DIR/hadoop-env.sh
echo "export HADOOP_HOME=$HADOOP_HOME" >> $CONF_DIR/hadoop-env.sh
echo "export HADOOP_LOG_DIR=${PROJECT_DIR}/logs" >> $CONF_DIR/hadoop-env.sh
echo "export YARN_LOG_DIR=${PROJECT_DIR}/logs" >> $CONF_DIR/hadoop-env.sh

echo "export JAVA_HOME=$ACTUAL_JAVA_HOME" >> $CONF_DIR/yarn-env.sh
echo "export HADOOP_CONF_DIR=$CONF_DIR" >> $CONF_DIR/yarn-env.sh
echo "export HADOOP_HOME=$HADOOP_HOME" >> $CONF_DIR/yarn-env.sh
echo "export YARN_LOG_DIR=${PROJECT_DIR}/logs" >> $CONF_DIR/yarn-env.sh

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
    <property><name>yarn.nodemanager.env-whitelist</name><value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_MAPRED_HOME</value></property>
</configuration>
EOF

cat <<EOF > $CONF_DIR/mapred-site.xml
<configuration>
    <property><name>mapreduce.framework.name</name><value>yarn</value></property>
    <property><name>yarn.app.mapreduce.am.env</name><value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value></property>
    <property><name>mapreduce.map.env</name><value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value></property>
    <property><name>mapreduce.reduce.env</name><value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value></property>
</configuration>
EOF

> $CONF_DIR/workers
for node in "${NODES[@]}"; do echo $node >> $CONF_DIR/workers; done

hdfs namenode -format -force -nonInteractive
start-dfs.sh
start-yarn.sh

sleep 30

cd $PROJECT_DIR
python3 organize_hdfs.py

START_TIME=$(date +%s)

STREAM_JAR="${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar"

hadoop jar $STREAM_JAR \
    -file mapper_n_grams.py   -mapper "python3 mapper_n_grams.py" \
    -file reducer.py          -reducer "python3 reducer.py" \
    -input /project/corpus/*/* \
    -output /project/output/ngrams/run_${SLURM_JOB_ID}

hadoop jar $STREAM_JAR \
    -file tfidf_mapper.py          -mapper "python3 tfidf_mapper.py" \
    -file tfidf_reducer.py         -reducer "python3 tfidf_reducer.py" \
    -input /project/corpus/*/* \
    -output /project/output/tfidf/run_${SLURM_JOB_ID}

END_TIME=$(date +%s)

hdfs dfs -get /project/output/ngrams/run_${SLURM_JOB_ID} ${PROJECT_DIR}/ngrams_${SLURM_JOB_ID}
hdfs dfs -get /project/output/tfidf/run_${SLURM_JOB_ID} ${PROJECT_DIR}/tfidf_${SLURM_JOB_ID}

stop-yarn.sh
stop-dfs.sh

srun rm -rf $USER_SCRATCH
rm -rf $CONF_DIR

echo "${NODE_COUNT},$((END_TIME - START_TIME))" >> ${PROJECT_DIR}/scaling_results.csv