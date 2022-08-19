#!/usr/bin/python3

import sys
import os
import datetime
#import yaml
import time
import subprocess
import shlex
import traceback
import math
from utilities import *
from fuster import *



def run_remote_subprocess_and_return_stdout(user_name, host_name, remote_command_line_as_list) :
    '''
    Run the system command, but taking a list of tokens rather than a string, and
    running on a remote host.  Uses ssh, which needs to be set up for passowrdless
    login as the indicated user.
    Each element of command_line_as_list is escaped for bash, then composed into a
    single string, then submitted to system_with_error_handling().
    '''

    # Escape all the elements of command_line_as_list
    escaped_remote_command_line_as_list = [shlex.quote(el) for el in remote_command_line_as_list] 
    
    # Build up the command line by adding space between elements
    remote_command_line = space_out(escaped_remote_command_line_as_list)

    # Command line
    command_line_as_list = ['ssh', '-l', user_name, host_name, remote_command_line] ; 
    
    # Actually run the command
    stdout = run_subprocess_and_return_stdout(command_line_as_list)
    return stdout



def does_remote_file_exist(user_name, host_name, path) :
    escaped_source_path = shlex.quote(path) 
    remote_stat_command_line = 'test -a ' + escaped_source_path 
    command_line_as_list = ['/usr/bin/ssh', user_name+'@'+host_name, remote_stat_command_line] ;
    [return_code, stdout] = run_subprocess_and_return_code_and_stdout(command_line_as_list)
    if return_code == 0 :
        does_exist = True 
    elif return_code == 1 :
        does_exist = False 
    else :
        raise RuntimeError('Ambiguous result from "%s": Not clear if file/folder %s exists or not on host %s.  Return code is %d.  stdout is:\n%s' %
                           (str(command_line_as_list), path, host_name, return_code, stdout) )
    return does_exist



class UnableToListDirectoryError(Exception):
    def __init__(self, message):            
        super().__init__(message)



class CopyFileFromRemoteFailedError(Exception):
    def __init__(self, message):            
        super().__init__(message)



def compute_md5_on_remote(source_user, source_host, source_path) :
    escaped_source_path = shlex.quote(source_path) 
    host_spec = source_user + '@' + source_host
    remote_command_line = '/usr/bin/md5sum %s' % escaped_source_path
    command_line = ['/usr/bin/ssh', host_spec, remote_command_line]
    #[stdout, return_code] = run_subprocess_live_and_return_stdouterr(command_line, check=False) 
    #if return_code != 0 :
    #    raise RuntimeError('Unable to md5sum the file %s as user %s on host %s' % (source_path, source_user, source_host)) 
    stdout = run_subprocess_and_return_stdout(command_line) 
    tokens = stdout.strip().split()
    if isempty(tokens) :
        raise RuntimeError('Got a weird result while md5sum''ing the file %s as user %s on host %s.  Result was: %s' %
                           (source_path, source_user, source_host, stdout)) 
    hex_digest = tokens[0]
    return hex_digest



def compute_md5_on_local(local_path) :
    command_line = [ '/usr/bin/md5sum', local_path ]
    stdout = run_subprocess_and_return_stdout(command_line)
    tokens = stdout.strip().split()
    if isempty(tokens) :
        raise RuntimeError('Got a weird result while md5sum''ing the file %s.  Stdout/stderr was:\n%s' % (local_path, stdout))
    hex_digest = tokens[0] 
    return hex_digest



def copy_file_from_remote(source_user, source_host, source_path, dest_path) :
    #escaped_source_path = shlex.quote(source_path) 
    #escaped_dest_path = shlex.quote(dest_path) 
    source_spec = source_user + '@' + source_host + ':' + source_path
    start_time = time.time()
    command_line = [ '/usr/bin/scp', '-B', '-T', source_spec, dest_path ]
    [scp_return_code, scp_stdout] = run_subprocess_and_return_code_and_stdout(command_line) 
    # scp doesn't honor the user's umask, so we need to set the file
    # permissions explicitly
    if scp_return_code == 0:
        command_line = [ '/bin/chmod', 'u+rw-x,g+rw-x,o+r-wx', dest_path ]
        [chmod_return_code, chmod_stdout] = run_subprocess_and_return_code_and_stdout(command_line) 
    elapsed_time = time.time() - start_time
    if scp_return_code != 0 :
        raise CopyFileFromRemoteFailedError('Unable to copy the file %s as remote user %s from host %s to destination %s:\n%s' %
                                            (source_path, source_user, source_host, dest_path, scp_stdout) ) 
    elif chmod_return_code != 0 :
        raise CopyFileFromRemoteFailedError('Unable to set the permissions of %s after copy:\n%s' %
                                            (dest_path, chmod_stdout) ) 
    return elapsed_time



def extract_name_size_and_type_from_ls_long_line(line) :
    # We assume line looks like this: '-rw-r--r--  1 taylora scicompsoft     278 2020-12-02 17:09:49.027303272 -0500 "test_bw_smooth.m"'
    tokens = line.split()
    size_in_bytes = int(tokens[4]) 
    parts = line.split('"') 
    name = parts[1] 
    file_type_char = line[0] 
    is_file = (file_type_char == '-')
    is_dir =  (file_type_char == 'd')
    is_link = (file_type_char == 'l')
    mod_date_as_string = tokens[5] 
    mod_time_as_string_with_ns = tokens[6] 
    mod_time_as_string = mod_time_as_string_with_ns[0:15]   # only out to ms
    utc_offset_as_string = tokens[7] 
    mod_time_as_string = mod_date_as_string + ' ' + mod_time_as_string + ' ' + utc_offset_as_string   # date, time
    time_format = "%Y-%m-%d %H:%M:%S.%f %z"
    mod_time = datetime.datetime.strptime(mod_time_as_string, time_format)  # aware datetime, expressed in local timezone
    #mod_time = datetime.datetime.strptime(mod_time_as_string, time_format).astimezone(datetime.timezone.utc)   # Want a datetime in UTC timezone 
    return (name, size_in_bytes, is_file, is_dir, is_link, mod_time)



def list_remote_dir(source_user, source_host, source_path) :
    escaped_source_path = shlex.quote(source_path) 
    remote_ls_command_line = 'ls -l -A -U -Q --full-time -- ' + escaped_source_path
    command_line_as_list = ['/usr/bin/ssh', source_user+'@'+source_host, remote_ls_command_line ]
    completed_process = \
        subprocess.run(command_line_as_list,
                       stdout=subprocess.PIPE, 
                       encoding='utf-8',
                       check=False)
    if completed_process.returncode != 0 :
        raise UnableToListDirectoryError('Unable to list the directory %s as user %s on host %s' % (source_path, source_user, source_host))
    lines_raw = completed_process.stdout.strip().splitlines()
    lines = lines_raw[1:]  # drop 1st line
    line_count = len(lines) 
    file_names = [None] * line_count
    file_sizes_in_bytes = [0] * line_count
    is_file = [False] * line_count
    is_dir = [False] * line_count
    is_link = [False] * line_count
    mod_time = [None] * line_count
    for i in range(line_count) :
        line = lines[i] 
        (name, size_in_bytes, is_file_this, is_dir_this, is_link_this, mod_time_this) = extract_name_size_and_type_from_ls_long_line(line) 
        file_names[i] = name 
        file_sizes_in_bytes[i] = size_in_bytes 
        is_file[i] = is_file_this 
        is_dir[i] = is_dir_this 
        is_link[i] = is_link_this 
        mod_time[i] = mod_time_this 
    return (file_names, file_sizes_in_bytes, is_file, is_dir, is_link, mod_time)



