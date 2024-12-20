#!/usr/bin/python3

import os
import shlex

from tpt.utilities import *
from transfero import *
from turn_off_transfero import *

def turn_on_transfero(hr_argument=None, min_argument=None) :
    '''
    Install the transfero job in crontab.
    Can give optional hr_argument, min_argument args, which specify the time to run, in 24-hour
    clock format.  I.e. turn_on_transfero(23,11) sets it to run once a day at 11:11
    PM.  Default time is given in configuration file if no args are given.
    '''
    
    if not (hr_argument is None) :
        hr_argument = round(hr_argument) 
        if hr_argument<0 or hr_argument>23 :
            raise RuntimeError('hr_argument must be an integer between 0 and 23, inclusive') 
    if not (min_argument is None) :
        min_argument = round(min_argument) 
        if min_argument<0 or min_argument>59 :
            raise RuntimeError('min_argument must be an integer between 0 and 59, inclusive')

    # Load the configuration, based on the user name
    this_script_path = os.path.realpath(__file__)
    transfero_folder_path = os.path.dirname(this_script_path)
    user_name = get_user_name()
    configuration_file_name = '%s_configuration.yaml' % user_name
    configuration_file_path = os.path.join(transfero_folder_path, configuration_file_name)
    configuration = read_yaml_file_badly(configuration_file_path)
    
    # Get the path to the executable we want crontab to run
    launcher_script_path = os.path.join(transfero_folder_path, 'transfero_via_bsub_via_cron.bash') 
    escaped_launcher_script_path = shlex.quote(launcher_script_path) 
    
    if hr_argument is None :
        hr = configuration['launch_hour']
    else :
        hr = hr_argument
    if min_argument is None :
        min = configuration['launch_minute']
    else :
        min = min_argument    

    core_command_line = escaped_launcher_script_path

    hash_transfero = '#TRANSFERO' 
    escaped_hash_transfero = shlex.quote(hash_transfero) 
        
    command_line = '{ crontab -l | grep --invert-match %s; echo "%02d %02d * * *     %s   #TRANSFERO"; } | crontab' % \
                        (escaped_hash_transfero, 
                         min, 
                         hr, 
                         core_command_line)
    
    # Clear out any pre-existing #transfero crontab lines
    turn_off_transfero()

    # Execute the command to turn on transfero
    run_subprocess_live(command_line, shell=True)



if __name__ == "__main__":
    if len(sys.argv)>=2 :
        hr = int(sys.argv[1]) 
    else:
        hr = None
    if len(sys.argv)>=3 :
        min = int(sys.argv[2]) 
    else:
        min = None
    turn_on_transfero(hr, min)
