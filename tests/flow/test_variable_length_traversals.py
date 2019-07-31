from RLTest import Env
from redisgraph import Graph, Node, Edge
from base import FlowTestsBase

dis_redis = None
redis_graph = None
redis_con = None
node_names = ["A", "B", "C", "D"]

# A can reach 3 nodes, B can reach 2 nodes, C can reach 1 node
max_results = 6

class VariableLengthTraversals(FlowTestsBase):
    def __init__(self):
        super(VariableLengthTraversals, self).__init__()
        global redis_con
        global redis_graph
        redis_con = self.env.getConnection()
        redis_graph = Graph("G", redis_con)
        self.populate_graph()

    @classmethod
    def tearDownClass(cls):
        if dis_redis is not None:
            dis_redis.stop()

    @classmethod
    def populate_graph(cls):
        global redis_graph

        nodes = []
         # Create nodes
        for n in node_names:
            node = Node(label="node", properties={"name": n})
            redis_graph.add_node(node)
            nodes.append(node)

        # Create edges
        for i in range(len(nodes) - 1):
            edge = Edge(nodes[i], "knows", nodes[i+1], properties={"connects": node_names[i] + node_names[i+1]})
            redis_graph.add_edge(edge)

        redis_graph.commit()

    # Sanity check against single-hop traversal
    def test01_conditional_traverse(self):
        query = """MATCH (a)-[e]->(b) RETURN a.name, e.connects, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        expected_result = [['A', 'AB', 'B'],
                           ['B', 'BC', 'C'],
                           ['C', 'CD', 'D']]
        self.env.assertEquals(actual_result.result_set == expected_result)

    # Traversal with no labels
    def test02_unlabeled_traverse(self):
        query = """MATCH (a)-[*]->(b) RETURN a.name, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)

        query = """MATCH (a)<-[*]-(b) RETURN a, b ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)

    # Traversal with labeled source
    def test03_source_labeled(self):
        query = """MATCH (a:node)-[*]->(b) RETURN a.name, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)

        query = """MATCH (a:node)<-[*]-(b) RETURN a.name, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)

    # Traversal with labeled dest
    def test04_dest_labeled(self):
        query = """MATCH (a)-[*]->(b:node) RETURN a.name, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)

        query = """MATCH (a)<-[*]-(b:node) RETURN a.name, b.name ORDER BY a.name, b.name"""
        actual_result = redis_graph.query(query)
        self.env.assertEquals(len(actual_result.result_set), max_results)