def is_experiment_folder_given_contents(file_names) :
    lowercase_file_names = list(map(lambda s: s.lower(), file_names))
    # We check for three files.  If two or more are present, we consider it an
    # experiment folder
    has_movie_file = ( ('movie.ufmf' in lowercase_file_names) or ('movie.avi' in lowercase_file_names) or ('movie_movie.ufmf' in lowercase_file_names) )
    point_count = \
        has_movie_file + \
        ('metadata.xml' in lowercase_file_names) + \
        ('ABORTED' in file_names) 
    result = ( point_count >= 2) 
    return result



def find_remote_experiment_folders_helper(user_name, host_name, parent_relative_path, root_absolute_path, to_process_folder_name, spinner) :
    # Find the experiment folders on a remote host.  Returns relative paths,
    # relative to root_absolute_path.
  
    # Get a list of all files and folders
    parent_absolute_path = os.path.join(root_absolute_path, parent_relative_path) 
    try :
        (entries, _, _, is_entry_a_folder, _, _) = \
            list_remote_dir(user_name, host_name, parent_absolute_path) 
    except UnableToListDirectoryError as e :
        # if we can't list the dir, warn but continue
        spinner.print("Warning: can't list path %s on host %s as user %s" % (parent_absolute_path, host_name, user_name)) 
        spinner.print(str(e)) 
        return (relative_path_from_experiment_index, is_aborted_from_experiment_index)
    spinner.spin() ;

    # Separate source file, folder names    
    is_entry_a_file = listmap(lambda b: not b, is_entry_a_folder)
    file_names = ibb(entries, is_entry_a_file)
    folder_names = ibb(entries, is_entry_a_folder)

    # If the parent_path is an experiment folder, we're done
    if is_experiment_folder_given_contents(file_names) :
        if parent_relative_path == to_process_folder_name :
            spinner.print("Warning: found an experiment folder with relative path %s.  Can't synch because that's the path to the to-process folder" %
                          parent_absolute_path) 
        else :           
            is_aborted_from_experiment_index = [ ('ABORTED' in file_names) ]
            relative_path_from_experiment_index = [parent_relative_path] 
    else :
        # For each folder, recurse
        relative_path_from_experiment_index = [] 
        is_aborted_from_experiment_index = [] 
        folder_name_count = len(folder_names)
        for i in range(folder_name_count) :
            folder_name = folder_names[i]
            (relative_path_from_child_experiment_index, is_aborted_from_child_experiment_index) = \
                 find_remote_experiment_folders_helper(user_name, 
                                                       host_name, 
                                                       os.path.join(parent_relative_path, folder_name), 
                                                       root_absolute_path,
                                                       to_process_folder_name,
                                                       spinner) 
            relative_path_from_experiment_index.extend(relative_path_from_child_experiment_index)
            is_aborted_from_experiment_index.extend(is_aborted_from_child_experiment_index)
    return (relative_path_from_experiment_index, is_aborted_from_experiment_index)



def find_remote_experiment_folders(user_name, host_name, path, to_process_folder_name) :
    # record the start time
    start_time = time.time() 

    # print an informative message
    print("Looking for experiment folders within %s on host %s as user %s... " % (path, host_name, user_name))
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    (relative_path_from_experiment_index, is_aborted_from_experiment_index) = \
        find_remote_experiment_folders_helper(user_name, host_name, '', path, to_process_folder_name, spinner)
    spinner.stop() ;
   
    # print the number of experiment folders found
    print("%d experiment folders found\n" % len(relative_path_from_experiment_index))

    # print the elapsed time
    elapsed_time = time.time() - start_time
    print("Elapsed time: %0.1f seconds\n" % elapsed_time) 

    # Return the result
    return (relative_path_from_experiment_index, is_aborted_from_experiment_index)



def delete_remote_folder(remote_user_name, remote_dns_name, remote_folder_path) :
    # Delete (as in rm -rf) a remote folder
    
    # Check for a truly horrible mistake
    trimmed_remote_folder_path = remote_folder_path.strip() 
    if isempty(trimmed_remote_folder_path) or trimmed_remote_folder_path=='/' :
        raise RuntimeError('Yeah, I''m not going to rm -rf / on %s' % remote_dns_name) 
    
    escaped_remote_folder_path = shlex.quote(remote_folder_path) 
    remote_command_line = '/bin/rm -rf %s' % escaped_remote_folder_path
    command_line_as_list = ['/usr/bin/ssh',  remote_user_name+'@'+remote_dns_name, remote_command_line]
    return_code = run_subprocess_and_return_code(command_line_as_list) 
    if return_code != 0 :
        raise RuntimeError('Unable to delete the folder %s as user %s on host %s' %
                           (remote_folder_path, remote_user_name, remote_dns_name)) 



def aware_datetime_from_timestamp(timestamp) :
    naive_datetime = datetime.datetime.fromtimestamp(timestamp)
    return naive_datetime.astimezone()  # aware timezone, represented in local TZ



def simple_dir(folder_name) :
    name_from_index = os.listdir(folder_name)
    path_from_index = list(map(lambda name: os.path.join(folder_name, name), 
                               name_from_index))
    is_folder_from_index = list(map(lambda path: os.path.isdir(path), 
                                    path_from_index))
    byte_count_from_index = list(map(lambda path: os.path.getsize(path),
                                     path_from_index))
    timestamp_from_index = list(map(lambda path: os.path.getmtime(path),
                                    path_from_index))
    datetime_from_index = list(map(aware_datetime_from_timestamp, timestamp_from_index))
    return (name_from_index, is_folder_from_index, byte_count_from_index, datetime_from_index)



def add_links_to_to_process_folder(destination_folder, to_process_folder_name, relative_path_from_experiment_folder_index) :
    '''
    Makes a symbolic link from each folder in relative_path_from_experiment_folder_index into the to_process_folder_name.
    Both to_process_folder_name and each relative path in relative_path_from_experiment_folder_index are taken to be relative
    to destination_folder, which should be an absolute path.
    '''
    to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
    os.makedirs(to_process_folder_path, exist_ok=True)  # Create the to_process folder if it doesn't exist
    experiment_folder_relative_path_count = len(relative_path_from_experiment_folder_index) 
    for i in range(experiment_folder_relative_path_count) :
        experiment_folder_relative_path = relative_path_from_experiment_folder_index[i] 
        experiment_folder_absolute_path = os.path.join(destination_folder, experiment_folder_relative_path) 
        command_line = [ '/bin/ln', '-s', experiment_folder_absolute_path, to_process_folder_path ]
        run_subprocess_live(command_line) 



