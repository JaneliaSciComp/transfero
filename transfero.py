#! /usr/bin/python3

import sys
import os
import datetime
import yaml
import time
import subprocess
import shlex
import io
import traceback


class cd:
    """Context manager for changing the current working directory, and automagically changing back when done"""
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.old_path = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.old_path)



def listmap(f, lst) :
    return list(map(f, lst))



def get_git_report(source_repo_folder_path) :
    with cd(source_repo_folder_path) as _ :
        # Get the Python version
        python_ver_string = sys.version
        
        # This is hard to get working in a way that overrides
        # 'url."git@github.com:".insteadOf https://github.com/' for a single command.
        # Plus it hits github every time you run, which seems fragile\
        # % Make sure the git remote is up-to-date
        # system_with_error_handling('env GIT_SSL_NO_VERIFY=true GIT_TERMINAL_PROMPT=0 git remote update')     
        
        # Get the git hash
        so = run_subprocess_and_return_stdout(
                ['/usr/bin/env', 'GIT_SSL_NO_VERIFY=true', 'GIT_TERMINAL_PROMPT=0', '/usr/bin/git', 'rev-parse', '--verify', 'HEAD'])
        commit_hash = so.strip()

        # Get the git remote report
        git_remote_report = run_subprocess_and_return_stdout(
            ['/usr/bin/env', 'GIT_SSL_NO_VERIFY=true', 'GIT_TERMINAL_PROMPT=0', '/usr/bin/git',  'remote',  '-v'])     

        # Get the git status
        git_status = run_subprocess_and_return_stdout(
            ['/usr/bin/env', 'GIT_SSL_NO_VERIFY=true', 'GIT_TERMINAL_PROMPT=0', '/usr/bin/git', 'status'])     
        
        # Get the recent git log
        git_log = run_subprocess_and_return_stdout(
            ['/usr/bin/env', 'GIT_SSL_NO_VERIFY=true', 'GIT_TERMINAL_PROMPT=0', '/usr/bin/git', 'log', '--graph', '--oneline', '--max-count', '10']) 
            
    # Package everything up into a string
    breadcrumb_string = 'Python version:\n%s\n\nSource repo:\n%s\n\nCommit hash:\n%s\n\nRemote info:\n%s\n\nGit status:\n%s\n\nGit log:\n%s\n\n' % \
                        (python_ver_string, 
                         source_repo_folder_path, 
                         commit_hash, 
                         git_remote_report, 
                         git_status, 
                         git_log) 

    return breadcrumb_string



def printf(*args) :
    print(*args, end='')



def run_subprocess_and_return_stdout(command_as_list, shell=False) :
    completed_process = \
        subprocess.run(command_as_list, 
                       capture_output=True,
                       text=True,
                       encoding='utf-8',
                       check=True, 
                       shell=shell)
    stdout = completed_process.stdout
    #print('Result: %s' % result)                   
    return stdout



def run_subprocess_and_return_code_and_stdout(command_as_list, shell=False) :
    completed_process = \
        subprocess.run(command_as_list, 
                       capture_output=True,
                       text=True,
                       encoding='utf-8',
                       check=False, 
                       shell=shell)
    stdout = completed_process.stdout
    return_code = completed_process.returncode
    #print('Result: %s' % result)                   
    return (return_code, stdout)



def run_subprocess_and_return_code(command_as_list, shell=False) :
    completed_process = \
        subprocess.run(command_as_list, 
                       check=False, 
                       shell=shell)
    return_code = completed_process.returncode
    #print('Result: %s' % result)                   
    return return_code



def run_subprocess_live_and_return_stdouterr(command_as_list, check=True, shell=False) :
    '''
    Call an external executable, with live display of the output.  
    Return stdout+stderr as a string.
    '''
    with subprocess.Popen(command_as_list, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.STDOUT, 
                          bufsize=1, 
                          text=True, 
                          encoding='utf-8', 
                          shell=shell) as p, io.StringIO() as buf:
        for line in p.stdout :
            print(line, end='')
            buf.write(line)
        p.communicate()  # Seemingly needed to make sure returncode is set.  
                         # Hopefully will not deadlock b/c we've already 
                         # exhausted stdout.
        return_code = p.returncode
        if check :
            if return_code != 0 :
                raise RuntimeError("Running %s returned a non-zero return code: %d" % (str(command_as_list), return_code))
        stdouterr = buf.getvalue()     
    return (stdouterr, return_code)



def run_subprocess_live(command_as_list, check=True, shell=False) :
    '''
    Call an external executable, with live display of the output.
    '''
    with subprocess.Popen(command_as_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True, encoding='utf-8', shell=shell) as p, io.StringIO() as buf:
        for line in p.stdout :
            print(line, end='')
            buf.write(line)
        p.communicate()  # Seemingly needed to make sure returncode is set.  Hopefully will not deadlock b/c we've already exhausted stdout.    
        return_code = p.returncode
        if check :
            if return_code != 0 :
                raise RuntimeError("Running %s returned a non-zero return code: %d" % (str(command_as_list), return_code))
    return return_code



def space_out(lst) :
    '''
    Given a list of strings, return a single string with the list concatenated, but with spaces between them.
    '''
    result = '' 
    count = len(lst) 
    for i in range(count) :
        if i==0 :
            result = lst[i] 
        else :
            result = result + ' ' + lst[i] 
    return result



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



def listsetdiff(lst1, lst2) :
    # Set difference for lists
    s2 = set(lst2)
    result = [el for el in lst1 if el not in s2]    
    return result



def listsetintersect(lst1, lst2) :
    # Set intersection for lists
    s2 = set(lst2)
    result = [el for el in lst1 if el in s2]    
    return result



