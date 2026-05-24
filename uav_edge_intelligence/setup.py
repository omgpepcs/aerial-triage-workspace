import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'uav_edge_intelligence'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='alvaro',
    maintainer_email='alvaro@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'mock_node = uav_edge_intelligence.medical_sensor_mock:main',
            	'triage_node = uav_edge_intelligence.gcs_triage_node:main',
            	'uav02_node = uav_edge_intelligence.uav_02_bidder:main',
            	'navigator_node = uav_edge_intelligence.px4_navigator:main'
        ],
    },
)
