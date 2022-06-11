#! /bin/bash

escaped_bash_profile_path=${1}
python_executable_path=${2}
transfero_script_path=${3}
cluster_billing_account_name=${4}
escaped_transfero_logs_folder_path=${5}
date_as_string=`date +%Y-%m-%d`
transfero_log_file_name="transfero-${date_as_string}.log"
transfero_log_file_path="${escaped_transfero_logs_folder_path}/${transfero_log_file_name}"

. /misc/lsf/conf/profile.lsf
. ${escaped_bash_profile_path}
bsub -n1 -P ${cluster_billing_account_name} -o ${transfero_log_file_path} -e ${transfero_log_file_path} ${python_executable_path} ${transfero_script_path}
