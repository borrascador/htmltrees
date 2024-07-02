from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='htmltrees',
    version='1.0.0',
    url='https://github.com/borrascador/htmltrees.git',
    author='Jan Tabaczynski',
    author_email='jantabaczynski@gmail.com',
    description='ASCII tree generator for HTML pages',
    long_description=long_description,
    packages=find_packages(),    
    install_requires=['beautifulsoup4 >= 4.12.3', 'soupsieve >= 2.5'],
)