def find_experiment_folders_relative_helper(root_path, parent_relative_path, spinner) :
    # Get a list of all files and folders in the source, dest folders
    parent_path = os.path.join(root_path, parent_relative_path) 
    (entries, is_entry_a_folder, _, _) = simple_dir(parent_path) 
    spinner.spin() 

    # Separate source file, folder names    
    file_names = ibbn(entries, is_entry_a_folder) 
    raw_folder_names = ibb(entries, is_entry_a_folder)     
    
    # Exclude the to-process folder if in the root path
    if isempty(parent_relative_path) :
        is_to_process_folder = [name=='to-process' for name in raw_folder_names]
        folder_names = ibbn(raw_folder_names, is_to_process_folder) 
    else :
        folder_names = raw_folder_names 
    
    # If the parent_path is an experiment folder, we're done
    if is_experiment_folder_given_contents(file_names) :
        result = [ parent_relative_path ] 
    else :
        # For each folder, recurse
        result = []
        for i in range(len(folder_names)) :
            folder_name = folder_names[i] 
            child_folder_path_list = \
                 find_experiment_folders_relative_helper(root_path, \
                                                         os.path.join(parent_relative_path, folder_name), \
                                                         spinner) 
            result.extend(child_folder_path_list)
    return result



def find_experiment_folders_relative(source_path) :
    # record the start time
    start_time = time.time() 

    # print an informative message
    print("Looking for experiment folders within %s\ " % source_path)
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    experiment_folder_path_list = find_experiment_folders_relative_helper(source_path, '', spinner) 
    spinner.stop() 
   
    # print the number of files etc verified
    print("%d experiment folders found\n" % len(experiment_folder_path_list))

    # print the elapsed time
    elapsed_time = time.time() - start_time
    print("Elapsed time: %0.1f seconds\n" % elapsed_time) 

    return experiment_folder_path_list



def find_experiment_folders(source_path) :
    relative_path_from_experiment_index = find_experiment_folders_relative(source_path) 
    result = listmap(lambda rel_path: os.path.join(source_path, rel_path), 
                 relative_path_from_experiment_index)
    return result



def remote_verify_helper(source_user, source_host, source_parent_path, dest_parent_path, n_files_verified, n_dirs_verified, n_file_bytes_verified, spinner) :
    # get a list of all files and dirs in the source, dest dirs
    (name_from_source_entry_index, \
     size_from_source_entry_index, \
     is_file_from_source_entry_index, \
     is_folder_from_source_entry_index, \
     _, \
     mod_datetime_from_source_entry_index) = \
        list_remote_dir(source_user, source_host, source_parent_path) 
    [name_from_dest_entry_index, is_folder_from_dest_entry_index, size_from_dest_entry_index, mod_datetime_from_dest_entry_index] = \
        simple_dir(dest_parent_path) 
    
    # separate source file, dir names (ignore links)
    name_from_source_file_index = ibb(name_from_source_entry_index, is_file_from_source_entry_index) 
    size_from_source_file_index = ibb(size_from_source_entry_index, is_file_from_source_entry_index) 
    mod_datetime_from_source_file_index = ibb(mod_datetime_from_source_entry_index, is_file_from_source_entry_index) 
    name_from_source_folder_index = ibb(name_from_source_entry_index, is_folder_from_source_entry_index) 
        
    # separate dest file, dir names
    name_from_dest_folder_index = ibb(name_from_dest_entry_index, is_folder_from_dest_entry_index)     
    is_file_from_dest_entry_index = listmap(lambda b: not b, is_folder_from_dest_entry_index)
    name_from_dest_file_index = ibb(name_from_dest_entry_index, is_file_from_dest_entry_index)     
    size_from_dest_file_index = ibb(size_from_dest_entry_index, is_file_from_dest_entry_index) 
    mod_datetime_from_dest_file_index = ibb(mod_datetime_from_dest_entry_index, is_file_from_dest_entry_index) 
    
    # scan the source files, make sure they're all present in dest, with matching
    # hashes
    for source_file_index in range(len(name_from_source_file_index)) :
        file_name = name_from_source_file_index[source_file_index]
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name)         
        source_file_size = size_from_source_file_index[source_file_index]
        dest_file_indices = argfilter(lambda dest_name: (dest_name==file_name), name_from_dest_file_index)
        match_count = len(dest_file_indices)
        if match_count==0 :
            raise RuntimeError("There is a problem with destination file %s: It's missing." % dest_file_path) 
        elif match_count==1 :
            # this is the happy path
            dest_file_index = dest_file_indices[0]
            dest_file_size = size_from_dest_file_index[dest_file_index]
            spinner.spin() 
            if dest_file_size == source_file_size :
                source_mod_datetime = mod_datetime_from_source_file_index[source_file_index]
                dest_mod_datetime = mod_datetime_from_dest_file_index[dest_file_index]
                if ( source_mod_datetime < dest_mod_datetime ) :
                    # Compare hashes
                    source_hex_digest = compute_md5_on_remote(source_user, source_host, source_file_path) 
                    dest_hex_digest = compute_md5_on_local(dest_file_path) 
                    if source_hex_digest != dest_hex_digest :
                        raise RuntimeError("There is a problem with destination file %s: Its hash is %s, but the source file hash is %s." %
                                           (dest_file_path, dest_hex_digest, source_hex_digest) )
                else :
                    raise RuntimeError("There is a problem with destination file %s: Its modification time (%s )is before that of the source file (%s)." %
                                       (dest_file_path, str(dest_mod_datetime), str(source_mod_datetime) ) ) 
            else :
                raise RuntimeError("There is a problem with destination file %s: Its size (%d bytes) differs from that of the source file (%d bytes)." %
                                   (dest_file_path, dest_file_size, source_file_size) ) 
        else :
            raise RuntimeError('Something has gone horribly wrong in remote_verify_helper().  There seem to be two files with the same name (%s) in destination folder %s' %
                               (file_name, dest_parent_path) )
        
        # If we get here, destination file is present, it was modified after the source:
        # and the hashes match
        n_files_verified = n_files_verified + 1 
        n_file_bytes_verified = n_file_bytes_verified + source_file_size 

    # Verify that all source folders are in destination
    for source_folder_index in range(len(name_from_source_folder_index)) :
        folder_name = name_from_source_folder_index[source_folder_index]
        #is_match_from_dest_folder_index = listmap(lambda dest_folder_name: (folder_name==dest_folder_name), name_from_dest_folder_index)
        is_match_from_dest_folder_index = [dest_folder_name==folder_name for dest_folder_name in name_from_dest_folder_index]
        if not any(is_match_from_dest_folder_index) :
            dest_folder_path = os.path.join(dest_parent_path, folder_name) 
            raise RuntimeError("There is a problem with destination folder %s: It's missing." % dest_folder_path) 
        
    # for each source folder, recurse
    for i in range(len(name_from_source_folder_index)) :
        folder_name = name_from_source_folder_index[i] 
        source_folder_path = os.path.join(source_parent_path, folder_name) 
        dest_folder_path = os.path.join(dest_parent_path, folder_name)                 
        (n_files_verified, n_dirs_verified, n_file_bytes_verified) = \
             remote_verify_helper(source_user, 
                                  source_host, 
                                  source_folder_path, 
                                  dest_folder_path, 
                                  n_files_verified, 
                                  n_dirs_verified,  
                                  n_file_bytes_verified, 
                                  spinner) 

    # Return the counts
    return (n_files_verified, n_dirs_verified, n_file_bytes_verified)



