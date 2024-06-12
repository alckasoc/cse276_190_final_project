from setuptools import find_packages, setup

package_name = 'go_pupper_srv'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lriek',
    maintainer_email='lriek@ucsd.edu',
    description='Go Pupper Service: Robot commands as a service',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['service = go_pupper_srv.service_go_pupper:main',
                            'client = go_pupper_srv.client_go_pupper:main',
                            'salsa = go_pupper_srv.sample_controller:main',
        ],
    },
)

