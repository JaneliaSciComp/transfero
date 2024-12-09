#!/usr/bin/python3

import os
import shlex
import datetime
import subprocess
import argparse

from tpt.utilities import *
from transfero import *
from turn_off_transfero import *

def transfero_via_bsub(do_log=None, do_transfer=None, do_analyze=None) :
    '''
    Launch Transfero via bsub, with Transfero logging enabled.
    '''

    # Load the configuration, based on the user name
    this_script_path = os.path.realpath(__file__)
    transfero_folder_path = os.path.dirname(this_script_path)
    transfero_script_path = os.path.join(transfero_folder_path, 'transfero.py')
    user_name = get_user_name()
    configuration_file_name = '%s_configuration.yaml' % user_name
    configuration_file_path = os.path.join(transfero_folder_path, configuration_file_name)
    configuration = read_yaml_file_badly(configuration_file_path)

    # Get things we need out of configuration
    cluster_billing_account_name = configuration['cluster_billing_account_name']    
    destination_folder_path = configuration['destination_folder']
    if do_transfer is None:
        do_transfer = configuration['do_transfer_data_from_rigs']
    if do_analyze is None:
        do_analyze = configuration['do_run_analysis']

    # If not specified, log
    if do_log is None:
        do_log = True

    # Figure out the path to the Transfero log file
    print("do_log: %s" % str(do_log))
    if do_log:
        # Ensure that the Transfero log folder exists
        transfero_logs_folder_path = os.path.join(destination_folder_path, 'transfero-logs') 
        os.makedirs(transfero_logs_folder_path, exist_ok=True)

        # Synthesize Transfero log file name
        today = datetime.datetime.today()
        simple_date_as_string = today.strftime("%Y-%m-%d")
        simple_transfero_log_file_name = "transfero-%s.log" % simple_date_as_string
        simple_transfero_log_file_path = os.path.join(transfero_logs_folder_path, simple_transfero_log_file_name)

        # If a log file for today already exists, add the time on to the log file name        
        if os.path.exists(simple_transfero_log_file_path):
            date_and_time_as_string = today.strftime("%Y-%m-%d-%H-%M-%S")
            transfero_log_file_name = "transfero-%s.log" % date_and_time_as_string
            transfero_log_file_path = os.path.join(transfero_logs_folder_path, transfero_log_file_name)
        else:
            transfero_log_file_path = simple_transfero_log_file_path            
    else:
        transfero_log_file_path = '/dev/null'

    # Synthesize the Transfero arguments
    transfero_command_line_args = [ ("true" if do_transfer else "false") , ("true" if do_analyze else "false") ]

    # Synthesize the bsub command line and run it.
    # Check to see if one of the LSF envars is set.  If not, we assume we're running in a cron environment (or a similarly impoverished environment), 
    # and need to source a few files before running bsub.
    if 'LSF_BINDIR' in os.environ:
        # Synthesize the bsub command line as a list, and skip escaping
        bsub_command_line_as_list = \
            [ 'bsub', '-n', '1', '-P', cluster_billing_account_name, '-o', transfero_log_file_path, '-e', transfero_log_file_path, transfero_script_path] + transfero_command_line_args
        # Execute the command to launch transfero
        subprocess.run(bsub_command_line_as_list)
    else:
        # Impoverished (e.g. cron) environment

        # Get the path to the LSF profile 
        lsf_profile_path = '/misc/lsf/conf/profile.lsf'
        escaped_lsf_profile_path = shlex.quote(lsf_profile_path)

        # Get the path to the user's bash profile
        home_folder_path = os.getenv('HOME') 
        bash_profile_path = os.path.join(home_folder_path, '.bash_profile') 
        escaped_bash_profile_path = shlex.quote(bash_profile_path) 

        # Synthesize the bsub command line as a list, with escaping
        escaped_transfero_log_file_path = shlex.quote(transfero_log_file_path)
        escaped_transfero_script_path = shlex.quote(transfero_script_path)
        escaped_transfero_args = [ shlex.quote(arg) for arg in transfero_command_line_args ]
        bsub_command_line_as_list = \
            [ 'bsub', '-n', '1', '-P', cluster_billing_account_name, '-o', escaped_transfero_log_file_path, '-e', escaped_transfero_log_file_path, escaped_transfero_script_path ] + escaped_transfero_args
        bsub_command_line_as_string = space_out(bsub_command_line_as_list)
        command_line_as_string = "source %s && source %s && %s" % (escaped_lsf_profile_path, escaped_bash_profile_path, bsub_command_line_as_string)

        # Execute the command to launch transfero, running in a shell
        subprocess.run(command_line_as_string, shell=True)
# end def



def process_tristate_arg_pair(do, nodo, name):
    if do :
        if nodo :
            raise RuntimeError('Arguments --%s and --no-%s are mutually exclusive' % (name, name))
        else :
            result = True
    else :
        if nodo :
            result = False
        else :
            result = None
    return result
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool for launching Transfero on the cluster")
    parser.add_argument('--log', dest='log', action='store_true', help='Enable logging')
    parser.add_argument('--no-log', dest='nolog', action='store_true', help='Disable logging')
    parser.add_argument('--transfer', dest='transfer', action='store_true', help='Enable transfer of data from rigs')
    parser.add_argument('--no-transfer', dest='notransfer', action='store_true', help='Disable transfer of data from rigs')
    parser.add_argument('--analyze', dest='analyze', action='store_true', help='Enable analysis of data')
    parser.add_argument('--no-analyze', dest='noanalyze', action='store_true', help='Disable analysis of data')
    args = parser.parse_args()

    do_log = process_tristate_arg_pair(args.log, args.nolog, 'log')
    do_transfer = process_tristate_arg_pair(args.transfer, args.notransfer, 'transfer')
    do_analyze = process_tristate_arg_pair(args.analyze, args.noanalyze, 'analyze')

    transfero_via_bsub(do_log, do_transfer, do_analyze)