def remote_verify(source_user, source_host, source_path, dest_path, be_verbose=False) :
    # record the start time
    start_time = time.time()

    # print an informative message
    if be_verbose :
        print('Verifying that contents of\n%s@%s:%s\nare present in\n%s\n\ ' % (source_user, source_host, source_path, dest_path) )
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    if be_verbose :
        spinner = spinner_object() 
    else :
        spinner = spinner_object('mute') 
    [n_files_verified, n_dirs_verified, n_file_bytes_verified] = \
        remote_verify_helper(source_user, source_host, source_path, dest_path, 0, 0, 0, spinner)
            # this will throw if there's a verification failure
    spinner.stop()     
    
    # print the number of files etc verified
    #fprintf("%d files verified\n", n_files_verified) 
    #fprintf("%d folders verified\n", n_dirs_verified) 
    #fprintf("%d file bytes verified\n", n_file_bytes_verified) 
    if be_verbose :
        print("Success: All files and folders in source are present in destination.\n")

    # print the elapsed time
    elapsed_time = time.time() - start_time
    if be_verbose :
        print("Elapsed time: %0.1f seconds\n" % elapsed_time) 



def remote_sync_helper(source_user, \
                       source_host, \
                       source_parent_path, \
                       dest_parent_path, \
                       n_copied, \
                       n_failed, \
                       n_dir_failed, \
                       n_verified, \
                       n_dir_failed_to_list, \
                       time_spent_copying, \
                       spinner) :
    # get a list of all files and dirs in the source, dest dirs
    try :
        (source_entries, source_entry_sizes, is_source_entry_a_file, is_source_entry_a_dir, _, source_entry_mod_times) = \
            list_remote_dir(source_user, source_host, source_parent_path) 
    except UnableToListDirectoryError as e :
        # if we can't list the dir, warn but continue
        spinner.print("Warning: can't list path %s on host %s as user %s" % (source_parent_path, source_host, source_user)) 
        spinner.print(str(e)) 
        n_dir_failed_to_list = n_dir_failed_to_list + 1 
        return (n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying)
    [dest_entries, is_dest_entry_a_folder, dest_file_size, dest_file_mtimes] = simple_dir(dest_parent_path) 
    
    # separate source file, dir names (ignore links)
    source_file_names = ibb(source_entries, is_source_entry_a_file)
    source_file_sizes = ibb(source_entry_sizes, is_source_entry_a_file)
    source_file_mod_times = ibb(source_entry_mod_times, is_source_entry_a_file) 
    source_folder_names = ibb(source_entries, is_source_entry_a_dir) 
        
    # separate dest file, dir names
    dest_folder_names = ibb(dest_entries, is_dest_entry_a_folder)     
    dest_file_names = ibbn(dest_entries, is_dest_entry_a_folder)     
    size_from_dest_file_index = ibbn(dest_file_size, is_dest_entry_a_folder) 
    dest_file_mtimes = ibbn(dest_file_mtimes, is_dest_entry_a_folder) 
    
    # scan the source files, copy any that aren't in dest:
    # or that aren't up-to-date
    source_file_count = len(source_file_names) 
    for i in range(source_file_count) :
        file_name = source_file_names[i] 
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name) 
        spinner.spin() 
        #print("  %s" % source_file)
        dest_file_indices = argfilter(lambda dest_file_name: dest_file_name==file_name, dest_file_names)
        match_count = len(dest_file_indices)
        if isladen(dest_file_indices) :
            dest_file_index = dest_file_indices[0]
            source_file_size = source_file_sizes[i] 
            dest_file_size = size_from_dest_file_index[dest_file_index]
            if dest_file_size == source_file_size :
                source_mod_time = source_file_mod_times[i] 
                dest_mod_time = dest_file_mtimes[i] 
                if source_mod_time < dest_mod_time :
                    # Compare hashes
                    source_hex_digest = compute_md5_on_remote(source_user, source_host, source_file_path) 
                    dest_hex_digest = compute_md5_on_local(dest_file_path) 
                    is_file_verified = (source_hex_digest==dest_hex_digest) 
                else :
                    is_file_verified = False 
            else :
                is_file_verified = False 
        else :
            is_file_verified = False 

        if is_file_verified :
            n_verified = n_verified + 1 
        else :
            try :
                time_spent_copying = time_spent_copying + copy_file_from_remote(source_user,source_host, source_file_path, dest_file_path) 
                n_copied = n_copied + 1 
            except CopyFileFromRemoteFailedError as e :
                # orginally except IOError
                # if we can't copy the file, warn but continue
                spinner.print('Warning: can''t copy %s' % source_file_path) 
                spinner.print(str(e))
                n_failed = n_failed + 1 

    # scan source dirs, create any that that aren't in dest dirs
    source_folder_names_not_in_dest = listsetdiff(source_folder_names, dest_folder_names) 
    for i in range(len(source_folder_names_not_in_dest)) :
        source_folder_name = source_folder_names_not_in_dest[i] 
        dest_folder_path = os.path.join(dest_parent_path, source_folder_name) 
        try :
            os.mkdir(dest_folder_path) 
        except Exception as e :
            # if we can't make the dir, warn but continue
            spinner.print("Warning: can't make directory %s, error message was: " % (dest_folder_path, str(e))) 
            n_dir_failed = n_dir_failed + 1 
    
    # need to re-generate dest dirs, because we may have failed to 
    # create some of them
    (dest_entries, is_dest_entry_a_folder, _, _) = simple_dir(dest_parent_path) 
    dest_folder_names = ibb(dest_entries, is_dest_entry_a_folder) 
    folder_names_to_recurse_into = listsetintersect(source_folder_names, dest_folder_names) 
        
    # for each dir in both source_dirs and dest_folder_names, recurse
    for i in range(len(folder_names_to_recurse_into)) :
        folder_name = folder_names_to_recurse_into[i] 
        (n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying) = \
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
    return (n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying)



