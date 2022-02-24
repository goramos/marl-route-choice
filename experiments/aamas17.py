'''
Created on 20-Feb-17

@author: goramos
'''
import sys, os
#sys.path.insert(0, '..')

from problem import ProblemInstance
from simulation import run_simulation
from experiments import experiment

import time
import numpy as np

class aamas17(experiment):
    
    #-----------------------------------------------------------------------
    # experiments presented in the final (camera-ready) AAMAS paper
    def run_batch_AAMAS_camera_ready(self):
        
        REPLICATIONS = 30
        NETWORKS_ANDN_DECAYS = [['Braess_1_4200_10_c1', 0.99], ['Braess_2_4200_10_c1', 0.995], ['Braess_3_4200_10_c1', 0.9975]]
        ALGS = [True, False] # True=Ours, False=stdQL
        
        num_exps = REPLICATIONS * len(NETWORKS_ANDN_DECAYS) * len(ALGS)
        print 'Running %d experiments...' % (num_exps)
        
        sys.stdout = open('experiments/results/log_params_AAMAS_camera_ready.txt', 'w')
        
        fname = open('experiments/results/log_params_AAMAS_camera_ready_summary.txt', 'w')
        fname.write('id\talg\tnet\trep\tavg-tt\treal\test\tdiff\treldiff\truntime (s)\n')
        
        exp = 0
        for alg in ALGS:
            alg_name = ('Ours' if alg else 'stdQL')
            for net_id in xrange(len(NETWORKS_ANDN_DECAYS)):
                net_name = NETWORKS_ANDN_DECAYS[net_id][0]
                decay = NETWORKS_ANDN_DECAYS[net_id][1]
                for rep in xrange(1,REPLICATIONS+1):
                    
                    P = ProblemInstance(net_name)
                    exp += 1
                    
                    print '========================================================================'
                    print ' Experiment %i of %i' % (exp, num_exps)
                    print ' algorithm=%s, network=%s, replication=%i' % (alg_name, net_name, rep)
                    print '========================================================================\n'
                    
                    start = time.time()
                    values = [0, 0, 0]
                    try:
                        values = run_simulation(P, 10000, alpha=1.0, epsilon=1.0, alpha_decay=decay, epsilon_decay=decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=alg, extrapolate_costs=alg, plot_results=False)
                    except Exception:
                        print '[ERROR] Some exception prevented this experiment from finishing!'
                    else:
                        None
                    runtime = time.time() - start
                    
                    # write summary
                    fname.write('%i\t%s\t%s\t%i\t%f\t%f\t%f\t%f\n' % (exp, alg_name, net_name, rep, values[0], values[1], values[2], runtime))
                    fname.flush()
                    
                    print '\n========================================================================\n'
                    sys.stdout.flush()
            
        fname.close()
        sys.stdout = sys.__stdout__
        
        print 'finished!'

    #-----------------------------------------------------------------------
    # check whether the script is still producing the original results 
    # (which are not necessarily published)
    # the rationale here is that, after the script is changed, ideally the  
    # results should not change given the same random seed is used
    def validate_script(self):
        
        print "Validating script (it takes around 15 seconds)..."
        
        sys.stdout = open(os.devnull, 'w')
        
        # Braess_1_4200_10_c1
        np.random.seed(123456789)
        P = ProblemInstance('Braess_1_4200_10_c1')
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (17.87485260769432, 0.0490511312360153, 0.06446411167818451):
            sys.stderr.write("Error while validating script on network Braess_1_4200_10_c1! [%s]\n" % ', '.join(map(str,[repr(x) for x in res])))
        
        # Braess_2_4200_10_c1
        np.random.seed(123456789)
        P = ProblemInstance('Braess_2_4200_10_c1')
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (26.572295918360744, 0.01498349395316248, 0.04359264795920571):
            sys.stderr.write("Error while validating script on network Braess_2_4200_10_c1! [%s]\n" % ', '.join(map(str,[repr(x) for x in res])))
        
        # Braess_3_4200_10_c1
        np.random.seed(123456789)
        P = ProblemInstance('Braess_3_4200_10_c1')
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.9975, epsilon_decay=0.9975, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (35.56324319727688, 0.006523992913800927, 0.04611469104307984):
            sys.stderr.write("Error while validating script on network Braess_3_4200_10_c1! [%s]\n" % ', '.join(map(str,[repr(x) for x in res])))
        
        sys.stdout = sys.__stdout__
        print "Finished!"

    #-----------------------------------------------------------------------

    def run(self, params):
        
        if params['validate']:
            self.validate_script()
        elif params['setting'] == 'camera_ready':
            self.run_batch_AAMAS_camera_ready()

    #-----------------------------------------------------------------------

    @staticmethod
    def add_subparser_arguments(subparsers):
        subp = subparsers.add_parser('aamas17', help='experiments of the AAMAS-17 paper')

        subp.add_argument('--setting', dest='setting', action='store', type=str, choices=['camera_ready'],
            help='setting of experiments to run')
        subp.add_argument('--validate', dest='validate', action='store_true', 
            help='validate the experiment script')
        subp.set_defaults(exp_class='aamas17')
    
    #-----------------------------------------------------------------------

