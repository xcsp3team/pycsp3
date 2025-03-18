import os

from setuptools import setup, find_packages

__version__ = open(os.path.join(os.path.dirname(__file__), 'pycsp3/version.txt'), encoding='utf-8').read()

print("setup version", __version__)

setup(name='pycsp3',
      version=__version__,
      python_requires='>=3',
      project_urls={
          'Documentation': 'https://pycsp.org/',
          'Installation': 'http://pycsp.org/documentation/installation',
          'Models and Data': 'http://pycsp.org/models/',
          'Git': 'https://github.com/xcsp3team/pycsp3'
      },
      author='Lecoutre Christophe, Szczepanski Nicolas',
      author_email='lecoutre@cril.fr, szczepanski@cril.fr',
      maintainer='Szczepanski Nicolas',
      maintainer_email='szczepanski@cril.fr',
      keywords='IA CP constraint modeling CSP COP',
      classifiers=['Topic :: Scientific/Engineering :: Artificial Intelligence', 'Topic :: Education'],
      packages=find_packages(exclude=["problems/g7_todo/"]),
      package_dir={'pycsp3': 'pycsp3'},
      install_requires=['lxml'],  # , 'py4j', 'numpy'],
      include_package_data=True,
      description='Modeling Constrained Combinatorial Problems in Python',
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8').read(),
      long_description_content_type='text/markdown',
      license='MIT',
      platforms='LINUX')
