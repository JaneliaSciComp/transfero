#!/usr/bin/python3

import os
import itertools
from transfero import *



def check_for_aso_pipeline_output_files(relative_path_to_folder_from_experiment_index, transfero_destination_folder_path) :
    # This function prints stuff to stdout when there are test failures
    successful_test_file_names = [ 'movie.ufmf.flytracked/movie-track.mat', 'movie.ufmf.flytracked/movie-feat.mat', 'movie.ufmf.flytracked/movie-calibration.mat' ] 
    failed_test_file_names = [] 
    experiment_count = len(relative_path_to_folder_from_experiment_index) 
    all_tests_passed_from_experiment_index = [True] * len(relative_path_to_folder_from_experiment_index)
    for experiment_index in range(experiment_count) :
        relative_path_to_experiment_folder = relative_path_to_folder_from_experiment_index[experiment_index]
        experiment_folder_path = os.path.join(transfero_destination_folder_path, relative_path_to_experiment_folder) 
        # First check for the file that indicates we wouldn't expect a experiment to
        # process fully
        is_experiment_expected_to_succeed = not os.path.exists(os.path.join(experiment_folder_path, 'aso-pipeline-should-fail-for-this-experiment'))
        if is_experiment_expected_to_succeed :
            for i in range(len(successful_test_file_names)) :
                test_file_name = successful_test_file_names[i] 
                test_file_path = os.path.join(experiment_folder_path, test_file_name) 
                if not os.path.exists(test_file_path) :
                    printf('Test failure: No output file at %s\n' % test_file_path) 
                    all_tests_passed_from_experiment_index[experiment_index] = False 
        else :
            # Check for the files that *should* be there
            for i in range(len(failed_test_file_names)) :
                test_file_name = failed_test_file_names[i]
                test_file_path = os.path.join(experiment_folder_path, test_file_name) 
                if not os.path.exists(test_file_path) :
                    printf('Test failure: No output file at %s\n' % test_file_path) 
                    all_tests_passed_from_experiment_index[experiment_index] = False 
    return all_tests_passed_from_experiment_index



