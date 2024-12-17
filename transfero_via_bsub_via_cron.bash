#! /bin/bash

# Wrapper script to run transfero_via_bsub.py from a cron job.
# We do this in a Bash script rather than Python b/c we need to source
# /misc/lsf/conf/profile.lsf to set up the path to bsub, etc, and that's a 
# shell script.

. /misc/lsf/conf/profile.lsf  # "source" doesn't work in this context
#. "${HOME}/.bash_profile  # Surely we can do without this...

# Get the absolute path to transfero_via_bsub.py
PATH_TO_THIS_SCRIPT="${BASH_SOURCE[0]}"
CANONICAL_PATH_TO_THIS_SCRIPT=$(realpath "${PATH_TO_THIS_SCRIPT}")
PATH_TO_THIS_FOLDER=$(dirname "${CANONICAL_PATH_TO_THIS_SCRIPT}")
PATH_TO_TRANSFERO_VIA_BSUB_DOT_PY="${PATH_TO_THIS_FOLDER}/transfero_via_bsub.py"

# Call transfero_via_bsub.py
"${PATH_TO_TRANSFERO_VIA_BSUB_DOT_PY}" --isviacron
