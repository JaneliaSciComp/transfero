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


How to set up a new Transfero instance
--------------------------------------

1. Have the Systems groups set up a "robot" user for the lab.
E.g. `wilsonrobot` might be the robot user for the Wilson Lab.  Have
them add your ssh key to the list of keys that can log in to this
account.

2. Add e.g. a `wilsonrobot_configuration.yaml` to the repo.  Use one of
the existing `*_configuration.yaml` files as a template.

(Next few steps are on the rig computer(s).)

3. If the rig computer has a local `labadmin` user, use that.
Otherwise, create a e.g. `localwilsonrobot` user, and add it to the
Administrators group.

4. Login as the user from step 3.

5. Install cygwin.  Add openssh, emacs packages.

6. Start a cygwin terminal with ”Run as Administrator”

7. Run ”ssh-host-config” and when prompted enter:
```
strict mode: no
install sshd as a service: yes
value of CYGWIN: <LEAVE THIS EMPTY>
```

8. Either start the service with `cygrunsrv --start cygsshd` or
let it start automatically after a reboot.

9. Will likely have to open port 22 on Windows Firewall.

10.  If you created a user in step 3, then to ssh into that account
you will have to do e.g.
```
ssh wilsonlab-ww7+localwilsonrobot@wilsonlab-ww7.hhmi.org
```

11. From e.g. submit.int.janelia.org, use `ssh-copy-id` to enable
passwordless login into the rig machine.

12. ssh into submit.int.janelia.org as (e.g.) wilsonrobot, and use
\ssh-keygen` and `ssh-copy-id` to enable the wilsonrobot user to login
to the rig machine without using a password.  Use an empty passphrase
when you create the keys.

13. Now that you've configured things for passwordless login from your
account(s) and from wilsonrobot, disable passwordful login.  To do
this, launch a cygwin terminal as administrator, and edit the
/etc/sshd_config file.  Find the PasswordAuthentication line and
uncomment it if needed.  Make it so it reads:
```
PasswordAuthentication no
```

14. Back on your normal workstation, find your local transfero repo or
clone a fresh copy.  Create a e.g. wilsonrobot_configuration.yaml,
using one of the existing `*_configuration.yaml` files as a template.
Set that up appropriately.

15. Edit the `copy_into_production.py` file, adding a new
e.g. wilsonrobot entry to the `username_from_user_index` list.

16. Commit your changes, push, then run the `copy_into_production.py`
script.