def remote_sync(source_user, source_host, source_path, dest_path, be_verbose=False) :
    # record the start time
    start_time = time.time() 

    # if dest dir doesn't exist, create it
    os.path.exists(dest_path)
    if os.path.exists(dest_path) :
        # make sure it's a dir
        if not os.path.isdir(dest_path) :
            raise RuntimeError('Destination %s exists, but is a file, not a directory' % dest_path)
    else :
        os.makedirs(dest_path, exist_ok=True)
        
    # print an informative message
    if be_verbose :
        print('Copying contents of\n%s@%s:%s\ninto\n%s\n\ ' % (source_user, source_host, source_path, dest_path)) 

    # call helper
    # All those zeros are the numbers of different kinds of failures so far
    if be_verbose :
        spinner = spinner_object() 
    else :
        spinner = spinner_object('mute') 
    [n_copied, n_failed, n_dir_failed, n_verified, n_dir_failed_to_list, time_spent_copying] = \
        remote_sync_helper(source_user, source_host, source_path, dest_path, 0, 0, 0, 0, 0, 0.0, spinner)   
    spinner.stop() 
    
    # print the number of files copied
    if n_failed==0 and n_dir_failed==0 and n_dir_failed_to_list==0 :
        if be_verbose :
            print('Successfully copied contents of\n%s@%s:%s\ninto\n%s\n' % (source_user, source_host, source_path, dest_path))

        # print the elapsed time
        elapsed_time = time.time() - start_time
        if be_verbose :
            print("Elapsed time: %0.1f seconds\n" % elapsed_time) 
            print("Time spent copying: %0.1f seconds\n" % time_spent_copying) 
    else :
        # throw an error if there were any failures
        raise RuntimeError('There was at least one failure during the remote sync: %d file copies failed, %d directory creates failed, %d directories failed to list' %
                           (n_failed, n_dir_failed, n_dir_failed_to_list))



def remote_sync_and_verify(source_user, source_host, source_path, dest_path) :
    # Call the def that does the real work
    remote_sync(source_user, source_host, source_path, dest_path) 

    # Now verify that that worked (will raise an exception if verification fails)
    remote_verify(source_user, source_host, source_path, dest_path) 



def remote_sync_verify_and_delete_experiment_folders(source_user_name, \
                                                     source_host_name, \
                                                     source_root_absolute_path, \
                                                     dest_root_absolute_path, \
                                                     to_process_folder_name) :

    # Make sure the remote folder exists, return if not
    does_folder_exist = does_remote_file_exist(source_user_name, source_host_name, source_root_absolute_path) 
    if not does_folder_exist :
        print('Folder %s does not exist on host %s, so not searching for experiment folders in it.\n', source_root_absolute_path, source_host_name) 
        relative_path_from_synched_experiment_index = []
        return relative_path_from_synched_experiment_index
    
    # record the start time
    start_time = time.time() 
        
    # print an informative message
    #print('Searching for experiment folders in\n  %s@%s:%s...', source_user_name, source_host_name, source_root_absolute_path) 
    [relative_path_from_experiment_folder_index, is_aborted_from_experiment_folder_index] = \
        find_remote_experiment_folders(source_user_name, source_host_name, source_root_absolute_path, to_process_folder_name) 
    experiment_folder_count = len(relative_path_from_experiment_folder_index) 
    #print("%d experiment folders found.\n" , experiment_folder_count) 
    
    # sort the aborted from unaborted experiments
    relative_path_from_aborted_experiment_folder_index = ibb(relative_path_from_experiment_folder_index, is_aborted_from_experiment_folder_index)
    relative_path_from_unaborted_experiment_folder_index = ibbn(relative_path_from_experiment_folder_index, is_aborted_from_experiment_folder_index)

    # print an informative message
    aborted_experiment_folder_count = len(relative_path_from_aborted_experiment_folder_index) 
    if aborted_experiment_folder_count==0 :
        pass
    elif aborted_experiment_folder_count==1 :
        print('Deleting %d ABORTED experiment folder from\n  %s@%s:%s\n  ...\n' % 
              (aborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path)) 
    else :
        print('Deleting %d ABORTED experiment folders from\n  %s@%s:%s\n  ...\n' % 
              (aborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path)) 
    
    # Delete each experiment folder in turn
    did_delete_from_aborted_experiment_folder_index = [False] * experiment_folder_count
    for i in range(aborted_experiment_folder_count) :
        experiment_folder_relative_path = relative_path_from_aborted_experiment_folder_index[i] 
        source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
        try :
            delete_remote_folder(source_user_name, source_host_name, source_folder_absolute_path) 
            did_delete_from_aborted_experiment_folder_index[i] = True 
        except Exception as e :
            print('There was a problem during the deleting of ABORTED source experiment folder\n  %s\nThe problem was:\n%s\n' %
                  (source_folder_absolute_path, 
                   str(e)))     

    # print the number of ABORTED experiment folders deleted
    deleted_aborted_experiment_folder_count = sum(did_delete_from_aborted_experiment_folder_index)
    delete_error_count = aborted_experiment_folder_count - deleted_aborted_experiment_folder_count 
    if aborted_experiment_folder_count > 0 :
        print("Of %d ABORTED experiment folders:\n" % aborted_experiment_folder_count) 
        print("  %d deleted\n" % deleted_aborted_experiment_folder_count) 
        print("  %d failed to delete\n" % delete_error_count) 
    
    # print an informative message
    unaborted_experiment_folder_count = len(relative_path_from_unaborted_experiment_folder_index) 
    if unaborted_experiment_folder_count > 0 :
        print('Synching %d experiment folders from\n  %s@%s:%s\n  into\n  %s\n  ...\n' %
              (unaborted_experiment_folder_count, source_user_name, source_host_name, source_root_absolute_path, dest_root_absolute_path)) 

    # Sync each experiment folder in turn
    did_synch_from_unaborted_experiment_folder_index = [False] * unaborted_experiment_folder_count
    for i in range(unaborted_experiment_folder_count) :
        experiment_folder_relative_path = relative_path_from_unaborted_experiment_folder_index[i] 
        source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
        dest_folder_absolute_path = os.path.join(dest_root_absolute_path, experiment_folder_relative_path) 
        try :
            remote_sync_and_verify(source_user_name, \
                                   source_host_name, \
                                   source_folder_absolute_path, \
                                   dest_folder_absolute_path) 
            did_synch_from_unaborted_experiment_folder_index[i] = True 
        except Exception as e :
            print('There was a problem during the sync of source experiment folder\n  %s' % source_folder_absolute_path)
            print(repr(e))     
            tb = e.__traceback__
            traceback.print_tb(tb, file=sys.stdout)

    # print the number of experiment folders copied
    synched_experiment_folder_count = sum(did_synch_from_unaborted_experiment_folder_index) 
    synch_error_count = unaborted_experiment_folder_count - synched_experiment_folder_count 
    if unaborted_experiment_folder_count > 0 :
        print("Of %d unaborted experiment folders:\n" % unaborted_experiment_folder_count) 
        print("  %d synched and verified\n" % synched_experiment_folder_count) 
        print("  %d failed to synch or verify\n" % synch_error_count) 
    
    # Delete each synched experiment folder in turn
    relative_path_from_synched_experiment_index = ibb(relative_path_from_unaborted_experiment_folder_index, did_synch_from_unaborted_experiment_folder_index)
    synched_experiment_count = len(relative_path_from_synched_experiment_index) 
    did_delete_from_synched_experiment_index = [False] * synched_experiment_count 
    for i in range(unaborted_experiment_folder_count) :
        if did_synch_from_unaborted_experiment_folder_index[i] :
            experiment_folder_relative_path = relative_path_from_unaborted_experiment_folder_index[i] 
            source_folder_absolute_path = os.path.join(source_root_absolute_path, experiment_folder_relative_path) 
            try :
                delete_remote_folder(source_user_name, source_host_name, source_folder_absolute_path) 
                did_delete_from_synched_experiment_index[i] = True 
            except Exception as e :
                print('There was a problem during the post-synch deletion of source experiment folder\n  %s' %
                      source_folder_absolute_path) 
                print(repr(e))     
                tb = e.__traceback__
                traceback.print_tb(tb, file=sys.stdout)
    
    # print the number of experiment folders copied
    deleted_experiment_folder_count = sum(did_delete_from_synched_experiment_index) 
    delete_error_count = synched_experiment_folder_count - deleted_experiment_folder_count 
    if synched_experiment_folder_count > 0 :
        print("Of %d synched experiment folders:\n" % synched_experiment_folder_count) 
        print("  %d deleted\n" % deleted_experiment_folder_count) 
        print("  %d failed to delete\n" % delete_error_count) 

    # print the elapsed time
    elapsed_time = time.time() - start_time
    print("Total elapsed time: %0.1f seconds\n" % elapsed_time) 
    
