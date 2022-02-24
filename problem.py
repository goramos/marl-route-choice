from py_expression_eval import Parser
from sympy import diff, symbols

#=======================================================================

class ProblemInstance:
	
	def __init__(self, network_name, routes_per_OD=None, alt_route_file_name=None):
		
		self.__N = {}
		self.__L = {}
		self.__routes = {}
		self.__normalisation_factor_routes = float('-inf')
		
		self.__create_graph(network_name)
		
		self.__create_routes(network_name, routes_per_OD, alt_route_file_name)
		
		# reset the graph
		# this is necessary because, in order to compute the routes' 
		# normalisation factor, the links are created with maximum flow 
		self.reset_graph()
		
		# compute the free flow travel time of the routes
		# (it cannot be performed earlier because the graph
		# must be empty; but it was not, since the links are
		# created with maximum flow)
		for od in self.get_OD_pairs():
			for r in self.get_routes(od):
				r.set_free_flow_travel_time(r.get_cost(False), r.get_cost(True))
		
	def get_route_set_size(self, od=None):
		if od:
			return len(self.get_routes(od))
		else:
			return len(self.__routes[self.get_OD_pairs()[0]])
	
	def get_OD_order(self, od):
		return self.__OD_matrix.get_OD_order(od)
	
	def get_empty_solution(self):
		S = []
		
		for od in self.get_OD_pairs():
			S.append([0 for _ in self.get_routes_ids(od)])
		return S
	
	def get_OD_flow(self, od):
		return self.__OD_matrix.get_flow(od)
	
	def get_links(self):
		return self.__L.keys()
	
	def get_OD_pairs(self):
		return self.__OD_matrix.get_OD_pairs()
	
	def get_routes_ids(self, od_pair):
		return range(len(self.get_routes(od_pair)))
	
	def get_routes(self, od_pair=None):
		return self.__routes[od_pair]
	
	def get_route(self, od_pair, index):
		return self.__routes[od_pair][index]
	
	def get_link(self, link_name):
		return self.__L[link_name]
	
	def get_total_flow(self):
		return self.__OD_matrix.get_total_flow()	

	def get_normalisation_factor_routes(self):
		return self.__normalisation_factor_routes
	
	# read the graph from a file
	def __create_graph(self, network_name):
		
		OD_entries = []
		for line in open('networks/%s.net' % network_name, 'r'):
			
			# ignore \n
			line = line.rstrip()
			
			# ignore comments
			hash_pos = line.find('#')
			if hash_pos > -1:
				line = line[:hash_pos]
			
			# split the line
			taglist = line.split()
			if len(taglist) == 0:
				continue
			
			if taglist[0] == 'od':
				
				# if no flow is set for the OD pair, then 
				# it is not created (just to avoid problems
				# when computing OD-related statistics)
				if float(taglist[4]) > 0:
					
					OD_entries.append(taglist)
					
					# the set of routes is initialised (with the keys) here, 
					# but populated only in __create_routes
					self.__routes[taglist[1]] = []
		
		# create the OD matrix
		self.__OD_matrix = ODMatrix(OD_entries)
		total_flow = self.__OD_matrix.get_total_flow()
		
		F = {} # cost functions
		normalisation_factor = float('-inf')
		lineid = 0
		for line in open('networks/%s.net' % network_name, 'r'):
			
			lineid += 1
			
			# ignore \n
			line = line.rstrip()
			
			# ignore comments
			hash_pos = line.find('#')
			if hash_pos > -1:
				line = line[:hash_pos]
			
			# split the line
			taglist = line.split()
			if len(taglist) == 0:
				continue
			
			if taglist[0] == 'function':
				
				# process the params
				params = taglist[2][1:-1].split(',')
				if len(params) > 1:
					raise Exception('Cost functions with more than one parameter are not yet acceptable! (parameters defined: %s)' % str(params)[1:-1])
				
				# process the function
				expr = taglist[3]
				function = Parser().parse(expr)

				# compute the derivative of the function (for tolling)
				expr_deriv = str(diff(expr, params[0])) #compute derivative
				expr_deriv = expr_deriv.replace('**','^').replace(' ','') #convert syntax (from sympy to py_expression_eval)
				function_deriv = Parser().parse(expr_deriv) #create the function
				
				# handle the case where the parameter is not in the formula
				# (this needs to be handled because py-expression-eval does
				# not allows simplifying all variables of an expression)
				if taglist[1] not in function.variables():
					expr = '%s+%s-%s' % (expr, params[0], params[0])
					function = Parser().parse(expr)
					expr_deriv = '%s+%s-%s' % (expr_deriv, params[0], params[0])
					function_deriv = Parser().parse(expr_deriv)

				# process the constants
				constants = function.variables()
				if params[0] in constants: # the parameter must be ignored
					constants.remove(params[0])
				
				# store the function
				F[taglist[1]] = [params[0], constants, expr, expr_deriv, None]
			
			elif taglist[0] == 'node':
				self.__N[taglist[1]] = Node(taglist[1])
			
			elif taglist[0] == 'dedge' or taglist[0] == 'edge': # dedge is a directed edge
				
				# process the function
				func_tuple = F[taglist[4]] # get the corresponding function
				param_values = dict(zip(func_tuple[1], map(float, taglist[5:]))) # associate constants and values specified in the line (in order of occurrence)
				function = Parser().parse(func_tuple[2]) # create the function
				function = function.simplify(param_values) # replace constants

				# compute the function's first derivative w.r.t. the parameter
				function_deriv = Parser().parse(func_tuple[3])
				function_deriv = function_deriv.simplify(param_values)
				# check for zero division error, which shall happen when the parameter is a divisor (e.g., the BPR function)
				# Note: this is just a warning, since in this case we just need to assume the marginal cost to be zero (as done later, at link's marginal cost evaluation)
				try:
					function_deriv.evaluate({func_tuple[0]: 0.0})
				except ZeroDivisionError:
					if func_tuple[4] == None:
						# store a single warning message to avoid printing multiple ones
						func_tuple[4] = '[WARNING] The derivative (%s) of function %s (%s) has a parameter as divisor!' % (func_tuple[3], taglist[4], func_tuple[2])
				
				# create the edge(s)
				link_name = taglist[1]
				self.__L[link_name] = Link(link_name, taglist[2], taglist[3], function, function_deriv, func_tuple[0])
				if taglist[0] == 'edge':
					link_name = '%s-%s'%(taglist[3], taglist[2])
					self.__L[link_name] = Link(link_name, taglist[3], taglist[2], function, function_deriv, func_tuple[0])
				
				# store the greatest free flow time (used to normalise the links' costs)
				v = function.evaluate({func_tuple[0]: total_flow})
				if v > normalisation_factor:
					normalisation_factor = v
			
			elif taglist[0] == 'od':
				continue
			
			else:
				raise Exception('Network file does not comply with the specification! (line %d: "%s")' % (lineid, line))
		
		# print function warnings 
		for func in F:
			if F[func][4]:
				print F[func][4]

		# define the links' normalisation factor
		for l in self.__L.values():
			l.set_normalisation_factor(normalisation_factor)
			
			# set all links with maximum flow (used to calculate the 
			# normalisation factor, in function __create_routes)
			l.add_flow(self.get_total_flow())
		
	# read the set of routes from a file
	def __create_routes(self, network_name, routes_per_OD=None, alt_route_file_name=None):
		
		fname = 'networks/%s.routes' % network_name
		if alt_route_file_name != None:
			fname = alt_route_file_name # useful when an alternative route files must be used 
		f = open(fname, 'r')
		
		self.__normalisation_factor_routes = float('-inf')
		
		for line in f:
			
			# ignore \n
			line = line.rstrip()
			
			# ignore comments
			hash_pos = line.find('#')
			if hash_pos > -1:
				line = line[:hash_pos]
			
			# split the line
			spl = line.split()
			if len(spl) == 0:
				continue
			
			od = spl[0]
			
			# if the OD pair is not in the dictionary, it
			# means that it is invalid (e.g. zero flow)
			if od not in self.__routes:
				continue #self.__routes[od] = []
			
			# add the route to the list (up to routes_per_OD routes 
			# are stored for each OD pair) 
			if routes_per_OD <= 0 or len(self.__routes[od]) < routes_per_OD:
				route = Route(spl[1], self)
				self.__routes[od].append(route)
				
				if route.get_cost(False) > self.__normalisation_factor_routes:
					self.__normalisation_factor_routes = route.get_cost(False)
		
		#TODO find a better way of defining this value (OW 0.45, SF 0.05)
		# I believe this is a topology-demand-based question.
		if network_name == 'SF':
			self.__normalisation_factor_routes *= 0.05
		elif network_name == 'Berlin-Friedrichshain':
			self.__normalisation_factor_routes *= 0.1
		
		# set the normalisation factor on the routes
		for od in self.get_OD_pairs():
			for r in self.get_routes(od):
				r.set_normalisation_factor(self.__normalisation_factor_routes)
		
		f.close()
		
	# reset the graph non-fixed attributes (e.g., flow on each link)
	def reset_graph(self):
		# reset the flow and costs on links
		for l in self.__L:
			self.__L[l].reset()
		
		# reset the costs on routes
		for od in self.get_OD_pairs():
			for r in self.get_routes(od):
				r.update_cost()
	
	# evaluate the cost of a given assignment, where
	# - solution is the assignment itself (i.e., flow of each OD-route pair)
	# - solution_time_flexibility contains the aggregate time flexibility of agents (useful for tolling)
	# - check_consistency checks if the assignment is valid w.r.t. the total flow of the problem instance
	def evaluate_assignment(self, solution, solution_time_flexibility, check_consistency=True):
		
		# check if the solution is valid
		if check_consistency:
			if sum([ sum(x) for x in solution ]) != self.get_total_flow():
				print '[WARNING] The solution is not valid! (current flow %f differs from the expected one %f)' % (sum([ sum(x) for x in solution ]), self.get_total_flow())
		
		self.reset_graph()
		
		# update the flow (and aggregated time flexibility) on each link
		for i_od in xrange(len(solution)):
			for i_od_route in xrange(len(solution[i_od])):
				flow = solution[i_od][i_od_route]
				time_flexibility = solution_time_flexibility[i_od][i_od_route]
				if flow > 0.0:
					route = self.__routes[self.__OD_matrix.get_order_OD(i_od)][i_od_route]
					for link in route.get_links():
						self.__L[link].add_time_flexibility(time_flexibility) #time_flexibility needs to be added before flow
						self.__L[link].add_flow(flow)
		
		# update the routes' costs and compute the (normalised and non-normalised) 
		# total costs (i.e., the sum of travel time of all agents)
		total_cost = 0.0 # non-normalised
		normalised_total_cost = 0.0 # normalised
		for i_od in xrange(len(solution)):
			for i_od_route in xrange(len(solution[i_od])):
				route = self.__routes[self.__OD_matrix.get_order_OD(i_od)][i_od_route]
				route.update_cost()
				total_cost += route.get_cost(False) * solution[i_od][i_od_route]
				normalised_total_cost += route.get_cost(True) * solution[i_od][i_od_route]
		
		# compute the (normalised and non-normalised) average travel times
		avg_cost = total_cost / self.get_total_flow()
		normalised_avg_cost = normalised_total_cost / self.get_total_flow()

		
		# alternative way of calculating the average costs (according to Roughgarden's book, pg. 19)
		#~ att = 0.0
		#~ for l in self.__L:
			#~ att += self.__L[l].get_cost(False) * self.__L[l].get_flow()
		#~ att = att / self.get_total_flow()
		
		return avg_cost, normalised_avg_cost
		
