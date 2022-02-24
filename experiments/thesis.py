'''
Created on 08-Dec-17

@author: goramos
'''
import sys, os
#sys.path.insert(0, '..')

from problem import ProblemInstance
from simulation import run_simulation
from experiments import experiment

import time
import numpy as np

class thesis(experiment):
	
	#-----------------------------------------------------------------------
	
	def run_batch_file(self, run_file_name):
		
		SETS = []
		N_EXPERIMENTS = 0
		for line in open('%s.config'%run_file_name, 'r'):
			
			joint_decays = False
			indep_decays = False

			line = line.strip().replace(' ','')
			
			if line == "":
				continue

			if line[0] == '#':
				continue
			
			taglist = line.split(';')
			if len(taglist) == 0:
				continue
			
			this_set = []
			this_order = {}
			count_order = 0
			exps = 1
			
			for e in taglist:
				values = None
				taglist2 = e.split('=')
				
				if taglist2[0] == 'alg': # string values
					values = taglist2[1][1:-1].split(',')
					for alg_name in values:
						if alg_name not in ['aamas17', 'aamas17stdql', 'trc18', 'aamas18', 'deltatolling', 'differencerewards']:
							print 'Algorithm "%s" does not exist!' % alg_name
							sys.exit()
				elif taglist2[0] == 'net': # string values
					values = taglist2[1][1:-1].split(',')
				elif taglist2[0] == 'episodes': # single int value
					values = [int(taglist2[1])]
				elif taglist2[0] == 'rep': # single int value
					values = range(1, int(taglist2[1])+1)
				elif taglist2[0] == 'K': # int values
					values = [ int(x) for x in taglist2[1][1:-1].split(',') ]
				elif taglist2[0] == 'alpha_decay': # float values
					values = [ float(x) for x in taglist2[1][1:-1].split(',') ]
					indep_decays = True
				elif taglist2[0] == 'epsilon_decay': # float values
					values = [ float(x) for x in taglist2[1][1:-1].split(',') ]
					indep_decays = True
				elif taglist2[0] == 'decays': # float values
					values = [ float(x) for x in taglist2[1][1:-1].split(',') ]
					joint_decays = True
				else:
					print 'Invalid config file! (taglist: "%s")' % e
					sys.exit()
				
				this_set.append([taglist2[0], len(values), values])
				this_order[taglist2[0]] = count_order
				count_order += 1
				
				# update the number of experiments of this set
				exps *= len(values)
				
			if joint_decays and indep_decays:
				print 'An entry of the config file should specify either joint decays (specifying only the "decay" field, so that alpha and epsilon are the same) OR independent decays (specifying both "alpha_decay" and "epsilon_decay" fields, so that alpha and epsilon can have different values)!'
				sys.exit()

			if joint_decays:
				this_set.append(['dummy_decays', 1, [None]])
				this_order['dummy_decays'] = count_order
				count_order += 1
			
			# check for missing keys
			missing = [ x for x in ['alg', 'net', 'episodes', 'rep', 'K', 'alpha_decay', 'epsilon_decay', 'decays'] if x not in this_order.keys() ]
			if joint_decays:
				missing.remove('alpha_decay')
				missing.remove('epsilon_decay')
			else:
				missing.remove('decays')
			if len(missing) > 0:
				print 'One or more keys (%s) are missing in the following configuration line: %s' % (missing, line)
				sys.exit()


			this_set.append(this_order)
			SETS.append(this_set)

			# update the TOTAL number of experiments
			N_EXPERIMENTS += exps
		
		CUR_EXP = 0
		LAST_EXP = 0
		CUR_ATEMPT = 1
		control_file = None
		
		# if the control file exists, resume from where it stopped
		control_file_name = '%s.control'%run_file_name
		if os.path.isfile(control_file_name):
			
			# if the control file is empty (this is not expected) throw exception
			if os.stat(control_file_name).st_size < 3:
				print 'The control file is empty!'
				sys.exit()
			
			control_file = open(control_file_name, 'r+')
			
			status = control_file.read().strip()
			if status == 'finished':
				print 'Experiment already finished!'
				sys.exit()
			
			else:
				spl = status.split('#')
				CUR_ATEMPT = int(spl[0]) + 1
				LAST_EXP = int(spl[1])
			
		# otherwise, create a new file and start the experiments from the beginning
		else:
			control_file = open(control_file_name, 'w+')
			control_file.write('1#0')
		
		print 'Running %d experiments%s...' % (N_EXPERIMENTS, '' if CUR_ATEMPT == 1 else ' (attempt number %d, skipping %d experiments)'%(CUR_ATEMPT, LAST_EXP))
		
		sys.stdout = open('experiments/results/log_params_thesis%s.txt'%('' if CUR_ATEMPT == 1 else '_attempt%d'%CUR_ATEMPT), 'w')
		
		fname = open('experiments/results/log_params_thesis%s_summary.txt'%('' if CUR_ATEMPT == 1 else '_attempt%d'%CUR_ATEMPT), 'w')
		fname.write('id\talg\tepisodes\tnet\tk\talpha_decay\tepsilon_decay\trep\tavg-tt\treal\test\truntime (s)\n')
		fname.flush()
		
		# run the set of experiments defined in the file
		# keeping the order in which the parameters were 
		# defined in the file
		for SET in SETS:
			order = SET[-1]
			for p1 in xrange(SET[0][1]):
				for p2 in xrange(SET[1][1]):
					for p3 in xrange(SET[2][1]):
						for p4 in xrange(SET[3][1]):
							for p5 in xrange(SET[4][1]):
								for p6 in xrange(SET[5][1]):
									for p7 in xrange(SET[6][1]):
									
										pars = [p1, p2, p3, p4, p5, p6, p7]
										episodes = SET[order['episodes']][2][0]
										rep = SET[order['rep']][2][pars[order['rep']]]
										net_name = SET[order['net']][2][pars[order['net']]]
										if 'dummy_decays' in order:
											decays = SET[order['decays']][2][pars[order['decays']]]
											alpha_decay = decays
											epsilon_decay = decays
										else:
											alpha_decay = SET[order['alpha_decay']][2][pars[order['alpha_decay']]]
											epsilon_decay = SET[order['epsilon_decay']][2][pars[order['epsilon_decay']]]
										alg = SET[order['alg']][2][pars[order['alg']]]
										K = SET[order['K']][2][pars[order['K']]]

										CUR_EXP += 1
										
										print '========================================================================'
										print ' Experiment %i of %i' % (CUR_EXP, N_EXPERIMENTS)
										print ' algorithm=%s, episodes=%d, network=%s, k=%d, alpha_decay=%f, epsilon_decay=%f, replication=%i' % (alg, episodes, net_name, K, alpha_decay, epsilon_decay, rep)
										print '========================================================================\n'
										
										if CUR_EXP <= LAST_EXP:
											print 'Skipped!\n'
										
										else:
											
											alt_route_file = None
											if net_name in ['BBraess_1_2100_10_c1_2100', 'BBraess_3_2100_10_c1_900', 'BBraess_5_2100_10_c1_900', 'BBraess_7_2100_10_c1_900']:
												alt_route_file = 'networks/%s.TRC.routes' % net_name
											
											P = ProblemInstance(net_name, K, alt_route_file)
											
											start = time.time()
											values = [0, 0, 0, 0, 0]
											try:
												
												# configure the algorithm
												REGRET_AS_COST = False
												EXTRAPOLATE_COSTS = False
												USE_APP = False
												DIFFERENCE_REWARDS = False
												A_POSTERIORI_MCT = False
												DELTA_TOLLING = False
												THESIS_DELTA_TOLLING = False
												STAT_REGRET_DIFF = False
												if alg == 'aamas17':
													REGRET_AS_COST = True
													EXTRAPOLATE_COSTS = True
													STAT_REGRET_DIFF = True
												elif alg == 'aamas17stdql':
													STAT_REGRET_DIFF = True
												elif alg == 'trc18':
													REGRET_AS_COST = True
													EXTRAPOLATE_COSTS = True
													USE_APP = True
													STAT_REGRET_DIFF = True
												elif alg == 'aamas18':
													A_POSTERIORI_MCT = True
												elif alg == 'deltatolling':
													#DELTA_TOLLING = True
													THESIS_DELTA_TOLLING = True # a new (more efficient) version of the algorithm was implemented later; this alternative flag was then created to allow for the thesis version of deltatolling to be executed as well
												elif alg == 'differencerewards':
													DIFFERENCE_REWARDS = True

												# run the simulation
												values = run_simulation(P, episodes, alpha=1.0, epsilon=1.0, alpha_decay=alpha_decay, epsilon_decay=epsilon_decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=REGRET_AS_COST, extrapolate_costs=EXTRAPOLATE_COSTS, use_app=USE_APP, difference_rewards=DIFFERENCE_REWARDS, a_posteriori_MCT=A_POSTERIORI_MCT, delta_tolling=DELTA_TOLLING, thesis_delta_tolling=THESIS_DELTA_TOLLING, plot_results=False, stat_all=True, stat_regret_diff=STAT_REGRET_DIFF)
												
											except Exception:
												print '[ERROR] Some exception prevented this experiment from finishing!'
											else:
												None
											runtime = time.time() - start
											
											# write summary
											fname.write('%i\t%s\t%d\t%s\t%d\t%f\t%f\t%i\t%f\t%f\t%f\t%f\n' % (CUR_EXP, alg, episodes, net_name, K, alpha_decay, epsilon_decay, rep, values[0], values[1], values[2], runtime))
											fname.flush()
											
											print '\n========================================================================\n'
											sys.stdout.flush()
											
											LAST_EXP = CUR_EXP
											control_file.seek(0)
											control_file.write('{:<10}'.format('%d#%d'%(CUR_ATEMPT, LAST_EXP)))
											control_file.flush()
		
		# finish the experiment by setting a flag on the control file
		control_file.seek(0)
		control_file.write('{:<10}'.format('finished'))
		control_file.flush()
		
		# close the files
		fname.close()
		sys.stdout = sys.__stdout__
		control_file.close()
		
		print 'finished!'
		
	#-----------------------------------------------------------------------
	# check whether the script is still producing the original results 
	# (which are not necessarily published)
	# the rationale here is that, after the script is changed, ideally the  
	# results should not change given the same random seed is used
	def validate_script(self):
		
		print "Validating script (it takes around 13min)..."
		
		sys.stdout = open(os.devnull, 'w')

		trials = 0
		fails = 0

		alg_names = ['aamas17', 'trc18', 'aamas18', 'aamas17stdql', 'deltatolling']
		net_names = ['Braess_1_4200_10_c1', 'Braess_2_4200_10_c1', 'Braess_3_4200_10_c1', 'Braess_4_4200_10_c1', 'Braess_5_4200_10_c1', 'Braess_6_4200_10_c1', 'Braess_7_4200_10_c1', 'BBraess_1_2100_10_c1_2100', 'BBraess_3_2100_10_c1_900', 'BBraess_5_2100_10_c1_900', 'BBraess_7_2100_10_c1_900', 'OW', 'SF']

		expected_results = {
			'aamas17': {
				'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.658891723347011, 0.10623382653088378, 0.25092952097516913)],
				'Braess_2_4200_10_c1': [4, 0.995, 0.995, (27.48403514738267, 0.12423707482997126, 0.2762391534391447)],
				'Braess_3_4200_10_c1': [4, 0.99, 0.99, (41.36176020407948, 0.09617186791379342, 0.23671728741493236)],
				'Braess_4_4200_10_c1': [4, 0.99, 0.99, (50.020521541952675, 0.004024365079365229, 0.17182945578231312)],
				'Braess_5_4200_10_c1': [8, 0.995, 0.995, (61.610246598639975, 0.0784532738095006, 0.20205906557064923)],
				'Braess_6_4200_10_c1': [8, 0.995, 0.995, (74.66845578231077, 0.053910981535466106, 0.1769212925170026)],
				'Braess_7_4200_10_c1': [8, 0.995, 0.995, (84.52598809523748, 0.028728801020408354, 0.15144270408162336)],
				'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (8.313607709744398, 0.05435776077115378, 0.09211080498880325)],
				'BBraess_3_2100_10_c1_900': [4, 0.995, 0.995, (31.10083412697789, 0.10020349206357661, 0.30219198696146543)],
				'BBraess_5_2100_10_c1_900': [4, 0.995, 0.995, (57.15271190475977, 0.03583497039559119, 0.3000387112622725)],
				'BBraess_7_2100_10_c1_900': [4, 0.995, 0.995, (130.7899936507944, 0.02208753617321256, 0.29788835168988403)],
				'OW': [8, 0.995, 0.995, (81.8699176470589, 0.06055426153195076, 0.18763121878967437)],
				'SF': [4, 0.9999, 0.998, (606.7783587557409, 9.181356693965424e-05, 0.00010139659336468748)]
			},
			'trc18': {
				'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.667635487519094, 0.10670433106603265, 0.17386319759408098)],
				'Braess_2_4200_10_c1': [4, 0.995, 0.995, (27.498241496589284, 0.12403045918371287, 0.17814976148486508)],
				'Braess_3_4200_10_c1': [4, 0.99, 0.99, (41.30511564625631, 0.09570263463714988, 0.1462149078010494)],
				'Braess_4_4200_10_c1': [4, 0.99, 0.99, (50.02349206349457, 0.004171224489795965, 0.08607978584026221)],
				'Braess_5_4200_10_c1': [8, 0.995, 0.995, (61.603276643991435, 0.07890554232801895, 0.12282742635632733)],
				'Braess_6_4200_10_c1': [8, 0.995, 0.995, (74.69016326530394, 0.05430719144800241, 0.10632800880933906)],
				'Braess_7_4200_10_c1': [8, 0.995, 0.995, (84.50650396825336, 0.028773531037415326, 0.08806136715796775)],
				'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (8.310893424030171, 0.0557432539684336, 0.07690138699940324)],
				'BBraess_3_2100_10_c1_900': [4, 0.99, 0.99, (31.01730714285105, 0.10156975907038036, 0.18579699680338427)],
				'BBraess_5_2100_10_c1_900': [8, 0.995, 0.995, (82.59890476190553, 0.12742535095858737, 0.3050968879555036)],
				'BBraess_7_2100_10_c1_900': [4, 0.995, 0.995, (130.78034365079444, 0.022075301533324994, 0.15033246273200804)],
				'OW': [8, 0.995, 0.995, (81.81836470588237, 0.0605394033008887, 0.10842908825880483)],
				'SF': [4, 0.9999, 0.998, (606.5326078766424, 9.181101414753981e-05, 9.509770710033097e-05)]
			},
			'aamas18': {
				'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.467999999991706, 0.055672687074637725, 0.09941309415810554)],
				'Braess_2_4200_10_c1': [8, 0.99, 0.99, (24.965849206343993, 0.038896564625646904, 0.4075917605190364)],
				'Braess_3_4200_10_c1': [8, 0.99, 0.99, (34.845066326528766, 0.026036896258498102, 0.4933477428192948)],
				'Braess_4_4200_10_c1': [12, 0.99, 0.99, (44.79582539682733, 0.018225578231293515, 0.41942431972789)],
				'Braess_5_4200_10_c1': [12, 0.99, 0.99, (54.80873866213191, 0.014663223733936609, 0.3477584618291362)],
				'Braess_6_4200_10_c1': [16, 0.99, 0.99, (64.81061904761914, 0.012303172983496459, 0.2964392274052476)],
				'Braess_7_4200_10_c1': [16, 0.99, 0.99, (74.91415476190544, 0.010307142857137517, 0.2583309523809412)],
				'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (7.915383219949779, 0.10420607709717421, 0.10539655328765041)],
				'BBraess_3_2100_10_c1_900': [8, 0.99, 0.99, (31.512402380952707, 0.2992891156464251, 0.5405180452975712)],
				'BBraess_5_2100_10_c1_900': [4, 0.99, 0.99, (56.28252698412511, 0.08867499118164085, 0.29346792930926613)],
				'BBraess_7_2100_10_c1_900': [4, 0.99, 0.99, (129.69407936507963, 0.04473189018464778, 0.2595661529789578)],
				'OW': [8, 0.99, 0.99, (80.28925882352935, 0.10513853575962762, 0.4673880208774156)],
				'SF': [10, 0.9997, 0.999, (2168.986889462446, 0.0006119932635893602, 0.0006918085995888627)]
			},
			'aamas17stdql': {
				'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.718980725614134, 0.10376227324290013, 0.15152699624120222)],
				'Braess_2_4200_10_c1': [4, 0.995, 0.995, (27.299667800444166, 0.1164456046863578, 0.19808743566212061)],
				'Braess_3_4200_10_c1': [4, 0.99, 0.99, (40.79179081632475, 0.07703104024939637, 0.14486849827228865)],
				'Braess_4_4200_10_c1': [4, 0.99, 0.99, (50.106213151929936, 0.0014738208616781026, 0.06898456349206347)],
				'Braess_5_4200_10_c1': [8, 0.995, 0.995, (61.058041383220534, 0.07347248488281886, 0.2020907105064019)],
				'Braess_6_4200_10_c1': [8, 0.995, 0.995, (74.27680952380737, 0.0504627332361463, 0.17508419015224586)],
				'Braess_7_4200_10_c1': [8, 0.995, 0.995, (84.32258730158667, 0.028257439767573927, 0.14897524966930314)],
				'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (8.313607709744398, 0.05435776077115378, 0.05589745487366087)],
				'BBraess_3_2100_10_c1_900': [4, 0.995, 0.995, (30.79738650793003, 0.09868290249441419, 0.1604185891271735)],
				'BBraess_5_2100_10_c1_900': [4, 0.995, 0.995, (56.831100793648424, 0.035074251700705696, 0.13506650312242727)],
				'BBraess_7_2100_10_c1_900': [4, 0.995, 0.995, (130.30460555555607, 0.021402188478579096, 0.12300469343407369)],
				'OW': [8, 0.995, 0.995, (81.20949411764705, 0.059193647905205156, 0.2892511454365919)],
				'SF': [4, 0.9995, 0.999, (624.7627914510489, 9.360047138868666e-05, 9.833600272385135e-05)]
			},
			'deltatolling': {
				'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.479635487519808, -0.38741395124714184, 0.14053663498163677)],
				'Braess_2_4200_10_c1': [8, 0.99, 0.99, (25.166081632647597, -0.2786020823887184, 0.23219451499121305)],
				'Braess_3_4200_10_c1': [8, 0.99, 0.99, (35.10320918367154, -0.21808267573693985, 0.26975657454645763)],
				'Braess_4_4200_10_c1': [12, 0.99, 0.99, (45.073403628119905, -0.17716433673469267, 0.22470187074829795)],
				'Braess_5_4200_10_c1': [12, 0.99, 0.99, (55.02272675737003, -0.15006717214661933, 0.18367885959937397)],
				'Braess_6_4200_10_c1': [16, 0.99, 0.99, (65.0284523809525, -0.12852731535469625, 0.1550781268221575)],
				'Braess_7_4200_10_c1': [16, 0.99, 0.99, (75.04963095238158, -0.11251565972222274, 0.13421648313491497)],
				'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (7.918299886616365, -0.42838249433086917, 0.07171018118113488)],
				'BBraess_3_2100_10_c1_900': [8, 0.99, 0.99, (31.81661269841295, -0.22447714143987543, 0.2985269194573235)],
				'BBraess_5_2100_10_c1_900': [4, 0.99, 0.99, (56.77520476190284, -0.35096414399093123, 0.1424021927677734)],
				'BBraess_7_2100_10_c1_900': [4, 0.99, 0.99, (130.28962857142912, -0.3940506100853031, 0.1302662919449816)],
				'OW': [8, 0.99, 0.99, (81.02975294117644, -0.07150726195514197, 0.29136305120609357)],
				'SF': [10, 0.9997, 0.999, (2171.5054317580534, 0.000267982057621951, 0.0003478378959440302)]
			}
		}
		
		for alg in alg_names:

			# configure the algorithm
			REGRET_AS_COST = False
			EXTRAPOLATE_COSTS = False
			USE_APP = False
			DIFFERENCE_REWARDS = False
			A_POSTERIORI_MCT = False
			DELTA_TOLLING = False
			THESIS_DELTA_TOLLING = False
			STAT_REGRET_DIFF = False
			if alg == 'aamas17':
				REGRET_AS_COST = True
				EXTRAPOLATE_COSTS = True
				STAT_REGRET_DIFF = True
			elif alg == 'aamas17stdql':
				STAT_REGRET_DIFF = True
			elif alg == 'trc18':
				REGRET_AS_COST = True
				EXTRAPOLATE_COSTS = True
				USE_APP = True
				STAT_REGRET_DIFF = True
			elif alg == 'aamas18':
				A_POSTERIORI_MCT = True
			elif alg == 'deltatolling':
				#DELTA_TOLLING = True
				THESIS_DELTA_TOLLING = True # (see explanation above)
			elif alg == 'differencerewards':
				DIFFERENCE_REWARDS = True

			for net in net_names: 

				trials += 1

				sys.__stdout__.write('\tTesting algorithm "%s" on network "%s"...\n' % (alg, net))
				np.random.seed(123456789)

				K = expected_results[alg][net][0]
				alpha_decay = expected_results[alg][net][1]
				epsilon_decay = expected_results[alg][net][2]
				expected_values = expected_results[alg][net][3]

				alt_route_file = None
				if net in ['BBraess_1_2100_10_c1_2100', 'BBraess_3_2100_10_c1_900', 'BBraess_5_2100_10_c1_900', 'BBraess_7_2100_10_c1_900']:
					alt_route_file = 'networks/%s.TRC.routes' % net
				
				P = ProblemInstance(net, K, alt_route_file)

				res = run_simulation(P, 10, alpha=1.0, epsilon=1.0, alpha_decay=alpha_decay, epsilon_decay=epsilon_decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=REGRET_AS_COST, extrapolate_costs=EXTRAPOLATE_COSTS, use_app=USE_APP, difference_rewards=DIFFERENCE_REWARDS, a_posteriori_MCT=A_POSTERIORI_MCT, delta_tolling=DELTA_TOLLING, thesis_delta_tolling=THESIS_DELTA_TOLLING, plot_results=False, stat_all=True, stat_regret_diff=STAT_REGRET_DIFF)
				
				if res != expected_values:
					fails += 1
					sys.stderr.write("Error while validating algorithm %s on network %s! %s\n" % (alg, net, res))

		sys.__stdout__.write('\nTest completed! Failed trials: %d out of %d (%.1f%%)\n\n' % (fails, trials, (fails/float(trials))*100))

		sys.stdout = sys.__stdout__

	#-----------------------------------------------------------------------

	def run(self, params):
		
		if params['validate']:
			self.validate_script()
		else:
			self.run_batch_file(params['config'])

	#-----------------------------------------------------------------------

	@staticmethod
	def add_subparser_arguments(subparsers):
		subp = subparsers.add_parser('thesis', help='experiments of the PhD thesis')

		subp.add_argument('--config_file', dest='config', action='store', default='experiments/config/run_thesis', type=str, 
			help='configuration file of the experiment')
		subp.add_argument('--validate', dest='validate', action='store_true', 
			help='validate the experiment script')
		subp.set_defaults(exp_class='thesis')
	
	#-----------------------------------------------------------------------
	

