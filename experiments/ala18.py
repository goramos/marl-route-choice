'''
Created on 27-Apr-18

@author: goramos
'''
import sys, os
# sys.path.insert(0, '..')

from problem import ProblemInstance
from simulation import run_simulation
from experiments import experiment

import time
from datetime import datetime
import traceback
import numpy as np

class ala18(experiment):

    __algs_list = ['aamas17', 'aamas17stdql', 'ala18', 'deltatolling', 'differencerewards', 'stdql', 'trc18']

    #-----------------------------------------------------------------------

    def run_batch_file(self, params):

        alg = params['alg']
        episodes = params['episodes']
        net_name = params['net']
        K = params['k']
        alpha_decay = params['decay-alpha']
        epsilon_decay = params['decay-eps']
        rep = params['rep']
        avf = params['avf']
        pid = params['pid']
        logs_dir = params['logs-dir']

        if alg not in ala18.__algs_list:
            print('Algorithm "%s" does not exist!' % alg)
            sys.exit()

        timestamp = datetime.utcnow().strftime("%Y%b%d-%Hh%Mm%Ss%fms")

        sys.stdout = open('%s/%s_%s_ala18.txt' % (logs_dir, timestamp, pid), 'w')

        fname = open('%s/%s_%s_ala18_summary.txt' % (logs_dir, timestamp, pid), 'w')
        fname.write('pid\talg\tepisodes\tnet\tk\talpha_decay\tepsilon_decay\tagent_vehicles_factor\trep\tavg-tt\treal\test\truntime (s)\n')
        fname.flush()

        for it in xrange(1, rep+1):
        
            print('========================================================================')
            print(' algorithm=%s, episodes=%d, network=%s, k=%d, alpha_decay=%f, epsilon_decay=%f, agent_vehicles_factor=%d, replication=%i' % (alg, episodes, net_name, K, alpha_decay, epsilon_decay, avf, it))
            print('========================================================================\n')

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
                STAT_REGRET_DIFF = False
                PRINT_OD_PAIRS_EVERY_EPISODE = False
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
                elif alg == 'ala18':
                    A_POSTERIORI_MCT = True
                elif alg == 'deltatolling':
                    DELTA_TOLLING = True
                elif alg == 'differencerewards':
                    DIFFERENCE_REWARDS = True
                elif alg == 'stdql':
                    pass

                # run the simulation
                values = run_simulation(P, episodes, alpha=1.0, epsilon=1.0, alpha_decay=alpha_decay, epsilon_decay=epsilon_decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=REGRET_AS_COST, extrapolate_costs=EXTRAPOLATE_COSTS, use_app=USE_APP, difference_rewards=DIFFERENCE_REWARDS, a_posteriori_MCT=A_POSTERIORI_MCT, delta_tolling=DELTA_TOLLING, agent_vehicles_factor=avf, plot_results=False, stat_all=True, stat_regret_diff=STAT_REGRET_DIFF, print_OD_pairs_every_episode=PRINT_OD_PAIRS_EVERY_EPISODE)

            except Exception as e:
                print('[ERROR] %s' % e)
                traceback.print_exc()
            else:
                None

            runtime = time.time() - start

            # write summary
            fname.write('%s\t%s\t%d\t%s\t%d\t%f\t%f\t%d\t%i\t%f\t%f\t%f\t%f\n' % (pid, alg, episodes, net_name, K, alpha_decay, epsilon_decay, avf, it, values[0], values[1], values[2], runtime))
            fname.flush()

            print('\n========================================================================\n')
            sys.stdout.flush()
        
        # close the files
        fname.close()
        sys.stdout = sys.__stdout__

    #-----------------------------------------------------------------------
    # check whether the script is still producing the original results 
    # (which are not necessarily published)
    # the rationale here is that, after the script is changed, ideally the  
    # results should not change given the same random seed is used
    def validate_script(self):
        
        print "Validating script (it takes around 17min)..."
        
        sys.stdout = open(os.devnull, 'w')

        trials = 0
        fails = 0

        algs_to_ignore = ['stdql']
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
            'ala18': {
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
                'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.481179705207088, -0.17325150510221782, 0.2743976162130247)],
                'Braess_2_4200_10_c1': [8, 0.99, 0.99, (25.06608163264772, -0.14420010770996966, 0.40914067082390626)],
                'Braess_3_4200_10_c1': [8, 0.99, 0.99, (34.91891156462391, -0.13019413548751782, 0.36094122448975663)],
                'Braess_4_4200_10_c1': [12, 0.99, 0.99, (44.88106122449174, -0.11731578684807047, 0.2843775351473912)],
                'Braess_5_4200_10_c1': [12, 0.99, 0.99, (54.89007653061263, -0.10590796485259533, 0.22795711451244555)],
                'Braess_6_4200_10_c1': [16, 0.99, 0.99, (64.9038571428572, -0.09444633219952889, 0.18905706916099788)],
                'Braess_7_4200_10_c1': [16, 0.99, 0.99, (74.97566666666727, -0.08622648809523935, 0.16142232142856433)],
                'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (7.920249999994998, -0.014422329932237465, 0.12595669501103945)],
                'BBraess_3_2100_10_c1_900': [8, 0.99, 0.99, (32.0026865079372, 0.06640876700691468, 0.45272930980734655)],
                'BBraess_5_2100_10_c1_900': [4, 0.99, 0.99, (56.781019047617114, -0.07785217498111448, 0.35617216049381417)],
                'BBraess_7_2100_10_c1_900': [4, 0.99, 0.99, (130.2810079365085, -0.11986659809955524, 0.3430619787280014)],
                'OW': [8, 0.99, 0.99, (81.08100000000005, -0.06068233178163349, 0.3040021371138391)],
                'SF': [10, 0.9997, 0.999, (2171.4961475876717, 0.0003867102520913507, 0.0004665675673128153)]
            },
            'differencerewards': {
                'Braess_1_4200_10_c1': [4, 0.99, 0.99, (15.474868480717216, -0.6639307200339724, 1.9923919431025884e-05)],
                'Braess_2_4200_10_c1': [8, 0.99, 0.99, (25.102148526071826, -0.39735262226528356, 4.5140529821233156e-05)],
                'Braess_3_4200_10_c1': [8, 0.99, 0.99, (35.0288911564607, -0.2835071839410541, 5.4183244112600644e-05)],
                'Braess_4_4200_10_c1': [12, 0.99, 0.99, (45.01382993197475, -0.22036250557388903, 4.6854566957231714e-05)],
                'Braess_5_4200_10_c1': [12, 0.99, 0.99, (55.03477324263084, -0.18023843187744854, 3.934590030343765e-05)],
                'Braess_6_4200_10_c1': [16, 0.99, 0.99, (65.00432653061232, -0.15170768433959297, 3.381225904666499e-05)],
                'Braess_7_4200_10_c1': [16, 0.99, 0.99, (75.01422222222284, -0.13038108022021225, 2.963406550204383e-05)],
                'BBraess_1_2100_10_c1_2100': [4, 0.98, 0.98, (7.99877777777269, -0.7398934134267005, 2.7585031873586494e-05)],
                'BBraess_3_2100_10_c1_900': [8, 0.99, 0.99, (32.74408174603319, -0.42688754594414857, 7.644275310494947e-05)],
                'BBraess_5_2100_10_c1_900': [4, 0.99, 0.99, (56.94145952380738, -0.416509647034962, 4.3089658210065106e-05)],
                'BBraess_7_2100_10_c1_900': [4, 0.99, 0.99, (130.52669523809578, -0.42267625446900237, 3.5258280502025145e-05)],
                'OW': [8, 0.99, 0.99, (82.30097647058824, -0.23601814991118988, 0.00010677999897750874)],
                'SF': [10, 0.9997, 0.999, (2218.3544778845267, -4.100377493630104e-05, 4.261356916280514e-09)]
            }
        }
        
        for alg in self.__algs_list:

            if alg in algs_to_ignore: 
                continue

            # configure the algorithm
            REGRET_AS_COST = False
            EXTRAPOLATE_COSTS = False
            USE_APP = False
            DIFFERENCE_REWARDS = False
            A_POSTERIORI_MCT = False
            DELTA_TOLLING = False
            STAT_REGRET_DIFF = False
            PRINT_OD_PAIRS_EVERY_EPISODE = False
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
            elif alg == 'ala18':
                A_POSTERIORI_MCT = True
            elif alg == 'deltatolling':
                DELTA_TOLLING = True
            elif alg == 'differencerewards':
                DIFFERENCE_REWARDS = True
            elif alg == 'stdql':
                pass

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

                res = run_simulation(P, 10, alpha=1.0, epsilon=1.0, alpha_decay=alpha_decay, epsilon_decay=epsilon_decay, min_alpha=0.0, min_epsilon=0.0, normalise_costs=True, regret_as_cost=REGRET_AS_COST, extrapolate_costs=EXTRAPOLATE_COSTS, use_app=USE_APP, difference_rewards=DIFFERENCE_REWARDS, a_posteriori_MCT=A_POSTERIORI_MCT, delta_tolling=DELTA_TOLLING, plot_results=False, stat_all=True, stat_regret_diff=STAT_REGRET_DIFF)
                
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
            self.run_batch_file(params)

    #-----------------------------------------------------------------------

    @staticmethod
    def add_subparser_arguments(subparsers):

        subp = subparsers.add_parser('ala18', help='experiments of the ALA-18 and TRC papers')

        subp.add_argument('--alg', dest='alg', action='store', default='ala18', type=str, choices=ala18.__algs_list,
                            help='algorithm to use')
        subp.add_argument('--episodes', dest='episodes', action='store', default=1000, type=int,
                            help='number of episodes to run the simulation')
        subp.add_argument('--net', dest='net', action='store', default='Braess_1_4200_10_c1', type=str,
                            help='Network environment')
        subp.add_argument('--k', dest='k', action='store', default=4, type=int,
                            help='number of roads')
        subp.add_argument('--rep', dest='rep', action='store', default=1, type=int,
                            help='number of trials per episode')
        subp.add_argument('--decay-eps', dest='decay-eps', action='store', default=0.99, type=float,
                            help='decay for epsilon')
        subp.add_argument('--decay-alpha', dest='decay-alpha', action='store', default=0.99, type=float,
                            help='decay for alpha')
        subp.add_argument('--avf', dest='avf', action='store', default=1, type=int,
                            help='number of vehicles controlled by each agent')
        subp.add_argument('--pid', dest='pid', action='store', default='', type=str, required=False, 
                            help='process ID (can include job ID as well)')
        subp.add_argument('--logs-dir', dest='logs-dir', action='store', default='results', type=str, required=False, 
                            help='the folder where the log files should be written')
        subp.add_argument('--validate', dest='validate', action='store_true', 
                            help='validate the experiment script')
        subp.set_defaults(exp_class='ala18')

    #-----------------------------------------------------------------------


    