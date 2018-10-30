from setuptools import setup

# Load reStructedText description.
# Online Editor   - http://rst.ninjs.org/
# Quick Reference - http://docutils.sourceforge.net/docs/user/rst/quickref.html
readme = open('README.rst', 'r')
longdesc = readme.read()
readme.close()

setup(
  name='twnews',
  version='0.1.0',
  description='To tear down news webpages in Taiwan.',
  long_description=longdesc,
  url='https://github.com/virus-warnning/twnews',
  license='MIT',
  author='Raymond Wu',
  python_requires='>=3.7'
)
