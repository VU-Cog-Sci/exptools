from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()


version = '0.3.1'

install_requires = [
    'quest',
    'numpy',
    'psychopy',
    'pygame',
    # 'pygaze',
    # 'pylink', # this is not the pylink that we want to be using
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
]


setup(name='exptools',
    version=version,
    description="Experimental tools of the Knapen lab at the Vrije Universiteit",
    long_description=README,
     classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='',
    author='Gilles de Hollander, Tomas Knapen, Daan van Es',
    author_email='gilles.de.hollander@gmail.com',
    url='https://github.com/Gilles86/exp_tools',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires, 
)
