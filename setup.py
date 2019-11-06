from setuptools import setup
import autofff

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as fh:
    install_requires = fh.readlines()

setup(name='autofff',
      version=autofff.__version__,
      description='Auto-generate FFF fake definitions for C API header files',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/ChiefGokhlayeh/autofff',
      author='Andreas Baulig',
      author_email='free.geronimo@hotmail.de',
      license='MIT',
      packages=['autofff'],
      zip_safe=False,
      classifiers=[
          "Programming Language :: Python :: 3.6",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],
      install_requires=install_requires)
