from setuptools import setup

package_name = 'openbci_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Monica Perez-Serrano',
    maintainer_email='moperez@ethz.ch',
    description='ROS 2 driver for OpenBCI Cyton boards using healthcare_msgs/EEG',
    license='MIT',
    entry_points={
        'console_scripts': [
            'openbci_driver = openbci_driver.openbci_driver:main',
        ],
    },
)