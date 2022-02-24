#!/usr/bin/python
'''
KSP v1.42

Created on February 10, 2014 by Gabriel de Oliveira Ramos <goramos@inf.ufrgs.br>

Versions history:
v1.0 (10-Feb-2014) -  Creation.
v1.1 (20-Apr-2014) -  Adjusted error related with the creation of root and spur paths.
					  By definition, the spur node must be both in root AND spur paths
					  (previously the spur node was not in root path, and some problems
					  were identified in Ortuzar network for AM pair and K=4).
v1.2 (12-May-2014) -  Call of algorithm was changed from 'main(...)' to 'run(...)', and
					  parameters 'origin' and 'destination' were replaced by 'OD_list'
					  (a list of OD-pairs). Furthermore, the list of parameters of the 
					  command line call (__main__) was changed accordingly.
					  Finally, the output text was changed according to the specification
					  defined by Dr. Ana Bazzan.
v1.21 (5-Jun-2014) -  Created the function getKRoutes(graph_file, origin, destination, K)
                      to be called externally by another applications. The function returns,
                      for a given origin and destination, the K shortest routes in a list
                      format. The list structure was specified in the following way:
                          [ [route1, cost1], [route2, cost2], ..., [routeK, costK] ]
                      This function runs one OD-pair each time. For multiple OD-pairs,
                      it needs to be called multiple times.
v1.22 (25-Nov-2014) - Changed the type of edges' length attribute from int to float.
v1.23 (09-Dez-2015) - Fixed the problem that was allowing the occurrence of loops in 
                      the paths. Creation of function generateGraphFromList that generates 
                      the list of nodes and edges from given lists. Creation of a new function 
                      getKRoutes to generate the K routes of a given OD pair AND the list 
                      of nodes and vertices (the other version creates such lists from the 
                      network file). The old version still works but was renamed to 
                      getKRoutesNetFile. Creation of function pickEdgesListAll to return
                      all edges arriving and leaving the given node. Changed the way edges 
                      are printed: now a '|' symbol is used to separate its start and
                      end nodes.
v1.3 (07-Jun-2016) -  Several adjustments to make the script compliant with the new network
					  files specification (http://wiki.inf.ufrgs.br/network_files_specification). 
					  Specifically: (i) the script recognises only the new format, (ii) no
					  OD pairs are required when calling the script (in this case, the routes 
					  are generated for ALL OD pairs specified in the network file), (iii) the
					  generateGraph function now also returns the set of OD pairs, (iv) the
					  edges lengths are now called costs, (v) alterado o tipo arc para dedge,
					  and (vi) minor issues.
v1.31 (25-Aug-2016) - Small fixes related to edges names; according to the current network 
                      specification, links are named with a dash (A-B) rather than a pipe (A|B).
v1.32 (19-Set-2016) - Small fix related with dedges' name (A-B is named A-B in the forward link 
                      but B-A in the backward one).
v1.42 (12-Nov-2016) - Added parameter to define the flow of vehicles to be used when computing
					  the links' costs.
<new versions here>

'''

import argparse
from py_expression_eval import Parser

# represents a node in the graph
class Node:
	def __init__(self, name):
		self.name = name	# name of the node
		self.dist = 1000000	# distance to this node from start node
		self.prev = None	# previous node to this node
		self.flag = 0		# access flag

# represents an edge in the graph
class Edge:
	def __init__(self, name, u, v, cost):
		self.name = name
		self.start = u
		self.end = v
		self.cost = cost # represents the edge's cost under free flow

# read a text file and generate the graph according to declarations
def generateGraph(graph_file, flow=0.0):
	V = [] # vertices
	E = [] # edges
	F = {} # cost functions
	OD = [] # OD pairs
	
	lineid = 0
	for line in open(graph_file, 'r'):
		
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
			function = Parser().parse(taglist[3])
			
			# process the constants
			constants = function.variables()
			if params[0] in constants: # the parameter must be ignored
				constants.remove(params[0]) 
			
			# store the function
			F[taglist[1]] = [params[0], constants, function]
			
		elif taglist[0] == 'node':
			V.append(Node(taglist[1]))
			
		elif taglist[0] == 'dedge' or taglist[0] == 'edge': # dedge is a directed edge
			
			# process the cost
			function = F[taglist[4]] # get the corresponding function
			param_values = dict(zip(function[1], map(float, taglist[5:]))) # associate constants and values specified in the line (in order of occurrence)
			param_values[function[0]] = flow # set the function's parameter with the flow value 
			cost = function[2].evaluate(param_values) # calculate the cost
			
			# create the edge(s)
			E.append(Edge(taglist[1], taglist[2], taglist[3], cost))
			if taglist[0] == 'edge':
				E.append(Edge('%s-%s'%(taglist[3], taglist[2]), taglist[3], taglist[2], cost))
			
		elif taglist[0] == 'od':
			OD.append(taglist[1])
		
		else:
			raise Exception('Network file does not comply with the specification! (line %d: "%s")' % (lineid, line))
	
	
	return V, E, OD

