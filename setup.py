from distutils.core import setup

setup(
    name='metamorph',
    version='0.1',
    packages=['lib', 'etc', 'plugins', 'plugins.library'],
    url='https://github.com/RHQE/metamorph',
    license='',
    author='Jiri Kulda',
    author_email='Kulda12@seznam.cz, jkulda@redhat.com',
    description='Exhibiting structural change of test metadata.', requires=['ansible']
)
