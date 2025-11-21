To set up the environment for `emerge`, follow these steps:

1.  **Create a Python virtual environment:**
    ```bash
    python3 -m venv venv
    ```

2.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```
    *(Note: You'll need to do this every time you work on the project in a new terminal session.)*

3.  **Install the required dependencies:**
    ```bash
    pip install wheel && pip install -r requirements.txt
    ```

4.  **Install `setuptools`:**
    This is required to run the tests and the application.
    ```bash
    pip install setuptools
    ```

5.  **Create the export directory:**
    This directory is required by the default configuration file.
    ```bash
    mkdir -p ./emerge/export/emerge
    ```

After these steps, your environment is set up. You can verify it by running the tests:

```bash
python run_tests.py
```

And then run `emerge` on its own codebase:

```bash
python emerge.py -c emerge/configs/emerge.yaml
```