#     # throw an error if there were any failures
#     if synch_error_count > 0 || delete_error_count > 0 ,
#         error("There was at least one failure during the synching of unaborted experiment folders from the remote host") 
#     end
    
    # Return the synched experiments, whether or not they were deleted
    relative_path_from_synched_experiment_index = ibb(relative_path_from_unaborted_experiment_folder_index, did_synch_from_unaborted_experiment_folder_index)
    return relative_path_from_synched_experiment_index
# end remote_sync_verify_and_delete_experiment_folders



def local_verify_helper(source_parent_path, dest_parent_path, n_files_verified, n_dirs_verified, n_file_bytes_verified, spinner) :
    # get a list of all files and dirs in the source, dest dirs
    [name_from_source_entry_index, is_folder_from_source_entry_index, size_from_source_entry_index, mod_datetime_from_source_entry_index] = \
        simple_dir(source_parent_path) 
    is_file_from_source_entry_index = listmap(lambda b: not b, is_folder_from_source_entry_index)
    [name_from_dest_entry_index, is_folder_from_dest_entry_index, size_from_dest_entry_index, mod_datetime_from_dest_entry_index] = \
        simple_dir(dest_parent_path) 
    is_file_from_dest_entry_index = listmap(lambda b: not b, is_folder_from_dest_entry_index)
    
    # separate source file, dir names (ignore links)
    name_from_source_file_index = ibb(name_from_source_entry_index, is_file_from_source_entry_index) 
    size_from_source_file_index = ibb(size_from_source_entry_index, is_file_from_source_entry_index) 
    mod_datetime_from_source_file_index = ibb(mod_datetime_from_source_entry_index, is_file_from_source_entry_index) 
    name_from_source_folder_index = ibb(name_from_source_entry_index, is_folder_from_source_entry_index) 
        
    # separate dest file, dir names
    name_from_dest_folder_index = ibb(name_from_dest_entry_index, is_folder_from_dest_entry_index)     
    name_from_dest_file_index = ibb(name_from_dest_entry_index, is_file_from_dest_entry_index)     
    size_from_dest_file_index = ibb(size_from_dest_entry_index, is_file_from_dest_entry_index) 
    mod_datetime_from_dest_file_index = ibb(mod_datetime_from_dest_entry_index, is_file_from_dest_entry_index) 
    
    # verify that all files in source are also in dest
    are_all_source_files_in_dest = isempty(listsetdiff(name_from_source_file_index, name_from_dest_file_index)) 
    if not are_all_source_files_in_dest :
        raise RuntimeError('The local files in %s do not include all the remote files in %s' % (dest_parent_path, source_parent_path) )
    
    # scan the source files, compute the md5sum, compare to that for the dest file
    for source_file_index in range(len(name_from_source_file_index)) :
        file_name = name_from_source_file_index[source_file_index]
        source_file_path = os.path.join(source_parent_path, file_name) 
        dest_file_path = os.path.join(dest_parent_path, file_name)         
        source_file_size = size_from_source_file_index[source_file_index] 
        dest_file_indices = argfilter(lambda dest_file_name: dest_file_name==file_name, name_from_dest_file_index)
        if len(dest_file_indices) == 0 :
            raise RuntimeError('Internal error in local_verify_helper(): No destination file named %s' % file_name)
        elif len(dest_file_indices) > 1 :
            raise RuntimeError('Internal error in local_verify_helper(): More than one destination file named %s' % file_name)
        dest_file_index = dest_file_indices[0]
        dest_file_size = size_from_dest_file_index[dest_file_index]
        spinner.spin() 
        if dest_file_size == source_file_size :
            source_mod_datetime = mod_datetime_from_source_file_index[source_file_index]
            dest_mod_datetime = mod_datetime_from_dest_file_index[dest_file_index]
            if ( source_mod_datetime < dest_mod_datetime ) :
                # Compare hashes
                source_hex_digest = compute_md5_on_local(source_file_path) 
                dest_hex_digest = compute_md5_on_local(dest_file_path) 
                is_file_verified = (source_hex_digest == dest_hex_digest) 
            else :
                is_file_verified = False 
        else :
            is_file_verified = False 
        
        if is_file_verified :
            n_files_verified = n_files_verified + 1 
            n_file_bytes_verified = n_file_bytes_verified + source_file_size 
        else :
            raise RuntimeError("There is a problem with destination file %s: It's missing, or the wrong size, or the hashes don't match." %
                               dest_file_path) 

    # Verify that all source folders are in destination
    are_all_source_files_in_dest = isempty(listsetdiff(name_from_source_folder_index, name_from_dest_folder_index)) 
    if are_all_source_files_in_dest :
        n_dirs_verified = n_dirs_verified + len(name_from_source_folder_index) 
    else :
        raise RuntimeError('The destination folder names in %s do not include all the source folder names in %s' % (dest_parent_path, source_parent_path) )
    
    # for each source folder, recurse
    for i in range(len(name_from_source_folder_index)) :
        folder_name = name_from_source_folder_index[i] 
        source_folder_path = os.path.join(source_parent_path, folder_name) 
        dest_folder_path = os.path.join(dest_parent_path, folder_name)                 
        (n_files_verified, n_dirs_verified, n_file_bytes_verified) = \
             local_verify_helper(source_folder_path, 
                                 dest_folder_path, 
                                 n_files_verified, 
                                 n_dirs_verified,  
                                 n_file_bytes_verified, 
                                 spinner) 

    return (n_files_verified, n_dirs_verified, n_file_bytes_verified)