#=======================================================================

# represents a node in the graph
class Node:
	def __init__(self, name):
		self.__name = name
		self.__out_edges = []
	
	def __str__(self):
		return self.__name

#=======================================================================

# represents a link in the graph
class Link:
	def __init__(self, name, origin, destination, cost_function, cost_function_deriv, param_name):
		self.__name = name
		self.__origin = origin
		self.__destination = destination
		
		self.__cost_function = cost_function
		self.__cost_function_deriv = cost_function_deriv
		self.__param_name = param_name

		# store the sum of time flexibility of all drivers using the 
		# present link (required for computing marginal cost tolls)
		# EXPLANATION: following the MCT definition, the toll on a link is 
		# 		flow * vdf_derivative 
		# a.k.a. the marginal cost; my generalised version includes a time 
		# flexibility parameter (\eta_i for driver i), which rewrites tolls as 
		# 		((1-\eta_1) * vdf_deriv) + ((1-\eta_2) * vdf_deriv) + ...
		# for all drivers 1, 2, ... using that link, which is equivalent 
		# to the original definition if \eta=1 for all drivers; to simplify 
		# the process, we can compute this generalised toll value as 
		# 		((1-\eta_1) + (1-\eta_2) + ...) * vdf_derivative
		# hence, this variable is used to store that sum of time flexibility, 
		# which reduces the complexity of computing the toll values
		self.__sum_time_flexibility = 0.0
		
		# used to compute the normalised cost
		self.__normalisation_factor = None

		# create/reset non-static variables (those that may change during simulations, like flow and cost)
		self.reset()
	
	def __get_cost(self, value):
		return self.__cost_function.evaluate({self.__param_name: value})
	
	def __get_cost_deriv(self, value):
		try:
			return self.__cost_function_deriv.evaluate({self.__param_name: value})
		except ZeroDivisionError:
			if value == 0.0:
				return 0.0
			else:
				raise Exception('Error on evaluating marginal cost of link %s with flow %f!' % (self.__name, value))

	def get_origin(self):
		return self.__origin
	
	def get_destination(self):
		return self.__destination
	
	def set_normalisation_factor(self, normalisation_factor):
		self.__normalisation_factor = normalisation_factor
		self.reset()
	
	# reset the flow and costs of the link
	# during instantiation, it is called by the __init__ method without
	# the normalisation factor, and thus without creating the normalised
	# cost; the normalised cost is created only after the 
	# set_normalisation_factor method is called
	def reset(self):
		self.__flow = 0.0
		self.__cost = self.__get_cost(self.__flow)
		self.__marginal_cost = self.__get_cost_deriv(self.__flow)
		if self.__normalisation_factor:
			self.__normalised_cost = self.__cost / self.__normalisation_factor
			self.__normalised_marginal_cost = self.__marginal_cost / self.__normalisation_factor
		self.__sum_time_flexibility = 0.0
	
	def add_time_flexibility(self, time_flexibility):
		self.__sum_time_flexibility += time_flexibility

	def get_marginal_cost(self):
		if self.__normalisation_factor:
			return self.__normalised_marginal_cost
		else:
			return self.__marginal_cost

	def add_flow(self, amount):
		self.__flow += amount
		
		# update the costs
		self.__cost = self.__get_cost(self.__flow)
		self.__marginal_cost = self.__sum_time_flexibility * self.__get_cost_deriv(self.__flow)
		if self.__normalisation_factor:
			self.__normalised_cost = self.__cost / self.__normalisation_factor
			self.__normalised_marginal_cost = self.__marginal_cost / self.__normalisation_factor
	
	def get_flow(self):
		return self.__flow
	
	def get_cost(self, normalise=False):
		if normalise:
			if self.__normalisation_factor:
				if self.__normalised_cost > 1:
					raise Exception('Error on cost normalisation of link %s (cost is %f and normalised cost is %f)!' % (self, self.__cost, self.__normalised_cost))
				return self.__normalised_cost
			else:
				raise Exception('Cost normalisation is not supported on link %s!'%self)
		else:
			return self.__cost
	
	def __str__(self):
		return self.__name

