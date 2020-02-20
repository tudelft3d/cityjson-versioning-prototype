from setuptools import setup

setup(
    name='cjv',
    version='0.1',
    py_modules=['cjv'],
    install_requires=[
        'Click',
        'colorama',
        'networkx'
    ],
    entry_points='''
        [console_scripts]
        cjv=cjv:cli
    ''',
)
