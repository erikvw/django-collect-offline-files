[![Build Status](https://travis-ci.com/erikvw/django-collect-offline-files.svg?branch=develop)](https://travis-ci.com/erikvw/django-collect-offline-files?branch=develop)
[![Coverage Status](https://coveralls.io/repos/erikvw/django-collect-offline-files/badge.svg?branch=develop&service=github)](https://coveralls.io/github/erikvw/django-collect-offline-files?branch=develop)


# django-collect-offline-files

Transfer `django_collect_offline` transactions as files using SFTP over an SSH connection.

Data flows from client to server where a server is either a node server or the central server.

see also `django_collect_offline`.


## Usage

On the client:

    python manage.py export_transactions


On the server or receiving host:

    python manage.py incoming_observer

    python manage.py deserialize_observer


## FileQueueObservers

Two FileQueueObservers do the work using use `watchdog` observers; `IncomingTransactionsFileQueueObserver` and `DeserializeTransactionsFileQueueObserver`. They are called using management commands:

    python manage.py incoming_observer

and
    
    python manage.py deserialize_observer
    
### IncomingTransactionsFileQueueObserver

The client exports data to JSON and sends to the server. Using `TransactionExporter`, data is exported into a JSON file from `django_collect_offline.models.OutgoingTransaction` on the client and sent to the server using `TransactionFileSender`.

Once a file is sent to the server, the `IncomingTransactionsFileQueueObserver` detects it and adds the filename to the queue (`IncomingTransactionsFileQueue`). 

### DeserializeTransactionsFileQueue

Processed files in the queue `IncomingTransactionsFileQueue` are moved to the pending folder watched by `DeserializeTransactionsFileQueueObserver`.and added to the its queue, `DeserializeTransactionsFileQueue`. 


## Processing queue items / filenames

Each queue has a processor, (see `process_queue`). The processor calls the `next_task` method for each item in the queue in FIFO order infinitely or until it gets a `None` item.
