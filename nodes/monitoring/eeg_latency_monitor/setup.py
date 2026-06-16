from setuptools import setup, find_packages

package_name = 'eeg_latency_monitor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'influxdb-client',
        'python-dotenv'
    ],
    zip_safe=True,
    maintainer='Tjalf',
    maintainer_email='tjalf@ethz.ch',
    description='ROS2 node for monitoring EEG pipeline latency',
    license='MIT',
    entry_points={
        'console_scripts': [
            'eeg_latency_monitor = monitoring.eeg_latency_monitor:main',
        ],
    },
)