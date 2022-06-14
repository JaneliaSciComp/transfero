#!/usr/bin/env python

from transfero import *



def turn_off_transfero() :
    command_line = "crontab -l | grep --invert-match '#TRANSFERO' | crontab"    # Remove line containing #TRANSFERO
    run_subprocess_live(command_line, shell=True)



if __name__ == "__main__":
    turn_off_transfero()
