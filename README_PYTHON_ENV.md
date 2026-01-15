## Python Virtual Environment and Dependencies

This project uses a Python virtual environment for all Python dependencies, including EEG processing libraries like `mne`.

- The default venv path is: `/home/tjalf/ros2_ws/src/-healthcare_msgs_demonstration/.venv`
- All scripts and launch commands should use the Python interpreter from this venv:
  
  ```bash
  /home/tjalf/ros2_ws/src/-healthcare_msgs_demonstration/.venv/bin/python <script.py>
  ```
- If you install new Python packages, always activate the venv or use the full path to `pip`:
  
  ```bash
  /home/tjalf/ros2_ws/src/-healthcare_msgs_demonstration/.venv/bin/pip install <package>
  ```
- This ensures all dependencies (e.g., `mne`, `numpy`, `matplotlib`) are available to your scripts and ROS 2 nodes.

If you encounter `ModuleNotFoundError` for any package, verify you are using the correct Python environment as above.
