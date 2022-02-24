#import sys, os
#sys.path.insert(0, '..')

from abc import ABCMeta, abstractmethod

from os import listdir
from os.path import dirname, basename

# required to create the abstract class (compatible with Python 2 *and* 3)
ABC = ABCMeta('ABC', (object,), {'__slots__': ()}) 

# update the list of classes within this package
__all__ = [basename(f)[:-3] for f in listdir(dirname(__file__)) if f[-3:] == ".py" and not f.endswith("__init__.py")]

class experiment(ABC):
	
	@abstractmethod
	def validate_script(self):
		pass

	@abstractmethod
	def run(self, params):
		pass

	@abstractmethod
	def add_subparser_arguments(subparsers):
		pass

	@abstractmethod
	def add_subparser_arguments(subparsers):
		pass