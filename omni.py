def filename_abs = absolute_filename(filename)

    if is_filename_absolute(filename)
        filename_abs = filename 
    else
        filename_abs = os.path.join(pwd(), filename) 
    end

end
def add_links_to_to_process_folder(destination_folder, to_process_folder_name, relative_path_from_experiment_folder_index)
    to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
    escaped_to_process_folder_path = escape_string_for_bash(to_process_folder_path) 
    experiment_folder_relative_path_count = length(relative_path_from_experiment_folder_index) 
    for i = 1 : experiment_folder_relative_path_count :
        experiment_folder_relative_path = relative_path_from_experiment_folder_index{i} 
        experiment_folder_absolute_path = os.path.join(destination_folder, experiment_folder_relative_path) 
        escaped_experiment_folder_absolute_path = escape_string_for_bash(experiment_folder_absolute_path) 
        command_line = sprintf('ln -s %s %s', escaped_experiment_folder_absolute_path, escaped_to_process_folder_path) 
        system_with_error_handling(command_line) 
    end
end
def result = bransonlab_configuration()
    result = struct() 
    result.cluster_billing_account_name = 'branson' 
    result.host_name_from_rig_index = { 'arrowroot.hhmi.org', 'beet.hhmi.org', 'carrot.hhmi.org', 'daikon.hhmi.org' } 
    result.rig_user_name_from_rig_index = repmat({'bransonk'}, [1 4]) 
    result.data_folder_path_from_rig_index = repmat({'/cygdrive/e/flydisco_data/branson'}, [1 4]) 
    result.destination_folder = '/groups/branson/bransonlab/flydisco_data' 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    flydisco_analysis_path = os.path.dirname(this_folder_path) 
    result.settings_folder_path = os.path.join(flydisco_analysis_path, 'settings') 
    result.does_use_per_user_folders = false 
end
def all_tests_passed_from_experiment_index = \
        check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path)
    # This def prints stuff to stdout when there are test failures
    successful_test_file_names = {'registered_trx.mat' 'wingtracking_results.mat' 'automatic_checks_complete_results.txt' } 
    failed_test_file_names = { 'automatic_checks_complete_results.txt' } 
    #excluded_test_file_names = { 'registered_trx.mat' 'wingtracking_results.mat' }     
    experiment_count = length(relative_path_to_folder_from_experiment_index) 
    all_tests_passed_from_experiment_index = true(size(relative_path_to_folder_from_experiment_index)) 
    for experiment_index = 1 : experiment_count :
        relative_path_to_experiment_folder = relative_path_to_folder_from_experiment_index{experiment_index} 
        experiment_folder_path = os.path.join(goldblum_destination_folder_path, relative_path_to_experiment_folder) 
        % First check for the file that indicates we wouldn't expect a experiment to
        % process fully
        is_experiment_expected_to_succeed = ~exist(os.path.join(experiment_folder_path, 'flydisco-pipeline-should-fail-for-this-experiment'), 'file') 
        if is_experiment_expected_to_succeed :
            for i = 1 : length(successful_test_file_names) :
                test_file_name = successful_test_file_names{i} 
                test_file_path = \
                    os.path.join(experiment_folder_path, test_file_name) 
                if ~exist(test_file_path, 'file') :
                    fprintf('Test failure: No output file at %s\n', test_file_path) 
                    all_tests_passed_from_experiment_index(experiment_index) = false 
                end
            end
        else
            % Check for the files that *should* be there
            for i = 1 : length(failed_test_file_names) :
                test_file_name = failed_test_file_names{i} 
                test_file_path = \
                    os.path.join(experiment_folder_path, test_file_name) 
                if ~exist(test_file_path, 'file') :
                    fprintf('Test failure: No output file at %s\n', test_file_path) 
                    all_tests_passed_from_experiment_index(experiment_index) = false 
                end
            end
#             % Check for the files that should *not* be there
#             for i = 1 : length(excluded_test_file_names) :
#                 test_file_name = excluded_test_file_names{i} 
#                 test_file_path = \
#                     os.path.join(experiment_folder_path, test_file_name) 
#                 if exist(test_file_path, 'file') :
#                     fprintf('Test failure: Output file is at %s, but it shouldn''t be!\n', test_file_path) 
#                     all_tests_passed_from_experiment_index(experiment_index) = false 
#                 end
#             end            
        end
    end
end
def hex_digest = compute_md5_on_local(local_path) 
    escaped_local_path = escape_path_for_bash(local_path) 
    command_line = sprintf('md5sum %s', escaped_local_path) 
    [return_code, stdout] = system(command_line) 
    if return_code ~= 0 :
        error('Unable to md5sum the file %s.  Stdout/stderr was:\n%s', local_path, stdout) 
    end
    tokens = strsplit(strtrim(stdout)) 
    if isempty(tokens) :
        error('Got a weird result while md5sum''ing the file %s.  Stdout/stderr was:\n%s', local_path, stdout)
    end        
    hex_digest = tokens{1} 
end
def hex_digest =  compute_md5_on_remote(source_user, source_host, source_path)
    escaped_source_path = escape_path_for_bash(source_path) 
    host_spec = horzcat(source_user, '@', source_host) 
    command_line = sprintf('ssh %s md5sum %s', host_spec, escaped_source_path) 
    [return_code, stdout] = system(command_line) 
    if return_code ~= 0 :
        error('Unable to md5sum the file %s as user %s on host %s', source_path, source_user, source_host) 
    end
    tokens = strsplit(stdout) 
    if isempty(tokens) :
        error('Got a weird result while md5sum''ing the file %s as user %s on host %s.  Result was: %s', \
              source_path, source_user, source_host, stdout) 
    end
    hex_digest = tokens{1} 
end
    def elapsed_time = copy_file_from_remote(source_user, source_host, source_path, dest_path)
    escaped_source_path = escape_path_for_bash(source_path) 
    escaped_dest_path = escape_path_for_bash(dest_path) 
    source_spec = horzcat(source_user, '@', source_host, ':', escaped_source_path) 
    tic_id = tic() 
    command_line = sprintf('scp -v -B -T %s %s', source_spec, escaped_dest_path) 
    [scp_return_code, stdout] = system(command_line) 
    # scp doesn't honor the user's umask, so we need to set the file
    # permissions explicitly
    if scp_return_code == 0:
        command_line = sprintf('chmod u+rw-x,g+rw-x,o+r-wx %s', escaped_dest_path) 
        [chmod_return_code, stdout] = system(command_line) 
    end
    elapsed_time = toc(tic_id) 
    if scp_return_code ~= 0 :
        error('copy_file_from_remote:failed', \
              'Unable to copy the file %s as remote user %s from host %s to destination %s:\n%s', \ 
              source_path, source_user, source_host, dest_path, stdout) 
    elseif chmod_return_code ~= 0 :
        error('copy_file_from_remote:failed', \
              'Unable to set the permissions of %s after copy:\n%s', \
              dest_path, stdout) 
    end    
end
def copy_goldblum_into_production()
    # Determine the FlyDiscoAnalysis folder path
    goldblum_folder_path = os.path.dirname(mfilename('fullpath')) 
    fda_folder_path = os.path.dirname(goldblum_folder_path) 
    
    # Make sure there are no uncommitted changes
    error_if_uncommited_changes(fda_folder_path) 
    
    # Do Branson Lab instance
    copy_to_single_user_account('bransonlab', fda_folder_path) 
    
    # Do Dickson Lab instance
    copy_to_single_user_account('dicksonlab', fda_folder_path) 
    
    # Do Rubin Lab instance
    copy_to_single_user_account('rubinlab', fda_folder_path) 

    # If get here, everything went well
    fprintf('Successfully copied %s into all the *lab user accounts\n', fda_folder_path) 
end



def copy_to_single_user_account(user_name, fda_folder_path)
    # Copy the folder over
    host_name = 'login2'   % Why not?
    fprintf('Copying into the %s user account\', user_name) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'rm', '-rf', 'FlyDiscoAnalysis'}) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'cp', '-R', '-T', fda_folder_path, 'FlyDiscoAnalysis'}) 
    fprintf('done.\n') 
end
do_use_bqueue = false 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'aborted-example-experiments-read-only') 
working_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'aborted-example-experiments') 

# Delete the destination folder
if exist(working_example_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_example_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_example_experiments_folder_path, read_only_example_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_example_experiments_folder_path) 

# Run the script under test
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                           do_force_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
experiment_folder_path = '/groups/branson/bransonlab/flydisco_data/locomotionGtACR1_emptySplit24m_RigB_20210216T115316' 
settings_folder_path = '/groups/branson/bransonlab/taylora/flydisco/goldblum/FlyDiscoAnalysis/settings' 
do_run_analysis_in_debug_mode = false 

goldblum_FlyDiscoPipeline_wrapper(experiment_folder_path, settings_folder_path, do_run_analysis_in_debug_mode) 
do_use_bqueue = false 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_analysis_folder_path, 'too-much-memory-example-experiments-blank-slate-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_analysis_folder_path, 'too-much-memory-example-experiments-blank-state') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                           do_force_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
def delete_remote_folder_contents(remote_user_name, remote_dns_name, remote_folder_path) 
    # Delete the contents of the remote folder after successful transfer
    escaped_remote_folder_path = escape_path_for_bash(remote_folder_path) 
    remote_command_line = \
        sprintf('ls -1 -A %s | while read line do echo %s/$line done | xargs -d ''\\n'' rm -rf', escaped_remote_folder_path, escaped_remote_folder_path) 
    escaped_remote_command_line = escape_path_for_bash(remote_command_line) 
    command_line = sprintf('ssh %s@%s %s', remote_user_name, remote_dns_name, escaped_remote_command_line) 
    [return_code, stdout] = system(command_line) 
    if return_code ~= 0 :
        error('Unable to delete the contents of folder %s as user %s on host %s.  Stdout/stderr was:\n%s\n', \
                remote_folder_path, remote_user_name, remote_dns_name, stdout) 
    end
end
def delete_remote_folder(remote_user_name, remote_dns_name, remote_folder_path)
    # Delete (as in rm -rf) a remote folder
    
    # Check for a truly horrible mistake
    trimmed_remote_folder_path = strtrim(remote_folder_path) 
    if isempty(trimmed_remote_folder_path) || isequal(trimmed_remote_folder_path, '/') :
        error('Yeah, I''m not going to rm -rf / on %s', remote_dns_name) 
    end
    
    escaped_remote_folder_path = escape_string_for_bash(remote_folder_path) 
    command_line = sprintf('ssh %s@%s rm -rf %s', remote_user_name, remote_dns_name, escaped_remote_folder_path) 
    return_code = system(command_line) 
    if return_code ~= 0 :
        error('Unable to delete the folder %s as user %s on host %s', \
              remote_folder_path, remote_user_name, remote_dns_name) 
    end
end
    def delete_stuff_in_rig_data_folder(remote_user_name, remote_dns_name, root_remote_folder_path, does_use_per_user_folders)
    # Delete the contents of the remote folder after successful transfer
    if does_use_per_user_folders :
        try
            [remote_entries, ~, ~, is_remote_entry_a_dir] = \
                list_remote_dir(remote_user_name, remote_dns_name, root_remote_folder_path) 
        except me :
            % orginally caught OSError
            if isequal(me.identifier, 'list_remote_dir:failed') :
                fprintf('Unable to delete the contents of folder %s as user %s on host %s\n', root_remote_folder_path, remote_user_name, remote_dns_name) 
                disp(me.getReport()) 
            else
                rethrow(me) 
            end
        end

        % separate remote dirs out (these should be the user folders)
        remote_user_folder_names = remote_entries(is_remote_entry_a_dir) 

        % delete the contents of each of the remote user folders
        for i = 1 : length(remote_user_folder_names) :
            remote_user_folder_name = remote_user_folder_names{i} 
            remote_user_folder_path = os.path.join(root_remote_folder_path, remote_user_folder_name) 
            delete_remote_folder_contents(remote_user_name, remote_dns_name, remote_user_folder_path) 
        end
    else
        % If not using per-user folders, can just delete contents of whole
        % folder
        delete_remote_folder_contents(remote_user_name, remote_dns_name, root_remote_folder_path) 
    end
end
def does_exist = does_remote_file_exist(user_name, host_name, path) 
    escaped_source_path = escape_path_for_bash(path) 
    remote_stat_command_line = horzcat('test -a ', escaped_source_path) 
    command_line = horzcat('ssh ', user_name, '@', host_name, ' ', remote_stat_command_line) 
    [return_code, stdout] = system(command_line) 
    if return_code==0 :
        does_exist = true 
    elseif return_code == 1 :
        does_exist = false 
    else
        error('Ambiguous result from "%s": Not clear if file/folder %s exists or not on host %s.  Return code is %d.  stdout is:\n%s', \
              command_line, path, host_name, return_code, stdout) 
    end
end
def ensure_file_does_not_exist(raw_file_path)
    file_path = absolute_filename(raw_file_path) 
    ensure_file_does_not_exist_helper(file_path) 
end



def ensure_file_does_not_exist_helper(file_path)
    if exist(file_path, 'file') :
        if exist(file_path, 'dir') :
            error('Want to delete file at %s, but there''s a folder there, and I''m scared to delete a whole subtree', file_path) 
        else
            % Presumably a regular file (or a symlink), so we delete it
            delete(file_path)
        end
    else
        % nothing to do, already there's no file at that path
    end        
end
def ensure_file_or_folder_does_not_exist(raw_file_path)
    file_path = absolute_filename(raw_file_path) 
    ensure_file_or_folder_does_not_exist_helper(file_path) 
end



def ensure_file_or_folder_does_not_exist_helper(file_path)
    if exist(file_path, 'file') :
        if exist(file_path, 'dir') :
            system_from_list_with_error_handling({'rm', '-rf', file_path}) 
        else
            % Presumably a regular file (or a symlink), so we delete it
            delete(file_path)
        end
    else
        % nothing to do, already there's no file at that path
    end        
end
def ensure_folder_exists(raw_folder_path)
    folder_path = absolute_filename(raw_folder_path) 
    ensure_folder_exists_helper(folder_path) 
end



def ensure_folder_exists_helper(folder_path)
    if exist(folder_path, 'file') :
        if exist(folder_path, 'dir') :
            % do nothing, all is well, return
        else
            error('Want to create folder %s, but a file (not a folder) already exists at that location', folder_path) 
        end
    else
        parent_folder_path = os.path.dirname(folder_path) 
        ensure_folder_exists_helper(parent_folder_path) 
        mkdir(folder_path) 
    end        
end
def error_if_uncommited_changes(repo_path)
    original_pwd =pwd() 
    cleaner = onCleanup(@()(cd(original_pwd))) 
    cd(repo_path) 
    stdout = system_with_error_handling('git status --porcelain=v1') 
    trimmed_stdout = strtrim(stdout)   % Will be empty if no uncomitted changes
    if ~isempty(trimmed_stdout) :
        error('The git repo seems to have uncommitted changes:\n%s', stdout) 
    end
    #stdout = system_with_error_handling('git rev-parse --verify HEAD') 
    #result = strtrim(stdout) 
end
def [name, size_in_bytes, is_file, is_dir, is_link, mod_time] = extract_name_size_and_type_from_ls_long_line(line)
    # We assume line looks like this: '-rw-r--r--  1 taylora scicompsoft     278 2020-12-02 17:09:49.027303272 -0500 "test_bw_smooth.m"'
    tokens = strsplit(line) 
    size_in_bytes = str2double(tokens{5}) 
    parts = strsplit(line, '"') 
    name = parts{2} 
    file_type_char = line(1) 
    is_file = isequal(file_type_char, '-') 
    is_dir =  isequal(file_type_char, 'd') 
    is_link = isequal(file_type_char, 'l') 
    mod_date_as_string = tokens{6} 
    mod_time_as_string_with_ns = tokens{7} 
    mod_time_as_string = mod_time_as_string_with_ns(1:15)   % only out to ms
    utc_offset_as_string = tokens{8} 
    mod_time_as_string = horzcat(mod_date_as_string, ' ', mod_time_as_string, ' ', utc_offset_as_string)   % date, time
    time_format = 'yyyy-MM-dd HH:mm:ss.SSSSSS XX' 
    mod_time = datetime(mod_time_as_string, 'InputFormat', time_format, 'TimeZone', 'UTC')   % Want a datetime in UTC timezone 
end
def [parent, name] = os.path.dirname2(path) 
    [parent, base, ext] = os.path.dirname(path) 
    name = horzcat(base, ext) 
end
def result = find_experiment_folders(source_path)
    relative_path_from_experiment_index = find_experiment_folders_relative(source_path) 
    result = cellfun(@(rel_path)(os.path.join(source_path, rel_path)), relative_path_from_experiment_index, 'UniformOutput', false) 
end
def result = find_experiment_folders_relative_helper(root_path, parent_relative_path, spinner)
    # Get a list of all files and folders in the source, dest folders
    parent_path = os.path.join(root_path, parent_relative_path) 
    [entries, is_entry_a_folder] = simple_dir(parent_path) 
    spinner.spin() 

    # Separate source file, folder names    
    file_names = entries(~is_entry_a_folder) 
    raw_folder_names = entries(is_entry_a_folder)     
    
    # Exclude the to-process folder if in the root path
    if isempty(parent_relative_path) :
        is_to_process_folder = strcmp(raw_folder_names, 'to-process') 
        folder_names = raw_folder_names(~is_to_process_folder) 
    else
        folder_names = raw_folder_names 
    end
    
    # If the parent_path is an experiment folder, we're done
    if is_experiment_folder_given_contents(file_names) :
        result = {parent_relative_path} 
    else            
        % For each folder, recurse
        result = cell(0,1) 
        for i = 1 : length(folder_names) :
            folder_name = folder_names{i} 
            child_folder_path_list = \
                 find_experiment_folders_relative_helper(root_path, \
                                                         os.path.join(parent_relative_path, folder_name), \
                                                         spinner) 
            result = [ result  child_folder_path_list ]   %#ok<AGROW>
        end
    end