def local_verify(source_path, dest_path) :
    # record the start time
    start_time = time.time() 

    # print an informative message
    print("Verifying that contents of\n%s\nare also present in\n%s\n\ " % (source_path, dest_path) )
    
    # call helper
    # All those zeros are the numbers of different kinds of things that have been verified so far
    spinner = spinner_object() 
    (n_files_verified, n_dirs_verified, n_file_bytes_verified) = \
        local_verify_helper(source_path, dest_path, 0, 0, 0, spinner) 
    spinner.stop()     
    
    # print the number of files etc verified
    print("%d files verified\n" % n_files_verified) 
    print("%d folders verified\n" % n_dirs_verified) 
    print("%d file bytes verified\n" % n_file_bytes_verified) 
    print("Success: All files and folders in source are present in destination.\n")

    # print the elapsed time
    elapsed_time = time.time() - start_time
    print("Elapsed time: %0.1f seconds\n" % elapsed_time) 



def transfero_analyze_experiment_folders(analysis_executable_path, folder_path_from_experiment_index, cluster_billing_account_name, slots_per_job, maximum_slot_count) :
    # Specify job/cluster parameters
    do_use_fuster = True
    do_run_on_cluster = True
    #maximum_slot_count = 480
    #slots_per_job = 48

    # Report how many experiments are to be analyzed
    experiment_count = len(folder_path_from_experiment_index)
    printf('There are %d experiments that will be analyzed.\n' % experiment_count) 
    if experiment_count > 0 :
        printf('Submitting these for analysis...\n') 

    # Want elapsed time
    tic_id = tic()

    # Run analysis_executable_path on each experiment folder, typically using fuster
    if do_use_fuster :
        bqueue = bqueue_type(do_run_on_cluster, maximum_slot_count) 
        for experiment_index in range(experiment_count) :
            experiment_folder_path = folder_path_from_experiment_index[experiment_index]
            command_line_as_list = [analysis_executable_path, experiment_folder_path]
            stdouterr_file_path = os.path.join(experiment_folder_path, 'transfero-analysis.log')
            bsub_job_name = '%s-transfero-%d' % (cluster_billing_account_name, experiment_index)
            bsub_options_as_list = [ '-P', cluster_billing_account_name, '-J', bsub_job_name ]
            bqueue.enqueue(slots_per_job, stdouterr_file_path, bsub_options_as_list, command_line_as_list)   # the 20 is an arg to pause()
        maximum_wait_time = math.inf
        do_show_progress_bar = True 
        tic_id = tic() 
        job_status_from_experiment_index = bqueue.run(maximum_wait_time, do_show_progress_bar)
        elapsed_time = toc(tic_id)
        print('Elapsed time was %g seconds' % elapsed_time)
        print('Final job_status_from_experiment_index: %s' % str(job_status_from_experiment_index)) 
    else :
        # If not using Fuster, just run them normally (usually just for debugging)
        job_status_from_experiment_index = [ math.nan ] * experiment_count
        for i in range(experiment_count) :
            experiment_folder_path = folder_path_from_experiment_index[experiment_index]
            command_line_as_list = [analysis_executable_path, experiment_folder_path]
            rc = run_subprocess_live(command_line_as_list, check=False)
            job_status = +1 if (rc==0) else -1
            job_status_from_experiment_index[i] = job_status

    # Report on any failed runs
    was_successful_from_experiment_index = [job_status==+1 for job_status in job_status_from_experiment_index]
    successful_job_count = sum(was_successful_from_experiment_index) 
    did_error_from_experiment_count =  [job_status==-1 for job_status in job_status_from_experiment_index]
    errored_job_count = sum(did_error_from_experiment_count) 
    did_not_finish_from_experiment_index = [job_status==0 for job_status in job_status_from_experiment_index]
    did_not_finish_job_count = sum(did_not_finish_from_experiment_index)
    if experiment_count == successful_job_count :
        # All is well
        printf('All %d jobs completed successfully.\n' % successful_job_count) 
    else :
        # Print the folders that completed successfully
        did_complete_successfully = [ job_status==+1 for job_status in job_status_from_experiment_index ]
        folder_path_from_successful_experiment_index = ibb(folder_path_from_experiment_index, did_complete_successfully) 
        if isladen(folder_path_from_successful_experiment_index) :
            printf('These %d jobs completed successfully:\n' % successful_job_count) 
            for i in range(len(folder_path_from_successful_experiment_index)) :
                experiment_folder_path = folder_path_from_successful_experiment_index[i]
                printf('    %s\n' % experiment_folder_path) 
            printf('\n') 
        
        # Print the folders that had errors
        had_error = [ job_status==-1 for job_status in job_status_from_experiment_index ]
        folder_path_from_errored_experiment_index = ibb(folder_path_from_experiment_index, had_error) 
        if isladen(folder_path_from_errored_experiment_index) :
            printf('These %d experiment folders had errors:\n' % errored_job_count) 
            for i in range(len(folder_path_from_errored_experiment_index)) :
                experiment_folder_path = folder_path_from_errored_experiment_index[i] 
                printf('    %s\n' % experiment_folder_path) 
            printf('\n') 
        
        # Print the folders that did not finish
        did_not_finish = [ job_status==0 for job_status in job_status_from_experiment_index ] 
        folder_path_from_unfinished_experiment_index = ibb(folder_path_from_experiment_index, did_not_finish) 
        if isladen(folder_path_from_unfinished_experiment_index) :
            printf('These %d experiment folders did not finish processing in the alloted time:\n' % did_not_finish_job_count) 
            for i in range(len(folder_path_from_unfinished_experiment_index)) :
                experiment_folder_path = folder_path_from_unfinished_experiment_index[i] 
                printf('    %s\n' % experiment_folder_path) 
            printf('\n') 

    # Report elapsed time
    elapsed_time = toc(tic_id)
    if experiment_count > 0 :
        print("Elapsed time for analysis was %0.1f seconds" % elapsed_time)



