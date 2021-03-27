# Backup Manager

https://cuyu.github.io/python/2016/08/15/Terminate-multiprocess-in-Python-correctly-and-gracefully
This is the solution for being able to kill an rsync job in the middle.  Actually run the rsync in a separate process that I can then kill if we receive a SIGTERM for the parent process.

Automate rsync and creation of backup tarballs.


## Integration Testing

The integration tests require that the user running the tests can ssh to root@localhost witout having to enter the password; i.e., add the public ssh key of the user running the tests to the authorized keys of the root user on the localhost.

### Setting up to run Integration Tests in Eclipse

In order to setup Eclipse to run the integration tests and step through the code you will need to do the following

1. Setup the test environment.
```./run-tests.sh --setup-only```

1. Run Eclipse from the same terminal that you run the following.
```./run-tests-sh --export-env-vars-only```
