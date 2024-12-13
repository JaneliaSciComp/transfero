Transfero
=========

Program for transferring experiment folders from rig computers to an
NFS filesystem, with subsequent automated analysis on an LSF cluster.
Meant to be run from a cron job or similar.

Also provided is an executable Python script,
`transfero-via-bsub-without-transfer`, which runs Transfero on-demand,
but with transfer from the rigs disabled.  (So only analysis is
enabled.)

Requires Python >=3.6.  (The system Python in Oracle Linux 8.4 works.)