#=======================================================================

# represents a route
class Route:
	def __init__(self, route_str, problem_instance):
		
		self.__links = []
		self.__name = ''
		
		self.__cost = 0.0
		self.__normalised_cost = 0.0

		# store the weighted marginal cost of the route (i.e., the marginal 
		# cost considering the individual preferences/flexibility of agents)
		self.__weighted_marginal_cost = 0.0
		self.__normalised_weighted_marginal_cost = 0.0
		
		# used to compute the normalised cost
		self.__normalisation_factor = None
		
		# store the problem instance for updating the route cost
		self.__problem_instance = problem_instance
		
		# read the route from links
		spl = route_str.split(',')
		for l in spl:
			self.__links.append(l)
			link = self.__problem_instance.get_link(l)
			
			# create the route name (based on nodes)
			if self.__name == '':
				self.__name = link.get_origin()
			self.__name = '%s-%s' % (self.__name, link.get_destination())
			
		# update the route cost
		self.update_cost()
		
		# the free flow travel time
		self.__free_flow_travel_time = 0.0
		self.__free_flow_travel_time_normalised = 0.0
		
	def set_free_flow_travel_time(self, fftt, fftt_normalised):
		self.__free_flow_travel_time = fftt
		self.__free_flow_travel_time_normalised = fftt_normalised
	
	def get_free_flow_travel_time(self, normalise=False):
		if normalise:
			return self.__free_flow_travel_time_normalised
		else:
			return self.__free_flow_travel_time
		
	def set_normalisation_factor(self, normalisation_factor):
		self.__normalisation_factor = normalisation_factor
		self.update_cost()
	
	# update the route cost
	def update_cost(self):
		self.__cost = 0.0
		self.__normalised_cost = 0.0

		self.__weighted_marginal_cost = 0.0
		self.__normalised_weighted_marginal_cost = 0.0

		for l in self.__links:
			self.__cost += self.__problem_instance.get_link(l).get_cost()
			self.__weighted_marginal_cost += self.__problem_instance.get_link(l).get_marginal_cost()
			
		if self.__normalisation_factor:
			self.__normalised_cost = self.__cost / self.__normalisation_factor
			self.__normalised_weighted_marginal_cost = self.__weighted_marginal_cost / self.__normalisation_factor
		
	def get_cost(self, normalise=False):
		if normalise:
			if self.__normalised_cost > 1:
				# IMPORTANT: do not comment exception below
				raise Exception('Error on cost normalisation of route %s (cost is %f, normalised cost is %f and normalisation factor is %f)!' % (self, self.__cost, self.__normalised_cost, self.__normalisation_factor))
			return self.__normalised_cost
		else:
			return self.__cost

	def get_weighted_marginal_cost(self, normalise=False):
		if normalise:
			if self.__normalised_weighted_marginal_cost > 1:
				# IMPORTANT: do not comment exception below
				raise Exception('Error on marginal cost normalisation of route %s (cost is %f, normalised cost is %f and normalisation factor is %f)!' % (self, self.__weighted_marginal_cost, self.__normalised_weighted_marginal_cost, self.__normalisation_factor))
			return self.__normalised_weighted_marginal_cost
		else:
			return self.__weighted_marginal_cost
	
	def get_links(self):
		return self.__links
	
	def __str__(self):
		return self.__name
	
