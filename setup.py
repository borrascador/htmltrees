from setuptools import setup, find_packages

setup(
    name='htmltrees',
    version='1.0.0',
    url='https://github.com/borrascador/htmltrees.git',
    author='Jan Tabaczynski',
    author_email='jantabaczynski@gmail.com',
    description='ASCII tree generator for HTML pages',
    packages=find_packages(),    
    install_requires=['beautifulsoup4 >= 4.12.3', 'soupsieve >= 2.5'],
)