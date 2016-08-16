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
    * ssh-copy-id  user@remote_machine_ip

### Override edc_sync.ini and specify attributes

- user your/remote_username
- file_server_folder where/to/copy/files/from
- file_server remote_ip
- media_dir_upload where/to/copy/files/to

#### Add above attributes for AppConfig in your Application in the child class of Edc Sync AppConfig

```
    config_attrs = {
        'edc_sync': ['file_server', 'file_server_folder', 'role', 'media_dir_upload' ],
    }
```
