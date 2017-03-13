# edc-sync-files

### EDC Sync File Transfer

Transfer user generated media files as part of the synchronization process managed by `edc_sync`.


### Data Flow

client -> node -> server
client -> server

### Setup SSH Keys

1. Generate public key for the server or client.
    * ssh-keygen -t rsa
2. Copy public key to machine you want to connect to with ssh-copy-id.
    * ssh-copy-id  user@device_ip

- user
- device_ip
- source_folder where/to/copy/files/from
- destination_folder where/to/copy/files/to
- archive_folder where/to/copy/files/to/archive

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

```

### Setup USB

```
	1. Renamed USB to BCPP.
	2. mkdir -p /Volumes/BCPP/transactions/incoming
	3. mkdir -p /Volumes/BCPP/transactions/archive
```
### Start Watchdog Observer In The Server.

```
	1. workon bcpp
	2. cd source/bcpp/
	3. python manage.py start_observer
```