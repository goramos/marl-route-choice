from pylab import errorbar, plot
import matplotlib.pyplot as plt

#=======================================================================

class Plotter(object):
	
	def __init__(self, x_axis_range, title, x_axis_label, y_axis_label):
		self.__data = {}
		self.__x_axis = x_axis_range
		self.__title = title
		self.__x_axis_label = x_axis_label
		self.__y_axis_label = y_axis_label
	
	def add(self, variable, value):
		if variable not in self.__data:
			self.__data[variable] = []
		self.__data[variable].append(value)
	
	def plot(self):
		
		# create a figure
		fig = plt.figure(figsize=(7,4))
		
		# plot the data
		labels={}
		for d in self.__data:
			if isinstance(self.__data[d][0],list):
				labels[d] = errorbar(self.__x_axis, self.__data[d][0], yerr=self.__data[d][1])[0]
			else:
				labels[d] = plot(self.__x_axis, self.__data[d])[0]
		
		# set axes limits and captions
		plt.xlim(self.__x_axis[0], self.__x_axis[-1])
		#plt.ylim(0,1)#0.55)
		
		# some extra configuration
		fig.legend(labels.values(), labels.keys(), loc='upper right', bbox_to_anchor=(0.90,0.90))
		plt.title(self.__title)
		plt.xlabel(self.__x_axis_label)
		plt.ylabel(self.__y_axis_label)

		# show the plot
		plt.show()

#=======================================================================

class DynamicPlotter(object):
	
	def __init__(self, episodes, title, x_axis_label, y_axis_label, line_label, baseline=None, init_episode=1):
		
		self.__baseline = baseline if baseline else 0.0
		self.__init_episode = init_episode

		self.xdata = []
		self.ydata = []
		self.axes = plt.gca()
		self.axes.set_xlim(init_episode, episodes+init_episode)

		# create the data lines (one for the algorithm and another for the baseline, if specified)
		self.line_main, = self.axes.plot(self.xdata, self.ydata, 'r-', label=line_label)
		if baseline != None:
			self.line_opt, = self.axes.plot([x for x in xrange(init_episode,episodes+init_episode)], [self.__baseline for _ in xrange(init_episode,episodes+init_episode)], 'b--', label='Baseline')
		
		# some extra configuration
		plt.legend(loc='upper right')
		plt.title(title)
		plt.xlabel(x_axis_label)
		plt.ylabel(y_axis_label)

	def update(self, x, y):
		
		self.xdata.append(x+self.__init_episode)
		self.ydata.append(y)
		self.line_main.set_xdata(self.xdata)
		self.line_main.set_ydata(self.ydata)
		self.axes.set_ylim(self.__baseline*.95, max(self.ydata))
		plt.draw()
		plt.pause(1e-17)

	def show_final(self):
		plt.show()
		
#=======================================================================

