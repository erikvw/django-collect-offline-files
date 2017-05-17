# edc-sync-files

### EDC Sync File Transfer

Transfer `edc_sync` transactions as files using SFTP over an SSH connection.

Data flows from client to server where a server is either a node server or the central server.


#### Add above attributes for AppConfig in your Application in the child class of Edc Sync AppConfig

```
CLIENT MACHINE

Connected to host edc.sample.com.

patterns: *.json
host: edc.sample.com
Incoming folder: /Users/edc_user/source/bcpp/transactions/incoming
Outgoing folder: /Users/edc_user/source/bcpp/transactions/outgoing
Archive folder: /Users/edc_user/source/bcpp/transactions/archive

SERVER MACHINE

Upload folder: remote_user@edc.sample.com:/Users/edc_user/source/bcpp/transactions/tmp
Incoming folder: remote_user@edc.sample.com:/Users/edc_user/source/bcpp/transactions/incoming
Outgoing folder: remote_user@edc.sample.com:/Users/edc_user/source/bcpp/transactions/outgoing
Archive folder: remote_user@edc.sample.com:/Users/edc_user/source/bcpp/transactions/archive

### Start Watchdog Observer In The Server.

```
	1. source myenv/bin/activate
	2. cd source/my_project/
	3. python manage.py start_observer
```

### Setup SSH Keys

Generate public key for the server or client.

    ssh-keygen -t rsa
Copy public key to machine you want to connect to with ssh-copy-id.
    
    ssh-copy-id  user@device_ip
