# python-atomic-write
Safely, atomically write a file using python.

This demonstrates simple atomic writes to a file, often useful for file-IPC between threads or processes without locking.

To run the demo, simply clone the repo and run `./writer.py`

To see what can happen when you do not use atomic writes, change the write thread to use the unsafe function and run. You should quickly hit a race condition where the read thread will read the status file while it is being written, causing the read thread to read in an incomplete JSON structure and crash.
``` python
        write_status_safe(new_status, new_message, status_file)
        # write_status_unsafe(new_status, new_message, status_file)
```
