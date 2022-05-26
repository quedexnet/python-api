from setuptools import setup

# TODO: add pgpy once 4.0.2 released to PyPI
setup(
  name='quedex_api',
  version='0.1.0',
  packages=['quedex_api'],
  install_requires=[
    'autobahn==17.6.2',
    'twisted==22.4.0',
    'cryptography==2.0.3',
    'pyOpenSSL==17.1.0',
    'pgpy==0.4.2',
    'six==1.10.0'
  ],
)