class Statistics(object):

	def __init__(self, P, D, iterations, stat_regret_diff, plot_results, plotter, plotter_regret, stat_all, print_OD_pairs_every_episode):
		
		self.__P = P # problem instance
		self.__D = D # set of drivers
		
		# parameters of the problem instance
		self.__iterations = iterations
		self.__stat_regret_diff = stat_regret_diff
		self.__plot_results = plot_results
		self.__plotter = plotter
		self.__plotter_regret = plotter_regret
		self.__stat_all = stat_all
		self.__print_OD_pairs_every_episode = print_OD_pairs_every_episode

	#-------------------------------------------------------------------

	def print_statistics(self, S, v, best, sum_regrets, routes_costs_sum):

		# print the average regrets of each OD pair along the iterations
		print '\nAverage regrets over all timesteps (real, estimated, absolute difference, relative difference) per OD pair:'
		for od in self.__P.get_OD_pairs():
			print '\t%s\t%f\t%f\t%f\t%f' % (od, sum_regrets[od][0] / self.__iterations, sum_regrets[od][1] / self.__iterations, sum_regrets[od][2] / self.__iterations, sum_regrets[od][3] / self.__iterations)
		
		# print the average cost of each route of each OD pair along iterations
		print '\nAverage cost of routes:'
		for od in self.__P.get_OD_pairs():
			print od
			for r in xrange(int(self.__P.get_route_set_size(od))):
				routes_costs_sum[od][r] /= self.__iterations
				print '\t%i\t%f' % (r, routes_costs_sum[od][r])
		
		print '\nLast solution %s = %f' % (S, v)
		print 'Best value found was of %f' % best
		
		# print the average strategy (for each OD pair)
		print '\nAverage strategy per OD pair:'
		for od in self.__P.get_OD_pairs():
			strategies = { r: 0.0 for r in xrange(len(self.__P.get_routes(od))) }
			for d in self.__D:
				if d.get_OD_pair() == od:
					S = d.get_strategy()
					for s in S:
						strategies[s] += S[s]
			for s in strategies:
				strategies[s] = round(strategies[s] / self.__P.get_OD_flow(od), 3)
			print '\t%s\t%s' % (od, strategies)
		
		print '\nAverage expected cost of drivers per OD pair'
		expected_cost_sum = { od: 0.0 for od in self.__P.get_OD_pairs() }
		for d in self.__D:
			summ = 0.0
			for r in d.get_strategy():
				summ += d.get_strategy()[r] * routes_costs_sum[d.get_OD_pair()][r]
			expected_cost_sum[d.get_OD_pair()] += summ
		total = 0.0
		for od in self.__P.get_OD_pairs():
			total += expected_cost_sum[od]
			print '%s\t%f' % (od, expected_cost_sum[od] / self.__P.get_OD_flow(od))
		print 'Average: %f' % (total / self.__P.get_total_flow())

	#-------------------------------------------------------------------

	def print_statistics_episode(self, iteration, v, sum_regrets):
		
		# store the SUM of regrets over all drivers in the CURRENT timestep
		# for each od [w, x, y, z], where w and x represent the real and estimated 
		# regrets, and y and z represent absolute and relative difference between
		# the estimated and real regrets
		regrets = { od: [0.0, 0.0, 0.0, 0.0] for od in self.__P.get_OD_pairs() }
		
		gen_real = 0.0
		gen_estimated = 0.0
		gen_diff = 0.0
		gen_relative_diff = 0.0
		
		# compute the drivers' regret on CURRENT iteration
		
		for d in self.__D:
			
			# get the regrets
			real = d.get_real_regret()
			estimated = d.get_estimated_regret()

			# store in the appropriate space
			regrets[d.get_OD_pair()][0] += real
			regrets[d.get_OD_pair()][1] += estimated
			
			gen_real += real
			gen_estimated += estimated

		if self.__stat_regret_diff:
			for d in self.__D:
				
				# compute the regrets
				real = d.get_real_regret()
				estimated = d.get_estimated_regret()
				diff = abs(estimated - real)
				fxy = max(abs(estimated), abs(real))
				try: 
					relative_diff = (diff / fxy) #https://en.wikipedia.org/wiki/Relative_change_and_difference
				except ZeroDivisionError:
					relative_diff = 0.0

				# store in the appropriate space
				regrets[d.get_OD_pair()][2] += diff
				regrets[d.get_OD_pair()][3] += relative_diff
				
				gen_diff += diff
				gen_relative_diff += relative_diff
		
		# calculate the total averages
		gen_real /= self.__P.get_total_flow()
		gen_estimated /= self.__P.get_total_flow()
		if self.__stat_regret_diff:
			gen_diff /= self.__P.get_total_flow()
			gen_relative_diff /= self.__P.get_total_flow()
		
		str_print = '%d\t%f\t%f\t%f' % (iteration, v, gen_real, gen_estimated)
		if self.__stat_regret_diff:
			str_print = '%s\t%f\t%f' % (str_print, gen_diff, gen_relative_diff)
		
		# calculate the average regrets (real, estimated, absolute difference 
		# and relative difference) and then store and plot them (ALL iterations)
		to_print = []
		for od in self.__P.get_OD_pairs():
			
			# calculate the averages
			real = regrets[od][0] / self.__P.get_OD_flow(od)
			estimated = regrets[od][1] / self.__P.get_OD_flow(od)
			
			# store (over all timesteps)
			sum_regrets[od][0] += real
			sum_regrets[od][1] += estimated
			
			# plot
			if self.__plot_results:
				self.__plotter_regret.add('real %s' % od, real)
				self.__plotter_regret.add('estimated %s' % od, estimated)
			
			# store important information from current iteration
			to_print.append([real, estimated])
			
		if self.__stat_regret_diff:
			for iod, od in enumerate(self.__P.get_OD_pairs()):
				
				# compute the averages
				diff = regrets[od][2] / self.__P.get_OD_flow(od)
				relative_diff = regrets[od][3] / self.__P.get_OD_flow(od)
				
				# store (over all timesteps)
				sum_regrets[od][2] += diff
				sum_regrets[od][3] += relative_diff
				
				# plot
				if self.__plot_results:
					self.__plotter_regret.add('abs. diff. %s' % od, diff)
				
				# store important information from current iteration
				to_print[iod].append(diff)
				to_print[iod].append(relative_diff)
				
		# print important information from current iteration
		if self.__stat_all:
			str_add = ''
			if self.__print_OD_pairs_every_episode:
				str_add = '%s' % ('\t'.join(map(str, [item for sublist in to_print for item in sublist])))
			print '%s\t%s' % (str_print, str_add)

		# print the regrets on the last iteration
		#if iteration == iterations-1:
		#	print '\nDrivers\' regrets (last iteration):'
		#	print 'od\tstrategy\taction\tcost\taverage cost\testimated\treal\tabs diff\trelative difference'
		#	for d in self.__D:
		#		print '%s\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f' % (d.get_OD_pair(), d.get_strategy(), d.get_last_action(), d.get_last_cost(), d.get_average_cost(), estimated, real, diff, relative_diff)

		return gen_real, gen_estimated, gen_diff, gen_relative_diff, sum_regrets

#=======================================================================

