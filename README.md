# Backup Manager

https://cuyu.github.io/python/2016/08/15/Terminate-multiprocess-in-Python-correctly-and-gracefully
This is the solution for being able to kill an rsync job in the middle.  Actually run the rsync in a separate process that I can then kill if we receive a SIGTERM for the parent process.

Automate rsync and creation of backup tarballs.

## Integration Testing

The integration tests require that the user running the tests can ssh to root@localhost witout having to enter the password; i.e., add the public ssh key of the user running the tests to the authorized keys of the root user on the localhost.

### Setting up to run Integration Tests in VSCode

In order to setup VSCode to run the integration tests and step through the code you will need to do the following.  The requisite configs are already present in the provided `.vscode/settings.json` file.

1. Export the path to the version of python3.11 that you want to use.  If you already have one that will suffice, skip this step.
    ```
    export BACKUPMGRINTTEST_PYTHON=<path-to-python-binary>
    ```

1. Setup the test environment.  The following will create a `.env` file at the root of the repository that you can "import" into VSCode and build the test container.
    ```
    ./run-tests.sh --dev-setup-only
    ```

1. Configure VSCode
    1. Press `CTRL+SHIFT+P` and select **Python: Configure Tests**
    1. Select **pytest**.  Even though we are using the `unittest` library for testing this seems to be the only test configuration in VSCode that works for running and debugging the tests for the time being.
    1. Choose **backupmanager** as the root directory for the tests
    1. Click on the **Testing** icon in the left-hand side-bar and you should see a list of all of the tests that you can now run or debug.

        > If you do not see any tests listed or see an error in the panel check the **Output** Panel and select **Python** from the dropdown menu for any relevant error messages.


## Dependency Management

First-order dependencies for `requirements.txt`, `requirements_test.txt`, and `requirements_dev.txt` are defined in the respective `.in` files.  If you make updates to the first order dependencies you need to "compile" the full dependency list.  First, ensure that `pip-tools` is installed in your dev virtual environment.
```
pip install .[dev]
```

Then run the following
```
pip-compile -v --no-emit-trusted-host --no-emit-index-url requirements.in
pip-compile -v --no-emit-trusted-host --no-emit-index-url requirements_test.in
pip-compile -v --no-emit-trusted-host --no-emit-index-url requirements_dev.in
```