#=======================================================================

# stores the OD matrix
class ODMatrix:
	
	def __init__(self, OD_entries):
		
		# the OD matrix itself
		self.__OD_matrix = {}
		
		# keeps an additional, sorted list of OD pairs
		self.__OD_pairs = []
		
		# keeps the order of the OD pairs (used to ensure the ODs correspondence between different representations)
		self.__OD_order = {}
		
		# keeps the OD of each order (i.e., whereas the order itself is the value in OD_order, here it is the key)
		self.__order_OD = {}
		
		# the total number of vehicles
		self.__total_flow = 0.0
		
		self.__create_OD_matrix(OD_entries)
		
	def __create_OD_matrix(self, OD_entries):
		
		# read the OD matrix from a file
		order = 0
		for entry in OD_entries:
			od_name = entry[1]
			
			self.__OD_matrix[od_name] = float(entry[4])
			
			self.__OD_pairs.append(od_name)
			
			self.__OD_order[od_name] = order
			self.__order_OD[order] = od_name
			order += 1
	
			# compute the total flow
			self.__total_flow += float(entry[4])
		
	def get_total_flow(self):
		return self.__total_flow
	
	def get_OD_pairs(self):
		return self.__OD_pairs
		
	def get_flow(self, od):
		return self.__OD_matrix[od]
	
	def get_OD_order(self, od):
		return self.__OD_order[od]
	
	def get_order_OD(self, index):
		return self.__order_OD[index]

#=======================================================================
