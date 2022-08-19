#!/usr/bin/python3

import os

from transfero import *

def test_transfero_on_aso_rig_2nd(do_transfer_data_from_rigs=False, do_run_analysis=False) :
    # Where does this script live?
    this_script_path = os.path.realpath(__file__)
    this_folder_path = os.path.dirname(this_script_path)
    project_folder_path = os.path.dirname(this_folder_path) 
    root_example_experiments_folder_path = os.path.join(project_folder_path, 'example-experiments') 
    read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-fake-aso-experiment-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-katie-experiment-2022-04-05-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-passing-test-suite-experiment-with-tracking-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
    #read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

    # Specify the "per-lab" configuration here
    #cluster_billing_account_name = 'scicompsoft' 
    cluster_billing_account_name = 'aso'
    rig_host_name = 'asolab-ww1.hhmi.org' 
    rig_user_name = 'ASOLAB-WW1+labadmin' 
    rig_data_folder_path = '/cygdrive/d/fake-test-data'
    transfero_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-transfero-on-aso-rig-destination-folder') 
    per_lab_configuration = {}
    per_lab_configuration['cluster_billing_account_name'] = cluster_billing_account_name
    per_lab_configuration['host_name_from_rig_index'] = [rig_host_name] 
    per_lab_configuration['rig_user_name_from_rig_index'] = [rig_user_name] 
    per_lab_configuration['data_folder_path_from_rig_index'] = [rig_data_folder_path]
    per_lab_configuration['destination_folder'] = transfero_destination_folder_path     
    #per_lab_configuration['analysis_executable_path'] = '/bin/echo'
    per_lab_configuration['analysis_executable_path'] = '../aso-deepmind-experiment-analysis-pipeline/aso_deepmind_experiment_analysis_pipeline.py'  # this is interpreted realtive to folder containing transfero.py
    per_lab_configuration['slots_per_analysis_job'] = 48
    per_lab_configuration['maximum_analysis_slot_count'] = 480

    # # Get the relative paths of all the experiment folders
    # absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
    # relative_path_to_folder_from_experiment_index = \
    #     [os.path.relpath(abs_path, read_only_example_experiments_folder_path) for abs_path in absolute_path_to_read_only_folder_from_experiment_index]

    # # Delete the destination folder
    # if os.path.exists(transfero_destination_folder_path) :
    #     run_subprocess_live(['rm', '-rf', transfero_destination_folder_path]) 

    # # # Recopy the analysis test folder from the template
    # # print('Resetting analysis test folder...\n') 
    # # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-transfero-example-experiments-folder') 
    # # reset_transfero_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # # Copy it to the rig computer (or just direct to the destination folder)
    # if do_transfer_data_from_rigs :
    #     print('Transfering data to the rig computer...')  
    #     command_line = 'scp -B -r %s/* %s@%s:%s' % (read_only_example_experiments_folder_path, rig_user_name, rig_host_name, rig_data_folder_path)
    #     run_subprocess_live(command_line, shell=True) 
    #     print('Done transfering data to the rig computer.')  
    # else :
    #     print('Transfering data to the destination path...') 
    #     os.makedirs(os.path.dirname(transfero_destination_folder_path), exist_ok=True )
    #     command_line = ['cp', '-R', '-T', read_only_example_experiments_folder_path, transfero_destination_folder_path] 
    #     run_subprocess_live(command_line)   
    #     # Should make transfero_destination_folder_path a clone of
    #     # example_experiments_folder_path, since we use -T option

    #     # Add symlinks to the to-process folder so that they will actually get processed
    #     folder_path_from_experiment_index = find_experiment_folders(transfero_destination_folder_path) 
    #     to_process_folder_path = os.path.join(transfero_destination_folder_path, 'to-process') 
    #     os.makedirs(to_process_folder_path, exist_ok=True) 
    #     experiment_count = len(folder_path_from_experiment_index)
    #     for i in range(experiment_count) : 
    #         experiment_folder_path = folder_path_from_experiment_index[i] 
    #         command_line = ['ln', '-s', experiment_folder_path, to_process_folder_path] 
    #         run_subprocess_live(command_line) 
    #     print('Done transfering data to the destination path.') 
 
    # Run transfero
    #analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
    print('Running transfero...') 
    transfero(False, False, per_lab_configuration)
# end of test_transfero()



if __name__ == "__main__":
    test_transfero_on_aso_rig_2nd(False, False)
