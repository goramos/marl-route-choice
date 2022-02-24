import numpy as np

#=======================================================================

class Driver:
	def __init__(self, od_pair, actions, initial_costs=None, extrapolate_costs=True, navigation_app=None, time_flexibility=0.5, flow=1.0): 
		
		#self.__name = 'Driver_%i' % identifier
		self.__OD_pair = od_pair
		
		# whether the average cost estimations should extrapolate 
		# the experimented costs
		self.__extrapolate_costs = extrapolate_costs
		
		# the navigation app of the driver
		self.__navigation_app = navigation_app
		
		# strategy (policy)
		self.__strategy = { a: 0.0 for a in actions }#initialising with initial_costs[a] produces almost the same results, but is more difficult to explain...
		
		# sum of the experimented costs (used to obtain the average cost)
		self.__sum_cost = 0.0
		
		self.__last_action = None
		
		# iteration counter
		self.__iteration = 0

		# the time-money trade-off (the higher time_flexibility is, the more the agent prefers 
		# saving money or, alternatively, the less it cares about travelling fast)
		self.__time_flexibility = time_flexibility

		# the flow controlled by the agent; it is within the interval ]0,d], 
		# where d is the total flow of the current agent's OD pair; the general setting is flow=1.0
		self.__flow = flow

		# for each action, store an [sum, samples, extrapolated_sum, avg, last, last_time] array, where:
		# * sum is the sum of costs experimented for this action (considering only those times when it is, in fact, chosen), 
		# * samples is the number of samples composing the sum (the number of times the action was chosen), 
		# * extrapolated_sum is an extrapolation of the sum of costs (when the action is not the chosen one, then the sum is incremented with the last value, given in the next field) and 
		# * avg is the average cost, which may be defined (using parameter self.__extrapolate_costs) considering the sum or the extrapolated_sum 
		# * last is the most updated cost of this action
		# * last_time is the most updated travel time of this action (useful for computing deltatolling)
		self.__history_actions_costs = { a: [0.0, 0.0, 0.0, 0.0, 0.0 if not initial_costs else initial_costs[a], 0.0 ] for a in actions } #although the last item is initialised with initial_costs, tests have shown that it makes no difference (as for the strategy initialisation)
		
		# estimated regret
		self.__estimated_regret = None
		self.__estimated_action_regret = { a: 0.0 for a in actions }

		# real regret
		self.__real_regret = 0.0

		# minimum average cost (stored here to enhance performance)
		self.__min_avg_cost = 0.0

	def get_strategy(self):
		return self.__strategy
	
	def get_last_action(self):
		return self.__last_action
	
	def get_OD_pair(self):
		return self.__OD_pair

	def get_flow(self):
		return self.__flow
	
	# calculate the driver's estimated regret
	def __estimate_regret(self):
		
		self.__estimated_regret = (self.__sum_cost / self.__iteration) - self.__min_avg_cost
		
		# estimated regret per action
		for a in self.__history_actions_costs:
			if not self.__extrapolate_costs and self.__history_actions_costs[a][1] == 0: #just to handle initial cases
				self.__estimated_action_regret[a] = 0.0
			else:
				self.__estimated_action_regret[a] = self.__history_actions_costs[a][3] - self.__min_avg_cost
	
	# calculate the real regret given the real minimum average cost
	def update_real_regret(self, real_min_avg):
		self.__real_regret = self.get_average_cost() - real_min_avg
	
	def get_real_regret(self):
		return self.__real_regret

	def get_estimated_regret(self, action=None):
		if action == None:
			return self.__estimated_regret
		else:
			return self.__estimated_action_regret[action]
	
	def get_last_cost(self):
		return self.__history_actions_costs[self.__last_action][4]
	
	def get_average_cost(self):
		return self.__sum_cost / self.__iteration

	def get_time_flexibility(self):
		return self.__time_flexibility
	
	#-------------------------------------------------------------------
	# choose action
	
	def choose_action(self, epsilon=None):
		
		# increment the iteration counter
		self.__iteration += 1
		
		# epsilon-greedy: choose the action with highest probability with probability 1-epsilon
		# otherwise, choose any action uniformly at random
		if np.random.random() < epsilon:
			self.__last_action = int(np.random.random() * len(self.__strategy)) #slightly slower than random.random, but it is less biased
		else:
			self.__last_action = max(self.__strategy, key=self.__strategy.get)

		# choose the action
		return self.__last_action

	#-------------------------------------------------------------------
	
	# compute the toll values
	def compute_toll_dues(self, cost, a_posteriori_MCT=False, indifferent_MCT=False, weighted_MCT=False, delta_tolling=False, thesis_delta_tolling=False, additional_cost=0.0):
		
		if indifferent_MCT:
			# indifferent preferences MCT
			# define a toll that makes agents indifferent with respect to time and money (i.e., it overrides their preferences)
			toll_mct = (cost - additional_cost) # original MCT (the marginal cost itself)
			self.__toll_dues = (toll_mct + cost * self.__time_flexibility) / self.__time_flexibility #the indifferent MCT

		elif weighted_MCT:
			# weighted MCT
			# define a toll proportional to the weighted marginal cost of agents (i.e., considering their preferences)
			# Note: this is NOT equivalent to the original MCT
			self.__toll_dues = additional_cost / self.__time_flexibility # additional_cost is the weighted marginal cost

		elif delta_tolling:
			prev_cost = self.__history_actions_costs[self.__last_action][5]
			self.__toll_dues = prev_cost - additional_cost

		elif thesis_delta_tolling: # old implementation used on my thesis (not incorrect, but less effective)
			prev_cost = self.__history_actions_costs[self.__last_action][4]
			self.__toll_dues = prev_cost - additional_cost

		else:
			# MCT with preferences
			# Note 1: this is equivalent to the original MCT if the preference parameter is 0.5 for all agents
			# Note 2: the expression is multiplied by 2 to make it fully compatible with the original MCT formulation (and to make the code retro-compatible with previous algorithms and validations)
			self.__toll_dues = cost - additional_cost # marginal cost

		return self.__toll_dues

	#-------------------------------------------------------------------
	
	# compute the total cost (considering travel time and tolls)
	def compute_cost(self, cost, additional_cost, indifferent_MCT):

		new_cost = (1.0 - self.__time_flexibility) * cost + self.__time_flexibility * self.__toll_dues - additional_cost

		# except for the indifferent_MCT, the cost is multiplied by 2 to make the preference-based MCT formulation fully compatible with the original MCT formulation (and to make the code retro-compatible with previous algorithms and validations)
		if not indifferent_MCT:
			new_cost *= 2.0 

		return new_cost

	#-------------------------------------------------------------------

	# update strategy
	def update_strategy(self, cost, alpha=None, regret_as_cost=False, a_posteriori_MCT=False, indifferent_MCT=False, weighted_MCT=False, delta_tolling=False, thesis_delta_tolling=False, additional_cost=0.0): #, additional_cost2=0.0):
		
		# store the dictionary locally to improve performance
		self_hac = self.__history_actions_costs

		# update most recent travel time of current taken action (useful for computing deltatolling)
		self_hac[self.__last_action][5] = cost 
		
		# if necessary, update the cost following the a posteriori MCT formulation 
		if a_posteriori_MCT or delta_tolling:
			cost = self.compute_cost(cost, additional_cost, indifferent_MCT)

		# update the sum of costs (used to compute the average cost)
		self.__sum_cost += cost
		
		# receive the recommendation
		recommendation = None
		if self.__navigation_app:
			recommendation = self.__navigation_app.get_recommendation(self.get_OD_pair())

		# update the costs history
		
		# Pt1: for the current action
		self_hac[self.__last_action][0] += cost #add current cost
		self_hac[self.__last_action][1] += 1 #increment number of samples
		self_hac[self.__last_action][4] = cost #update last cost
		#NOTE: position 5 in the array is updated earlier to keep the travel time (instead of cost)

		# Pt2: for all actions...
		self.__min_avg_cost = float('inf')
		for a in self_hac:
			
			# update the extrapolated sum
			self_hac[a][2] += self_hac[a][4] #add last cost to extrapolate estimation
		
			# compute the average cost
			if self.__extrapolate_costs:
				avg_cost = self_hac[a][2] / self.__iteration
			else:
				try: #just to handle initial cases
					avg_cost = self_hac[a][0] / self_hac[a][1]
				except ZeroDivisionError:
					avg_cost = 0
			
			self_hac[a][3] = avg_cost

			# incorporate the recommendation into the avg_cost;
			# observe that the recommendation is only used for
			# computing the latter term of regret (or, in the case
			# of maximising reward, the former term)  
			if recommendation:
				p=0.5
				avg_cost = avg_cost*(1-p) + recommendation[a]*p
			
			if avg_cost < self.__min_avg_cost:
				self.__min_avg_cost = avg_cost

		# update the regret
		self.__estimate_regret()
		if regret_as_cost:
			cost = self.get_estimated_regret(self.__last_action)
		
		# if necessary, update the cost following the a posteriori MCT formulation 
		# NOTE: the cost is computed in the end of this procedure only for the deltatolling version used on my thesis (whose implementation is still correct, though less effective)
		if thesis_delta_tolling:
			cost = self.compute_cost(cost, additional_cost, indifferent_MCT)

		# update the strategy
		self.__update_strategy_Q_learning(cost, alpha)
		
	#-------------------------------------------------------------------
	# Q-learning (stateless, so the gamma parameter is not required)
	def __update_strategy_Q_learning(self, normalised_cost, alpha):
		
		normalised_utility = 1 - normalised_cost
		
		self.__strategy[self.__last_action] = (1 - alpha) * self.__strategy[self.__last_action] + alpha * normalised_utility

