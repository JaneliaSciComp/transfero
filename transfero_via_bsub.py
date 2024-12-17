#!/usr/bin/python3

import os
import shlex
import datetime
import subprocess
import argparse

from tpt.utilities import *
from transfero import *
from turn_off_transfero import *

def transfero_via_bsub(do_log=None, do_transfer=None, do_analyze=None, is_via_cron=False, analysis_executable_name=None, manual_configuration_file_name=None) :
    '''
    Launch Transfero via bsub.
    '''

    # Get the path to the transfero.py script, and the Transfero folder
    this_script_path = os.path.realpath(__file__)
    transfero_folder_path = os.path.dirname(this_script_path)
    transfero_script_path = os.path.join(transfero_folder_path, 'transfero.py')

    # Load the configuration
    if manual_configuration_file_name is None:
        user_name = get_user_name()
        configuration_file_name = '%s_configuration.yaml' % user_name  
            # Don't want to overwrite configuration_file_name passed in by caller
        configuration_file_path = os.path.join(transfero_folder_path, configuration_file_name)
    else:
        configuration_file_name = manual_configuration_file_name
        configuration_file_path = os.path.realpath(configuration_file_name)
    configuration = read_yaml_file_badly(configuration_file_path)

    # Get things we need out of configuration
    cluster_billing_account_name = configuration['cluster_billing_account_name']    
    destination_folder_path = configuration['destination_folder']

    # If not specified, log
    if do_log is None:
        do_log = True

    # Figure out the path to the Transfero log file
    if do_log:
        # Ensure that the Transfero log folder exists
        transfero_logs_folder_path = os.path.join(destination_folder_path, 'transfero-logs') 
        os.makedirs(transfero_logs_folder_path, exist_ok=True)

        # Synthesize Transfero log file name
        today = datetime.datetime.today()
        if is_via_cron:
            # If running via cron, which should only happen once a day, just use the date to name the log file
            simple_date_as_string = today.strftime("%Y-%m-%d")
            transfero_log_file_name = "transfero-%s.log" % simple_date_as_string
            transfero_log_file_path = os.path.join(transfero_logs_folder_path, transfero_log_file_name)
        else:
            # If not running via cron, use the date and time to name the log file
            date_and_time_as_string = today.strftime("%Y-%m-%d-%H-%M-%S")
            transfero_log_file_name = "transfero-%s.log" % date_and_time_as_string
            transfero_log_file_path = os.path.join(transfero_logs_folder_path, transfero_log_file_name)
    else:
        transfero_log_file_path = '/dev/null'

    # Synthesize the Transfero arguments
    transfero_command_line_args = ([] if (do_transfer is None) else (["--transfer"] if do_transfer else ["--no-transfer"])) + \
                                  ([] if (do_analyze  is None) else (["--analyze" ] if do_analyze  else ["--no-analyze" ])) + \
                                  ([] if (analysis_executable_name is None) else ["--analysis-executable", analysis_executable_name]) + \
                                  ([] if (manual_configuration_file_name is None) else ["--configuration-file", manual_configuration_file_name])

    # Synthesize the bsub command line and run it.
    # We assume that /misc/lsf/conf/profile.lsf has been sourced in the parent process, so that bsub etc are on the path, and
    # the LSF_* envars have been set.
    # Synthesize the bsub command line as a list, and skip escaping
    bsub_command_line_as_list = \
        [ 'bsub', '-n', '1', '-P', cluster_billing_account_name, '-o', transfero_log_file_path, '-e', transfero_log_file_path, transfero_script_path] + transfero_command_line_args
    # Execute the command to launch transfero
    subprocess.run(bsub_command_line_as_list)
# end def



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool for launching Transfero on the cluster")
    parser.add_argument('--isviacron', dest='isviacron', action='store_true', help='Signal that we are running via cron.  Currently only affects log file naming.')
    parser.add_argument('--log', dest='log', action='store_true', help='Enable *Transfero* logging (different than per-experiment log)')
    parser.add_argument('--no-log', dest='nolog', action='store_true', help='Disable *Transfero* logging (different than per-experiment log)')
    parser.add_argument('--transfer', dest='transfer', action='store_true', help='Enable transfer of data from rigs, overriding setting in configuration file')
    parser.add_argument('--no-transfer', dest='notransfer', action='store_true', help='Disable transfer of data from rigs, overriding setting in configuration file')
    parser.add_argument('--analyze', dest='analyze', action='store_true', help='Enable analysis of data, overriding setting in configuration file')
    parser.add_argument('--no-analyze', dest='noanalyze', action='store_true', help='Disable analysis of data, overriding setting in configuration file')
    parser.add_argument('--analysis-executable', dest='analysisexecutable', help='Specify analysis executable, overriding determination from configuration file')
    parser.add_argument('--configuration-file', dest='configurationfile', help='Specify configuration file, overriding determination from user name')
    args = parser.parse_args()

    do_log = process_tristate_arg_pair(args.log, args.nolog, 'log')
    do_transfer = process_tristate_arg_pair(args.transfer, args.notransfer, 'transfer')
    do_analyze = process_tristate_arg_pair(args.analyze, args.noanalyze, 'analyze')

    transfero_via_bsub(do_log=do_log, 
                       do_transfer=do_transfer, 
                       do_analyze=do_analyze, 
                       is_via_cron=args.isviacron, 
                       analysis_executable_name=args.analysisexecutable, 
                       manual_configuration_file_name=args.configurationfile)
