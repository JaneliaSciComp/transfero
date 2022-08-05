import sys
import os
import pwd
import time
import subprocess
import io
import datetime
import ast


class cd:
    """Context manager for changing the current working directory, and automagically changing back when done"""
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.old_path = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.old_path)



def boolean_from_string(s) :
    if s.lower()=='true' :
        return True
    elif s.lower()=='false' :
        return False
    else :
        raise RuntimeError('Unable to convert string "%s" to True or False')



def tic() :
    return time.time()



def toc(t) :
    return time.time() - t



def listmap(f, lst) :
    return list(map(f, lst))



def abspath_relative_to_transfero(path) :
    this_script_path = os.path.realpath(__file__)
    this_script_folder_path = os.path.dirname(this_script_path)
    with cd(this_script_folder_path) as _:
        result = os.path.realpath(os.path.abspath(path))
    return result



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
    with subprocess.Popen(command_as_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, encoding='utf-8', shell=shell) as p, io.StringIO() as buf:
        for line in p.stdout :
            print(line, end='')
            buf.write(line)
        p.communicate()  # Seemingly needed to make sure returncode is set.  Hopefully will not deadlock b/c we've already exhausted stdout.    
        return_code = p.returncode
        if check :
            if return_code != 0 :
                raise RuntimeError("Running %s returned a non-zero return code: %d" % (str(command_as_list), return_code))
    return return_code



def run_subprocess_with_log_and_return_code(command_as_list, log_file_name, shell=False) :
    '''
    Call an external executable, with stdout+stderr to log file.
    '''
    with open(log_file_name, 'w') as fid:
        completed_process = subprocess.run(command_as_list, stdout=fid, stderr=subprocess.STDOUT, encoding='utf-8', shell=shell, check=False)
        return_code = completed_process.returncode
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



def get_user_name():
    return pwd.getpwuid(os.getuid())[0]



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



def ibl(lst, old_index_from_new_index) :
    # "Index By List"
    # Designed to mimic Matlab's x(old_index_from_new_index) syntax when old_index_from_new_index is an array of indices
    new_count = len(old_index_from_new_index)
    old_count = len(lst)
    if new_count>old_count :
        raise RuntimeError('old_index_from_new_index has more elements (%d) than lst (%d)' % (new_count, old_count))
    result = [None] * new_count  # pre-allocate output, although I'm not sure this helps with perf
    for new_index in range(new_count) :
        old_index = old_index_from_new_index[new_index]
        result[new_index] = lst[old_index]
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



def assign_where_true_bang(lst, pred, el) :
    # If pred[i] is true, lst[i] is set to el.
    # This mutates lst.
    for i in range(len(lst)) :
        if pred[i]:
            lst[i] = el


def elementwise_list_and(a, b) :
  return [ (el_a and el_b) for (el_a,el_b) in zip(a, b) ]



def elementwise_list_or(a, b) :
  return [ (el_a or el_b) for (el_a,el_b) in zip(a, b) ]



def elementwise_list_not(a) :
  return [ (not el_a) for el_a in a ]



def flatten(lst):
    return [item for sublist in lst for item in sublist]



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



class progress_bar_object :
    # properties
    #     n_
    #     i_
    #     percent_as_displayed_last_
    #     did_print_at_least_one_line_
    #     did_print_final_newline_
    #     data_queue_
    # end
    
    def __init__(self, n) :
        self.n_ = n 
        self.i_ = 0 
        self.percent_as_displayed_last_ = [] 
        self.did_print_at_least_one_line_ = False 
        self.did_print_final_newline_ = False 
    
    def update(self, di=1) :
        # Should be called from within the for loop
        if self.did_print_final_newline_ :
            return
        self.i_ = min(self.i_ + di, self.n_) 
        i = self.i_ 
        n = self.n_ 
        percent = 100 if n==0 else 100*(i/n) 
        percent_as_displayed = round(percent*10)/10
        if percent_as_displayed != self.percent_as_displayed_last_ :
            if self.did_print_at_least_one_line_ :
                delete_bar = ''.join(['\b'] * (1+50+1+2+4+1)) 
                printf(delete_bar) 
            bar = ''.join(['*'] * round(percent/2))
            printf('[%-50s]: %4.1f%%' % (bar, percent_as_displayed)) 
            self.did_print_at_least_one_line_ = True 
        if i==n :
            if not self.did_print_final_newline_ :
                printf('\n') 
                self.did_print_final_newline_ = True 
        self.percent_as_displayed_last_ = percent_as_displayed 



def where(t) :
    return [i for i, x in enumerate(t) if x]



def noop() :
    pass



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



def read_yaml_file_badly(file_name) :
    result = {}
    with open(file_name, 'r', encoding='UTF-8') as file:
        line_from_line_index = file.readlines()
    line_count = len(line_from_line_index)
    for line_index in range(line_count) :
        line = line_from_line_index[line_index].strip()
        index_of_colon = line.find(':')
        if index_of_colon < 0 :
            continue
        key = line[:index_of_colon].strip()
        value_as_string = line[index_of_colon+1:].strip()
        value = ast.literal_eval(value_as_string)
        result[key] = value
    return result
    