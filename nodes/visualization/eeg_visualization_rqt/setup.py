from setuptools import setup, find_packages

setup(
    name='eeg_visualization_rqt',
    version='0.0.1',
    packages=find_packages(where='.'),
    package_dir={"": "."},
    package_data={
        'eeg_visualization_rqt': ['resource/*'],
    },
    install_requires=['setuptools'],
    zip_safe=True,
    author='tjalf',
    author_email='tjalf@example.com',
    maintainer='tjalf',
    maintainer_email='tjalf@example.com',
    url='https://github.com/TCUL8/-healthcare_demo',
    download_url='https://github.com/TCUL8/-healthcare_demo/releases',
    keywords=['ROS2', 'rqt', 'EEG', 'visualization'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
    ],
    description='RQT plugin for visualizing raw and preprocessed EEG data',
    long_description='A custom rqt plugin that displays real-time plots of EEG signals before and after preprocessing.',
    license='Apache-2.0',
    entry_points={
        'rqt_gui_py.plugins': [
            'eeg_visualization_rqt.eeg_visualization_widget.EEGVisualizationPlugin = eeg_visualization_rqt.eeg_visualization_widget:EEGVisualizationPlugin',
        ],
    },
    data_files=[
        ('share/eeg_visualization_rqt/resource', ['resource/eeg_visualization_rqt.xml']),
        ('share/eeg_visualization_rqt', ['package.xml']),
        ('share/ament_index/resource_index/packages', ['resource/eeg_visualization_rqt']),
    ],
)