# generate the graph from a list of nodes* and a list of edges**
# * a node here is represented by a string referring to its name
# ** an edge is represented by a list [origin, destination, cost]
# (this function was created to be called externally by another applications)
def generateGraphFromList(listNodes, listEdges, generateBackwardEdges=False):
	V = []
	E = []
	
	# generate the list of nodes
	for v in listNodes:
		V.append(Node(v))
	
	# generate the list of edges
	for e in listEdges:
		E.append(Edge(e[0], e[1], e[2]))
		# generate backward edges
		if generateBackwardEdges:
			E.append(Edge(e[1], e[0], e[2]))
	
	return V, E

# reset graph's variables to default
def resetGraph(N, E):
	for node in N:
		node.dist = 1000000.0
		node.prev = None
		node.flag = 0

# returns the smallest node in N but not in S
def pickSmallestNode(N):
	minNode = None
	for node in N:
		if node.flag == 0:
			minNode = node
			break
	if minNode == None:
		return minNode
	for node in N:
		if node.flag == 0 and node.dist < minNode.dist:
			minNode = node
	return minNode

# returns the list of edges starting in node u
def pickEdgesList(u, E):
	uv = []
	for edge in E:
		if edge.start == u.name:
			uv.append(edge)
	return uv

# returns the list of edges that start or end in node u
def pickEdgesListAll(u, E):
	uv = []
	for edge in E:
		if edge.start == u.name or edge.end == u.name:
			uv.append(edge)
	return uv

# Dijkstra's shortest path algorithm
def findShortestPath(N, E, origin, destination, ignoredEdges):
	
	# reset the graph (so as to discard information from previous runs)
	resetGraph(N, E)
	
	# set origin node distance to zero, and get destination node
	dest = None
	for node in N:
		if node.name == origin:
			node.dist = 0
		if node.name == destination:
			dest = node
	
	u = pickSmallestNode(N)
	while u != None:
		u.flag = 1
		uv = pickEdgesList(u, E)
		n = None
		for edge in uv:
			
			# avoid ignored edges
			if edge in ignoredEdges:
				continue
			
			# take the node n
			for node in N:
				if node.name == edge.end:
					n = node
					break
			if n.dist > u.dist + edge.cost:
				n.dist = u.dist + edge.cost
				n.prev = u
		
		u = pickSmallestNode(N)
		# stop when destination is reached
		if u == dest:
			break
	
	# generate the final path
	S = []
	u = dest
	while u.prev != None:
		S.insert(0,u)
		u = u.prev
	S.insert(0,u)
	
	return S

# generate a string from the path S in a specific format
def pathToString(S, E):
	strout = '['
	for i in xrange(0,len(S)-1):
		if i > 0:
			strout += ', '
		strout += '\'' + getEdge(E, S[i].name, S[i+1].name).name + '\''
	return strout + ']'

# generate a list with the edges' names of a given route S
def pathToListOfString(S, E):
	lout = []
	for i in xrange(0,len(S)-1):
		lout.append(getEdge(E, S[i].name, S[i+1].name).name)
	return lout

# get the directed edge from u to v
def getEdge(E, u, v):
	for edge in E:
		if edge.start == u and edge.end == v:
			return edge
	return None

def runKShortestPathsStep(V, E, origin, destination, k, A, B):
	# Step 0: iteration 1
	if k == 1:
		A.append(findShortestPath(V, E, origin, destination, []))
		
	# Step I: iterations 2 to K
	else:
		lastPath = A[-1] 
		for i in range(0, len(lastPath)-1):
			# Step I(a)
			spurNode = lastPath[i]
			rootPath = lastPath[0:i+1]
			toIgnore = []
			
			for path in A:
				if path[0:i+1] == rootPath:
					ed = getEdge(E, spurNode.name, path[i+1].name)
					toIgnore.append(ed)
			
			# ignore the edges passing through nodes already in rootPath (except for the spurNode)
			for noder in rootPath[:-1]: 
				edgesn = pickEdgesListAll(noder, E)
				for ee in edgesn:
					toIgnore.append(ee)
			
			# Step I(b)
			spurPath = findShortestPath(V, E, spurNode.name, destination, toIgnore)
			if spurPath[0] != spurNode:
				continue
			
			# Step I(c)
			totalPath = rootPath + spurPath[1:]
			B.append(totalPath)
		
		# handle the case where no spurs (new paths) are available
		if not B:
			return False
			
		# Step II
		bestInB = None
		bestInBcost = 999999999
		for path in B:
			cost = calcPathCost(path, E)
			if cost < bestInBcost:
				bestInBcost = cost
				bestInB = path
		A.append(bestInB)
		while bestInB in B:
			B.remove(bestInB)
		
	return True

