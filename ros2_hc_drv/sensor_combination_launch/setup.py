from setuptools import setup
from glob import glob
import os
"""
Setup for sensor_combination_launch package.

Copyright (c) 2026 TCUL8. All rights reserved.
"""

from glob import glob
import os
from setuptools import setup

package_name = 'sensor_combination_launch'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TCUL8',
    maintainer_email='your@email.com',
    description='Sensor combination launch package.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
