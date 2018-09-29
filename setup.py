from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='autofff',
      version='0.2',
      description='Auto-generate FFF fake definitions for C API header files',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/FreeGeronimo/autofff',
      author='Andreas Baulig',
      author_email='free.geronimo@hotmail.de',
      license='MIT',
      packages=['autofff'],
      zip_safe=False,
      classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ])