#! /bin/bash

escaped_bash_profile_path=${1}
transfero_script_path=${2}
cluster_billing_account_name=${3}
escaped_transfero_logs_folder_path=${4}

date_as_string=`date +%Y-%m-%d`
transfero_log_file_name="transfero-${date_as_string}.log"
transfero_log_file_path="${escaped_transfero_logs_folder_path}/${transfero_log_file_name}"

. /misc/lsf/conf/profile.lsf
. ${escaped_bash_profile_path}
#conda activate transfero
bsub -n1 -P ${cluster_billing_account_name} -o ${transfero_log_file_path} -e ${transfero_log_file_path} ${transfero_script_path}