def ibb(lst, pred) :
    # "Index By Boolean"
    # Designed to mimic Matlab's x(is_something) syntax when is_something is a boolan array
    result =[]
    for i in range(len(lst)) :
        if pred[i]:
            result.append(lst[i])
    return result



def ibbn(lst, pred) :
    # "Index By Boolean Negated"
    # Designed to mimic Matlab's x(~is_something) syntax when is_something is a boolan array
    result =[]
    for i in range(len(lst)) :
        if not pred[i]:
            result.append(lst[i])
    return result



def argfilter(pred, lst) :
    # Like filter(), but returns the indices of elements that would be returned by filter(), not the elements themselves
    result = []
    n = len(lst)
    for i in range(n) :
        el = lst[i]
        if pred(el) :
            result.append(i)
    return result



def isempty(lst) :
    return (len(lst)==0)



def isladen(lst) :
    return (len(lst)>0)



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
        raise Exception('Ambiguous result from "%s": Not clear if file/folder %s exists or not on host %s.  Return code is %d.  stdout is:\n%s' %
                        str(command_line_as_list), path, host_name, return_code, stdout) ;
    return does_exist



class UnableToListDirectoryError(Exception):
    def __init__(self, message):            
        super().__init__(message)



class CopyFileFromRemoteFailedError(Exception):
    def __init__(self, message):            
        super().__init__(message)



class spinner_object :
    # Class for indicting progress
    def __init__(self, type="") :
        self.cursors = '|/-\\' 
        self.cursor_count = len(self.cursors) 
        self.cursor_index = 0 
        self.is_first_call = True 
        if type == 'mute' :
            self.is_mute = True 
        else :
            self.is_mute = False 

    def spin(self) :
        if not self.is_mute :
            if self.is_first_call :
                cursor = self.cursors[self.cursor_index]
                print(cursor) 
                self.is_first_call = False 
            else :
                print('\b')
                self.cursor_index = (self.cursor_index + 1) 
                if self.cursor_index >= self.cursor_count :
                    self.cursor_index = 0 
                cursor = self.cursors[self.cursor_index]
                print(cursor)

    def print(self, *varargin) :
        # Want things printed during spinning to look nice
        if not self.is_mute :
            print('\b\n')   # Delete cursor, then newline
            print(*varargin)   # print whatever
            cursor = self.cursors[self.cursor_index]   # get the same cursor back
            print(cursor)   # write it again on its own line

    def stop(self) :
        if not self.is_mute :
            print('\bdone.\n')



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
                       capture_output=True,
                       text=True,
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
    to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
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
            print('There was a problem during the synch of source experiment folder\n  %s' % source_folder_absolute_path)
            print(repr(e))     
            tb = e.__traceback__
            traceback.print_tb(tb)

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
                traceback.print_tb(tb)
    
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



def transfero(configuration_or_configuration_file_name, do_transfer_data_from_rigs=True, do_run_analysis=True):
    '''
    TRANSFERO Transfer experiment folders from rig computers and analyze them.
       transfero() transfers experiment folders from the specified rig
       computers and then runs an analysis script on them.  What rig computers to
       search, and a variety of other settings, are determined from the username of
       the user running transfero().    
    '''

    # Load the per-lab configuration file
    this_script_path = os.path.realpath(__file__)
    this_script_folder_path = os.path.dirname(this_script_path)
    if configuration_or_configuration_file_name == None:
        user_name = os.getlogin()
        configuration_file_name = '%s_configuration.yml' % user_name
        configuration_file_path = os.path.join(this_script_folder_path, configuration_file_name)
        with open(configuration_file_path, 'r') as stream:
            configuration = yaml.safe_load(stream)
    elif isinstance(configuration_or_configuration_file_name, str) :
        configuration_file_name = configuration_or_configuration_file_name
        configuration_file_path = os.path.abspath(configuration_file_name)
        with open(configuration_file_path, 'r') as stream:
            configuration = yaml.safe_load(stream)
    else:
        configuration = configuration_or_configuration_file_name

    # Unpack the per-lab configuration dict
    #cluster_billing_account_name = configuration['cluster_billing_account_name']
    host_name_from_rig_index = configuration['host_name_from_rig_index']
    rig_user_name_from_rig_index = configuration['rig_user_name_from_rig_index'] 
    data_folder_path_from_rig_index = configuration['data_folder_path_from_rig_index'] 
    destination_folder = configuration['destination_folder']     
    analysis_executable_path = configuration['analysis_executable_path']
    to_process_folder_name = 'to-process' 

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
                traceback.print_tb(tb)

    else :
        print('Skipping transfer of data from rigs.\n') 
    
    # Run the analysis script on links in the to-process folder
    if do_run_analysis :
        # Get the links from the to_process_folder_name folder
        to_process_folder_path = os.path.join(destination_folder, to_process_folder_name) 
        folder_name_from_experiment_index = os.listdir(to_process_folder_path) 
        link_path_from_experiment_index = \
            [os.path.join(to_process_folder_path, folder_name) for folder_name in folder_name_from_experiment_index]

        # Run the analysis script    
        # The analysis executable should return a 0 return code even if thing go wrong,
        # so that this doesn't error out
        run_subprocess_live([analysis_executable_path, to_process_folder_path]) 
        
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
        print('Skipping analysis.\n') 
    
    # Want the start and end of a single transfero run to be clear in the log
    print('\n') 
    print('********************************************************************************\n') 
    print('\n') 
    print('Transfero run started at %s is ending\n' % start_time_as_char) 
    print('\n') 
    print('********************************************************************************\n') 
    print('\n')    
# end of transfero()




if __name__ == "__main__":
    if len(sys.argv)>=2 :
        transfero(sys.argv[1])
    else:
        transfero()