#=======================================================================

class NavigationApp(object):
	
	def __init__(self, P):
		
		# store the problem instance
		self.__P = P
		
		# store all information of every route
		# OD
		# +-- route
		#     +----- avg
		#     +----- sum
		#     +----- samples
		self.__od_route_info = { od: [ {'avg':0.0, 'sum':0.0, 'samples':0, 'last':0.0} for _ in xrange(self.__P.get_route_set_size(od)) ] for od in self.__P.get_OD_pairs() }
		
		# store the recommendations (sorted list of routes) for each od pair
		# OD
		# +-- sorted list
		#self.__od_recommendation = { od: [ x for x in xrange(self.__P.get_route_set_size()) ] for od in self.__P.get_OD_pairs() }
		self.__od_recommendation = { od: [ 0.0 for _ in xrange(self.__P.get_route_set_size(od)) ] for od in self.__P.get_OD_pairs() }
		
	def update_info(self, normalise=False):
		
		# update the info structure
		for od in self.__P.get_OD_pairs():
			for r in xrange(self.__P.get_route_set_size(od)):
				self.__od_route_info[od][r]['last'] = self.__P.get_route(od, r).get_cost(normalise)
				self.__od_route_info[od][r]['sum'] += self.__od_route_info[od][r]['last']
				self.__od_route_info[od][r]['samples'] += 1
				self.__od_route_info[od][r]['avg'] = self.__od_route_info[od][r]['sum'] / self.__od_route_info[od][r]['samples']
			
			# update the recommendation for the current OD pair
			# as a list ordered by the 'avg' field (no sorting 
			# procedure is required because __od_route_info[od]
			# is already in the right order)
			#self.__od_recommendation[od] = sorted(self.__od_route_info[od], key=lambda k: k['avg'])
			self.__od_recommendation[od] = [ e['avg'] for e in self.__od_route_info[od]]  
			
	# return the current recommendation 
	def get_recommendation(self, od):
		return self.__od_recommendation[od]

#=======================================================================

