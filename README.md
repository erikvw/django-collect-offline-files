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

### Override edc_sync.ini and specify attributes

- user
- device_ip
- source_folder where/to/copy/files/from
- destination_folder where/to/copy/files/to

#### Add above attributes for AppConfig in your Application in the child class of Edc Sync AppConfig

```
    config_attrs = {
        'edc_sync_files': ['device_ip', 'source_folder', 'role', 'destination_folder' ],
    }
```
