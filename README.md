## Backup restore solution
https://hackattic.com/challenges/backup_restore

## Requirements
* Docker up and run
* User that will execute script has rights to execute docker commands
* Python  3.7.13 and higher

### Tested on
* Ubuntu 20.04 LTS python 3.8.10
* Fedora 35 python 3.10.4
* Rocky Linux python 3.7.13

### How to run

1. `git clone git@github.com:tutunak/hackattic_backup_restore.git` or `git clone https://github.com/tutunak/hackattic_backup_restore.git`
2. cd hackattic_backup_restore
3. pip3 install -r requirements.txt
4. python3 backup_restore.py


### Hot it works
1. Install postgresql 10.19
2. Get dump from hackattic
3. Save gzipped dump to local directory
4. Mount dump to docker container
5. Restore dump
6. Execute query
7. Send post request to hackattic with query result

