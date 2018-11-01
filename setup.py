from setuptools import setup, find_packages

# Load reStructedText description.
# Online Editor   - http://rst.ninjs.org/
# Quick Reference - http://docutils.sourceforge.net/docs/user/rst/quickref.html
readme = open('README.rst', 'r')
longdesc = readme.read()
readme.close()

# See
# https://packaging.python.org/tutorials/packaging-projects/
# https://python-packaging.readthedocs.io/en/latest/non-code-files.html
setup(
    name='twnews',
    version='0.1.7',
    description='To tear down news web pages in Taiwan.',
    long_description=longdesc,
    packages=find_packages(),
    url='https://github.com/virus-warnning/twnews',
    license='MIT',
    author='Raymond Wu',
    package_data={
        'twnews': ['conf/*', 'samples/*']
    },
    install_requires=[
        'beautifulsoup4',
        'lxml',
        'requests'
    ],
    python_requires='>=3.7'
)
