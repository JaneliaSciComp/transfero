#! /usr/bin/python3

import os
import shlex

from transfero import *
from turn_off_transfero import *

def turn_on_transfero(hr=22, min=0) :
    '''
    Install the transfero job in crontab.
    Can give optional hr, min args, which specify the time to run, in 24-hour
    clock format.  I.e. turn_on_transfero(23,11) sets it to run once a day at 11:11
    PM.  Default time is 10:00 PM if no args are given.
    '''
    
    hr = round(hr) 
    if hr<0 or hr>23 :
        raise RuntimeError('hr must be an integer between 0 and 23, inclusive') 
    min = round(min) 
    if min<0 or min>59 :
        raise RuntimeError('min must be an integer between 0 and 59, inclusive')

    # Load the configuration, based on the user name
    this_script_path = os.path.realpath(__file__)
    transfero_folder_path = os.path.dirname(this_script_path)
    python_executable_path = os.path.join(transfero_folder_path, 'python/bin/python3')
    transfero_script_path = os.path.join(transfero_folder_path, 'transfero.py')
    user_name = os.getlogin()
    configuration_file_name = '%s_configuration.yaml' % user_name
    configuration_file_path = os.path.join(transfero_folder_path, configuration_file_name)
    with open(configuration_file_path, 'r') as stream:
        configuration = yaml.safe_load(stream)
    cluster_billing_account_name = configuration['cluster_billing_account_name']
    
    destination_folder_path = configuration['destination_folder']
    escaped_destination_folder_path = shlex.quote(destination_folder_path)    
    transfero_logs_folder_path = os.path.join(destination_folder_path, 'transfero-logs') 
    escaped_transfero_logs_folder_path = shlex.quote(transfero_logs_folder_path) 
    
    home_folder_path = os.getenv('HOME') 
    bash_profile_path = os.path.join(home_folder_path, '.bash_profile') 
    escaped_bash_profile_path = shlex.quote(bash_profile_path) 
    
    launcher_script_path = os.path.join(transfero_folder_path, 'transfero_launcher.sh') 
    escaped_launcher_script_path = shlex.quote(launcher_script_path) 
    
#     escaped_bash_profile_path=${1}
#     escaped_fly_disco_analysis_folder_path=${2}
#     pi_last_name=${3}
#     escaped_transfero_logs_folder_path=${4}
#     date_as_string=`date +%Y-%m-%d`
#     transfero_log_file_name="transfero-${date_as_string}.log"
#     transfero_log_file_path="${escaped_transfero_logs_folder_path}/${transfero_log_file_name}" 

    core_command_line = \
        '%s %s %s %s %s %s' % (escaped_launcher_script_path, 
                               escaped_bash_profile_path, 
                               python_executable_path,
                               transfero_script_path, 
                               cluster_billing_account_name, 
                               escaped_transfero_logs_folder_path) 

#     core_command_line = \
#         sprintf(['. /misc/lsf/conf/profile.lsf  ' \
#                  '. #s  ' \
#                  'cd #s  ' \
#                  'bsub -n1 -P #s -o #s -e #s /misc/local/matlab-2019a/bin/matlab -nodisplay -batch ''modpath transfero(true, true)'''], \
#                 escaped_bash_profile_path, \
#                 escaped_fly_disco_analysis_folder_path, \
#                 pi_last_name, \
#                 escaped_transfero_log_folder_path, \
#                 escaped_transfero_log_folder_path)  %#ok<NOPRT>
    escaped_core_command_line = shlex.quote(core_command_line) 
    
    hash_transfero = '#TRANSFERO' 
    escaped_hash_transfero = shlex.quote(hash_transfero) 
        
    command_line = '{ crontab -l | grep --invert-match %s; echo "%02d %02d * * *     flock --nonblock %s --command %s   #TRANSFERO"; } | crontab' % \
                        (escaped_hash_transfero, 
                         min, 
                         hr, 
                         escaped_destination_folder_path, 
                         escaped_core_command_line)
    
    # Clear out any pre-existing #transfero crontab lines
    turn_off_transfero()

    # Execute the command to turn on transfero
    run_subprocess_live(command_line, shell=True)



if __name__ == "__main__":
    turn_on_transfero()