def test_transfero_on_aso_rig(do_transfer_data_from_rigs=True, do_run_analysis=True) :
    # Where does this script live?
    this_script_path = os.path.realpath(__file__)
    this_folder_path = os.path.dirname(this_script_path)
    project_folder_path = os.path.dirname(this_folder_path) 
    root_example_experiments_folder_path = os.path.join(project_folder_path, 'example-experiments')     
    read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-short-aso-experiment-read-only') 
    #read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-fake-aso-experiment-read-only') 
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
    per_lab_configuration['user_name_for_configuration_purposes'] = 'asorobot'
    per_lab_configuration['log_file_name'] = 'transfero-analysis.log'

    # Get the relative paths of all the experiment folders
    absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
    relative_path_to_folder_from_experiment_index = \
        [os.path.relpath(abs_path, read_only_example_experiments_folder_path) for abs_path in absolute_path_to_read_only_folder_from_experiment_index]

    # Delete the destination folder
    if os.path.exists(transfero_destination_folder_path) :
        run_subprocess_live(['rm', '-rf', transfero_destination_folder_path]) 

    # # Recopy the analysis test folder from the template
    # print('Resetting analysis test folder...\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-transfero-example-experiments-folder') 
    # reset_transfero_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy it to the rig computer (or just direct to the destination folder)
    if do_transfer_data_from_rigs :
        print('Transfering data to the rig computer...')  
        command_line = 'scp -B -r %s/* %s@%s:%s' % (read_only_example_experiments_folder_path, rig_user_name, rig_host_name, rig_data_folder_path)
        run_subprocess_live(command_line, shell=True) 
        print('Done transfering data to the rig computer.')  
    else :
        print('Transfering data to the destination path...') 
        os.makedirs(os.path.dirname(transfero_destination_folder_path), exist_ok=True )
        command_line = ['cp', '-R', '-T', read_only_example_experiments_folder_path, transfero_destination_folder_path] 
        run_subprocess_live(command_line)   
        # Should make transfero_destination_folder_path a clone of
        # example_experiments_folder_path, since we use -T option

        # Add symlinks to the to-process folder so that they will actually get processed
        folder_path_from_experiment_index = find_experiment_folders(transfero_destination_folder_path) 
        to_process_folder_path = os.path.join(transfero_destination_folder_path, 'to-process') 
        os.makedirs(to_process_folder_path, exist_ok=True) 
        experiment_count = len(folder_path_from_experiment_index)
        for i in range(experiment_count) : 
            experiment_folder_path = folder_path_from_experiment_index[i] 
            command_line = ['ln', '-s', experiment_folder_path, to_process_folder_path] 
            run_subprocess_live(command_line) 
        print('Done transfering data to the destination path.') 
 
    # Run transfero
    #analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
    print('Running transfero...') 
    (relative_path_from_synched_experiment_folder_index, job_status_from_experiment_index) = \
        transfero(do_transfer_data_from_rigs, do_run_analysis, per_lab_configuration)

    # Check that the expected files are present on dm11
    local_verify(read_only_example_experiments_folder_path, transfero_destination_folder_path) 

    # Check the return values from transfero()
    if len(relative_path_from_synched_experiment_folder_index)==0 and len(job_status_from_experiment_index)==1 and all(job_status==+1 for job_status in job_status_from_experiment_index) :
        # all is well
        pass
    else :
        print('relative_path_from_synched_experiment_folder_index: ', relative_path_from_synched_experiment_folder_index)
        print('job_status_from_experiment_index: ', job_status_from_experiment_index)
        raise RuntimeError('It seems transfero had issues')

    # Check that some of the expected outputs were generated
    all_tests_passed_from_experiment_index = check_for_aso_pipeline_output_files(relative_path_to_folder_from_experiment_index, transfero_destination_folder_path) 
    if all(all_tests_passed_from_experiment_index) :
        print('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
    else :
        some_tests_failed_from_experiment_index = map(lambda x: (not x), all_tests_passed_from_experiment_index) ;
        relative_path_to_folder_from_failed_experiment_index = \
            itertools.compress(relative_path_to_folder_from_experiment_index, some_tests_failed_from_experiment_index)
        print("Experiment(s) with problems at first check:\n")
        map(lambda path: print("  %s\n", path), relative_path_to_folder_from_failed_experiment_index)
        raise Exception('Some experiments had problems at 1st check') 

    # Check that the rig lab folder is empty now
    if do_transfer_data_from_rigs :
        (relative_path_from_experiment_folder_index, _) = \
            find_remote_experiment_folders(rig_user_name, rig_host_name, rig_data_folder_path)
        experiment_folder_count = len(relative_path_from_experiment_folder_index)
        if experiment_folder_count > 0 :
            print("Experiment(s) that still exist on the remote machine:")
            map(lambda path: print("  %s\n", path), relative_path_from_experiment_folder_index)
            raise RuntimeError('Rig lab data folder %s:%s seems to still contain %d experiments' % 
                               (rig_host_name, rig_data_folder_path, experiment_folder_count))

    # Run transfero again, make sure nothing has changed
    (relative_path_from_synched_experiment_folder_index, job_status_from_experiment_index) = \
        transfero(do_transfer_data_from_rigs, do_run_analysis, per_lab_configuration)         

    # Check that the expected files are present on dm11
    local_verify(read_only_example_experiments_folder_path, transfero_destination_folder_path) 

    # Check the return values from transfero()
    # Both should be empty b/c there was nothing to do on the re-run
    if len(relative_path_from_synched_experiment_folder_index)==0 and len(job_status_from_experiment_index)==0 :
        # all is well
        pass
    else :
        print('relative_path_from_synched_experiment_folder_index: ', relative_path_from_synched_experiment_folder_index)
        print('job_status_from_experiment_index: ', job_status_from_experiment_index)
        raise RuntimeError('It seems transfero had issues')

    # Check that some of the expected outputs were generated
    all_tests_passed_from_experiment_index = check_for_aso_pipeline_output_files(relative_path_to_folder_from_experiment_index, transfero_destination_folder_path) 
    if all(all_tests_passed_from_experiment_index) :
        print('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
    else :
        some_tests_failed_from_experiment_index = map(lambda x: (not x), all_tests_passed_from_experiment_index)
        relative_path_to_folder_from_failed_experiment_index = \
            itertools.compress(relative_path_to_folder_from_experiment_index, some_tests_failed_from_experiment_index)
        raise Exception('Some experiments had problems at 2nd check')

    # Check that the rig lab folder is empty now
    if do_transfer_data_from_rigs :
        (relative_path_from_experiment_folder_index, _) = \
            find_remote_experiment_folders(rig_user_name, rig_host_name, rig_data_folder_path)
        experiment_folder_count = len(relative_path_from_experiment_folder_index)
        if experiment_folder_count > 0 :
            print("Experiment(s) that still exist on the remote machine:\n")
            map(lambda path: print("  %s\n", path), relative_path_from_experiment_folder_index)
            raise Exception('Rig lab data folder %s:%s seems to still contain %d experiments' % 
                            (rig_host_name, rig_data_folder_path, experiment_folder_count))

    # If get here, all is well
    this_script_name = os.path.basename(this_script_path) 
    print('All tests in %s.m passed.' % this_script_name)
# end of test_transfero()



if __name__ == "__main__":
    test_transfero_on_aso_rig(False, True)