end
def experiment_folder_path_list = find_experiment_folders_relative(source_path)
    # record the start time
    start_time = tic() 

    # print an informative message
    fprintf("Looking for experiment folders within %s\ ", source_path)
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    experiment_folder_path_list = find_experiment_folders_relative_helper(source_path, '', spinner) 
    spinner.stop() 
   
    # print the number of files etc verified
    fprintf("%d experiment folders found\n" , length(experiment_folder_path_list))

    # print the elapsed time
    elapsed_time = toc(start_time) 
    fprintf("Elapsed time: %0.1f seconds\n", elapsed_time) 
end
def result = find_free_log_file_name(experiment_folder_path)
    max_index_to_try = 99 
    did_find_free_name = false 
    for i = 1 : max_index_to_try :
        file_name = sprintf('flydisco-analysis-log-run-%02d.txt', i) 
        result = os.path.join(experiment_folder_path, file_name) 
        if ~exist(result, 'file') :
            did_find_free_name = true 
            break
        end
    end
    if ~did_find_free_name :
        error('Folder %s has too many log files', experiment_folder_path) 
    end
end
def [relative_path_from_experiment_index, is_aborted_from_experiment_index] = \
        find_remote_experiment_folders_helper(user_name, host_name, parent_relative_path, root_absolute_path, to_process_folder_name, spinner)
    # Find the experiment folders on a remote host.  Returns relative paths:
    # relative to root_absolute_path.
  
    # Get a list of all files and folders
    parent_absolute_path = os.path.join(root_absolute_path, parent_relative_path) 
    try
        [entries, ~, ~, is_entry_a_folder, ~] = \
            list_remote_dir(user_name, host_name, parent_absolute_path) 
    except me :
        % if we can't list the dir, warn but continue
        if isequal(me.identifier, 'list_remote_dir:failed') :
            spinner.print("Warning: can't list path %s on host %s as user %s", parent_absolute_path, host_name, user_name) 
            spinner.print("%s", me.getReport()) 
            return
        else
            rethrow(me) 
        end
    end
    spinner.spin() 

    # Separate source file, folder names    
    file_names = entries(~is_entry_a_folder) 
    folder_names = entries(is_entry_a_folder)     

    # If the parent_path is an experiment folder, we're done
    if is_experiment_folder_given_contents(file_names) :
        if isequal(parent_relative_path, to_process_folder_name) :
            spinner.print("Warning: found an experiment folder with relative path %s.  Can't synch because that's the path to the to-process folder", \
                          parent_absolute_path) 
        else            
            is_aborted_from_experiment_index = any(strcmp('ABORTED', file_names)) 
            relative_path_from_experiment_index = {parent_relative_path} 
        end
    else            
        % For each folder, recurse
        relative_path_from_experiment_index = cell(0,1) 
        is_aborted_from_experiment_index = false(0,1) 
        for i = 1 : length(folder_names) :
            folder_name = folder_names{i} 
            [relative_path_from_child_experiment_index, is_aborted_from_child_experiment_index] = \
                 find_remote_experiment_folders_helper(user_name, \
                                                       host_name, \
                                                       os.path.join(parent_relative_path, folder_name), \
                                                       root_absolute_path, \
                                                       to_process_folder_name, \
                                                       spinner) 
            relative_path_from_experiment_index = [ relative_path_from_experiment_index  relative_path_from_child_experiment_index ]   %#ok<AGROW>
            is_aborted_from_experiment_index = [ is_aborted_from_experiment_index  is_aborted_from_child_experiment_index ]   %#ok<AGROW>
        end
    end
end
def [relative_path_from_experiment_index, is_aborted_from_experiment_index] = \
        find_remote_experiment_folders(user_name, host_name, path, to_process_folder_name)
    # record the start time
    start_time = tic() 

    # print an informative message
    fprintf("Looking for experiment folders within %s on host %s as user %s\ ", path, host_name, user_name)
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    [relative_path_from_experiment_index, is_aborted_from_experiment_index] = \
        find_remote_experiment_folders_helper(user_name, host_name, '', path, to_process_folder_name, spinner) 
    spinner.stop() 
   
    # print the number of experiment folders found
    fprintf("%d experiment folders found\n" , length(relative_path_from_experiment_index))

    # % print the elapsed time
    elapsed_time = toc(start_time) 
    fprintf("Elapsed time: %0.1f seconds\n", elapsed_time) 
end
def finish()
    try
        % Clean up any host-and-PID-specific scratch folder
        host_name = get_short_host_name() 
        parpool_data_location_folder_name = ['host-' host_name '-pid-' num2str(feature('getpid'))] 
        parpool_data_location_folder_path = os.path.join(get_scratch_folder_path(), parpool_data_location_folder_name) 
        if exist(parpool_data_location_folder_path, 'file') :
            escaped_parpool_data_location_folder_path = escape_string_for_bash(parpool_data_location_folder_path)             
            command_line = sprintf('rm -rf %s', escaped_parpool_data_location_folder_path) 
            system_with_error_handling(command_line) 
        end
    except me
        fprintf('There was a problem during execution of the finish() def:\n') 
        fprintf('%s\n', me.getReport()) 
    end
end
def result = geniegeneric_configuration()
    result = struct() 
    result.cluster_billing_account_name = 'genie' 
    result.host_name_from_rig_index = {'flybowl-ww1.hhmi.org'} 
    result.rig_user_name_from_rig_index = {'labadmin'} 
    result.data_folder_path_from_rig_index = {'/cygdrive/e/flydisco_data/genie'} 
    result.destination_folder = '/groups/genie/genie/flydisco_data' 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    flydisco_analysis_path = os.path.dirname(this_folder_path) 
    result.settings_folder_path = os.path.join(flydisco_analysis_path, 'settings') 
    result.does_have_per_user_folders = true 
end
def name = get_short_host_name()
    [ret, name] = system('hostname -s')    % Want the short version of the host name, without domain
    if ret == 0 :
        name = strtrim(name) 
    else
       if ispc()
          name = getenv('COMPUTERNAME')
       else      
          name = getenv('HOSTNAME')      
       end
       name = strtrim(lower(name))
    end
end
def goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                             do_use_bqueue, do_actually_submit_jobs, analysis_parameters_as_name_value_list)
    #goldblum_analyze_experiment_folders  Runs the FlyDisco pipeline on a set of
    #                                     experiment folders.
    #
    #   goldblum_analyze_experiment_folders(experiment_folder_list) runs the
    #   FlyDisco pipeline on the experiment folders given in the cell array of
    #   strings experiment_folder_list.  This is the def used by Goldblum to
    #   run experiments through the FlyDisco pipeline.  Note in particular that this
    #   def first runs the pipeline on all the experiments with the
    #   automaticcheckscomplete stage turned off, then runs them all with *only* the
    #   automaticcheckscomplete stage turned on.  By default, each run of the
    #   pipeline is submitted as a single LSF cluster job.  The def
    #   FlyDiscoPipeline() is used to run the pipeline.  See the documentation for
    #   that def for more details.
    #
    #   goldblum_analyze_experiment_folders(experiment_folder_list, settings_folder_path)
    #   uses analysis-protocol folders drawn from settings_folder_path instead of
    #   the default setting folder path.  Again, see the documentation of
    #   FlyDiscoPipeline() for more details.
    #
    #   goldblum_analyze_experiment_folders(\, cluster_billing_account_name)
    #   bills any jobs submitted to the LSF cluster to the account specified by 
    #   the string cluster_billing_account_name.  Examples might be 'branson':
    #   'rubin', and 'scicompsoft'.  
    #   
    #   goldblum_analyze_experiment_folders(\, do_use_bqueue), if do_use_bqueue is
    #   true, uses the bqueue_type() framework for submitting jobs to the LSF
    #   cluster.  If do_use_bqueue is false, jobs are run locally, and without first
    #   submitting them to a bqueue.  This option is mostly useful for debugging.
    #   If missing or empty, do_use_bqueue defaults to true.
    #
    #   goldblum_analyze_experiment_folders(\, do_actually_submit_jobs), if 
    #   do_use_bqueue is true, determines whether jobs are actually submitted to the
    #   LSF queue or are simply run locally.  Again, this is mostly useful for
    #   debugging purposes.  If do_use_bqueue is false, this argument is ignored.  
    #   If missing or empty, do_actually_submit_jobs defaults to true.
    #
    #   goldblum_analyze_experiment_folders(\, analysis_parameters_as_name_value_list)
    #   allows the caller to specify additional (key, value) pairs that are passed to
    #   FlyDiscoPipeline().  For instance, a caller might set this argument to 
    #   {'docomputeperframestats', 'off'} to disable the computeperframestats stage
    #   of FlyDiscoPipeline().  See the documentation of FlyDiscoPipeline() for more
    #   details, including a complete list of the supported keys.  If missing or
    #   empty, analysis_parameters_as_name_value_list defaults to cell(1,0).

    # Process arguments                                
    if ~exist('do_use_bqueue', 'var') || isempty(do_use_bqueue) :
        do_use_bqueue = true 
    end
    if ~exist('do_actually_submit_jobs', 'var') || isempty(do_actually_submit_jobs) :
        do_actually_submit_jobs = true 
    end
    if ~exist('analysis_parameters_as_name_value_list', 'var') || isempty(analysis_parameters_as_name_value_list) :
        analysis_parameters_as_name_value_list = cell(1,0) 
    end

    # Specify bsub parameters
    maxiumum_slot_count = 400 
    slots_per_job = 4 
    do_use_xvfb = true   % Matlab on linux leaks memory when you call getframe() without an X11 server
    
#     % If do_force_analysis is true, clear any files indicating ongoing run
#     experiment_count = length(folder_path_from_experiment_index) 
#     if do_force_analysis :
#         for i = 1 : experiment_count :
#             experiment_folder_path = folder_path_from_experiment_index{i} 
#             analysis_in_progress_file_path = os.path.join(experiment_folder_path, 'PIPELINE-IN-PROGRESS') 
#             try
#                 ensure_file_does_not_exist(analysis_in_progress_file_path) 
#             except me
#                 fprintf('Tried to delete the file %s (if it exists), but something went wrong.  Proceeding nevertheless.\n', analysis_in_progress_file_path) 
#                 fprintf('Here''s some information about what went wrong:\n') 
#                 fprintf('%s\n', me.getReport())                 
#             end
#         end
#     end
    
