#! /usr/bin/python3

import os

from transfero import *



def error_if_uncommited_changes(repo_path) :
    with cd(repo_path) as _ :
        stdout = run_subprocess_and_return_stdout(['git', 'status', '--porcelain=v1']) 
        trimmed_stdout = stdout.strip()  # Will be empty if no uncomitted changes
        if isladen(trimmed_stdout) :
            raise RuntimeError('The git repo seems to have uncommitted changes:\n%s' % stdout) 



def copy_to_single_user_account(user_name, transfero_folder_path):
    # Copy the folder over
    host_name = 'login2'   # Why not?
    printf('Copying into the %s user account...' % user_name) 
    run_remote_subprocess_and_return_stdout(user_name, host_name, ['rm', '-rf', 'transfero']) 
    run_remote_subprocess_and_return_stdout(user_name, host_name, ['cp', '-R', '-T', transfero_folder_path, 'transfero']) 
    printf('done.\n') 



def copy_transfero_into_production() :
    # Determine the Transfero folder path
    this_script_path = os.path.realpath(__file__)
    transfero_folder_path = os.path.dirname(this_script_path)
    
    # Make sure there are no uncommitted changes
    error_if_uncommited_changes(transfero_folder_path)
    
    # Do Aso Lab instance
    copy_to_single_user_account('asorobot', transfero_folder_path) 

    # If get here, everything went well
    printf('Successfully copied %s into all the *lab/*robot user accounts\n' % transfero_folder_path) 



if __name__ == "__main__":
    copy_transfero_into_production()
