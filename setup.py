import os

from setuptools import setup, find_packages

__version__ = open(os.path.join(os.path.dirname(__file__), 'pycsp3/version.txt'), encoding='utf-8').read()

print("setup version", __version__)

setup(name='pycsp3',
      version=__version__,
      python_requires='>=3.10',
      project_urls={
          'Documentation': 'https://pycsp.org/',
          'Installation': 'https://pycsp.org/documentation/installation',
          'Models and Data': 'https://pycsp.org/models/',
          'Source': 'https://github.com/xcsp3team/pycsp3',
          'Issues': 'https://github.com/xcsp3team/pycsp3/issues',
          'Guide (arXiv)': 'https://doi.org/10.48550/arXiv.2009.00326'
      },
      author='Lecoutre Christophe, Szczepanski Nicolas',
      author_email='lecoutre@cril.fr, szczepanski@cril.fr',
      maintainer='Szczepanski Nicolas',
      maintainer_email='szczepanski@cril.fr',
      keywords='constraint programming, combinatorial optimization, modeling, CSP, COP, XCSP3, solver, AI',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Education',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3 :: Only',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12',
                   'Programming Language :: Python :: 3.13',
                   'Programming Language :: Python :: 3.14',
                   'Programming Language :: Python :: 3.15',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence',
                   'Topic :: Scientific/Engineering :: Mathematics',
                   'Topic :: Education'],
      packages=find_packages(exclude=["problems/g7_todo/"]),
      package_dir={'pycsp3': 'pycsp3'},
      install_requires=['lxml'],  # , 'py4j', 'numpy'],
      extras_require={'cosoco': ['cosoco>=2.6.1']},
      include_package_data=True,
      description='Modeling Constrained Combinatorial Problems in Python',
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8').read(),
      long_description_content_type='text/markdown',
      license='MIT',
      platforms=['Linux', 'macOS', 'Windows'])
