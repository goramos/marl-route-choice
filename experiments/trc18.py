'''
Created on 09-Mar-17

@author: goramos
'''
import sys, os
#sys.path.insert(0, '..')

from problem import ProblemInstance
from simulation import run_simulation
from experiments import experiment

import time
import numpy as np

class trc18(experiment):

    #-----------------------------------------------------------------------

    def run_batch_file(self, run_file_name):
        
        SETS = []
        N_EXPERIMENTS = 0
        for line in open('%s.config'%run_file_name, 'r'):
            
            line = line.strip().replace(' ','')
            
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
                
                if taglist2[0] == 'rep': # single int value
                    values = range(1, int(taglist2[1])+1)
                elif taglist2[0] == 'K': # int values
                    values = [ int(x) for x in taglist2[1][1:-1].split(',') ]
                elif taglist2[0] == 'decay': # float values
                    values = [ float(x) for x in taglist2[1][1:-1].split(',') ] 
                elif taglist2[0] == 'app': # boolean values
                    values = [ True if x=='True' else False for x in taglist2[1][1:-1].split(',') ]
                else: # string values
                    values = taglist2[1][1:-1].split(',')
                
                this_set.append([taglist2[0], len(values), values])
                #this_set[taglist2[0]] = values
                this_order[taglist2[0]] = count_order
                count_order += 1
                
                # update the number of experiments of this set
                exps *= len(values)# if type(values) is list else values 
            
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
        
        sys.stdout = open('experiments/results/log_params_TRC%s.txt'%('' if CUR_ATEMPT == 1 else '_attempt%d'%CUR_ATEMPT), 'w')
        
        fname = open('experiments/results/log_params_TRC%s_summary.txt'%('' if CUR_ATEMPT == 1 else '_attempt%d'%CUR_ATEMPT), 'w')
        fname.write('id\tnet\tk\tdecay\tapp\trep\tavg-tt\treal\test\truntime (s)\n')
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
                                
                                pars = [p1, p2, p3, p4, p5]
                                rep = SET[order['rep']][2][pars[order['rep']]]
                                net_name = SET[order['net']][2][pars[order['net']]]
                                decay = SET[order['decay']][2][pars[order['decay']]]
                                app = SET[order['app']][2][pars[order['app']]]
                                K = SET[order['K']][2][pars[order['K']]]
                                
                                CUR_EXP += 1
                                
                                print '========================================================================'
                                print ' Experiment %i of %i' % (CUR_EXP, N_EXPERIMENTS)
                                print ' network=%s, k=%d, decay=%f, app=%s, replication=%i' % (net_name, K, decay, app, rep)
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
                                        values = run_simulation(P, 1000, alpha=1.0, epsilon=1.0, alpha_decay=decay, epsilon_decay=decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=app, plot_results=False)
                                    except Exception:
                                        print '[ERROR] Some exception prevented this experiment from finishing!'
                                    else:
                                        None
                                    runtime = time.time() - start
                                    
                                    # write summary
                                    fname.write('%i\t%s\t%d\t%f\t%s\t%i\t%f\t%f\t%f\t%f\n' % (CUR_EXP, net_name, K, decay, app, rep, values[0], values[1], values[2], runtime))
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
        
        print "Validating script (it takes around 1 minute)..."
         
        sys.stdout = open(os.devnull, 'w')
         
        net = 'Braess_1_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (17.876696712002676, 0.04901963208635559, 0.05717411243834065):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
          
        net = 'Braess_2_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (28.150256235818755, 0.017926762660643157, 0.028345552443374018):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
          
        net = 'Braess_3_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (39.54823129251494, 0.016041376984097914, 0.02531379415469834):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'Braess_4_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (50.02816326530857, 0.000864934240362699, 0.009560876173870221):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'Braess_5_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 8)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (59.04352607709874, 0.02236392214661536, 0.033043320440792674):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'Braess_6_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 8)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (71.10539795918233, 0.019154097667634328, 0.030254111338520098):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'Braess_7_4200_10_c1'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 8)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (81.09731349206372, 0.01298665787981078, 0.024803593870961906):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'BBraess_1_2100_10_c1_2100'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4, 'networks/%s.TRC.routes' % net)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (9.159592403619715, 0.027191306689473428, 0.029588519231558454):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'BBraess_3_2100_10_c1_900'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4, 'networks/%s.TRC.routes' % net)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (24.847269841260655, 0.06233493735833484, 0.06838126165572478):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        net = 'BBraess_5_2100_10_c1_900'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 12, 'networks/%s.TRC.routes' % net)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.99, epsilon_decay=0.99, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (65.80720238095249, 0.0953541426209693, 0.12641721501320058):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
        
        net = 'BBraess_7_2100_10_c1_900'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 4, 'networks/%s.TRC.routes' % net)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (127.29053650793541, 0.017996803018044887, 0.027426301080543055):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
        
        net = 'OW'
        sys.__stdout__.write('\tTesting network "%s"...\n' % net)
        np.random.seed(123456789)
        P = ProblemInstance(net, 8)
        res = run_simulation(P, 100, alpha=1.0, epsilon=1.0, alpha_decay=0.995, epsilon_decay=0.995, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=True, extrapolate_costs=True, use_app=True, plot_results=False, stat_all=False, stat_regret_diff=False)
        if res != (74.9434470588235, 0.04458316758358024, 0.049571630503084246):
            sys.stderr.write("Error while validating script on network %s! [%s]\n" % (net, ', '.join(map(str,[repr(x) for x in res]))))
         
        sys.stdout = sys.__stdout__
        print "\nFinished!"

    #-----------------------------------------------------------------------

    def run(self, params):
        
        if params['validate']:
            self.validate_script()
        else:
            self.run_batch_file(params['config'])

    #-----------------------------------------------------------------------

    @staticmethod
    def add_subparser_arguments(subparsers):
        subp = subparsers.add_parser('trc18', help='experiments of the TRC-18 paper')

        subp.add_argument('--config_file', dest='config', action='store', default='experiments/config/run_TRC', type=str, 
            help='configuration file of the experiment')
        subp.add_argument('--validate', dest='validate', action='store_true', 
            help='validate the experiment script')
        subp.set_defaults(exp_class='trc18')
    
    #-----------------------------------------------------------------------

    