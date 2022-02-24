import sys
import argparse
import time
import numpy as np
from experiments import *

def parse_arguments():
	
	# argparse action to call the validation procedure of every experiment class
	class ValidateAllAction(argparse.Action):
		def __init__(self, option_strings, version=None, dest=None, default=None, help=None):
			super(ValidateAllAction, self).__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)
			self.version = version
		def print_line(self):
			print '-----------------------------------------------------------------------'
		def __call__(self, parser, namespace, values, option_string=None):
			
			self.print_line()
			print '\n Running complete validation (it takes around 65 minutes)...\n'

			t_start = time.time()

			# call the validation procedure of every experiment class
			for c in sorted([x.__name__ for x in experiment.__subclasses__()]):
				self.print_line()
				print 'validating script of experiment \'%s\'' % (c)
				self.print_line()

				exp = globals()[c]()

				p_start = time.time()
				exp.validate_script()
				p_runtime = time.time() - p_start

				print '\nRuntime: %f seconds\n' % p_runtime

			t_runtime = time.time() - t_start
			self.print_line()
			print '\nTotal runtime: %s minutes\n' % (t_runtime/60.0)
			self.print_line()

			parser.exit()

	# create the top-level parser
	parser = argparse.ArgumentParser(description='Proof of concept of Gabriel\'s PhD thesis.')
	parser.add_argument('--validate_all', dest='validate_all', action=ValidateAllAction, 
		help='validate all experiments')
		
	# create the sub-parsers (one for each experiment class)
	subparsers = parser.add_subparsers(help='experiment to run')
	for c in sorted([x.__name__ for x in experiment.__subclasses__()]):
		getattr(globals()[c], 'add_subparser_arguments')(subparsers)
	
	# process the received arguments
	args = parser.parse_args()

	return vars(args)

if __name__ == '__main__':

	# #########################
	# # TODO remove this block of code (used only for test purposes)
	# alg = ['ala18', 'indifferentMCT', 'weightedMCT'][1]
	# revenue_division_rate=0.99
	# sys.argv += ('aamas20 --logs-dir results --alg %s --net OW --k 12 --decay-alpha 0.999 --decay-eps 0.999 --revenue-division-rate %f --episodes 10000 --avf 10 --flex-dist DIST_TRUNC_NORMAL --flex-dist-params 0.5 0.1 0.0 1.0' % (alg, revenue_division_rate)).split()
	# #sys.argv += ('aamas20 --logs-dir results --alg indifferentMCT --net BBraess_1_2100_10_c1_2100 --k 4 --decay-alpha 0.999 --decay-eps 0.999 --episodes 10000 --avf 10 --flex-dist DIST_TRUNC_NORMAL --flex-dist-params 0.5 0.1 0.0 1.0').split()
	# #sys.argv += ('aamas20 --logs-dir results --alg %s --net SF --k 12 --decay-alpha 0.9997 --decay-eps 0.999 --episodes 10000 --avf 25' % alg).split()
	# #sys.argv += ('aamas20 --validate').split()
	# np.random.seed(123456789)
	# #########################

	args = parse_arguments()
	
	# instantiate the (chosen) experiment class
	exp = globals()[args['exp_class']]()
	exp.run(args)
	







