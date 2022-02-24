import KSP # KSP algorithm
from tqdm import tqdm # loading bar
import argparse # arguments

def generate_routes_file(net_file, k, flow):

	# generate the list of vertices and edges from the network file
	V, E, OD = KSP.generateGraph(net_file, flow)

	# create the routes file
	arq = open(net_file.replace('.net','.routes'), 'w')
	arq.write('#OD route\n')

	# for each OD pair
	for od in tqdm(OD, ascii=True, desc='Generating routes (k=%d, |OD|=%d)' % (k, len(OD))): # to look at all pairs, use the variable OD (above)

		#~ print 'Pair %s' % od
		origin, destination = od.split('|')
		
		# run the algorithm (return the K routes and associated costs of the given origin-destination pair)
		routes = KSP.getKRoutes(V, E, origin, destination, k)
		
		# print the routes
		for i in routes:
			
			# the route as a list of strings, where each element corresponds to a link's name
			route = i[0]
			
			# the cost of the route (a float value)
			cost = i[1]
			
			# add the current route to the file
			arq.write('%s %s\n' % (od, str(route).replace('[','').replace(']','').replace('\'','').replace(' ','')))

		arq.flush()

	arq.close()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generates the set of K shortest routes for each OD pair of the specified network (which must follow Maslab\'s network files specification [1]).',
        epilog = '\n\nREFERENCES' +
        '\n[1] http://wiki.inf.ufrgs.br/network_files_specification.' +
        '\n\nAUTHOR' +
        '\nCreated on February 21, 2017, by Gabriel de Oliveira Ramos <goramos@inf.ufrgs.br>.',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--net', dest='net_file', required=True, type=str,
                        help='the network file (the file format is detailed in [1])')
    parser.add_argument('--k', dest='k', default=16, type=int,
                        help='the number of routes to find (as for the Braess networks, we used k=100)')
    parser.add_argument('--flow', dest='flow', default=0.0, type=float, 
                        help='the flow of vehicles to be used when computing the links\' costs (as for the Braess networks, we used flow=1.0 to differentiate routes with fixed and non-fixed costs)')
    args = parser.parse_args()
    
    generate_routes_file(net_file=args.net_file, k=args.k, flow=args.flow)
