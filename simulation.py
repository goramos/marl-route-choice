from agent import Driver, NavigationApp
from misc import Distribution
from analytics import *
import sys
import random
import scipy.stats as sc_stats
import matplotlib.pyplot as plt
from decimal import Decimal

# return the cost observed by agent d after taking its action
# (created this method to avoid redundant code)
def get_cost(P, d, difference_rewards, difference_reward_per_route, NORMALISE_COSTS):
	cost = 0.0
	route = P.get_route(d.get_OD_pair(), d.get_last_action())
	if difference_rewards:
		cost = difference_reward_per_route[d.get_OD_pair()][d.get_last_action()][d.get_flow()]
	else:
		cost = route.get_cost(NORMALISE_COSTS)
	return cost

# run_simulation: run a route choice simulation
# Parameters:
# * P: problem instance
# * iterations: number of iterations
# * alpha: learning rate
# * epsilon: exploration rate
# * alpha_decay: decay rate on the learning rate
# * epsilon_decay: decay rate on the exploration rate
# * min_alpha: minimum value for learning rate (lower bound consider it is decaying)
# * min_epsilon: minimum value for exploration rate (lower bound consider it is decaying)
# * normalise_costs: whether or not cost functions should be normalised in the interval [0,1]
# * regret_as_cost: whether or not regret should be used as reinforcement signal
# * extrapolate_costs: whether or not regret estimates should extrapolate over all episodes (True; in this case, an action's most recent reward is assumed to remain unchanged when it is not taken) or over the experimented ones only (False)
# * use_app: whether or not the navigation app should be used
# * difference_rewards: whether or not difference rewards should be used as reinforcement signal
# * a_posteriori_MCT: whether or not marginal-cost tolling should be used
# * indifferent_MCT: employs the MCT with indifferent preferences 
# * weighted_MCT: employs the weighted MCT
# * delta_tolling: whether or not delta-tolling (an MCT-based scheme, by Sharon+2017aamas) should be used
# * thesis_delta_tolling: whether or not delta-tolling (similar to above, but using the version implemented with my thesis, which is still correct, though less effective) should be used
# * revenue_division_rate: fraction of the total revenue (collected from tolls) to be divided among the agents
# * time_flexibility_distribution: specifies the probability distribution from which the drivers' time flexibility (over money) should be drawn
# * agent_vehicles_factor: specifies the number of vehicles each agent should control (it can even be a fraction)
# * ignore_avf_difference_rewards: whether agents should be considered one unit (or agent_vehicles_factor units) flow each when computing the difference rewards
# * plot_results: whether or not results should be plotted
# * dynamic_plot_results: whether or not results should be plotted in real time
# * stat_all: whether or not a report with simulation statistics should be printed after the simulation is completed
# * stat_regret_diff: whether or not the above report should print additional regret statistics (absolute and relative difference between estimated and real regrets) as well
# * print_OD_pairs_every_episode: whether or not information about each OD pair should be printed on every episode
def run_simulation(P, iterations=1000, alpha=0.5, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=False, use_app=False, difference_rewards=False, a_posteriori_MCT=False, indifferent_MCT=False, weighted_MCT=False, delta_tolling=False, thesis_delta_tolling=False, revenue_division_rate=0.0, time_flexibility_distribution=None, agent_vehicles_factor=1.0, ignore_avf_difference_rewards=True, plot_results=False, dynamic_plot_results=False, stat_all=True, stat_regret_diff=True, print_OD_pairs_every_episode=True):
	
	ITERATIONS = iterations
	
	ALPHA = alpha
	ALPHA_DECAY = alpha_decay
	MIN_ALPHA = min_alpha
	EPSILON = epsilon
	EPSILON_DECAY = epsilon_decay
	MIN_EPSILON= min_epsilon
	
	NORMALISE_COSTS = normalise_costs
	
	REGRET_AS_COST = regret_as_cost
	
	# if no distribution was defined for time flexibility, then instantiate a default fixed distribution
	if not isinstance(time_flexibility_distribution, Distribution):
		time_flexibility_distribution = Distribution(Distribution.DIST_FIXED)

	# create a plotter
	plotter = None
	plotter_regret = None
	if plot_results:
		plotter = Plotter(x_axis_range=range(1,ITERATIONS+1), title='Average travel time along episodes', x_axis_label='episodes', y_axis_label='average travel time')
		plotter_regret = Plotter(x_axis_range=range(1,ITERATIONS+1), title='Average regret along episodes', x_axis_label='episodes', y_axis_label='regret')

	# create a dynamic plotter
	dyn_plotter = None
	if dynamic_plot_results:
		dyn_plotter = DynamicPlotter(ITERATIONS, title='Average travel time along episodes', x_axis_label='episodes', y_axis_label='average travel time', line_label='algorithm', baseline=66.92)
	
	# create an instance of the navigation app
	app = NavigationApp(P)
	app_to_agent = None
	if use_app:
		app_to_agent = app
	
	# create the drivers
	D = [] # set of drivers
	flow_rates = set([agent_vehicles_factor]) # set of flow rates in use, defined as [agent_vehicles_factor] U [ r_od | od in OD ], where r_od is the remainder flow of OD pair od; this set is necessary to efficiently compute the difference rewards
	for od in P.get_OD_pairs():

		# specifies the number of vehicles each agent should control
		# if int(P.get_OD_flow(od)) % agent_vehicles_factor != 0:
		# 	print '[ERROR] The agent_vehicles_factor should be multiple of all OD pairs! (OD="%s", flow=%d, agent_vehicles_factor=%d)' % (od, int(P.get_OD_flow(od)), agent_vehicles_factor)
		# 	return 0
		# n_of_agents = int(P.get_OD_flow(od)) / agent_vehicles_factor
		# n_of_agents = int(P.get_OD_flow(od) / float(agent_vehicles_factor))
		# remainder = P.get_OD_flow(od) % float(agent_vehicles_factor)

		
		#n_of_agents = int(P.get_OD_flow(od) / float(agent_vehicles_factor))
		#remainder = P.get_OD_flow(od) - n_of_agents * float(agent_vehicles_factor)
		# compute the number of vehicles and the remainder flow (if it exists); the Decimal class
		# is used to minimise the problems associated with floating point errors (IEEE 754; 
		# e.g., when flow=49.95 or 500.001 and avf=25 or even when flow=0.3 and avf=0.1) 
		n_of_agents = int( Decimal(str(P.get_OD_flow(od))) / Decimal(str(float(agent_vehicles_factor))) )
		remainder = float( Decimal(str(P.get_OD_flow(od))) - Decimal(str(n_of_agents)) * Decimal(str(float(agent_vehicles_factor))) )
		# if n_of_agents * agent_vehicles_factor + remainder != P.get_OD_flow(od):
		# 	raise Exception('Error with decimal representation!  (OD_flow=%f, agent_vehicles_factor=%f, n_of_agents=%f, remainder=%f)' % (P.get_OD_flow(od), agent_vehicles_factor, n_of_agents, remainder))
		if remainder > 0:
			n_of_agents += 1 # this extra agent controls the remainder flow
			flow_rates.add(remainder)

		# create the set of actions
		actions = range(len(P.get_routes(od)))
		
		# compute the initial costs (used to initialise the estimated 
		# regret values)
		initial_costs = []
		for r in P.get_routes(od):
			initial_costs.append(r.get_cost(NORMALISE_COSTS))
		
		# create the drivers
		#print 'OD pair %s has %d agents with %f flow each (remainder is %f)' % (od, n_of_agents, agent_vehicles_factor, remainder)
		for i in xrange(n_of_agents):
			flow = agent_vehicles_factor
			if i == 0 and remainder > 0.0:
				flow = remainder
			D.append(Driver(od, actions, initial_costs=initial_costs, extrapolate_costs=extrapolate_costs, navigation_app=app_to_agent, time_flexibility=time_flexibility_distribution.sample(), flow=flow))
	
	# check if the sum of agents' flow match the OD matrix
	od_flow_check = { od: Decimal('0.0') for od in P.get_OD_pairs() }
	for d in D:
		od_flow_check[d.get_OD_pair()] += Decimal(str(d.get_flow()))
	errors_count = 0
	for od in od_flow_check:
		ofc = Decimal(str(P.get_OD_flow(od)))
		if ofc != od_flow_check[od]:
			print '[ERROR] OD pair %s should have a flow of %f but has of %f (difference of %f)!' % (od, ofc, od_flow_check[od], ofc-od_flow_check[od])
			errors_count += 1
	if errors_count > 0:
		raise Exception('Error on the decimal representation of %d OD pairs!' % errors_count)

	# create structures to store difference rewards 
	# (to avoid computing the difference of each driver) 
	# (this structure is recomputed at each iteration)
	# (the innermost dictionary generalises the algorithm to infinitesimal and non-uniform flows, rather than always 1)
	if difference_rewards:
		# difference reward per link
		difference_reward_per_link = { link : { fr: 0.0 for fr in flow_rates} for link in P.get_links() }

		# difference reward per route and OD pair
		difference_reward_per_route = { od: [ { fr: 0.0 for fr in flow_rates} for _ in xrange(P.get_route_set_size(od)) ] for od in P.get_OD_pairs() }
	else:
		difference_reward_per_route = None

	# sum of routes' costs along time (used to compute the averages)
	routes_costs_sum = { od: [ 0.0 for _ in xrange(P.get_route_set_size(od)) ] for od in P.get_OD_pairs() }
	routes_costs_min = { od: 0.0 for od in P.get_OD_pairs() }
	
	# sum of the average regret per OD pair (used to measure the 
	# averages along time)
	# for each OD pair, it stores a tuple [w, x, y, z], with w the average 
	# real regret, x the average estimated regret, y the average absolute
	# difference between them, and z the relative difference between them
	sum_regrets = { od : [0.0, 0.0, 0.0, 0.0] for od in P.get_OD_pairs() }
	
	# declare the report functions locally to improve performance
	stats = Statistics(P, D, ITERATIONS, stat_regret_diff, plot_results, plotter, plotter_regret, stat_all, print_OD_pairs_every_episode)
	
	if stat_all:

		# print the report headings
		head1 = '\tgeneral\t\t'
		head2 = 'it\tavg-tt\treal\test'
		if stat_regret_diff:
			head1 = '%s\t\t' % (head1)
			head2 = '%s\tdiff\treldiff' % (head2)
		if print_OD_pairs_every_episode:
			for od in P.get_OD_pairs():
				head1 = '%s\t%s\t' % (head1, od)
				head2 = '%s\treal\test' % (head2)
				if stat_regret_diff:
					head1 = '%s\t\t' % (head1)
					head2 = '%s\tdiff\treldiff' % (head2)
		print head1
		print head2

	# run the simulation
	best = float('inf')
	for iteration in xrange(ITERATIONS):
		
		# flush stdout
		sys.stdout.flush()

		#-------------------------------------------
		# generate an empty solution
		
		# store the flow of vehicles for each OD-route pair
		S = P.get_empty_solution()

		# store the sum of agents' time flexibility for each OD-route pair
		S_time_flexibility = P.get_empty_solution()

		#-------------------------------------------
		# choose actions
		
		for d in D:

			# choose the action
			a = d.choose_action(EPSILON)

			# update the assignment
			od = P.get_OD_order(d.get_OD_pair())
			S[od][a] += d.get_flow()

			# update the sum of time flexibility of the vehicles within this route
			S_time_flexibility[od][a] += d.get_flow() * (1 - d.get_time_flexibility())
		
		if EPSILON > MIN_EPSILON:
			EPSILON = EPSILON * EPSILON_DECAY
		else:
			EPSILON = MIN_EPSILON
		
		#-------------------------------------------
		# update network

		# compute the (non-normalised) average travel time and the (normalised) total cost
		v, norm_v = P.evaluate_assignment(S, S_time_flexibility) 

		if v < best:
			best = v
		
		if plot_results:
			plotter.add('average travel time', v)

		if dynamic_plot_results:
			dyn_plotter.update(iteration, v)
		
		# compute the difference reward for each route of each OD pair
		if difference_rewards:
			
			# NOTE: the complexity of computing the difference for each route is much higher
			# than computing for each link. The latter, however, should be calculated in a
			# different way to account for the fact that some links are used by multiple routes.
			# What I did here is to firstly computing how much a single (one) unit of flow contributes 
			# to the total cost (cost * flow) of each link. Such a difference can then be summed up 
			# for each route, whose difference is then obtained as D = (x(c')-A) / (x^2-x), where
			# x is the total flow, A is the total cost (i.e., the sum of travel times experienced by
			# all agents), and c' is the sum of cost difference of each link.
			# Also important: the costs normalisation must be done on routes (rather than on links) 
			# because the normalisation factors for links and routes are not the same.


			# compute the cost difference of each link
			for link_name in P.get_links():

				link = P.get_link(link_name)

				for fr in flow_rates:

					if link.get_flow() > 0:

						# get the current total cost (cost * flow) of the link
						tc_link = link.get_cost(False) * link.get_flow()

						# define the amount of flow to compute the difference; the usual amount is 1.0
						# (i.e., each agent controls one unit of flow), but this value may vary if agents
						# control a different fraction of flow (e.g., if agent_vehicles_factor = 0.3)
						flow_to_add = fr
						if ignore_avf_difference_rewards:
							flow_to_add = 1.0

						# remove one unit of flow and compute the new total cost (cost * flow) of the link
						link.add_flow(-flow_to_add)
						tc_link_minus_one = link.get_cost(False) * link.get_flow()

						# undo the flow change (the cost is then automatically updated)
						link.add_flow(+flow_to_add)

						# compute (and store) the link's cost difference
						difference_reward_per_link[link_name][fr] = tc_link - tc_link_minus_one
					
					else:
						difference_reward_per_link[link_name][fr] = 0.0

			# compute the difference of each route
			tf = P.get_total_flow() # total flow
			tc = norm_v * tf # total cost
			for od in P.get_OD_pairs():
				for r in xrange(int(P.get_route_set_size(od))):
					for fr in flow_rates:
					
						# sum the links' cost differences
						sum_diff = 0.0
						for link_name in P.get_route(od, r).get_links():
							sum_diff += difference_reward_per_link[link_name][fr]
						
						if NORMALISE_COSTS:
							sum_diff /= P.get_normalisation_factor_routes()

						# compute (and store) the route's difference
						difference_reward_per_route[od][r][fr] = (tf * sum_diff - tc) / (tf * (tf - 1.0))
			
		#-------------------------------------------
		# update strategies
		
		# compute the tolls first
		# additionally, compute the revenue (from tolls) to be redistributed among the agents
		if a_posteriori_MCT or delta_tolling or thesis_delta_tolling:
			
			if revenue_division_rate > 0.0:
				tolls_share_per_OD = [ 0.0 for _ in xrange(len(P.get_OD_pairs())) ]

			for d in D:
				
				route = P.get_route(d.get_OD_pair(), d.get_last_action())
				
				# compute the cost
				cost = get_cost(P, d, difference_rewards, difference_reward_per_route, NORMALISE_COSTS)

				# toll-based methods required additional values to compute rewards: 
				# weighted MCT needs the weighted marginal costs
				if weighted_MCT:
					additional_cost = route.get_weighted_marginal_cost(NORMALISE_COSTS)
				# other methods need the free flow travel time
				else:
					additional_cost = route.get_free_flow_travel_time(NORMALISE_COSTS)

				# compute the toll
				toll = d.compute_toll_dues(cost, a_posteriori_MCT=a_posteriori_MCT, indifferent_MCT=indifferent_MCT, weighted_MCT=weighted_MCT, delta_tolling=delta_tolling, thesis_delta_tolling=thesis_delta_tolling, additional_cost=additional_cost)

				# update the total revenue 
				if revenue_division_rate > 0.0:
					od = P.get_OD_order(d.get_OD_pair())
					tolls_share_per_OD[od] += toll

			# compute the share to be redistributed with the agents
			if revenue_division_rate > 0.0:
				for od in P.get_OD_pairs():
					tolls_share_per_OD[P.get_OD_order(od)] = (tolls_share_per_OD[P.get_OD_order(od)] * revenue_division_rate) / P.get_OD_flow(od)

		# update the strategies
		for d in D:
			
			# compute the cost
			cost = get_cost(P, d, difference_rewards, difference_reward_per_route, NORMALISE_COSTS)
			
			if a_posteriori_MCT or delta_tolling or thesis_delta_tolling: 
				
				additional_cost = 0.0
				if revenue_division_rate > 0.0:
					additional_cost = tolls_share_per_OD[P.get_OD_order(d.get_OD_pair())]

				d.update_strategy(cost, ALPHA, REGRET_AS_COST, a_posteriori_MCT=a_posteriori_MCT, indifferent_MCT=indifferent_MCT, weighted_MCT=weighted_MCT, delta_tolling=delta_tolling, thesis_delta_tolling=thesis_delta_tolling, additional_cost=additional_cost)
			else:
				d.update_strategy(cost, ALPHA, REGRET_AS_COST)
				
		
		# agents use initial (before trip) recommendations to compute their regret
		# NOTE: the update is made only after the recommendation because, otherwise, 
		# extra data structures would be required to store the initial recommendation
		# before the update
		app.update_info(NORMALISE_COSTS)
		
		if ALPHA > MIN_ALPHA:
			ALPHA = ALPHA * ALPHA_DECAY
		else:
			ALPHA = MIN_ALPHA
		
		#-------------------------------------------
		# compute the episode statistics

		# update the sum of routes' costs (used to compute the averages)
		for od in P.get_OD_pairs():
			for r in xrange(int(P.get_route_set_size(od))):
				cc = P.get_route(od, r).get_cost(NORMALISE_COSTS)
				if a_posteriori_MCT or delta_tolling or thesis_delta_tolling:
					# NOTE: I do not know exactly why, but regret is not being computed  
					# properly in the case of delta_tolling. I tried to consider not 2*cc, 
					# but cc + most_recent_cost (which in theory is the right way). However, 
					# the results remain weird. I decided to use the same way as for the
					# a_posteriori_MCT, to make things simple. Therefore, the real regret
					# should NOT be reported in its current form.
					cc = 2*cc - P.get_route(od, r).get_free_flow_travel_time(NORMALISE_COSTS)
				routes_costs_sum[od][r] += cc
			routes_costs_min[od] = min(routes_costs_sum[od]) / (iteration + 1)
		
		# compute the agents' real regret
		for d in D:
			d.update_real_regret(routes_costs_min[d.get_OD_pair()])

		if stat_all or iteration == ITERATIONS-1:
			gen_real, gen_estimated, gen_diff, gen_relative_diff, sum_regrets = stats.print_statistics_episode(iteration, v, sum_regrets)
	
	# keep the dynamic plot visible in the end of simulation
	if dynamic_plot_results:
		dyn_plotter.show_final()

	# print (and compute) the statistics
	if stat_all:

		stats.print_statistics(S, v, best, sum_regrets, routes_costs_sum)
		
		if plot_results:
			plotter.plot()
			plotter_regret.plot()

	return v, gen_real, gen_estimated