# Yen's K shortest loopless paths algorithm
def KShortestPaths(V, E, origin, destination, K):
	# the K shortest paths
	A = []
	
	# potential shortest paths
	B = []
	
	for k in xrange(1,K+1):
		try:
			if not runKShortestPathsStep(V, E, origin, destination, k, A, B):
				break
		except:
			print 'Problem on generating more paths! Only %d paths were found!' % (k-1)
			break
		
	return A

# calculate path S's cost
def calcPathCost(S, E):
	cost = 0
	prev = None
	for node in S:
		if prev != None:
			cost += getEdge(E, prev.name, node.name).cost
		prev = node
	
	return cost

# main procedure for many OD-pairs
def run(graph_file, K, OD_pairs=None, flow=0.0):
	
	# read graph from file
	N, E, OD = generateGraph(graph_file, flow)
	
	# process the list of OD-pairs (if no OD pair was defined by the 
	# user, then all OD pairs from the network file are considered)
	if OD_pairs != None:
		OD = OD_pairs.split(';')
	for i in xrange(0,len(OD)):
		OD[i] = OD[i].split('|')
	
	# find K shortest paths of each OD-pair
	print 'ksptable = ['
	lastod = len(OD)-1
	for iod, (o, d) in enumerate(OD):
		# find K shortest paths for this specific OD-pair
		S = KShortestPaths(N, E, o, d, K)
		
		# print the result for this specific OD-pair
		print '\t[ # ' + str(o) + '|' + str(d) + ' flow'
		last = len(S)-1
		for i, path in enumerate(S):
			comma = ','
			if i == last:
				comma = ''
			print '\t\t' + pathToString(path, E) + comma + " # cost " + str(calcPathCost(path, E))
		comma = ','
		if iod == lastod:
			comma = ''
		print '\t]' + comma
	print ']'

# return a list with the K shortest paths for the given origin-destination pair,
# given a network file (this function was created to be called externally by 
# another applications)
def getKRoutesNetFile(graph_file, origin, destination, K):
	
	lout = []
	
	# read graph from file
	N, E, _ = generateGraph(graph_file)
	
	# find K shortest paths for this specific OD-pair
	S = KShortestPaths(N, E, origin, destination, K)
	
	for path in S:
		# store the path (in list of strings format) and cost to the out list 
		lout.append([pathToListOfString(path, E), calcPathCost(path, E)])
		
	return lout

# return a list with the K shortest paths for the given origin-destination pair,
# given the lists of nodes and edges (this function was created to be called 
# externally by another applications)
def getKRoutes(N, E, origin, destination, K):
	
	lout = []
	
	# find K shortest paths for this specific OD-pair
	S = KShortestPaths(N, E, origin, destination, K)
	
	for path in S:
		# store the path (in list of strings format) and cost to the out list 
		lout.append([pathToListOfString(path, E), calcPathCost(path, E)])
		
	return lout
	
# initializing procedure
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='KSP v1.42\nCompute the K shortest loopless paths between two nodes of a given graph, using Yen\'s algorithm [1]. Complete instructions available at [2].',
		epilog='GRAPH FILE FORMATTING INSTRUCTIONS' +
		'\nSee [3] for complete instructions.'+
		'\n\nREFERENCES' +
		'\n[1] Yen, J.Y.: Finding the k shortest loopless paths in a network. Management Science 17(11) (1971) 712-716.' +
		'\n[2] http://wiki.inf.ufrgs.br/K_Shortest_Loopless_Paths.' +
		'\n[3] http://wiki.inf.ufrgs.br/network_files_specification.' +
		'\n\nAUTHOR' +
		'\nCreated in February 10, 2014, by Gabriel de Oliveira Ramos <goramos@inf.ufrgs.br>.',
		formatter_class=argparse.RawTextHelpFormatter)

	parser.add_argument('-f', dest='file', required=True,
						help='the graph file')
	parser.add_argument('-k', dest='K', type=int, required=True,
						help='number of shortest paths to find')
	parser.add_argument('-l', dest='OD_pairs', required=False,
						help='list of OD-pairs, in the format \'O|D;O|D;[and so on]\', where O are valid origin nodes, and D are valid destination nodes')
	parser.add_argument('-n', dest='flow', type=float, required=False, default=0.0,
						help='number of vehicles (flow) to consider when computing the links\' costs')
	args = parser.parse_args()

	graph_file = args.file
	OD_pairs = args.OD_pairs
	K = args.K
	flow = args.flow

	run(graph_file=graph_file, K=K, OD_pairs=OD_pairs, flow=flow)
