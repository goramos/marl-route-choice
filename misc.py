import random
import scipy.stats as sc_stats
import collections

class Distribution(object):
	
	# available distributions
	DIST_FIXED = 1
	DIST_UNIFORM = 2
	DIST_NORMAL = 3
	DIST_TRUNC_NORMAL = 4
	__dist_list = {
		'DIST_FIXED': DIST_FIXED,
		'DIST_UNIFORM': DIST_UNIFORM,
		'DIST_NORMAL': DIST_NORMAL,
		'DIST_TRUNC_NORMAL': DIST_TRUNC_NORMAL
	}

	# set of default parameters for each distribution
	# (OrderedDicts were used here to keep track of the order of the parameters, 
	# which is useful when the class is initialised with a single list of 
	# parameters instead of setting one by one)
	__default_params = {}
	# set the general params
	__default_params[0] = collections.OrderedDict([('dist', DIST_TRUNC_NORMAL), ('precision', None), ('num_of_samples', 1)])
	# set the distributions' params
	__default_params[DIST_FIXED] = collections.OrderedDict([('value', 0.5)])
	__default_params[DIST_UNIFORM] = collections.OrderedDict([('min_value', 0.0), ('max_value', 1.0)])
	__default_params[DIST_NORMAL] = collections.OrderedDict([('mean', 0.5),	('deviation', 0.1)])
	__default_params[DIST_TRUNC_NORMAL] = collections.OrderedDict([('mean', 0.5), ('deviation', 0.1), ('min_value', 0.0), ('max_value', 1.0)])

	# parameters:
	# * dist: the distribution (as defined by the DIST_* constants above)
	# * precision: if set, then the samples will be rounded up to the specified decimal precision (otherwise values are not rounded)
	# * num_of_samples: specifies how many samples are expected to be drawn from this distribution (useful for efficiency purposes)
	# * kwargs: the parameters of the distribution, which can be defined individually (each with its own name) or as a list of values; the parameters themselves are specified by __default_params (which has the corresponding default values, in case no other values are set)
	def __init__(self, dist=DIST_TRUNC_NORMAL, precision=None, num_of_samples=1, **kwargs):
		
		# store the general parameters
		self.__default_params[0]['dist'] = dist
		self.__default_params[0]['precision'] = precision
		self.__default_params[0]['num_of_samples'] = num_of_samples

		# check if distribution parameters were correctly defined (and store them)
		# PS: the parameters can be informed one by one or as a single list
		if 'params_as_list' in kwargs: # params as a blind list of values

			# extract the parameters only if they were set, otherwise keep the defaults
			# (i.e., setting params_as_list to None is equivalent to setting no kwargs)
			if kwargs['params_as_list'] != None:

				if len(self.__default_params[dist].keys()) != len(kwargs['params_as_list']):
					raise Exception('List of parameters set for %s is invalid! Expected %s but received %s.' % (self.get_dist_name(dist), str(self.__default_params[dist].keys()).replace('\'', ''), kwargs['params_as_list']))

				for i, v in enumerate(self.__default_params[dist].keys()):
					self.__default_params[dist][v] = kwargs['params_as_list'][i]

		else: # named params

			for arg in kwargs:
				if arg in self.__default_params[dist]:
					self.__default_params[dist][arg] = kwargs[arg]
				else:
					raise Exception('Parameter \'%s\' is invalid for %s!' % (arg, self.get_dist_name(dist)))

		# call the general distribution initialisation
		self.__init_func()

	def __init_func(self):
		
		# get the general parameters' value
		dist = self.__default_params[0]['dist']
		precision = self.__default_params[0]['precision']
		num_of_samples = self.__default_params[0]['num_of_samples']

		# initialise the selected distribution
		if dist == self.DIST_FIXED:
			self.__init_fixed(
				value = self.__default_params[dist]['value']
			)
		elif dist == self.DIST_UNIFORM:
			self.__init_uniform(
				min_value = self.__default_params[dist]['min_value'], 
				max_value = self.__default_params[dist]['max_value']
			)
		elif dist == self.DIST_NORMAL:
			self.__init_normal(
				mean = self.__default_params[dist]['mean'], 
				deviation = self.__default_params[dist]['deviation']
			)
		elif dist == self.DIST_TRUNC_NORMAL:
			self.__init_truncated_normal(
				mean = self.__default_params[dist]['mean'], 
				deviation = self.__default_params[dist]['deviation'], 
				min_value = self.__default_params[dist]['min_value'], 
				max_value = self.__default_params[dist]['max_value'], 
				num_of_samples = int(num_of_samples)
			)
		else:
			raise Exception('Distribution \'%s\' is invalid!' % dist)
		
		# include round on the function, if desired
		if precision != None:
			self.__function_comp = self.__function
			self.__function = lambda: round(self.__function_comp(), precision)

	# fixed distribution that always returns value
	# Note: to be more precise, this could be seen as a uniform distribution in the interval [value, value]
	def __init_fixed(self, value):
		self.__function = lambda: value

	# uniform distribution in the interval [min_value, max_value]
	# Note: the interval is closed on both sides, but on the right it occurs less often (as explained by random.uniform documentation)
	def __init_uniform(self, min_value, max_value):
		self.__function = lambda: random.uniform(min_value, max_value)

	# normal distribution with mean mean and deviation standard deviation
	def __init_normal(self, mean, deviation):
		self.__function = lambda: random.gauss(mean, deviation)

	# truncated normal distribution in the interval [min_value, max_value] with mean mean and deviation standard deviation
	# Note: the complexity of this distribution is considerably higher than the previous ones
	def __init_truncated_normal(self, mean, deviation, min_value, max_value, num_of_samples):
		self.__trunc_norm_iter = iter(sc_stats.truncnorm((min_value-mean)/deviation, (max_value-mean)/deviation, loc=mean, scale=deviation).rvs(num_of_samples))
		self.__function = lambda: self.__trunc_norm_iter.next()
	
	# return a single, randomly generated sample of the distribution
	def sample(self):
		try:
			return self.__function()
		except StopIteration:
			self.__init_func()
			return self.__function()

	# return the name of a distribution given its id
	@staticmethod
	def get_dist_name(dist):
		return Distribution.__dist_list.keys()[Distribution.__dist_list.values().index(dist)]

	# return the id of a distribution given its name
	@staticmethod
	def get_dist_id(dist_name):
		return Distribution.__dist_list[dist_name]

	# return the list of available distributions
	@staticmethod
	def get_list_of_distributions():
		return Distribution.__dist_list.keys()

	# generate the specified number of samples and plot them as a histogram
	def plot_distribution(self, n_of_samples=1000000):
		
		import matplotlib.pyplot as plt

		# generate the specified number of samples
		samples = [ self.sample() for _ in xrange(n_of_samples) ]
		
		# plot them as a histogram
		plt.hist(samples, 100)
		plt.show()