def transfero_core(do_transfer_data_from_rigs, do_run_analysis, configuration, this_script_path, this_script_folder_path):
    # Unpack the per-lab configuration dict
    cluster_billing_account_name = configuration['cluster_billing_account_name']
    host_name_from_rig_index = configuration['host_name_from_rig_index']
    rig_user_name_from_rig_index = configuration['rig_user_name_from_rig_index'] 
    data_folder_path_from_rig_index = configuration['data_folder_path_from_rig_index'] 
    destination_folder = configuration['destination_folder']     
    # We support relative paths (relative to this script for analysis exectuables)
    raw_analysis_executable_path = configuration['analysis_executable_path']
    analysis_executable_path = abspath_relative_to_transfero(raw_analysis_executable_path)
    to_process_folder_name = 'to-process' 
    slots_per_analysis_job = configuration['slots_per_analysis_job']
    maximum_analysis_slot_count = configuration['maximum_analysis_slot_count']

    # # For debugging
    # print('do_transfer_data_from_rigs: %s' % str(do_transfer_data_from_rigs))
    # print('do_run_analysis: %s' % str(do_run_analysis))

    # Add a "banner" to the start of the log
    tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    start_time_as_char = datetime.datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M %Z')    
    print('\n') 
    print('********************************************************************************\n') 
    print('\n') 
    print('Transfero run starting at %s\n' % start_time_as_char) 
    print('\n') 
    print('********************************************************************************\n') 
    print('\n')     

    # Get info about the state of the repo, output to log
    source_folder_path = os.path.dirname(this_script_path)
    git_report = get_git_report(this_script_folder_path) 
    print(git_report) 
    
    # For each rig, copy the data over to the Janelia filesystem, and delete the
    # original data
    if do_transfer_data_from_rigs :
        rig_count = len(host_name_from_rig_index) 
        for rig_index in range(rig_count) :
            rig_host_name = host_name_from_rig_index[rig_index] 
            rig_user_name = rig_user_name_from_rig_index[rig_index] 
            lab_data_folder_path = data_folder_path_from_rig_index[rig_index]

            try :
                relative_path_from_synched_experiment_folder_index = \
                    remote_sync_verify_and_delete_experiment_folders(rig_user_name, \
                                                                     rig_host_name, \
                                                                     lab_data_folder_path, \
                                                                     destination_folder, \
                                                                     to_process_folder_name)                 
                add_links_to_to_process_folder(destination_folder, to_process_folder_name, relative_path_from_synched_experiment_folder_index) 
            except Exception as e :
                print('There was a problem doing the sync from %s:%s as %s to %s:' % \
                      (rig_host_name, lab_data_folder_path, rig_user_name, destination_folder) )
                print(repr(e))     
                tb = e.__traceback__
                traceback.print_tb(tb, file=sys.stdout)
    else :
        print('Skipping transfer of data from rigs.') 
    
    # Run the analysis script on links in the to-process folder
    if do_run_analysis :
        # Get the links from the to_process_folder_name folder
        to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
        folder_name_from_experiment_index = os.listdir(to_process_folder_path) 
        link_path_from_experiment_index = \
            [ os.path.join(to_process_folder_path, folder_name) for folder_name in folder_name_from_experiment_index ]
        folder_path_from_experiment_index = [ os.path.realpath(experiment_folder_link_path) for experiment_folder_link_path in link_path_from_experiment_index ]

        # Submit the per-experiment analysis jobs to the cluster
        transfero_analyze_experiment_folders(analysis_executable_path, folder_path_from_experiment_index, cluster_billing_account_name, slots_per_analysis_job, maximum_analysis_slot_count)
        
        # Whether those succeeded or failed, remove the links from the
        # to-process folder
        experiment_folder_count = len(link_path_from_experiment_index)
        for i in range(experiment_folder_count) :
            experiment_folder_link_path = link_path_from_experiment_index[i]  
            # experiment_folder_link_path is almost certainly a symlink, but check
            # anyway
            if os.path.islink(experiment_folder_link_path) :
                os.remove(experiment_folder_link_path) 
    else :
        print('Skipping analysis.') 
    
    # Want the start and end of a single transfero run to be clear in the log
    print('\n') 
    print('********************************************************************************\n') 
    print('\n') 
    print('Transfero run started at %s is ending\n' % start_time_as_char) 
    print('\n') 
    print('********************************************************************************\n') 
    print('\n')    
# end of transfero()



def transfero(do_transfer_data_from_rigs_argument=None, do_run_analysis_argument=None, configuration_or_configuration_file_name=None):
    '''
    TRANSFERO Transfer experiment folders from rig computers and analyze them.
       transfero() transfers experiment folders from the specified rig
       computers and then runs an analysis script on them.  What rig computers to
       search, and a variety of other settings, are determined from the username of
       the user running transfero().    
    '''

    # # For debugging
    # print('do_transfer_data_from_rigs_argument: %s' % str(do_transfer_data_from_rigs_argument))
    # print('do_run_analysis_argument: %s' % str(do_run_analysis_argument))

    # Load the per-lab configuration file
    this_script_path = os.path.realpath(__file__)
    this_script_folder_path = os.path.dirname(this_script_path)
    if configuration_or_configuration_file_name == None:
        user_name = get_user_name()
        configuration_file_name = '%s_configuration.yaml' % user_name
        configuration_file_path = os.path.join(this_script_folder_path, configuration_file_name)
        configuration = read_yaml_file_badly(configuration_file_path)
        # with open(configuration_file_path, 'r') as stream:
        #     configuration = yaml.safe_load(stream)
    elif isinstance(configuration_or_configuration_file_name, str) :
        configuration_file_name = configuration_or_configuration_file_name
        configuration_file_path = os.path.abspath(configuration_file_name)
        configuration = read_yaml_file_badly(configuration_file_path)
        # with open(configuration_file_path, 'r') as stream:
        #     configuration = yaml.safe_load(stream)
    else:
        configuration = configuration_or_configuration_file_name

    # Unpack the per-lab configuration dict
    cluster_billing_account_name = configuration['cluster_billing_account_name']
    host_name_from_rig_index = configuration['host_name_from_rig_index']
    rig_user_name_from_rig_index = configuration['rig_user_name_from_rig_index'] 
    data_folder_path_from_rig_index = configuration['data_folder_path_from_rig_index'] 
    destination_folder = configuration['destination_folder']     
    # We support relative paths (relative to this script for analysis exectuables)
    raw_analysis_executable_path = configuration['analysis_executable_path']
    analysis_executable_path = abspath_relative_to_transfero(raw_analysis_executable_path)
    to_process_folder_name = 'to-process' 
    slots_per_analysis_job = configuration['slots_per_analysis_job']
    maximum_analysis_slot_count = configuration['maximum_analysis_slot_count']

    # Figure out what stages to run
    if do_transfer_data_from_rigs_argument is None :
        do_transfer_data_from_rigs = configuration['do_transfer_data_from_rigs']
    else :
        do_transfer_data_from_rigs = do_transfer_data_from_rigs_argument
    if do_run_analysis_argument is None :
        do_run_analysis = configuration['do_run_analysis']
    else :
        do_run_analysis = do_run_analysis_argument

    # Don't want to run if transfero is already running, so check for lock file
    lock_file_path = os.path.join(destination_folder, 'transfero.lock')
    with LockFile(lock_file_path) as lock :
        if lock.have_lock() :
            transfero_core(do_transfer_data_from_rigs, do_run_analysis, configuration, this_script_path, this_script_folder_path)
        else :
            raise RuntimeError('Lock file %s already exists.  Exiting.' % lock_file_path)
# end of transfero()




if __name__ == "__main__":
    if len(sys.argv)==1 :
        transfero()
    elif len(sys.argv)==2 :
        transfero(boolean_from_string(sys.argv[1]))
    elif len(sys.argv)==3 :
        transfero(boolean_from_string(sys.argv[1]), boolean_from_string(sys.argv[2]))
    elif len(sys.argv)==4 :
        transfero(boolean_from_string(sys.argv[1]), boolean_from_string(sys.argv[2]), sys.argv[3])
    else:
        raise RuntimeError('Too many arguments to Transfero')