#     % We don't analyze experiments that are already being analyzed
#     is_to_be_analyzed_from_experiment_index = true(experiment_count, 1) 
#     for i = 1 : experiment_count :
#         experiment_folder_path = folder_path_from_experiment_index{i} 
#         analysis_in_progress_file_path = os.path.join(experiment_folder_path, 'PIPELINE-IN-PROGRESS') 
#         is_to_be_skipped = \
#           exist(analysis_in_progress_file_path, 'file') 
#         is_to_be_analyzed_from_experiment_index(i) = ~is_to_be_skipped 
#     end

    # Report how many experiments are to be analyzed
    experiment_count = length(folder_path_from_experiment_index) 
    fprintf('There are %d experiments that will be analyzed.\n', experiment_count) 
    if experiment_count > 0 :
        fprintf('Submitting these for analysis\\n') 
    end

    # Run goldblum_FlyDiscoPipeline_wrapper() on all experiments
    if do_use_bqueue :
        bqueue = bqueue_type(do_actually_submit_jobs, maxiumum_slot_count, do_use_xvfb) 

        % Queue the jobs
        for i = 1 : experiment_count :
            experiment_folder_path = folder_path_from_experiment_index{i} 
            [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
            % We use the options list to pass the stdout/stderr file, b/c the
            % usual mechanism doesn't support appending.
            stdouterr_file_path = os.path.join(experiment_folder_path, 'flydisco-analysis-log.txt') 
            bsub_options = sprintf('-P %s -J %s-flydisco-%s -o %s -e %s', \
                                   cluster_billing_account_name, \
                                   cluster_billing_account_name, \
                                   experiment_folder_name, \
                                   stdouterr_file_path, \
                                   stdouterr_file_path) 
            bqueue.enqueue(slots_per_job, \
                           [], \
                           bsub_options, \
                           @goldblum_FlyDiscoPipeline_wrapper, \
                               experiment_folder_path, \
                               settings_folder_path, \
                               analysis_parameters_as_name_value_list) 
        end

        % Actually run the jobs
        maximum_wait_time = inf 
        do_show_progress_bar = true 
        tic_id = tic() 
        job_statuses = bqueue.run(maximum_wait_time, do_show_progress_bar) 
        toc(tic_id)
        
        % Report on any failed runs
        successful_job_count = sum(job_statuses==1) 
        errored_job_count = sum(job_statuses==-1) 
        did_not_finish_job_count = sum(job_statuses==0) 
        if experiment_count == successful_job_count :
            % All is well
            fprintf('All %d jobs completed successfully.\n', successful_job_count) 
        else
            % Print the folders that completed successfully
            did_complete_successfully = (job_statuses==+1) 
            folder_path_from_successful_experiment_index = folder_path_from_experiment_index(did_complete_successfully) 
            if ~isempty(folder_path_from_successful_experiment_index) :
                fprintf('These %d jobs completed successfully:\n', successful_job_count) 
                for i = 1 : length(folder_path_from_successful_experiment_index) :
                    experiment_folder_path = folder_path_from_successful_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end            
            
            % Print the folders that had errors
            had_error = (job_statuses==-1) 
            folder_path_from_errored_experiment_index = folder_path_from_experiment_index(had_error) 
            if ~isempty(folder_path_from_errored_experiment_index) :
                fprintf('These %d experiment folders had errors:\n', errored_job_count) 
                for i = 1 : length(folder_path_from_errored_experiment_index) :
                    experiment_folder_path = folder_path_from_errored_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end
            
            % Print the folders that did not finish
            did_not_finish = (job_statuses==0) 
            folder_path_from_unfinished_experiment_index = folder_path_from_experiment_index(did_not_finish) 
            if ~isempty(folder_path_from_unfinished_experiment_index) :
                fprintf('These %d experiment folders did not finish processing in the alloted time:\n', did_not_finish_job_count) 
                for i = 1 : length(folder_path_from_unfinished_experiment_index) :
                    experiment_folder_path = folder_path_from_unfinished_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end
        end
    else
        % If not using bqueue, just run them normally (usually just for debugging)
        job_statuses = nan(1, experiment_count) 
        for i = 1 : experiment_count :
            experiment_folder_path = folder_path_from_experiment_index{i} 
            goldblum_FlyDiscoPipeline_wrapper(experiment_folder_path, settings_folder_path, analysis_parameters_as_name_value_list) 
            job_statuses(i) = +1   % Indicates completed sucessfully
        end
    end

    
    
    #
    # "Caboose" phase
    #
        
#     % If the user has specified doautomaticcheckscomplete in analysis_parameters, honor that.
#     % Otherwise, default to turning it on.  (TODO: Do we really need a special case
#     % for this?  Seems baroque.  It's simpler to explain if FlyDiscoPipeline() and
#     % FlyDiscoCaboose() get the same parameters, but FDP runs (at most) everything except the
#     % completion auto-checks, and FDC runs (at most) just the completion
#     % auto-checks.  --ALT, 2021-09-09
#     try
#         lookup_in_name_value_list(analysis_parameters_as_name_value_list, 'doautomaticcheckscomplete') 
#         % if get here, must be specified in analysis_parameters_as_name_value_list
#         caboose_analysis_parameters_as_name_value_list = analysis_parameters_as_name_value_list         
#     except me :
#         if strcmp(me.identifier, 'lookup_in_name_value_list:not_found') :
#             % if get here, must be unspecified in analysis_parameters_as_name_value_list, so
#             % we set it
#             caboose_analysis_parameters_as_name_value_list = \
#                 merge_name_value_lists(analysis_parameters_as_name_value_list, \
#                                        {'doautomaticcheckscomplete', 'on'}) 
#         else
#             rethrow(me) 
#         end
#     end
    
    if experiment_count > 0 :
        fprintf('Submitting %d experiments for caboose phase\\n', experiment_count) 
    end

    # Run the caboose jobs
    if do_use_bqueue :
        caboose_bqueue = bqueue_type(do_actually_submit_jobs, maxiumum_slot_count, do_use_xvfb) 

        % Queue the jobs
        for i = 1 : experiment_count :
            experiment_folder_path = folder_path_from_experiment_index{i} 
            [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
            % We use the options list to pass the stdout/stderr file, b/c the
            % usual mechanism doesn't support appending.
            stdouterr_file_path = os.path.join(experiment_folder_path, 'flydisco-analysis-log.txt') 
            bsub_options = sprintf('-P %s -J %s-flydisco-caboose-%s -o %s -e %s', \
                                   cluster_billing_account_name, \
                                   cluster_billing_account_name, \
                                   experiment_folder_name, \
                                   stdouterr_file_path, \
                                   stdouterr_file_path) 
            caboose_bqueue.enqueue(slots_per_job, \
                                   [], \
                                   bsub_options, \
                                   @goldblum_FlyDiscoCaboose_wrapper, \
                                        experiment_folder_path, \
                                        settings_folder_path, \
                                        analysis_parameters_as_name_value_list) 
        end

        % Actually run the jobs
        maximum_wait_time = inf 
        do_show_progress_bar = true 
        tic_id = tic() 
        job_statuses = caboose_bqueue.run(maximum_wait_time, do_show_progress_bar) 
        toc(tic_id)
        
        % Report on any failed runs
        successful_job_count = sum(job_statuses==1) 
        errored_job_count = sum(job_statuses==-1) 
        did_not_finish_job_count = sum(job_statuses==0) 
        if experiment_count == successful_job_count :
            % All is well
            fprintf('All %d caboose jobs completed successfully.\n', successful_job_count) 
        else
            % Print the folders that completed successfully
            did_complete_successfully = (job_statuses==+1) 
            folder_path_from_successful_experiment_index = folder_path_from_experiment_index(did_complete_successfully) 
            if ~isempty(folder_path_from_successful_experiment_index) :
                fprintf('These %d caboose jobs completed successfully:\n', successful_job_count) 
                for i = 1 : length(folder_path_from_successful_experiment_index) :
                    experiment_folder_path = folder_path_from_successful_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end            
            
            % Print the folders that had errors
            had_error = (job_statuses==-1) 
            folder_path_from_errored_experiment_index = folder_path_from_experiment_index(had_error) 
            if ~isempty(folder_path_from_errored_experiment_index) :
                fprintf('These %d experiment folders had errors during the caboose phase:\n', errored_job_count) 
                for i = 1 : length(folder_path_from_errored_experiment_index) :
                    experiment_folder_path = folder_path_from_errored_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end
            
            % Print the folders that did not finish
            did_not_finish = (job_statuses==0) 
            folder_path_from_unfinished_experiment_index = folder_path_from_experiment_index(did_not_finish) 
            if ~isempty(folder_path_from_unfinished_experiment_index) :
                fprintf('These %d experiment folders did not finish processing in the alloted time during the caboose phase:\n', did_not_finish_job_count) 
                for i = 1 : length(folder_path_from_unfinished_experiment_index) :
                    experiment_folder_path = folder_path_from_unfinished_experiment_index{i} 
                    fprintf('    %s\n', experiment_folder_path) 
                end
                fprintf('\n') 
            end
        end
    else
        % If not using bqueue, just run them normally (usually just for debugging)
        job_statuses = nan(1, experiment_count) 
        for i = 1 : experiment_count :
            experiment_folder_path = folder_path_from_experiment_index{i} 
            goldblum_FlyDiscoCaboose_wrapper(experiment_folder_path, settings_folder_path, analysis_parameters_as_name_value_list) 
            job_statuses(i) = +1   % Indicates completed sucessfully
        end
    end    
end
def goldblum_FlyDiscoCaboose_wrapper(experiment_folder_path, settings_folder_path, overriding_analysis_parameters_as_list)
    # This is the def that is submitted by goldblum to the bqueue to run each
    # experiment.
  
    # Handle arguments
    if ~exist('settings_folder_path', 'var') || isempty(settings_folder_path) :
        script_folder_path = os.path.dirname(mfilename('fullpath')) 
        fly_disco_analysis_folder_path = os.path.dirname(script_folder_path) 
        settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
    end
    if ~exist('overriding_analysis_parameters_as_list', 'var') || isempty(overriding_analysis_parameters_as_list) :
        overriding_analysis_parameters_as_list = cell(1, 0) 
    end
    
    # Print the date to the stdout, so it gets logged
    dt = datetime('now') 
    date_as_string = string(datetime(dt, 'Format', 'uuuu-MM-dd')) 
    time_as_string = string(datetime(dt, 'Format', 'HH:mm:ss')) 
    header_string = sprintf('Running FlyDiscoPipeline() with caboose-appropriate settings on %s at %s', date_as_string, time_as_string) 
    asterisks_string = repmat('*', [1 length(header_string)]) 
    fprintf('\n\n\n\n\n') 
    fprintf('%s\n', asterisks_string)     
    fprintf('%s\n', header_string) 
    fprintf('%s\n\n', asterisks_string)     
    
    # Convert param list to a struct
    overriding_analysis_parameters = struct_from_name_value_list(overriding_analysis_parameters_as_list) 

    # Build up the parameters cell array
    default_analysis_parameters = struct('settingsdir', {settings_folder_path}) 
    
    # Combine the caller-supplied analysis parameters with the defaults       
    analysis_parameters = merge_structs(default_analysis_parameters, overriding_analysis_parameters) 
    
    # Now turn off everything *except* the auto-checks-complete
    analysis_parameters.doautomaticchecksincoming = 'off' 
    analysis_parameters.doflytracking = 'off' 
    analysis_parameters.doregistration = 'off' 
    analysis_parameters.doledonoffdetection = 'off' 
    analysis_parameters.dosexclassification = 'off' 
    analysis_parameters.dotrackwings = 'off' 
    analysis_parameters.docomputeperframefeatures = 'off' 
    analysis_parameters.docomputehoghofperframefeatures = 'off' 
    analysis_parameters.dojaabadetect = 'off' 
    analysis_parameters.docomputeperframestats = 'off' 
    analysis_parameters.doplotperframestats = 'off' 
    analysis_parameters.domakectraxresultsmovie = 'off' 
    analysis_parameters.doextradiagnostics = 'off' 
    analysis_parameters.doanalysisprotocol = 'off' 
    
    # Call the def to do the real work
    FlyDiscoPipeline(experiment_folder_path, analysis_parameters) 
end
def goldblum_FlyDiscoPipeline_wrapper(experiment_folder_path, settings_folder_path, overriding_analysis_parameters_as_list)
    # This is the def that is submitted by goldblum to the bqueue to run each
    # experiment.
  
    # Handle arguments
    if ~exist('settings_folder_path', 'var') || isempty(settings_folder_path) :
        script_folder_path = os.path.dirname(mfilename('fullpath')) 
        fly_disco_analysis_folder_path = os.path.dirname(script_folder_path) 
        settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
    end
    if ~exist('overriding_analysis_parameters_as_list', 'var') || isempty(overriding_analysis_parameters_as_list) :
        overriding_analysis_parameters_as_list = cell(1, 0) 
    end

    # Print the date to the stdout, so it gets logged
    dt = datetime('now') 
    date_as_string = string(datetime(dt, 'Format', 'uuuu-MM-dd')) 
    time_as_string = string(datetime(dt, 'Format', 'HH:mm:ss')) 
    header_string = sprintf('Running FlyDiscoPipeline() on %s at %s', date_as_string, time_as_string) 
    asterisks_string = repmat('*', [1 length(header_string)]) 
    fprintf('\n\n\n\n\n') 
    fprintf('%s\n', asterisks_string)     
    fprintf('%s\n', header_string) 
    fprintf('%s\n\n', asterisks_string)     
    
    # Convert param list to a struct
    overriding_analysis_parameters = struct_from_name_value_list(overriding_analysis_parameters_as_list) 

    # Build up the parameters cell array
    default_analysis_parameters = struct('settingsdir', {settings_folder_path}) 
    
    # Combine the caller-supplied analysis parameters with the defaults       
    analysis_parameters = merge_structs(default_analysis_parameters, overriding_analysis_parameters) 
    
    # Now turn off the auto-checks-complete, we do that separately in goldblum
    analysis_parameters.doautomaticcheckscomplete = 'off' 
    
    # Call the def to do the real work
    FlyDiscoPipeline(experiment_folder_path, analysis_parameters) 
end
def goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, configuration)
    #GOLDBLUM Transfer FlyDisco experiment folders from rig computers and analyze them.
    #   goldblum() transfers FlyDisco experiment folders from the specified rig
    #   computers and analyzes them on an LSF cluster.  What rig computers to
    #   searched, and a variety of other settings, are determined from the username of
    #   the user running goldblum().    
    
    # Deal with arguments
    if ~exist('do_transfer_data_from_rigs', 'var') || isempty(do_transfer_data_from_rigs) :
        do_transfer_data_from_rigs = true 
    end
    if ~exist('do_run_analysis', 'var') || isempty(do_run_analysis) :
        do_run_analysis = true 
    end
    if ~exist('do_use_bqueue', 'var') || isempty(do_use_bqueue) :
        do_use_bqueue = true 
    end
    if ~exist('do_actually_submit_jobs', 'var') || isempty(do_actually_submit_jobs) :
        do_actually_submit_jobs = true 
    end
    if ~exist('analysis_parameters', 'var') || isempty(analysis_parameters) :
        analysis_parameters = cell(1,0) 
    end
    if ~exist('configuration', 'var') || isempty(configuration) :
        % Load the per-lab configuration file
        user_name = get_user_name() 
        configuration_def_name = sprintf('%s_configuration', user_name) 
        configuration = feval(configuration_def_name) 
    end
    
    # Unpack the per-lab configuration file
    cluster_billing_account_name = configuration.cluster_billing_account_name 
    host_name_from_rig_index = configuration.host_name_from_rig_index 
    rig_user_name_from_rig_index = configuration.rig_user_name_from_rig_index 
    data_folder_path_from_rig_index = configuration.data_folder_path_from_rig_index 
    destination_folder = configuration.destination_folder     
    settings_folder_path = configuration.settings_folder_path 
    #does_use_per_user_folders = configuration.does_use_per_user_folders 
    to_process_folder_name = 'to-process' 

    # Add a "banner" to the start of the log
    start_time_as_char = char(datetime('now','TimeZone','local','Format','y-MM-dd HH:mm Z')) 
    fprintf('\n') 
    fprintf('********************************************************************************\n') 
    fprintf('\n') 
    fprintf('Goldblum run starting at %s\n', start_time_as_char) 
    fprintf('\n') 
    fprintf('********************************************************************************\n') 
    fprintf('\n')     

    # Get info about the state of the repo, output to log
    this_script_path = mfilename('fullpath') 
    source_folder_path = os.path.dirname(os.path.dirname(this_script_path)) 
    git_report = get_git_report(source_folder_path) 
    fprintf('%s', git_report) 
    
#     % Convert e.g. flybowl-ww1.hhmi.org to flybowl-ww1    
#     short_host_name_from_rig_index = cellfun(@short_host_name_from_host_name, host_name_from_rig_index, 'UniformOutput', false) 
#     
#     % Destination folder is different for each rig, to avoid name collisions
#     destination_folder_from_rig_index = \
#         cellfun(@(short_host_name)(os.path.join(destination_folder, short_host_name)), \
#                 short_host_name_from_rig_index, \
#                 'UniformOutput', false) 
    
    # % Get the full path to the Python script that copies data from the rig machines
    # this_script_path = mfilename('fullpath') 
    # this_folder_path = os.path.dirname(this_script_path) 
    # sync_script_path = os.path.join(this_folder_path, 'remote_sync_and_delete_contents.py') 
    
    # For each rig, copy the data over to the Janelia filesystem, and delete the
    # original data
    if do_transfer_data_from_rigs :
        rig_count = length(host_name_from_rig_index) 
        for rig_index = 1 : rig_count :
            rig_host_name = host_name_from_rig_index{rig_index} 
            rig_user_name = rig_user_name_from_rig_index{rig_index} 
            lab_data_folder_path = data_folder_path_from_rig_index{rig_index} 

            try
                relative_path_from_synched_experiment_folder_index = \
                    remote_sync_verify_and_delete_experiment_folders(rig_user_name, \
                                                                     rig_host_name, \
                                                                     lab_data_folder_path, \
                                                                     destination_folder, \
                                                                     to_process_folder_name)                 
                add_links_to_to_process_folder(destination_folder, to_process_folder_name, relative_path_from_synched_experiment_folder_index) 
            except me 
                fprintf('There was a problem doing the sync from %s:%s as %s to %s:\n', \
                             rig_host_name, lab_data_folder_path, rig_user_name, destination_folder) 
                disp(me.getReport())     
            end                        
        end
    else
        fprintf('Skipping transfer of data from rigs.\n') 
    end
    
    # Run the analysis script on links in the to-process folder
    if do_run_analysis :
        % Get the links from the to_process_folder_name folder
        to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
        folder_name_from_experiment_index = simple_dir(to_process_folder_path) 
        link_path_from_experiment_index = \
            cellfun(@(folder_name)(os.path.join(to_process_folder_path, folder_name)), \
                                   folder_name_from_experiment_index, \
                                   'UniformOutput', false) 
        canonical_path_from_experiment_index = cellfun(@realpath, link_path_from_experiment_index, 'UniformOutput', false) 
        goldblum_analyze_experiment_folders(canonical_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                            do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
        
        % Whether those succeeded or failed, remove the links from the
        % to-process folder
        experiment_folder_count = length(link_path_from_experiment_index) 
        for i = 1 : experiment_folder_count :
            experiment_folder_link_path = link_path_from_experiment_index{i}  
            % experiment_folder_link_path is almost certainly a symlink, but check
            % anyway
            if is_symbolic_link(experiment_folder_link_path) :
                delete(experiment_folder_link_path) 
            end
        end
    else
        fprintf('Skipping analysis.\n') 
    end       
    
    # Want the start and end of a single goldblum run to be clear in the log
    fprintf('\n') 
    fprintf('********************************************************************************\n') 
    fprintf('\n') 
    fprintf('Goldblum run started at %s is ending\n', start_time_as_char) 
    fprintf('\n') 
    fprintf('********************************************************************************\n') 
    fprintf('\n')     
end
def result = is_an_analysis_protocol_folder(folder_name)
    if exist(folder_name, 'dir') :
        putative_dataloc_params_txt_file_name = os.path.join(folder_name, 'dataloc_params.txt') 
        result = logical( exist(putative_dataloc_params_txt_file_name, 'file') ) 
    else
        result = false 
    end
end
def result = is_experiment_folder_given_contents(file_names)
    lowercase_file_names = lower(file_names) 
    # We check for three files.  If two or more are present, we consider it an
    # experiment folder
    has_movie_file = ( ismember('movie.ufmf', lowercase_file_names) || ismember('movie.avi', lowercase_file_names) ) 
    point_count = \
        double(has_movie_file) + \
        double(ismember('metadata.xml', lowercase_file_names)) + \
        double(ismember('ABORTED', file_names)) 
    result = ( point_count >= 2) 
end
def result = is_experiment_folder_path(path) 
    putative_ufmf_file_path = os.path.join(path, 'movie.ufmf') 
    if exist(putative_ufmf_file_path, 'file') :
        result = true 
        return
    end
    putative_avi_file_path = os.path.join(path, 'movie.avi') 
    if exist(putative_avi_file_path, 'file') :
        result = true 
        return
    end    
    result = false 
end
def retval=is_filename_absolute(filename)

    # If you do x=os.path.dirname(x) until you reach steady-state:
    # the steady-state x will be empty if and only if the initial x is relative.
    # If absolute, the steady-state x will be "/" on Unix-like OSes, and
    # something like "C:\" on Windows.
    #
    # Note that this will return true for the empty string.  This may be
    # convoversial.  But, you know: garbage in, garbage out.
    
    path=filename
    parent=os.path.dirname(path)
    while ~strcmp(path,parent)
        path=parent
        parent=os.path.dirname(path)
    end
    # at this point path==parent
    retval=~isempty(path)

end
def result = is_symbolic_link(path)
    escaped_path = escape_string_for_bash(path) 
    command_line = sprintf('test -L %s', escaped_path) 
    retval = system(command_line) 
    result = (retval==0) 
end
def [file_names, file_sizes_in_bytes, is_file, is_dir, is_link, mod_time] = list_remote_dir(source_user, source_host, source_path) 
    escaped_source_path = escape_path_for_bash(source_path) 
    remote_ls_command_line = horzcat('ls -l -A -U -Q --full-time -- ', escaped_source_path) 
    command_line = horzcat('ssh ', source_user, '@', source_host, ' ', remote_ls_command_line) 
    [return_code, stdout] = system(command_line) 
    if return_code ~= 0 :
        error('list_remote_dir:failed', 'Unable to list the directory %s as user %s on host %s', source_path, source_user, source_host)
    end
    lines_raw = splitlines(strtrim(stdout)) 
    lines = lines_raw(2:end)  % drop 1st line
    line_count = length(lines) 
    file_names = cell(line_count, 1) 
    file_sizes_in_bytes = zeros(line_count, 1) 
    is_file = false(line_count, 1) 
    is_dir = false(line_count, 1) 
    is_link = false(line_count, 1) 
    mod_time = NaT(line_count, 1, 'TimeZone', 'UTC') 
    for i = 1 : line_count :
        line = lines{i} 
        [name, size_in_bytes, is_file_this, is_dir_this, is_link_this, mod_time_this] = extract_name_size_and_type_from_ls_long_line(line) 
        file_names{i} = name 
        file_sizes_in_bytes(i) = size_in_bytes 
        is_file(i) = is_file_this 
        is_dir(i) = is_dir_this 
        is_link(i) = is_link_this 
        mod_time(i) = mod_time_this 
    end
end
def [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
        local_verify_helper(source_parent_path, dest_parent_path, n_files_verified, n_dirs_verified, n_file_bytes_verified, spinner) 
    # get a list of all files and dirs in the source, dest dirs
    [name_from_source_entry_index, is_folder_from_source_entry_index, size_from_source_entry_index, mod_datetime_from_source_entry_index] = \
        simple_dir(source_parent_path) 
    is_file_from_source_entry_index = ~is_folder_from_source_entry_index 
    [name_from_dest_entry_index, is_folder_from_dest_entry_index, size_from_dest_entry_index, mod_datetime_from_dest_entry_index] = \
        simple_dir(dest_parent_path) 
    is_file_from_dest_entry_index = ~is_folder_from_dest_entry_index 
    
    # separate source file, dir names (ignore links)
    name_from_source_file_index = name_from_source_entry_index(is_file_from_source_entry_index) 
    size_from_source_file_index = size_from_source_entry_index(is_file_from_source_entry_index) 
    mod_datetime_from_source_file_index = mod_datetime_from_source_entry_index(is_file_from_source_entry_index) 
    name_from_source_folder_index = name_from_source_entry_index(is_folder_from_source_entry_index) 
        
    # separate dest file, dir names
    name_from_dest_folder_index = name_from_dest_entry_index(is_folder_from_dest_entry_index)     
    name_from_dest_file_index = name_from_dest_entry_index(is_file_from_dest_entry_index)     
    size_from_dest_file_index = size_from_dest_entry_index(is_file_from_dest_entry_index) 
    mod_datetime_from_dest_file_index = mod_datetime_from_dest_entry_index(is_file_from_dest_entry_index) 
    
    # verify that all files in source are also in dest
    are_all_source_files_in_dest = isempty(setdiff(name_from_source_file_index, name_from_dest_file_index)) 
    if ~are_all_source_files_in_dest :
        error('The local files in %s do not include all the remote files in %s', dest_parent_path, source_parent_path) 
    end
    
    # scan the source files, compute the md5sum, compare to that for the dest file
    for source_file_index = 1 : length(name_from_source_file_index) :
        file_name = name_from_source_file_index{source_file_index} 
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name)         
        source_file_size = size_from_source_file_index(source_file_index) 
        dest_file_index = find(strcmp(file_name, name_from_dest_file_index))         
        dest_file_size = size_from_dest_file_index(dest_file_index) 
        spinner.spin() 
        if dest_file_size == source_file_size :
            source_mod_datetime = mod_datetime_from_source_file_index(source_file_index) 
            dest_mod_datetime = mod_datetime_from_dest_file_index(dest_file_index) 
            if ( source_mod_datetime < dest_mod_datetime ) :
                % Compare hashes
                source_hex_digest = compute_md5_on_local(source_file_path) 
                dest_hex_digest = compute_md5_on_local(dest_file_path) 
                is_file_verified = isequal(source_hex_digest, dest_hex_digest) 
            else 
                is_file_verified = false 
            end
        else 
            is_file_verified = false 
        end
        
        if is_file_verified :
            n_files_verified = n_files_verified + 1 
            n_file_bytes_verified = n_file_bytes_verified + source_file_size 
        else
            error("There is a problem with destination file %s: It's missing, or the wrong size, or the hashes don't match.", \
                  dest_file_path) 
        end
    end

    # Verify that all source folders are in destination
    are_all_source_files_in_dest = isempty(setdiff(name_from_source_folder_index, name_from_dest_folder_index)) 
    if are_all_source_files_in_dest :
        n_dirs_verified = n_dirs_verified + length(name_from_source_folder_index) 
    else
        error('The destination folder names in %s do not include all the source folder names in %s', dest_parent_path, source_parent_path) 
    end
    
    # for each source folder, recurse
    for i = 1 : length(name_from_source_folder_index) :
        folder_name = name_from_source_folder_index{i} 
        source_folder_path = os.path.join(source_parent_path, folder_name) 
        dest_folder_path = os.path.join(dest_parent_path, folder_name)                 
        [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
             local_verify_helper(source_folder_path, \
                                 dest_folder_path, \
                                 n_files_verified, \
                                 n_dirs_verified, \ 
                                 n_file_bytes_verified, \
                                 spinner) 
    end
end
def local_verify(source_path, dest_path)
    # record the start time
    tic_id = tic() 

    # print an informative message
    fprintf("Verifying that contents of\n%s\nare also present in\n%s\n\ ", source_path, dest_path) 
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
        local_verify_helper(source_path, dest_path, 0, 0, 0, spinner) 
    spinner.stop()     
    
    # print the number of files etc verified
    fprintf("%d files verified\n", n_files_verified) 
    fprintf("%d folders verified\n", n_dirs_verified) 
    fprintf("%d file bytes verified\n", n_file_bytes_verified) 
    fprintf("Success: All files and folders in source are present in destination.\n")

    # print the elapsed time
    elapsed_time = toc(tic_id) 
    fprintf("Elapsed time: %0.1f seconds\n", elapsed_time) 
end
input_folder_path = \
    os.path.join('/groups/branson/bransonlab/taylora/flydisco/experiments', \
             'emptysplit_20xUAS-ChrimsonRmVenusattp18_flyBowlMing_nopause_lengthofpersis_2min_10int_20191218T093239_2') 
output_folder_path = 'emptysplit_20xUAS-ChrimsonRmVenusattp18_flyBowlMing_nopause_lengthofpersis_2min_10int_20191218T093239_2_shortened' 

if ~exist(output_folder_path, 'file') :
  mkdir(output_folder_path) 
end

file_names_to_copy = {'metaData.xml', 'protocol.mat'} 
for i = 1 : length(file_names_to_copy) :
  file_name = file_names_to_copy{i} 
  source_path = os.path.join(input_folder_path, file_name) 
  target_path = os.path.join(output_folder_path, file_name) 
  if exist(target_path, 'file') :
    delete(target_path) 
  end
  copyfile(source_path, target_path) 
end

video_file_name = 'movie.ufmf' 
source_video_path = os.path.join(input_folder_path, video_file_name) 
target_video_path = os.path.join(output_folder_path, video_file_name) 

if exist(target_video_path, 'file') :
  delete(target_video_path) 
end

desired_frame_count = 2000 
shorten_ufmf(source_video_path, target_video_path, desired_frame_count) 



# try to read frames from the resulting file
header = ufmf_read_header(target_video_path) 
def modpath()
  % Add needed libraries to Matlab path
  
  path_to_this_script = mfilename('fullpath') 
  path_to_this_folder = os.path.dirname(path_to_this_script) 
  
#   % Run the FlyBowlAnalysis modpath script
#   fly_bowl_analysis_folder_path = os.path.join(path_to_this_folder, 'FlyDiscoAnalysis') 
#   fly_bowl_analysis_modpath_script_path = os.path.join(fly_bowl_analysis_folder_path, 'modpath.m') 
#   run(fly_bowl_analysis_modpath_script_path)   
  
  % Add the fuster folder
  addpath(os.path.join(path_to_this_folder, 'fuster')) 
  
  % Add this folder
  addpath(path_to_this_folder)   % do this so that we don't have to stay in this folder
  % Also useful b/c this file may be called from elsewhere
  def result = parse_simple_yaml_file(file_name)
    # Parse a file that is a list of field_name : value pairs, one per line.
    # Return the result in a flattened cell array of field_name, value pairs.  
    
    lines = read_file_into_cellstring(file_name) 
    result = cell(1,0) 
    for i = 1 : length(lines) :
        raw_line = lines{i} 
        line  = strtrim(raw_line) 
        if isempty(line) :
            continue
        end        
        colon_indices = strfind(line, ':') 
        if isempty(colon_indices) :
            error('At line %d: Unable to parse "%s"', i, raw_line) 
        end
        colon_index = colon_indices(1) 
        raw_field_name = line(1:(colon_index-1)) 
        if length(line) < colon_index+1 :
            error('At line %d: Unable to parse "%s"', i, raw_line) 
        end            
        raw_value_as_string = line((colon_index+1):end) 
        field_name = strtrim(raw_field_name) 
        field_value_as_string = strtrim(raw_value_as_string) 
        value = eval(field_value_as_string)   % risky
        result = horzcat(result, {field_name, value})   %#ok<AGROW>
    end
end
classdef path_object
    properties
        list_
        is_relative_
    end
    
    methods
        def self = path_object(varargin)
            if nargin==1 :
                path = varargin{1} 
                if isempty(path) :
                    error('path cannot be empty') 
                end
                if isequal(path(1), '/') :
                    self.is_relative_ = false 
                    if length(path)==1 :
                        normed_path = '' 
                    else
                        normed_path = path 
                    end
                else
                    self.is_relative_ = true 
                    normed_path = horzcat('/', path) 
                end
                self.list_ = list_from_normed_path(normed_path) 
            else
                self.list_ = varargin{1} 
                self.is_relative_ = varargin{2} 
            end
        end
        
        def result = list(self) 
            result = self.list_ 
        end
        
        def result = is_relative(self) 
            result = self.is_relative_ 
        end
        
        def result = is_absolute(self) 
            result = ~self.is_relative_ 
        end        
        
        def result = to_char(self)
            normed_path = normed_path_from_list(self.list_) 
            if self.is_relative_ :
                result = normed_path(2:end) 
            else
                result = normed_path 
            end
        end

        def result = cat(self, other)
            if is_absolute(other) :
                error('2nd argument can''t be an absolute path') 
            end
            result = path_object(horzcat(list(self), list(other)), \             
                                 is_relative(self)) 
        end
        
        def result = relpath(self, start)
            if ischar(start) :
                start_path_object = path_object(start) 
            else
                start_path_object = start 
            end
            if is_absolute(start_path_object) ~= is_absolute(self):
                error('start and self must both be absolute or both relative') 
            end
            result = path_object(relpath_helper(list(self), list(start_path_object)), \
                                 true)   % result is always relative            
        end
    end
end



def result = list_from_normed_path(normed_path) 
    if isequal(normed_path, '/') :
        result = cell(1,0) 
    else        
        [parent, name] = os.path.dirname2(normed_path) 
        result = horzcat(list_from_normed_path(parent), {name}) 
    end
end



def result = normed_path_from_list(list)
    if isempty(list) :
        result = '' 
    else
        head = list{1} 
        tail = list(2:end) 
        result = horzcat('/', head, normed_path_from_list(tail)) 
    end
end



def result = relpath_helper(list, start_list)
    if isempty(start_list) :
        result = list 
    else
        if isempty(list) :
            error('start_list is not a prefix of list') 
        else
            list_head = list{1} 
            start_list_head = start_list{1} 
            if isequal(list_head, start_list_head) :
                result = relpath_helper(list(2:end), start_list(2:end)) 
            else
                error('start_list is not a prefix of list') 
            end
        end
    end
end
def result = projtechreslab_configuration()
    result = struct() 
    result.cluster_billing_account_name = 'projtechres' 
    result.host_name_from_rig_index = {'flybowl-ww1.hhmi.org'} 
    result.rig_user_name_from_rig_index = {'labadmin'} 
    result.data_folder_path_from_rig_index = {'/cygdrive/e/flydisco_data/projtechres'} 
    result.destination_folder = '/groups/projtechres/projtechres/flydisco_data' 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    flydisco_analysis_path = os.path.dirname(this_folder_path) 
    result.settings_folder_path = os.path.join(flydisco_analysis_path, 'settings') 
    result.does_have_per_user_folders = true 
end
def push_goldblum_into_production_for_branson()
    push_goldblum_into_production('bransonlab') 
end
def push_goldblum_into_production_for_branson_rubin()
    push_goldblum_into_production({'bransonlab', 'rubinlab'}) 
end
def push_goldblum_into_production_for_testing()
    # Determine the FlyDiscoAnalysis folder path
    goldblum_folder_path = os.path.dirname(mfilename('fullpath')) 
    fda_folder_path = os.path.dirname(goldblum_folder_path) 
    
    # Make sure there are no uncommitted changes
    error_if_uncommited_changes(fda_folder_path) 
    
#     % Do Branson Lab instance
#     copy_to_single_user_account('bransonlab', fda_folder_path) 
#     
#     % Do Rubin Lab instance
#     copy_to_single_user_account('rubinlab', fda_folder_path) 

    # Do PTR instance
    copy_to_single_user_account('projtechreslab', fda_folder_path) 

    # Do GENIE instance
    copy_to_single_user_account('geniegeneric', fda_folder_path) 

    # If get here, everything went well
    fprintf('Successfully copied %s into all the *lab user accounts\n', fda_folder_path) 
end



def copy_to_single_user_account(user_name, fda_folder_path)
    # Copy the folder over
    host_name = 'login2'   % Why not?
    fprintf('Copying into the %s user account\', user_name) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'rm', '-rf', 'FlyDiscoAnalysis'}) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'cp', '-R', '-T', fda_folder_path, 'FlyDiscoAnalysis'}) 
    fprintf('done.\n') 
end
def push_goldblum_into_production(account_name_from_lab_index)
    # Deal with arguments
    if ~exist('account_name_from_lab_index', 'var') || isempty(account_name_from_lab_index) :
        % If no arg, do all labs
        account_name_from_lab_index = { 'bransonlab', 'rubinlab', 'projtechreslab', 'geniegeneric' } 
    end
    
    # If char arg, convert to cellstring
    if ischar(account_name_from_lab_index) :
        account_name_from_lab_index = { account_name_from_lab_index } 
    end
    
    # Determine the FlyDiscoAnalysis folder path
    goldblum_folder_path = os.path.dirname(mfilename('fullpath')) 
    fda_folder_path = os.path.dirname(goldblum_folder_path) 
    
    # Make sure there are no uncommitted changes
    error_if_uncommited_changes(fda_folder_path) 
    
    # Do each lab
    cellfun(@(account_name)(copy_to_single_user_account(account_name, fda_folder_path)), \
            account_name_from_lab_index) 

    # If get here, everything went well
    fprintf('Successfully copied %s into all the specified user accounts\n', fda_folder_path) 
end



def copy_to_single_user_account(user_name, fda_folder_path)
    # Copy the folder over
    host_name = 'login2'   % Why not?
    fprintf('Copying into the %s user account\', user_name) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'rm', '-rf', 'FlyDiscoAnalysis'}) 
    remote_system_from_list_with_error_handling(user_name, host_name, {'cp', '-R', '-T', fda_folder_path, 'FlyDiscoAnalysis'}) 
    fprintf('done.\n') 
end
def result = read_file_into_cellstring(file_name)
    fid = fopen(file_name, 'rt') 
    if fid<0 :
        error('Unable to open file %s for reading', file_name) 
    end
    cleaner = onCleanup(@()(fclose(fid))) 
    result = cell(0,1) 
    line = fgetl(fid) 
    while ischar(line) :
        result = vertcat(result, \
                         {line})   %#ok<AGROW>
        line = fgetl(fid) 
    end
end
def result = relpath(path, start_path)
    if ~exist('start_path', 'var') || isempty(start_path) :
        start_path = pwd() 
    end
    path_as_object = path_object(path) 
    start_path_as_object = path_object(start_path) 
    result_as_path_object = relpath(path_as_object, start_path_as_object) 
    result = to_char(result_as_path_object) 
end
def remote_sync_and_verify_and_delete_contents(source_user, source_host, source_path, dest_path, does_use_per_user_folders)
    remote_sync_and_verify(source_user, source_host, source_path, dest_path) 
    delete_stuff_in_rig_data_folder(source_user, source_host, source_path, does_use_per_user_folders) 
end
def remote_sync_and_verify_and_delete(source_user_name, source_host_name, source_path, dest_path) 
    # Synch the destination folder to the source folder
    remote_sync(source_user_name, source_host_name, source_path, dest_path) 

    # Now verify that that worked (will raise an exception if verification fails)
    remote_verify(source_user_name, source_host_name, source_path, dest_path) 
    
    # Finally, delete the remote folder
    delete_remote_folder(source_user_name, source_host_name, source_path) 
end
def remote_sync_and_verify(source_user, source_host, source_path, dest_path) 
    # Call the def that does the real work
    remote_sync(source_user, source_host, source_path, dest_path) 

    # Now verify that that worked (will raise an exception if verification fails)
    remote_verify(source_user, source_host, source_path, dest_path) 
end
def [n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying] = \
        remote_sync_helper(source_user, \
                           source_host, \
                           source_parent_path, \
                           dest_parent_path, \
                           n_copied, \
                           n_failed, \
                           n_dir_failed, \
                           n_verified, \
                           n_dir_failed_to_list, \
                           time_spent_copying, \
                           spinner) 
    # get a list of all files and dirs in the source, dest dirs
    try
        [source_entries, source_entry_sizes, is_source_entry_a_file, is_source_entry_a_dir, ~, source_entry_mod_times] = \
            list_remote_dir(source_user, source_host, source_parent_path) 
    except me :
        % if we can't list the dir, warn but continue
        if isequal(me.identifier, 'list_remote_dir:failed') :
            spinner.print("Warning: can't list path %s on host %s as user %s", source_path, source_host, source_user) 
            spinner.print("%s", me.getReport()) 
            n_dir_failed_to_list = n_dir_failed_to_list + 1 
            return
        else
            rethrow(me) 
        end
    end
    [dest_entries, is_dest_entry_a_folder, dest_file_size, dest_file_mtimes] = simple_dir(dest_parent_path) 
    
    # separate source file, dir names (ignore links)
    source_file_names = source_entries(is_source_entry_a_file) 
    source_file_sizes = source_entry_sizes(is_source_entry_a_file) 
    source_file_mod_times = source_entry_mod_times(is_source_entry_a_file) 
    source_folder_names = source_entries(is_source_entry_a_dir) 
        
    # separate dest file, dir names
    dest_folder_names = dest_entries(is_dest_entry_a_folder)     
    dest_file_names = dest_entries(~is_dest_entry_a_folder)     
    size_from_dest_file_index = dest_file_size(~is_dest_entry_a_folder) 
    dest_file_mtimes = dest_file_mtimes(~is_dest_entry_a_folder) 
    
    # scan the source files, copy any that aren't in dest:
    # or that aren't up-to-date
    source_file_count = length(source_file_names) 
    for i = 1 : source_file_count :
        file_name = source_file_names{i} 
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name) 
        spinner.spin() 
        %print("  %s" % source_file)
        dest_file_index = find(strcmp(file_name, dest_file_names))         
        if ~isempty(dest_file_index) :
            source_file_size = source_file_sizes(i) 
            dest_file_size = size_from_dest_file_index(dest_file_index) 
            if dest_file_size == source_file_size :
                source_mod_time = source_file_mod_times(i) 
                dest_mod_time = dest_file_mtimes(i) 
                if source_mod_time < dest_mod_time :
                    % Compare hashes
                    source_hex_digest = compute_md5_on_remote(source_user, source_host, source_file_path) 
                    dest_hex_digest = compute_md5_on_local(dest_file_path) 
                    is_file_verified = isequal(source_hex_digest, dest_hex_digest) 
                else 
                    is_file_verified = false 
                end
            else 
                is_file_verified = false 
            end
        else
            is_file_verified = false 
        end

        if is_file_verified :
            n_verified = n_verified + 1 
        else 
            try 
                time_spent_copying = time_spent_copying + copy_file_from_remote(source_user, \
                                                                                source_host, \ 
                                                                                source_file_path, \
                                                                                dest_file_path) 
                n_copied = n_copied + 1 
            except me :
                % orginally except IOError
                % if we can't copy the file, warn but continue
                if isequal(me.identifier, 'copy_file_from_remote:failed') :
                    spinner.print('Warning: can''t copy %s',  source_file_path) 
                    spinner.print("%s", me.getReport()) 
                    n_failed = n_failed + 1 
                else
                    rethrow(me) 
                end
            end
        end
    end

#     % scan dest dirs, delete any that that aren't in source dirs
#     dest_dirs_as_set = set(dest_dirs)
#     source_dirs_as_set = set(source_dirs)
#     dest_dirs_not_in_source = dest_dirs_as_set - source_dirs_as_set 
#     for dest_dir in dest_dirs_not_in_source :
#         shutil.rmtree(os.path.join(dest_path,dest_dir),1)
    
    # scan source dirs, create any that that aren't in dest dirs
    source_folder_names_not_in_dest = setdiff(source_folder_names, dest_folder_names) 
    for i = 1 : length(source_folder_names_not_in_dest) :
        source_folder_name = source_folder_names_not_in_dest{i} 
        dest_folder_path = os.path.join(dest_parent_path, source_folder_name) 
        [did_succeed, message] = mkdir(dest_folder_path) 
        if ~did_succeed :
            % if we can't make the dir, warn but continue
            spinner.print("Warning: can't make directory %s, error message was: ", dest_folder_path, message) 
            n_dir_failed = n_dir_failed + 1 
        end
    end
    
    # need to re-generate dest dirs, because we may have failed to 
    # create some of them
    [dest_entries, is_dest_entry_a_folder] = simple_dir(dest_parent_path) 
    dest_folder_names = dest_entries(is_dest_entry_a_folder) 
    folder_names_to_recurse_into = intersect(source_folder_names, dest_folder_names) 
        
    # for each dir in both source_dirs and dest_folder_names, recurse
    for i = 1 : length(folder_names_to_recurse_into) :
        folder_name = folder_names_to_recurse_into{i} 
        [n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying] = \
             remote_sync_helper(source_user, \
                                source_host, \
                                os.path.join(source_parent_path, folder_name), \
                                os.path.join(dest_parent_path, folder_name), \
                                n_copied, \
                                n_failed, \
                                n_dir_failed, \
                                n_verified, \
                                n_dir_failed_to_list,  \
                                time_spent_copying, \
                                spinner) 
    end
end
def remote_sync(source_user, source_host, source_path, dest_path, be_verbose)
    # Deal with arguments
    if ~exist('be_verbose', 'var') || isempty(be_verbose) :
        be_verbose = false 
    end
    
    # record the start time
    tic_id = tic() 

    # if dest dir doesn't exist, create it
    if exist(dest_path, 'file') :
        % make sure it's a dir
        if ~exist(dest_path, 'dir') :
            error('Destination %s exists, but is a file, not a directory', dest_path)
        end
    else
        ensure_folder_exists(dest_path) 
    end
        
    # print an informative message
    if be_verbose :
        fprintf('Copying contents of\n%s@%s:%s\ninto\n%s\n\ ', source_user, source_host, source_path, dest_path) 
    end
    
    # call helper
    # All those zeros are the numbers of different kinds of failures so far
    if be_verbose :
        spinner = spinner_object() 
    else
        spinner = spinner_object('mute') 
    end
    [n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying] = \
        remote_sync_helper(source_user, source_host, source_path, dest_path, 0, 0, 0, 0, 0, 0.0, spinner)   %#ok<ASGLU>
    spinner.stop() 
    
    # print the number of files copied
    if n_failed==0 && n_dir_failed==0 && n_dir_failed_to_list==0 :
        if be_verbose :
            fprintf('Successfully copied contents of\n%s@%s:%s\ninto\n%s\n', source_user, source_host, source_path, dest_path) 
        end

        % print the elapsed time
        elapsed_time = toc(tic_id) 
        if be_verbose :
            fprintf("Elapsed time: %0.1f seconds\n", elapsed_time) 
            fprintf("Time spent copying: %0.1f seconds\n", time_spent_copying) 
        end
    else
        % throw an error if there were any failures
        error('remote_sync:did_fail', \
              'There was at least one failure during the remote sync: %d file copies failed, %d directory creates failed, %d directories failed to list', \ 
              n_failed, n_dir_failed, n_dir_failed_to_list) 
    end
end
def relative_path_from_synched_experiment_index = \
        remote_sync_verify_and_delete_experiment_folders(source_user_name, \
                                                         source_host_name, \
                                                         source_root_absolute_path, \
                                                         dest_root_absolute_path, \
                                                         to_process_folder_name)
    # Make sure the remote folder exists, return if not
    does_folder_exist = does_remote_file_exist(source_user_name, source_host_name, source_root_absolute_path) 
    if ~does_folder_exist :
        fprintf('Folder %s does not exist on host %s, so not searching for experiment folders in it.\n', source_root_absolute_path, source_host_name) 
        relative_path_from_synched_experiment_index = cell(0,1) 
        return
    end
    
    # record the start time
    tic_id = tic() 
        
    # print an informative message
    #fprintf('Searching for experiment folders in\n  %s@%s:%s\', source_user_name, source_host_name, source_root_absolute_path) 
    [relative_path_from_experiment_folder_index, is_aborted_from_experiment_folder_index] = \
        find_remote_experiment_folders(source_user_name, source_host_name, source_root_absolute_path, to_process_folder_name) 
    experiment_folder_count = length(relative_path_from_experiment_folder_index) 
    #fprintf("%d experiment folders found.\n" , experiment_folder_count) 
    
    # sort the aborted from unaborted experiments
    relative_path_from_aborted_experiment_folder_index = relative_path_from_experiment_folder_index(is_aborted_from_experiment_folder_index) 
    relative_path_from_unaborted_experiment_folder_index = relative_path_from_experiment_folder_index(~is_aborted_from_experiment_folder_index)     

    # print an informative message
    aborted_experiment_folder_count = length(relative_path_from_aborted_experiment_folder_index) 
    if aborted_experiment_folder_count==0 :
        % do nothing
    elseif aborted_experiment_folder_count==1 :
        fprintf('Deleting %d ABORTED experiment folder from\n  %s@%s:%s\n  \\n', \
                aborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path) 
    else 
        fprintf('Deleting %d ABORTED experiment folders from\n  %s@%s:%s\n  \\n', \
                aborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path) 
    end
    
    # Delete each experiment folder in turn
    did_delete_from_aborted_experiment_folder_index = false(experiment_folder_count, 1) 
    for i = 1 : aborted_experiment_folder_count :
        experiment_folder_relative_path = relative_path_from_aborted_experiment_folder_index{i} 
        source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
        try
            delete_remote_folder(source_user_name, source_host_name, source_folder_absolute_path) 
            did_delete_from_aborted_experiment_folder_index(i) = true 
        except me :
            fprintf('There was a problem during the deleting of ABORTED source experiment folder\n  %s\nThe problem was:\n%s\n', \ 
                    source_folder_absolute_path, \
                    me.getReport())     
        end            
    end

    # print the number of ABORTED experiment folders deleted
    deleted_aborted_experiment_folder_count = sum(double(did_delete_from_aborted_experiment_folder_index)) 
    delete_error_count = aborted_experiment_folder_count - deleted_aborted_experiment_folder_count 
    if aborted_experiment_folder_count > 0 :
        fprintf("Of %d ABORTED experiment folders:\n", aborted_experiment_folder_count) 
        fprintf("  %d deleted\n", deleted_aborted_experiment_folder_count) 
        fprintf("  %d failed to delete\n", delete_error_count) 
    end
    
    # print an informative message
    unaborted_experiment_folder_count = length(relative_path_from_unaborted_experiment_folder_index) 
    if unaborted_experiment_folder_count > 0 :
        fprintf('Synching %d experiment folders from\n  %s@%s:%s\n  into\n  %s\n  \\n', \
                unaborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path, dest_root_absolute_path) 
    end

    # Sync each experiment folder in turn
    did_synch_from_unaborted_experiment_folder_index = false(unaborted_experiment_folder_count, 1) 
    for i = 1 : unaborted_experiment_folder_count :
        experiment_folder_relative_path = relative_path_from_unaborted_experiment_folder_index{i} 
        source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
        dest_folder_absolute_path = os.path.join(dest_root_absolute_path, experiment_folder_relative_path) 
        try
            remote_sync_and_verify(source_user_name, \
                                   source_host_name, \
                                   source_folder_absolute_path, \
                                   dest_folder_absolute_path) 
            did_synch_from_unaborted_experiment_folder_index(i) = true 
        except me :
            fprintf('There was a problem during the synch of source experiment folder\n  %s\nThe problem was:\n%s\n', \ 
                    source_folder_absolute_path, \
                    me.getReport())     
        end            
    end

    # print the number of experiment folders copied
    synched_experiment_folder_count = sum(double(did_synch_from_unaborted_experiment_folder_index)) 
    synch_error_count = unaborted_experiment_folder_count - synched_experiment_folder_count 
    if unaborted_experiment_folder_count > 0 :
        fprintf("Of %d unaborted experiment folders:\n", unaborted_experiment_folder_count) 
        fprintf("  %d synched and verified\n", synched_experiment_folder_count) 
        fprintf("  %d failed to synch or verify\n", synch_error_count) 
    end
    
    # Delete each synched experiment folder in turn
    relative_path_from_synched_experiment_index = relative_path_from_unaborted_experiment_folder_index(did_synch_from_unaborted_experiment_folder_index) 
    synched_experiment_count = length(relative_path_from_synched_experiment_index) 
    did_delete_from_synched_experiment_index = false(synched_experiment_count, 1) 
    for i = 1 : unaborted_experiment_folder_count :
        if did_synch_from_unaborted_experiment_folder_index(i) :
            experiment_folder_relative_path = relative_path_from_unaborted_experiment_folder_index{i} 
            source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
            try
                delete_remote_folder(source_user_name, source_host_name, source_folder_absolute_path) 
                did_delete_from_synched_experiment_index(i) = true 
            except me :
                fprintf('There was a problem during the post-synch deletion of source experiment folder\n  %s\nThe problem was:\n%s\n', \
                    source_folder_absolute_path, \
                    me.getReport()) 
            end
        end
    end
    
    # print the number of experiment folders copied
    deleted_experiment_folder_count = sum(double(did_delete_from_synched_experiment_index)) 
    delete_error_count = synched_experiment_folder_count - deleted_experiment_folder_count 
    if synched_experiment_folder_count > 0 :
        fprintf("Of %d synched experiment folders:\n", synched_experiment_folder_count) 
        fprintf("  %d deleted\n", deleted_experiment_folder_count) 
        fprintf("  %d failed to delete\n", delete_error_count) 
    end

    # print the elapsed time
    elapsed_time = toc(tic_id) 
    fprintf("Total elapsed time: %0.1f seconds\n", elapsed_time) 
    
#     % throw an error if there were any failures
#     if synch_error_count > 0 || delete_error_count > 0 :
#         error("There was at least one failure during the synching of unaborted experiment folders from the remote host") 
#     end
    
    # Return the synched experiments, whether or not they were deleted
    relative_path_from_synched_experiment_index = relative_path_from_unaborted_experiment_folder_index(did_synch_from_unaborted_experiment_folder_index) 
end
def stdout = remote_system_from_list_with_error_handling(user_name, host_name, remote_command_line_as_list)
    # Run the system command, but taking a list of tokens rather than a string, and
    # running on a remote host.  Uses ssh, which needs to be set up for passowrdless
    # login as the indicated user.
    # Each element of command_line_as_list is escaped for bash, then composed into a
    # single string, then submitted to system_with_error_handling().
    
    # Escape all the elements of command_line_as_list
    escaped_remote_command_line_as_list = cellfun(@escape_string_for_bash, remote_command_line_as_list, 'UniformOutput', false) 
    
    # Build up the command line by adding space between elements
    remote_command_line = space_out(escaped_remote_command_line_as_list) 

    # Command line
    command_line_as_list = {'ssh', '-l', user_name, host_name, remote_command_line}  
    
    # Actually run the command
    stdout = system_from_list_with_error_handling(command_line_as_list) 
end



def result = space_out(list)
    result = '' 
    count = length(list) 
    for i = 1 : count :
        if i==1 :
            result = list{i} 
        else
            result = [result ' ' list{i}]   %#ok<AGROW>
        end 
    end
enddef [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
        remote_verify_helper(source_user, source_host, source_parent_path, dest_parent_path, n_files_verified, n_dirs_verified, n_file_bytes_verified, spinner) 
    # get a list of all files and dirs in the source, dest dirs
    [name_from_source_entry_index, \
     size_from_source_entry_index, \
     is_file_from_source_entry_index, \
     is_folder_from_source_entry_index, \
     ~, \
     mod_datetime_from_source_entry_index] = \
        list_remote_dir(source_user, source_host, source_parent_path) 
    [name_from_dest_entry_index, is_folder_from_dest_entry_index, size_from_dest_entry_index, mod_datetime_from_dest_entry_index] = \
        simple_dir(dest_parent_path) 
    
    # separate source file, dir names (ignore links)
    name_from_source_file_index = name_from_source_entry_index(is_file_from_source_entry_index) 
    size_from_source_file_index = size_from_source_entry_index(is_file_from_source_entry_index) 
    mod_datetime_from_source_file_index = mod_datetime_from_source_entry_index(is_file_from_source_entry_index) 
    name_from_source_folder_index = name_from_source_entry_index(is_folder_from_source_entry_index) 
        
    # separate dest file, dir names
    name_from_dest_folder_index = name_from_dest_entry_index(is_folder_from_dest_entry_index)     
    is_file_from_dest_entry_index = ~is_folder_from_dest_entry_index 
    name_from_dest_file_index = name_from_dest_entry_index(is_file_from_dest_entry_index)     
    size_from_dest_file_index = size_from_dest_entry_index(is_file_from_dest_entry_index) 
    mod_datetime_from_dest_file_index = mod_datetime_from_dest_entry_index(is_file_from_dest_entry_index) 
    
    # scan the source files, make sure they're all present in dest, with matching
    # hashes
    for source_file_index = 1 : length(name_from_source_file_index) :
        file_name = name_from_source_file_index{source_file_index} 
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name)         
        source_file_size = size_from_source_file_index(source_file_index) 
        dest_file_index = find(strcmp(file_name, name_from_dest_file_index))         
        if isempty(dest_file_index) :
            error("There is a problem with destination file %s: It's missing.", dest_file_path) 
        elseif isscalar(dest_file_index) :
            dest_file_size = size_from_dest_file_index(dest_file_index) 
            spinner.spin() 
            if dest_file_size == source_file_size :
                source_mod_datetime = mod_datetime_from_source_file_index(source_file_index) 
                dest_mod_datetime = mod_datetime_from_dest_file_index(dest_file_index) 
                if ( source_mod_datetime < dest_mod_datetime ) :
                    % Compare hashes
                    source_hex_digest = compute_md5_on_remote(source_user, source_host, source_file_path) 
                    dest_hex_digest = compute_md5_on_local(dest_file_path) 
                    if ~isequal(source_hex_digest, dest_hex_digest) :
                        error("There is a problem with destination file %s: Its hash is %s, but the source file hash is %s.", \
                            dest_file_path, dest_hex_digest, source_hex_digest) 
                    end
                else
                    error("There is a problem with destination file %s: Its modification time (%s )is before that of the source file (%s).", \
                        dest_file_path, char(dest_mod_datetime), char(source_mod_datetime) ) 
                end
            else
                error("There is a problem with destination file %s: Its size (%d bytes) differs from that of the source file (%d bytes).", \
                    dest_file_path, dest_file_size, source_file_size) 
            end
        else
            error('Something has gone horribly wrong in remote_verify_helper().  There seem to be two files with the same name (%s) in destination folder %s', \
                  file_name, dest_parent_path) 
        end
        
        % If we get here, destination file is present, it was modified after the source:
        % and the hashes match
        n_files_verified = n_files_verified + 1 
        n_file_bytes_verified = n_file_bytes_verified + source_file_size 
    end

    # Verify that all source folders are in destination
    for source_folder_index = 1 : length(name_from_source_folder_index) :
        folder_name = name_from_source_folder_index{source_folder_index} 
        if ~any(strcmp(folder_name, name_from_dest_folder_index)) :
            dest_folder_path = os.path.join(dest_parent_path, folder_name) 
            error("There is a problem with destination folder %s: It's missing.", dest_folder_path) 
        end
    end    
        
    # for each source folder, recurse
    for i = 1 : length(name_from_source_folder_index) :
        folder_name = name_from_source_folder_index{i} 
        source_folder_path = os.path.join(source_parent_path, folder_name) 
        dest_folder_path = os.path.join(dest_parent_path, folder_name)                 
        [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
             remote_verify_helper(source_user, \
                                  source_host, \
                                  source_folder_path, \
                                  dest_folder_path, \
                                  n_files_verified, \
                                  n_dirs_verified, \ 
                                  n_file_bytes_verified, \
                                  spinner) 
    end
end
def remote_verify(source_user, source_host, source_path, dest_path, be_verbose)
    # Deal with arguments
    if ~exist('be_verbose', 'var') || isempty(be_verbose) :
        be_verbose = false 
    end
    
    # record the start time
    tic_id = tic() 

    # print an informative message
    if be_verbose :
        fprintf('Verifying that contents of\n%s@%s:%s\nare present in\n%s\n\ ', source_user, source_host, source_path, dest_path) 
    end
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    if be_verbose :
        spinner = spinner_object() 
    else
        spinner = spinner_object('mute') 
    end        
    [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
        remote_verify_helper(source_user, source_host, source_path, dest_path, 0, 0, 0, spinner)   %#ok<ASGLU>  
            % this will throw if there's a verification failure
    spinner.stop()     
    
    # print the number of files etc verified
    #fprintf("%d files verified\n", n_files_verified) 
    #fprintf("%d folders verified\n", n_dirs_verified) 
    #fprintf("%d file bytes verified\n", n_file_bytes_verified) 
    if be_verbose :
        fprintf("Success: All files and folders in source are present in destination.\n")
    end

    # print the elapsed time
    elapsed_time = toc(tic_id) 
    if be_verbose :
        fprintf("Elapsed time: %0.1f seconds\n", elapsed_time) 
    end
end
def reset_experiment_working_copies(working_copy_experiments_folder_path, read_only_experiments_folder_path)
    if exist(working_copy_experiments_folder_path, 'file') :
        system_from_list_with_error_handling({'rm', '-rf', working_copy_experiments_folder_path}) 
    end
    system_from_list_with_error_handling( \
        {'cp', '--no-preserve=mode', '-R', '-T', read_only_experiments_folder_path, working_copy_experiments_folder_path} ) 
end
def reset_goldblum_example_experiments_working_copy_folder(example_experiment_folder_path, read_only_example_experiment_folder_path)
    if exist(example_experiment_folder_path, 'file') :
        system_from_list_with_error_handling({'rm', '-rf', example_experiment_folder_path}) 
    end
    system_from_list_with_error_handling( \
        {'cp', '--no-preserve=mode', '-R', '-T', read_only_example_experiment_folder_path, example_experiment_folder_path} ) 
end
def result = rubinlab_configuration()
    result = struct() 
    result.cluster_billing_account_name = 'rubin' 
    result.host_name_from_rig_index = {'flybowl-ww1.hhmi.org', 'flybowl-ww3.hhmi.org'} 
    result.rig_user_name_from_rig_index = {'labadmin', 'labadmin'} 
    result.data_folder_path_from_rig_index = {'/cygdrive/e/flydisco_data/rubin', '/cygdrive/e/flydisco_data/rubin'} 
    result.destination_folder = '/groups/rubin/data0/rubinlab/flydisco_data' 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    flydisco_analysis_path = os.path.dirname(this_folder_path) 
    result.settings_folder_path = os.path.join(flydisco_analysis_path, 'settings') 
    result.does_have_per_user_folders = true 
end
# Test by copying some experiments to a single Branson Lab rig machine, then
# using goldblum to suck the data back and analyze the experiments

# Set some options
do_use_bqueue = true 
do_actually_submit_jobs = true 
analysis_parameters = \
         {'forcecompute',false,\
          'doautomaticchecksincoming',true,\
          'doflytracking',true, \
          'doregistration',true,\
          'doledonoffdetection',false,\
          'dosexclassification',true,\
          'dotrackwings',false,\
          'docomputeperframefeatures',true,\
          'docomputehoghofperframefeatures',false,\
          'dojaabadetect',true,\
          'docomputeperframestats',false,\
          'doplotperframestats',false,\
          'domakectraxresultsmovie',true,\
          'doextradiagnostics',false,\
          'doanalysisprotocol',true,\
          'doautomaticcheckscomplete',false}

# Figure out where this script lives in the filesystem
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 

# This stuff goes into the per-lab configuration that goldblum uses
cluster_billing_account_name = 'branson' 
remote_host_name = 'arrowroot.hhmi.org' 
remote_host_name_from_rig_index = { remote_host_name } 
remote_user_name = 'bransonk' 
rig_user_name_from_rig_index = { remote_user_name } 
remote_data_root_folder_path = '/cygdrive/e/flydisco_data' 
data_folder_path_from_rig_index = {remote_data_root_folder_path} 
destination_folder_path = '/groups/branson/bransonlab/flydisco_data' 
settings_folder_path = os.path.join(this_folder_path, 'FlyDiscoAnalysis/settings') 
does_use_per_user_folders = false 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = remote_host_name_from_rig_index 
per_lab_configuration.rig_user_name_from_rig_index = rig_user_name_from_rig_index 
per_lab_configuration.data_folder_path_from_rig_index = data_folder_path_from_rig_index 
per_lab_configuration.destination_folder = destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
per_lab_configuration.does_use_per_user_folders = does_use_per_user_folders 

# Run goldblum
goldblum(do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Test by copying some experiments to a single Branson Lab rig machine, then
# using goldblum to suck the data back and analyze the experiments

# Set some options
do_transfer_data_from_rigs = true 
do_use_bqueue = true 
do_actually_submit_jobs = true 
analysis_parameters = \
         {'forcecompute',false,\
          'doautomaticchecksincoming',true,\
          'doflytracking',true, \
          'doregistration',true,\
          'doledonoffdetection',true,\
          'dosexclassification',true,\
          'dotrackwings',false,\
          'docomputeperframefeatures',true,\
          'docomputehoghofperframefeatures',false,\
          'dojaabadetect',true,\
          'docomputeperframestats',false,\
          'doplotperframestats',false,\
          'domakectraxresultsmovie',true,\
          'doextradiagnostics',false,\
          'doanalysisprotocol',true,\
          'doautomaticcheckscomplete',false}

# Figure out where this script lives in the filesystem
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 

# This stuff goes into the per-lab configuration that goldblum uses
cluster_billing_account_name = 'branson' 
remote_host_name_from_rig_index = { 'arrowroot.hhmi.org', 'beet.hhmi.org', 'carrot.hhmi.org', 'daikon.hhmi.org' } 
remote_user_name = 'bransonk' 
rig_user_name_from_rig_index = repmat({remote_user_name}, [1 4]) 
remote_data_root_folder_path = '/cygdrive/e/flydisco_data' 
data_folder_path_from_rig_index = repmat({remote_data_root_folder_path}, [1 4]) 
destination_folder_path = '/groups/branson/bransonlab/flydisco_data' 
settings_folder_path = os.path.join(this_folder_path, 'FlyDiscoAnalysis/settings') 
does_use_per_user_folders = false 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = remote_host_name_from_rig_index 
per_lab_configuration.rig_user_name_from_rig_index = rig_user_name_from_rig_index 
per_lab_configuration.data_folder_path_from_rig_index = data_folder_path_from_rig_index 
per_lab_configuration.destination_folder = destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
per_lab_configuration.does_use_per_user_folders = does_use_per_user_folders 

# Run goldblum
goldblum(do_transfer_data_from_rigs, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         
# Test by copying some experiments to a single Branson Lab rig machine, then
# using goldblum to suck the data back and analyze the experiments

# Set some options
do_use_bqueue = true 
do_actually_submit_jobs = true 
do_run_analysis_in_debug_mode = false 

# Figure out where this script lives in the filesystem
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 

# This is a folder with several "raw" experiment folders in it.
# We don't write to this folder, we only read from it.
analysis_test_template_folder_path = os.path.join(this_folder_path, 'analysis-test-template') 

# This stuff goes into the per-lab configuration that goldblum uses
cluster_billing_account_name = 'branson' 
remote_host_name = 'beet.hhmi.org' 
remote_host_name_from_rig_index = { remote_host_name } 
remote_user_name = 'bransonk' 
rig_user_name_from_rig_index = { remote_user_name } 
remote_data_root_folder_path = '/cygdrive/e/flydisco_data' 
data_folder_path_from_rig_index = {remote_data_root_folder_path} 
destination_folder_path = '/groups/branson/bransonlab/flydisco_data' 
settings_folder_path = os.path.join(this_folder_path, 'FlyDiscoAnalysis/settings') 
does_use_per_user_folders = false 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = remote_host_name_from_rig_index 
per_lab_configuration.rig_user_name_from_rig_index = rig_user_name_from_rig_index 
per_lab_configuration.data_folder_path_from_rig_index = data_folder_path_from_rig_index 
per_lab_configuration.destination_folder = destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
per_lab_configuration.does_use_per_user_folders = does_use_per_user_folders 

# Run goldblum
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

def stdout = run_in_sub_matlab(do_actually_shell_out, def_handle, varargin)
    # Call a matlab def by invoking a sub-matlab at the command line to execute
    # it.  Doesn't provide a way to get def return values, so only useful for
    # defs with side-effects.
    if do_actually_shell_out :
        def_name = func2str(def_handle) 
        arg_string = generate_arg_string(varargin{:}) 
        matlab_command = sprintf('modpath %s(%s)', def_name, arg_string) 
        %matlab_command = sprintf('%s(%s)', def_name, arg_string) 
        bash_command_as_list = {'matlab', '-batch', matlab_command} 
        stdout = system_from_list_with_error_handling(bash_command_as_list) 
    else
        % Just call the def normally
        feval(def_handle, varargin{:}) 
    end        
end



def result = tostring(thing)
    # Converts a range of things to strings that will eval to the thing
    if ischar(thing) :
        result = sprintf('''%s''', thing) 
    elseif isnumeric(thing) || islogical(thing) :
        result = mat2str(thing) 
    elseif isstruct(thing) && isscalar(thing) :
        result = 'struct(' 
        field_names = fieldnames(thing) 
        field_count = length(field_names) 
        for i = 1 : field_count :
            field_name = field_names{i} 
            field_value = thing.(field_name) 
            field_value_as_string = tostring(field_value) 
            subresult = sprintf('''%s'', {%s}', field_name, field_value_as_string) 
            result = horzcat(result, subresult)  %#ok<AGROW>
            if i<field_count :
                result = horzcat(result, ', ')  %#ok<AGROW>
            end            
        end
        result = horzcat(result, ')') 
    elseif iscell(thing) && (isempty(thing) || isvector(thing)) :
        if isempty(thing) :
            result = sprintf('cell(%d,%d)', size(thing,1), size(thing,2)) 
        else
            if iscolumn(thing) :
                separator = '' 
            else
                separator = ',' 
            end            
            result = '{ ' 
            element_count = length(thing) 
            for i = 1 : element_count :
                element_value = thing{i} 
                element_value_as_string = tostring(element_value) 
                result = horzcat(result, element_value_as_string)  %#ok<AGROW>
                if i<element_count :
                    result = horzcat(result, [separator ' '])  %#ok<AGROW>
                end            
            end
            result = horzcat(result, ' }') 
        end
    else
        error('Don''t know how to convert something of class %s to string', class(thing)) 
    end
end



def result = generate_arg_string(varargin) 
    arg_count = length(varargin) 
    result = char(1,0)   % fall-through in case of zero args
    for i = 1 : arg_count :
        this_arg = varargin{i} 
        this_arg_as_string = tostring(this_arg) 
        if i == 1 :
            result = this_arg_as_string 
        else
            result = horzcat(result, ', ', this_arg_as_string)   %#ok<AGROW>
        end
    end
end
def [experiment_dir_names, other_dir_names] = separate_experiment_folders_from_others(parent_path, source_dir_names) 
    is_experiment_dir = false(size(source_dir_names)) 
    for i = 1 : length(source_dir_names) :
        source_dir_name = source_dir_names{i} 
        is_experiment_dir(i) = is_experiment_folder_path(os.path.join(parent_path, source_dir_name)) 
    end
    experiment_dir_names = source_dir_names(is_experiment_dir) 
    other_dir_names = source_dir_names(~is_experiment_dir) 
end
def set_parpool_job_storage_location()
    # This def should be called before any PCT code is executed in a MATLAB session
    # (perhaps by a suitable startup.m file at MATLAB startup?). It will iterate over all
    # known profiles for the current user, and if they have a JobStorageLocation property
    # it will append the current process PID. This ensures that on a single machine all
    # JobStorageLocation's for the same scheduler will end up using different folders, which
    # allows them to all submit jobs at exactly the same time, without potential file name
    # clashes that would otherwise arise. NOTE that you will need to set the JobStorageLocation
    # of any subsequent MATLAB by hand if you want to retrieve the results of a job in about
    # different MATLAB session. Finally, if you want to make JobStorageLocation's unique
    # across multiple computers (rather than just within one computer) then it would be best
    # to change the uniqueEndingStr below to call 'tempname' and extract the final part.
    # That will ensure that even with PID reuse across multiple machines you still get about
    # unique string for each MATLAB.
    
    #   Copyright 2016 The MathWorks, Inc.

    try    
        % Check to see if PCT is installed. If not simply return early as there
        % is nothing to do.
        if ~exist('parpool','file')
            return 
        end

        % Make sure that this can run in normal MATLAB as well as deployed MCR's.
        % Some of the code below checks that we are in a deployed (or overriden)
        % MATLAB, so do this first.
        if ~(isdeployed || parallel.internal.settings.qeDeployedOverride)
            parallel.internal.settings.qeDeployedOverride(true)
        end

        % Using parallel.Settings find the scheduler component for each profile
        S = parallel.Settings
        profiles = S.findProfile

        % Make a string that should be host-and-process specific
        host_name = get_short_host_name() 
        data_location_folder_name = ['host-' host_name '-pid-' num2str(feature('getpid'))] 

        for index = 1:numel(profiles)

            sc = profiles(index).getSchedulerComponent

            % Check if the scheduler component has a JobStorageLocation property that
            % we need to append to. If not loop to the next scheduler component.
            if ~isprop(sc, 'JobStorageLocation')
                continue
            end

    #         % Get the value at the user level (in case you've already called this
    #         % def once and set the value at the session level)
    #         baseDir = get(sc, 'JobStorageLocation', 'user')
    #         
    #         % If it isn't a string we will create a specific local cluster which will
    #         % have the correct default location and append to that instead
    #         if ~ischar( baseDir )
    #             l = parallel.cluster.Local
    #             baseDir = l.JobStorageLocation
    #         end

            data_location_folder_path = os.path.join(get_scratch_folder_path(), data_location_folder_name) 

            % Directory must exist 
            % finish.m should probably take care of deleting this folder
            if ~exist(data_location_folder_path, 'dir')
                mkdir (data_location_folder_path)
            end

            % Importantly, we are only making the change to the settings at a session
            % level so that when we restart the system
            set(sc, 'JobStorageLocation', data_location_folder_path, 'session')
        end    
    except me
        fprintf('There was a problem during execution of the set_parpool_job_storage_location() def:\n') 
        fprintf('%s\n', me.getReport())     
    end
end
def result = short_host_name_from_host_name(host_name)
    parts = strsplit(host_name, '.') 
    if isempty(parts) :
        error('Unable to derive a short host name from host name "%s"'. host_name) 
    else
        first_part = parts{1} 
        if isempty(first_part) :
            error('Unable to derive a short host name from host name "%s"', host_name) 
        else
            result = first_part 
        end
    end            
end
classdef spinner_object < handle
    # Class for indicting progress
    properties (SetAccess = private)
        cursors_
        cursor_count_
        cursor_index_
        is_first_call_
        is_mute_
    end
    
    methods
        def self = spinner_object(varargin)
            self.cursors_ = '|/-\\' 
            self.cursor_count_ = length(self.cursors_) 
            self.cursor_index_ = 1 
            self.is_first_call_ = true 
            if nargin>=1 && strcmp(varargin{1}, 'mute') :
                self.is_mute_ = true 
            else
                self.is_mute_ = false 
            end
        end

        def spin(self)
            if ~self.is_mute_ :
                if self.is_first_call_ :
                    cursor = self.cursors_(self.cursor_index_) 
                    fprintf('%s', cursor) 
                    self.is_first_call_ = false 
                else
                    fprintf('\b')
                    self.cursor_index_ = (self.cursor_index_ + 1) 
                    if self.cursor_index_ > 4 :
                        self.cursor_index_ = 1 
                    end
                    cursor = self.cursors_(self.cursor_index_) 
                    fprintf('%s', cursor)
                end
            end
        end

        def print(self, varargin)
            % Want things printed during spinning to look nice
            if ~self.is_mute :
                fprintf('\b\n')   % Delete cursor, then newline
                fprintf(varargin{:})   % print whatever
                cursor = self.cursors_(self.cursor_index_)   % get the same cursor back
                fprintf('%s', cursor)   % write it again on its own line
            end
        end    

        def stop(self)
            if ~self.is_mute_ :
                fprintf('\bdone.\n')
            end
        end
    end
end
def result = taylora_configuration()
    result = struct() 
    result.cluster_billing_account_name = 'scicompsoft' 
    result.host_name_from_rig_index = {'flybowl-ww1.hhmi.org'} 
    result.rig_user_name_from_rig_index = {'labadmin'} 
    result.data_folder_path_from_rig_index = {'/cygdrive/h/flydisco_data/scicompsoft'} 
    result.destination_folder = '/groups/branson/bransonlab/taylora/flydisco/goldblum/goldblum-test-destination-folder'     
    result.settings_folder_path = '/groups/branson/bransonlab/taylora/flydisco/goldblum/FlyDiscoAnalysis/settings' 
    result.does_use_per_user_folders = true 
end
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_analysis_folder_path, 'test-experiments-read-only', 'circa-2021-07-rubin-experiments') 
working_experiments_folder_path = os.path.join(fly_disco_analysis_folder_path, 'test-experiments-working') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                           do_force_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
experiment_folder_path = \
  os.path.join('/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/goldblum/example-experiments-working-copy', \
           'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141')
settings_folder_path = '/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/settings' 

FlyDiscoPipeline(experiment_folder_path, struct('settingsdir', {settings_folder_path})) 
#reset_goldblum_example_experiments_working_copy_folder() 

this_script_file_path = mfilename('fullpath') 
this_script_folder_path = os.path.dirname(this_script_file_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_script_folder_path) 

settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 

analysis_parameters = \
        {'settingsdir', settings_folder_path, \
         'doautomaticchecksincoming',true,\
         'doflytracking',true,\
         'doregistration',true,\
         'doledonoffdetection',true,\
         'dotrackwings',true,\
         'dosexclassification',true,\
         'docomputeperframefeatures',true,\
         'docomputehoghofperframefeatures',false,\
         'dojaabadetect',true,\
         'docomputeperframestats',false,\
         'doplotperframestats',false,\
         'domakectraxresultsmovie',false,\
         'doextradiagnostics',false,\
         'doanalysisprotocol',false,\
         'doautomaticcheckscomplete',false } 

example_experiments_folder_path = \
    os.path.join(this_script_folder_path, \
             'example-experiments-working-copy')         
     
folder_name_from_experiment_index = simple_dir(example_experiments_folder_path) 
#do_run_from_experiment_index = true(size(folder_name_from_experiment_index))   % modify this to run a subset
do_run_from_experiment_index = logical([0 0 1 1])   % modify this to run a subset

experiment_count = length(folder_name_from_experiment_index) 
for experiment_index = 1 : experiment_count :
    do_run = do_run_from_experiment_index(experiment_index) 
    if do_run :
        experiment_folder_name = folder_name_from_experiment_index{experiment_index} 
        experiment_folder_path = os.path.join(example_experiments_folder_path, experiment_folder_name)          

        fprintf('\n\n\nRunning FlyDiscoPipeline() on %s \\n', experiment_folder_name) 

        % Call the def to do the real work
        FlyDiscoPipeline(experiment_folder_path, analysis_parameters{:}) 

#         % Report success/failure
#         if success :
#             fprintf('FlyDiscoPipeline() ran successfully on experiment %s !\n', experiment_folder_name) 
#         else
#             summary_message = sprintf('FlyDiscoPipeline() encountered one or more problems at stage %s for experiment %s:\n', stage, experiment_folder_name) 
#             for i = 1 : length(msgs) :
#                 this_msg = msgs{i} 
#                 fprintf('%s\n', this_msg) 
#             end
#             error(summary_message)   %#ok<SPERR>
#         end
    end
end
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'passing-test-suite-experiments-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'passing-test-suite-experiments') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = false 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-dickson-2021-06-28-experiment-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-dickson-2021-06-28-experiment') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_force_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-flybubble-red-nonoptogenetic-experiment-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-flybubble-red-nonoptogenetic-experiment') 

# % Delete the destination folder
# if exist(working_experiments_folder_path, 'file') :
#     return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
# end
# 
# % Recopy the test folder from the template
# fprintf('Resetting working experiments folder\\n') 
# reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 


                                                                
                                
                                
                                
                                
                                
cluster_billing_account_name = 'branson'
do_use_bqueue = false     
do_actually_submit_jobs = false   

#settings_folder_path = '/groups/branson/home/robiea/Code_versioned/FlyDiscoAnalysis/settings' 
#analysis_protocol = '20211014_flybubbleRed_LED'
analysis_parameters = {'doautomaticcheckscomplete','off'}   
  % b/c there's no settings/20210520_flybubblered_nochr_flytracker/automatic_checks_complete_params.txt
# analysis_parameters = {'analysis_protocol',analysis_protocol, \ 
#     'doautomaticchecksincoming','force',\
#     'doflytracking','on', \
#     'doregistration','on',\
#     'doledonoffdetection','on',\
#     'dosexclassification','on',\
#     'dotrackwings','off',\
#     'docomputeperframefeatures','on',\
#     'docomputehoghofperframefeatures','off',\
#     'dojaabadetect','off',\
#     'docomputeperframestats','off',\
#     'doplotperframestats','off',\
#     'domakectraxresultsmovie','on',\
#     'doextradiagnostics','off',\
#     'doanalysisprotocol',isunix,\
#     'doautomaticcheckscomplete','force'}

# folder_path_from_experiment_index = {'/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00030_CsChr_RigC_20150826T144616',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00038_CsChr_RigB_20150729T150617',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00168_CsChr_RigD_20150909T111218'}

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)                              
                                % This isn't a proper test b/c it doesn't check whether anything worked
do_nuke_working_folder = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-problem-experiment-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-problem-experiment') 

if do_nuke_working_folder :
    # Delete the destination folder
    if exist(working_experiments_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
    end

    # Recopy the test folder from the template
    fprintf('Resetting working experiments folder\\n') 
    reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 
end

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 


                                                                
                                
                                
                                
                                
                                
cluster_billing_account_name = 'branson'
do_use_bqueue = false     
do_actually_submit_jobs = false   

#settings_folder_path = '/groups/branson/home/robiea/Code_versioned/FlyDiscoAnalysis/settings' 
#analysis_protocol = '20211014_flybubbleRed_LED'
analysis_parameters = cell(1,0)   
  % b/c there's no settings/20210520_flybubblered_nochr_flytracker/automatic_checks_complete_params.txt
# analysis_parameters = {'analysis_protocol',analysis_protocol, \ 
#     'doautomaticchecksincoming','force',\
#     'doflytracking','on', \
#     'doregistration','on',\
#     'doledonoffdetection','on',\
#     'dosexclassification','on',\
#     'dotrackwings','off',\
#     'docomputeperframefeatures','on',\
#     'docomputehoghofperframefeatures','off',\
#     'dojaabadetect','off',\
#     'docomputeperframestats','off',\
#     'doplotperframestats','off',\
#     'domakectraxresultsmovie','on',\
#     'doextradiagnostics','off',\
#     'doanalysisprotocol',isunix,\
#     'doautomaticcheckscomplete','force'}

# folder_path_from_experiment_index = {'/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00030_CsChr_RigC_20150826T144616',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00038_CsChr_RigB_20150729T150617',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00168_CsChr_RigD_20150909T111218'}

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)                              
                                % This isn't a proper test b/c it doesn't check whether anything worked

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
#settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-robie-experiment-2022-03-06-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-robie-experiment-2022-03-06') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 


                                
                                
                                
                                
                                
                                
                                
cluster_billing_account_name = 'branson'
do_use_bqueue = false     
do_actually_submit_jobs = false   

settings_folder_path = '/groups/branson/home/robiea/Code_versioned/FlyDiscoAnalysis/settings' 
analysis_protocol = '20211014_flybubbleRed_LED'

analysis_parameters = {'analysis_protocol',analysis_protocol, \ 
    'doautomaticchecksincoming','force',\
    'doflytracking','on', \
    'doregistration','on',\
    'doledonoffdetection','on',\
    'dosexclassification','on',\
    'dotrackwings','off',\
    'docomputeperframefeatures','on',\
    'docomputehoghofperframefeatures','off',\
    'dojaabadetect','off',\
    'docomputeperframestats','off',\
    'doplotperframestats','off',\
    'domakectraxresultsmovie','on',\
    'doextradiagnostics','off',\
    'doanalysisprotocol',isunix,\
    'doautomaticcheckscomplete','force'}

# folder_path_from_experiment_index = {'/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00030_CsChr_RigC_20150826T144616',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00038_CsChr_RigB_20150729T150617',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00168_CsChr_RigD_20150909T111218'}

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)                              
                                % This isn't a proper test b/c it doesn't check whether anything worked

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
#settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-robie-experiment-2022-03-06-with-links-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-robie-experiment-2022-03-06-with-links') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 


                                
                                
                                
                                
                                
                                
                                
cluster_billing_account_name = 'branson'
do_use_bqueue = false     
do_actually_submit_jobs = false   

settings_folder_path = '/groups/branson/home/robiea/Code_versioned/FlyDiscoAnalysis/settings' 
analysis_protocol = '20211014_flybubbleRed_LED'

analysis_parameters = {'analysis_protocol',analysis_protocol, \ 
    'doautomaticchecksincoming','force',\
    'doflytracking','on', \
    'doregistration','on',\
    'doledonoffdetection','on',\
    'dosexclassification','on',\
    'dotrackwings','off',\
    'docomputeperframefeatures','on',\
    'docomputehoghofperframefeatures','off',\
    'dojaabadetect','off',\
    'docomputeperframestats','off',\
    'doplotperframestats','off',\
    'domakectraxresultsmovie','on',\
    'doextradiagnostics','off',\
    'doanalysisprotocol',isunix,\
    'doautomaticcheckscomplete','force'}

# folder_path_from_experiment_index = {'/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00030_CsChr_RigC_20150826T144616',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00038_CsChr_RigB_20150729T150617',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00168_CsChr_RigD_20150909T111218'}

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)                              
                                % This isn't a proper test b/c it doesn't check whether anything worked
do_nuke_working_folder = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-passing-test-suite-experiment-with-tracking-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-passing-test-suite-experiment-with-tracking') 

if do_nuke_working_folder :
    # Delete the destination folder
    if exist(working_experiments_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
    end

    # Recopy the test folder from the template
    fprintf('Resetting working experiments folder\\n') 
    reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 
end

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 


                                                                
                                
                                
                                
                                
                                
cluster_billing_account_name = 'branson'
do_use_bqueue = false     
do_actually_submit_jobs = false   

#settings_folder_path = '/groups/branson/home/robiea/Code_versioned/FlyDiscoAnalysis/settings' 
#analysis_protocol = '20211014_flybubbleRed_LED'
analysis_parameters = cell(1,0)   
  % b/c there's no settings/20210520_flybubblered_nochr_flytracker/automatic_checks_complete_params.txt
# analysis_parameters = {'analysis_protocol',analysis_protocol, \ 
#     'doautomaticchecksincoming','force',\
#     'doflytracking','on', \
#     'doregistration','on',\
#     'doledonoffdetection','on',\
#     'dosexclassification','on',\
#     'dotrackwings','off',\
#     'docomputeperframefeatures','on',\
#     'docomputehoghofperframefeatures','off',\
#     'dojaabadetect','off',\
#     'docomputeperframestats','off',\
#     'doplotperframestats','off',\
#     'domakectraxresultsmovie','on',\
#     'doextradiagnostics','off',\
#     'doanalysisprotocol',isunix,\
#     'doautomaticcheckscomplete','force'}

# folder_path_from_experiment_index = {'/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00030_CsChr_RigC_20150826T144616',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00038_CsChr_RigB_20150729T150617',\
# '/groups/branson/home/robiea/Projects_data/JAABA/Data_FlyBubble/FlyTracker/cx_GMR_SS00168_CsChr_RigD_20150909T111218'}

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)                              
                                % This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'passing-test-suite-experiments-with-tracking-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'passing-test-suite-experiments-with-tracking-single-namespace') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'alices-three-nonopto-flybubble-rgb-examples-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'alices-three-nonopto-flybubble-rgb-examples') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = false 
do_actually_submit_jobs = false 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-katie-experiment-2022-04-05-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-katie-experiment-2022-04-05') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = false 
do_actually_submit_jobs = false 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-katie-experiment-2022-04-05-with-tracking-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-katie-experiment-2022-04-05-with-tracking') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
# This isn't a proper test b/c it doesn't check whether anything worked

do_use_bqueue = true 
do_actually_submit_jobs = true 
cluster_billing_account_name = 'branson'   % used for billing the jobs
do_force_analysis = false 
analysis_parameters = cell(1,0) 
# analysis_parameters = \
#          {'doautomaticchecksincoming',true,\
#           'doflytracking',true, \
#           'doregistration',true,\
#           'doledonoffdetection',true,\
#           'dosexclassification',true,\
#           'dotrackwings',false,\
#           'docomputeperframefeatures',true,\
#           'docomputehoghofperframefeatures',false,\
#           'dojaabadetect',true,\
#           'docomputeperframestats',false,\
#           'doplotperframestats',false,\
#           'domakectraxresultsmovie',true,\
#           'doextradiagnostics',false,\
#           'doanalysisprotocol',true,\
#           'doautomaticcheckscomplete',false}

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
fly_disco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
read_only_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-TrpAFemale3-experiment-read-only') 
working_experiments_folder_path = os.path.join(fly_disco_folder_path, 'example-experiments', 'single-TrpAFemale3-experiment') 

# Delete the destination folder
if exist(working_experiments_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', working_experiments_folder_path}) 
end

# Recopy the test folder from the template
fprintf('Resetting working experiments folder\\n') 
reset_experiment_working_copies(working_experiments_folder_path, read_only_experiments_folder_path) 

# Find the experiments
folder_path_from_experiment_index = find_experiment_folders(working_experiments_folder_path) 

# Run the script under test
fprintf('Running goldblum_analyze_experiment_folders\\n') 
goldblum_analyze_experiment_folders(folder_path_from_experiment_index, settings_folder_path, cluster_billing_account_name, \
                                    do_use_bqueue, do_actually_submit_jobs, analysis_parameters)
reset_goldblum_example_experiments_working_copy_folder() 

this_script_file_path = mfilename('fullpath') 
this_script_folder_path = os.path.dirname(this_script_file_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_script_folder_path) 

settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 

analysis_parameters = \
        {'doautomaticchecksincoming',true,\
         'doflytracking',true,\
         'doregistration',true,\
         'doledonoffdetection',true,\
         'dotrackwings',true,\
         'dosexclassification',true,\
         'docomputeperframefeatures',true,\
         'docomputehoghofperframefeatures',false,\
         'dojaabadetect',true,\
         'docomputeperframestats',false,\
         'doplotperframestats',false,\
         'domakectraxresultsmovie',false,\
         'doextradiagnostics',false,\
         'doanalysisprotocol',false,\
         'doautomaticcheckscomplete',false } 

example_experiments_folder_path = \
    os.path.join(this_script_folder_path, \
             'example-experiments-working-copy')         

folder_path_from_experiment_index = find_experiment_folders(example_experiments_folder_path) 
# folder_path_from_experiment_index = \
#     { '/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/goldblum/example-experiments-working-copy/FlyBowlOpto/SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \ 
#       '/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/goldblum/example-experiments-working-copy/FlyBowlOpto/emptysplit_20xUAS-ChrimsonRmVenusattp18_flyBowlMing_nopause_lengthofpersis_2min_10int_20191218T093239_2'   , \
#       '/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/goldblum/example-experiments-working-copy/FlyBubbleRGB/LED/locomotionGtACR1_24_EXT_VGLUT-GAL4_RigA_20210226T095136'                                              , \
#       '/groups/branson/bransonlab/taylora/flydisco/FlyDiscoAnalysis/goldblum/example-experiments-working-copy/FlyBubbleRGB/noLED/locomotionGtACR1_emptySplit24b_RigB_20210216T105603'                                                } 
do_run_from_experiment_index = true(size(folder_path_from_experiment_index))   % modify this to run a subset

experiment_count = length(folder_path_from_experiment_index) 
for experiment_index = 1 : experiment_count :
    do_run = do_run_from_experiment_index(experiment_index) 
    if do_run :
        experiment_folder_path = folder_path_from_experiment_index{experiment_index} 
        [~,experiment_folder_name] = os.path.dirname2(experiment_folder_path) 

        fprintf('\n\n\nRunning goldblum_FlyDiscoPipeline_wrapper() on %s \\n', experiment_folder_name) 

        % Call the def to do the real work
        goldblum_FlyDiscoPipeline_wrapper(experiment_folder_path, settings_folder_path, analysis_parameters) 

        % If get here, must have worked
        fprintf('goldblum_FlyDiscoPipeline_wrapper() ran successfully on experiment %s !\n', experiment_folder_name) 
    end
end
def test_goldblum_launcher()    
    pi_last_name = 'branson' 
    configuration_def_name = sprintf('%s_configuration', pi_last_name) 
    configuration = feval(configuration_def_name) 
    
    destination_folder_path = configuration.destination_folder 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
    
    goldblum_logs_folder_path = os.path.join(destination_folder_path, 'goldblum-logs') 
    
    home_folder_path = getenv('HOME') 
    bash_profile_path = os.path.join(home_folder_path, '.bash_profile') 
    
    launcher_script_path = os.path.join(this_folder_path, 'goldblum_launcher.sh') 
    
    # Execute the command to turn on goldblum
    stdout = \
        system_from_list_with_error_handling({launcher_script_path, \
                                             bash_profile_path, \
                                             fly_disco_analysis_folder_path, \
                                             pi_last_name, \
                                             goldblum_logs_folder_path}) 
end
do_transfer_data_from_rigs = true 
do_run_analysis = true 
do_use_bqueue = true 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-passing-test-suite-experiment-with-tracking-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

# Delete the destination folder
if exist(goldblum_destination_folder_path, 'file') :
    return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
end

# % Recopy the analysis test folder from the template
# fprintf('Resetting analysis test folder\\n') 
# read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
# reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

# Copy it to the rig computer (or just direct to the destination folder)
if do_transfer_data_from_rigs :
    fprintf('Transfering data to the rig computer\\n')   %#ok<UNRCH>
    command_line = sprintf('scp -B -r %s/* %s@%s:%s', read_only_example_experiments_folder_path, rig_user_name, rig_host_name, rig_data_folder_path)  %#ok<UNRCH>
    system_with_error_handling(command_line) 
else
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line)   
      % Should make goldblum_destination_folder_path a clone of
      % example_experiments_folder_path, since we use -T option
    
    # Add symlinks to the to-process folder so that they will actually get processed
    folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
    to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
    ensure_folder_exists(to_process_folder_path) 
    experiment_count = length(folder_path_from_experiment_index) 
    for i = 1 : experiment_count :
        experiment_folder_path = folder_path_from_experiment_index{i} 
        command_line = {'ln', '-s', experiment_folder_path, to_process_folder_path} 
        system_from_list_with_error_handling(command_line) 
    end    
end

# Run goldblum
#analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
analysis_parameters = { } 
fprintf('Running goldblum\\n') 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Check that the rig lab folder is empty now
if do_transfer_data_from_rigs :
    relative_path_from_experiment_folder_index = \
        find_remote_experiment_folders(rig_user_name, rig_host_name, rig_data_folder_path, 'to-process') 
    if ~isempty(relative_path_from_experiment_folder_index) :
        error('Rig lab data folder %s:%s seems to still contain %d experiments', \
              rig_host_name, rig_data_folder_path, length(relative_path_from_experiment_folder_index)) 
    end
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# Check that the rig lab folder is empty now
if do_transfer_data_from_rigs :
    relative_path_from_experiment_folder_index = \
        find_remote_experiment_folders(rig_user_name, rig_host_name, rig_data_folder_path, 'to-process') 
    if ~isempty(relative_path_from_experiment_folder_index) :
        error('Rig lab data folder %s:%s seems to still contain %d experiments', \
              rig_host_name, rig_data_folder_path, length(relative_path_from_experiment_folder_index)) 
    end
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_use_bqueue = true 
do_actually_submit_jobs = true 
do_run_analysis_in_debug_mode = true 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = 'scicompsoft' 
per_lab_configuration.host_name_from_rig_index = {'flybowl-ww1.hhmi.org', 'flybowl-ww3.hhmi.org'} 
per_lab_configuration.rig_user_name_from_rig_index = {'labadmin', 'labadmin'} 
per_lab_configuration.data_folder_path_from_rig_index = {'/cygdrive/h/flydisco_data/scicompsoft' '/cygdrive/e/flydisco_data/scicompsoft'} 
per_lab_configuration.destination_folder = '/groups/branson/bransonlab/taylora/flydisco/goldblum/goldblum-test-destination-folder'     
per_lab_configuration.settings_folder_path = '/groups/branson/bransonlab/taylora/flydisco/goldblum/FlyDiscoAnalysis/settings' 
per_lab_configuration.does_use_per_user_folders = true 

this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
analysis_test_template_folder_path = os.path.join(this_folder_path, 'analysis-test-template') 

# Delete the destination folder
destination_folder_path = os.path.join(this_folder_path, 'goldblum-test-destination-folder') 
if exist(destination_folder_path, 'file') :
    return_code = system_with_error_handling(sprintf('rm -rf %s', destination_folder_path)) 
end

# Recopy the analysis test folder from the template
reset_analysis_test_folder() 

# Copy it to the rig computer(s)
remote_host_name = 'flybowl-ww1.hhmi.org' 
remote_user_folder_path = '/cygdrive/h/flydisco_data/scicompsoft/taylora' 
remote_user_name = 'labadmin' 
command_line = sprintf('scp -r %s %s@%s:%s', analysis_test_template_folder_path, remote_user_name, remote_host_name, remote_user_folder_path) 
system_with_error_handling(command_line) 

# Run goldblum
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
analysis_test_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
local_verify(analysis_test_template_folder_path, analysis_test_folder_destination_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(analysis_test_folder_destination_path, \
                 '2020-01-07', \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig user folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_user_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_user_folder_path) 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
analysis_test_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
local_verify(analysis_test_template_folder_path, analysis_test_folder_destination_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(analysis_test_folder_destination_path, \
                 '2020-01-07', \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig user folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_user_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_user_folder_path) 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
# Test by copying some experiments to a single Branson Lab rig machine, then
# using goldblum to suck the data back and analyze the experiments

# Set some options
do_use_bqueue = true 
do_actually_submit_jobs = true 
do_run_analysis_in_debug_mode = true 

# Figure out where this script lives in the filesystem
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 

# This is a folder with several "raw" experiment folders in it.
# We don't write to this folder, we only read from it.
analysis_test_template_folder_path = os.path.join(this_folder_path, 'analysis-test-template') 

# This stuff goes into the per-lab configuration that goldblum uses
cluster_billing_account_name = 'scicompsoft' 
remote_host_name = 'beet.hhmi.org' 
remote_host_name_from_rig_index = { remote_host_name } 
remote_user_name = 'bransonk' 
rig_user_name_from_rig_index = { remote_user_name } 
remote_data_root_folder_path = '/cygdrive/e/flydisco_data' 
data_folder_path_from_rig_index = {remote_data_root_folder_path} 
destination_folder_path = os.path.join(this_folder_path, 'goldblum-test-destination-folder')     
settings_folder_path = os.path.join(this_folder_path, 'FlyDiscoAnalysis/settings') 
does_use_per_user_folders = false 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = remote_host_name_from_rig_index 
per_lab_configuration.rig_user_name_from_rig_index = rig_user_name_from_rig_index 
per_lab_configuration.data_folder_path_from_rig_index = data_folder_path_from_rig_index 
per_lab_configuration.destination_folder = destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
per_lab_configuration.does_use_per_user_folders = does_use_per_user_folders 

# Delete the destination folder so we're starting fresh
if exist(destination_folder_path, 'file') :
    return_code = system_with_error_handling(sprintf('rm -rf %s', destination_folder_path)) 
end

# Delete the remote lab data folder
remote_experiments_folder_path = remote_data_root_folder_path 
escaped_remote_experiments_folder_path = escape_path_for_bash(remote_experiments_folder_path) 
command_line = sprintf('ssh %s@%s rm -rf %s', remote_user_name, remote_host_name, escaped_remote_experiments_folder_path) 
system_with_error_handling(command_line) 

# Create the remote lab data folder
command_line = sprintf('ssh %s@%s mkdir %s', remote_user_name, remote_host_name, escaped_remote_experiments_folder_path) 
system_with_error_handling(command_line) 

# % Recopy the analysis test folder from the template
# reset_analysis_test_folder() 

# Copy experiments to the rig computer
experiment_names = simple_dir(analysis_test_template_folder_path) 
for i = 1 : length(experiment_names) :
    experiment_name = experiment_names{i} 
    local_experiment_folder_path = os.path.join(analysis_test_template_folder_path, experiment_name) 
    command_line = sprintf('scp -r %s %s@%s:%s', local_experiment_folder_path, remote_user_name, remote_host_name, remote_experiments_folder_path) 
    system_with_error_handling(command_line) 
end

# Run goldblum
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(analysis_test_template_folder_path, destination_folder_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(destination_folder_path, \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig experiments folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_experiments_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_experiments_folder_path) 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(analysis_test_template_folder_path, destination_folder_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(destination_folder_path, \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig experiments folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_experiments_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_experiments_folder_path) 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_use_bqueue = true 
do_actually_submit_jobs = true 
do_run_analysis_in_debug_mode = true 

# Specify the "per-lab" configuration here
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = 'scicompsoft' 
per_lab_configuration.host_name_from_rig_index = {'flybowl-ww1.hhmi.org'} 
per_lab_configuration.rig_user_name_from_rig_index = {'labadmin'} 
per_lab_configuration.data_folder_path_from_rig_index = {'/cygdrive/h/flydisco_data/scicompsoft'} 
per_lab_configuration.destination_folder = '/groups/branson/bransonlab/taylora/flydisco/goldblum/goldblum-test-destination-folder'     
per_lab_configuration.settings_folder_path = '/groups/branson/bransonlab/taylora/flydisco/goldblum/FlyDiscoAnalysis/settings' 
per_lab_configuration.does_use_per_user_folders = true 

this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
analysis_test_template_folder_path = os.path.join(this_folder_path, 'analysis-test-template') 

# Delete the destination folder
destination_folder_path = os.path.join(this_folder_path, 'goldblum-test-destination-folder') 
if exist(destination_folder_path, 'file') :
    return_code = system_with_error_handling(sprintf('rm -rf %s', destination_folder_path)) 
end

# Recopy the analysis test folder from the template
reset_analysis_test_folder() 

# Copy it to the rig computer
remote_host_name = 'flybowl-ww1.hhmi.org' 
remote_user_folder_path = '/cygdrive/h/flydisco_data/scicompsoft/taylora' 
remote_user_name = 'labadmin' 
command_line = sprintf('scp -r %s %s@%s:%s', analysis_test_template_folder_path, remote_user_name, remote_host_name, remote_user_folder_path) 
system_with_error_handling(command_line) 

# Run goldblum
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
analysis_test_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
local_verify(analysis_test_template_folder_path, analysis_test_folder_destination_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(analysis_test_folder_destination_path, \
                 '2020-01-07', \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig user folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_user_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_user_folder_path) 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_use_bqueue, do_actually_submit_jobs, do_run_analysis_in_debug_mode, per_lab_configuration)         

# Check that the expected files are present on dm11
analysis_test_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
local_verify(analysis_test_template_folder_path, analysis_test_folder_destination_path) 

# Check that some of the expected outputs were generated
test_file_names = {'perframe' 'scores_AttemptedCopulation.mat' 'scoresBackup.mat' 'registered_trx.mat' 'wingtracking_results.mat'} 
for i = 1 : length(test_file_names) :
    test_file_name = test_file_names{i} 
    test_file_path = \
        os.path.join(analysis_test_folder_destination_path, \
                 '2020-01-07', \
                 'SS36564_20XUAS_CsChrimson_mVenus_attP18_flyBowlMing_20200227_Continuous_2min_5int_20200107_20200229T132141', \
                 test_file_name) 
    if ~exist(test_file_path, 'file') :
        error('No output file at %s', test_file_path) 
    end
end    

# Check that the rig user folder is empty now
entry_names = \
    list_remote_dir(remote_user_name, remote_host_name, remote_user_folder_path) 
if ~isempty(entry_names) :
    error('Remote user folder %s:%s is not empty', remote_host_name, remote_user_folder_path) 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = true 
do_use_bqueue = true 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = true 
do_use_bqueue = true 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = true 
do_use_bqueue = true 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-red-experiment-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = false 
do_use_bqueue = false 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-passing-test-suite-experiment-with-tracking-read-only') 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doplotperframestats', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = false 
do_use_bqueue = false 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = true 
do_use_bqueue = false 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'single-passing-test-suite-experiment-with-tracking-read-only') 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
#analysis_parameters = { 'docomputeperframestats', 'on', 'doplotperframestats', 'on', 'plotperframestats_params', {'plothist', 2} } 
analysis_parameters = { 'docomputeperframestats', 'on', 'doplotperframestats', 'on'} 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
do_reset_destination_folder = true 
do_use_bqueue = false 
do_actually_submit_jobs = true 

# Where does this script live?
this_script_path = mfilename('fullpath') 
this_folder_path = os.path.dirname(this_script_path) 
fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
flydisco_folder_path = os.path.dirname(fly_disco_analysis_folder_path) 
root_example_experiments_folder_path = os.path.join(flydisco_folder_path, 'example-experiments') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'all-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-with-tracking-read-only') 
read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'passing-test-suite-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'no-experiments-read-only') 
#read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'one-aborted-one-faulty-experiment-read-only') 
#read_only_example_experiments_folder_path = '/groups/branson/bransonlab/flydisco_example_experiments_read_only' 

# Specify the "per-lab" configuration here
cluster_billing_account_name = 'scicompsoft' 
rig_host_name = 'beet.hhmi.org' 
rig_user_name = 'bransonk' 
rig_data_folder_path = '/cygdrive/e/flydisco_data/scicompsoft' 
goldblum_destination_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-destination-folder') 
settings_folder_path = os.path.join(fly_disco_analysis_folder_path, 'settings') 
per_lab_configuration = struct() 
per_lab_configuration.cluster_billing_account_name = cluster_billing_account_name 
per_lab_configuration.host_name_from_rig_index = {rig_host_name} 
per_lab_configuration.rig_user_name_from_rig_index = {rig_user_name} 
per_lab_configuration.data_folder_path_from_rig_index = {rig_data_folder_path} 
per_lab_configuration.destination_folder = goldblum_destination_folder_path     
per_lab_configuration.settings_folder_path = settings_folder_path 
#per_lab_configuration.does_use_per_user_folders = true 

# Get the relative paths of all the experiment folders
absolute_path_to_read_only_folder_from_experiment_index = find_experiment_folders(read_only_example_experiments_folder_path) 
relative_path_to_folder_from_experiment_index = \
    cellfun(@(abs_path)(relpath(abs_path, read_only_example_experiments_folder_path)), \
            absolute_path_to_read_only_folder_from_experiment_index, \
            'UniformOutput', false) 

if do_reset_destination_folder :
    # Delete the destination folder
    if exist(goldblum_destination_folder_path, 'file') :
        return_code = system_from_list_with_error_handling({'rm', '-rf', goldblum_destination_folder_path}) 
    end

    # % Recopy the analysis test folder from the template
    # fprintf('Resetting analysis test folder\\n') 
    # read_only_example_experiments_folder_path = os.path.join(root_example_experiments_folder_path, 'test-goldblum-example-experiments-folder') 
    # reset_goldblum_example_experiments_working_copy_folder(read_only_example_experiments_folder_path, read_only_example_experiments_folder_path) 

    # Copy to the destination folder
    rig_lab_data_folder_path = rig_data_folder_path 
    fprintf('Transfering data to the destination path\\n') 
    ensure_folder_exists(os.path.dirname(goldblum_destination_folder_path))   %#ok<UNRCH>
    command_line = {'cp', '-R', '-T', read_only_example_experiments_folder_path, goldblum_destination_folder_path} 
    system_from_list_with_error_handling(command_line) 
    # Should make goldblum_destination_folder_path a clone of
    # example_experiments_folder_path, since we use -T option
else
    # Just least goldblum_destination_folder_path as-is
end

# Add symlinks to the to-process folder so that they will actually get processed
folder_path_from_experiment_index = find_experiment_folders(goldblum_destination_folder_path) 
to_process_folder_path = os.path.join(goldblum_destination_folder_path, 'to-process') 
ensure_folder_exists(to_process_folder_path) 
experiment_count = length(folder_path_from_experiment_index) 
for i = 1 : experiment_count :
    experiment_folder_path = folder_path_from_experiment_index{i} 
    [~, experiment_folder_name] = os.path.dirname2(experiment_folder_path) 
    symlink_path = os.path.join(to_process_folder_path, experiment_folder_name) 
    command_line = {'ln', '-s', '-f', '-T', experiment_folder_path, symlink_path} 
    system_from_list_with_error_handling(command_line) 
end

# Run goldblum
analysis_parameters = { 'doautomaticcheckscomplete', 'on' } 
fprintf('Running goldblum\\n') 
do_transfer_data_from_rigs = false 
do_run_analysis = true 
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# Check that the expected files are present on dm11
local_verify(read_only_example_experiments_folder_path, goldblum_destination_folder_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experiment folder checks pass at 1st check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)   %#ok<NOPTS,NASGU>   
    error('Some experiments had problems at 1st check') 
end

# Run goldblum again, make sure nothing has changed
goldblum(do_transfer_data_from_rigs, do_run_analysis, do_use_bqueue, do_actually_submit_jobs, analysis_parameters, per_lab_configuration)         

# % Check that the expected files are present on dm11
# example_experiments_folder_destination_path = os.path.join(destination_folder_path, 'taylora', 'analysis-test-folder') 
# local_verify(example_experiments_folder_path, example_experiments_folder_destination_path) 

# Check that some of the expected outputs were generated
all_tests_passed_from_experiment_index = check_for_pipeline_output_files(relative_path_to_folder_from_experiment_index, goldblum_destination_folder_path) 
if all(all_tests_passed_from_experiment_index) :
    fprintf('All experimental folder checks pass at 2nd check, except those that were expected not to pass.\n') 
else
    relative_path_to_folder_from_failed_experiment_index = \
        relative_path_to_folder_from_experiment_index(~all_tests_passed_from_experiment_index)  %#ok<NOPTS,NASGU>
    error('Some experiments had problems at 2nd check') 
end

# If get here, all is well
[~, this_script_name] = os.path.dirname(this_script_path) 
fprintf('All tests in %s.m passed.\n', this_script_name) 
def touch(file_name) 
    fid = fopen(file_name, 'a') 
    if fid<0 :
        error('Unable to open file %s for touching', file_name) 
    end
    fclose(fid) 
end
def turn_off_goldblum()
    command_line = 'crontab -l | grep --invert-match ''#GOLDBLUM'' | crontab'    % Remove line containing #GOLDBLUM                       
    system_with_error_handling(command_line)     
end
def turn_on_goldblum(hr, min)
    # Install the goldblum job in crontab.
    # Can give optional hr, min args, which specify the time to run, in 24-hour
    # clock format.  I.e. turn_on_goldblum(23,11) sets it to run once a day at 11:11
    # PM.  Default time is 10:00 PM if no args are given.
    
    if ~exist('hr', 'var') || isempty(hr) :
        hr = 22 
    else
        hr = round(hr) 
        if hr<0 || hr>23 :
            error('hr must be an integer between 0 and 23, inclusive') 
        end
    end
    if ~exist('min', 'var') || isempty(min) :
        min = 0 
    else
        min = round(min) 
        if min<0 || min>59 :
            error('min must be an integer between 0 and 59, inclusive') 
        end
    end
    
    user_name = get_user_name() 
    configuration_def_name = sprintf('%s_configuration', user_name) 
    configuration = feval(configuration_def_name) 
    cluster_billing_account_name = configuration.cluster_billing_account_name 
    
    destination_folder_path = configuration.destination_folder 
    escaped_destination_folder_path = escape_string_for_bash(destination_folder_path) 
    this_folder_path = os.path.dirname(mfilename('fullpath')) 
    fly_disco_analysis_folder_path = os.path.dirname(this_folder_path) 
    escaped_fly_disco_analysis_folder_path = escape_string_for_bash(fly_disco_analysis_folder_path)     
    
    goldblum_logs_folder_path = os.path.join(destination_folder_path, 'goldblum-logs') 
    escaped_goldblum_logs_folder_path = escape_string_for_bash(goldblum_logs_folder_path) 
    
    home_folder_path = getenv('HOME') 
    bash_profile_path = os.path.join(home_folder_path, '.bash_profile') 
    escaped_bash_profile_path = escape_string_for_bash(bash_profile_path) 
    
    launcher_script_path = os.path.join(this_folder_path, 'goldblum_launcher.sh') 
    escaped_launcher_script_path = escape_string_for_bash(launcher_script_path) 
    
#     escaped_bash_profile_path=${1}
#     escaped_fly_disco_analysis_folder_path=${2}
#     pi_last_name=${3}
#     escaped_goldblum_logs_folder_path=${4}
#     date_as_string=`date +%Y-%m-%d`
#     goldblum_log_file_name="goldblum-${date_as_string}.log"
#     goldblum_log_file_path="${escaped_goldblum_logs_folder_path}/${goldblum_log_file_name}" 

    core_command_line = \
        sprintf('%s %s %s %s %s', \
                escaped_launcher_script_path, \
                escaped_bash_profile_path, \
                escaped_fly_disco_analysis_folder_path, \
                cluster_billing_account_name, \
                escaped_goldblum_logs_folder_path)  %#ok<NOPRT>

#     core_command_line = \
#         sprintf(['. /misc/lsf/conf/profile.lsf  ' \
#                  '. %s  ' \
#                  'cd %s  ' \
#                  'bsub -n1 -P %s -o %s -e %s /misc/local/matlab-2019a/bin/matlab -nodisplay -batch ''modpath goldblum(true, true)'''], \
#                 escaped_bash_profile_path, \
#                 escaped_fly_disco_analysis_folder_path, \
#                 pi_last_name, \
#                 escaped_goldblum_log_folder_path, \
#                 escaped_goldblum_log_folder_path)  %#ok<NOPRT>
    escaped_core_command_line = escape_string_for_bash(core_command_line) 
    
    hash_goldblum = '#GOLDBLUM' 
    escaped_hash_goldblum = escape_string_for_bash(hash_goldblum) 
        
    command_line = sprintf('{ crontab -l | grep --invert-match %s echo "%02d %02d * * *     flock --nonblock %s --command %s   #GOLDBLUM" } | crontab', \
                           escaped_hash_goldblum, \
                           min, \
                           hr, \
                           escaped_destination_folder_path, \
                           escaped_core_command_line)      %#ok<NOPRT> % Run at whenever every day                       
    
    # Clear out any pre-existing #GOLDBLUM crontab lines
    turn_off_goldblum()

    # Execute the command to turn on goldblum
    system_with_error_handling(command_line)     
end
