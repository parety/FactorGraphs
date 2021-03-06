"""OLD CODE"""
from manimlib.imports import *
import numpy as np
import networkx as nx


# %%
def kill_multiedges_reaxis_all(f, fg):
    """Combine all multiedges between f and its neighbor variables.

    DOES NOT PERFORM COMPUTATION. This is a helper function and should only be
    used in other functions which perform the appropriate computation.

    No indexing is performed on the factor of f. This purely deals with the
    edges in the factor graph and the axis attributes of the corresponding
    edges.

    The combination of edges in the graph is separate from the actual
    computation because actual products which might result in multiedges do not
    separately perform an indexing as that is extremely inefficient.
    (See combine_factors for an example.)

    Parameters
    ----------
    f : node key
        The factor.
    fg : MultiDiGraph
        The factor graph.

    Returns
    -------
    MultiDiGraph
        Copy of the factor graph with multiedges killed.

    """
    new_fg = fg.copy()

    indices = [0]*fg.degree(f)
    for edge in fg.edges(f, keys=True):
        indices[fg.edges[edge]['axis']] = edge[1]

    assert 0 not in indices, "Axes of the factor are not valid, the factor \
    graph is invalid"

    new_axes = {}  # the new axis of each variable
    keep_axes = {}  # the axis of the edge to keep for each variable
    keep_keys = {}  # the edge key for the edge to keep for each variable
    c = 0
    for i, ind in enumerate(indices):
        if ind not in new_axes.keys():
            new_axes[ind] = c
            keep_axes[ind] = i
            keep_keys[ind] = [edge for edge in fg.edges(f, keys=True)
                              if fg.edges[edge]['axis'] == i][0][2]
            c += 1

    for edge in fg.edges(f, keys=True):
        # remove edges if their axes isnt one that should be kept
        if fg.edges[edge]['axis'] not in keep_axes.values():
            ind = edge[1]
            edge_data = fg.edges[edge]
            keep_edge_data = new_fg.edges[f, ind, keep_keys[ind]]
            if 'contraction' not in keep_edge_data:
                keep_edge_data['contraction'] = {}
            keep_edge_data['contraction'][edge] = edge_data
            new_fg.remove_edge(*edge)

    # reassign new axes
    for edge in new_fg.edges(f, keys=True):
        new_fg.edges[edge]['axis'] = new_axes[edge[1]]

    # new_fg.edges(data='contraction')
    # new_fg.edges(data='axis')

    return new_fg


# %%


def get_fg_node(n, G):
    node = G.node[n]
    type_to_shape = {
        'variable': Circle,
        'factor': Square
    }

    def node_color(node_dict):
        if node_dict['type'] == 'factor':
            return GREEN
        return WHITE if not node_dict['summed'] else GRAY

    bg = type_to_shape[node['type']](color=BLACK, fill_color=node_color(node),
                                     fill_opacity=1, radius=0.3,
                                     side_length=0.8)
    node_name = TextMobject(n, color=BLACK)
    x, y = node['pos']
    grp = VGroup(bg, node_name)
    grp.move_to(x*RIGHT + y*UP)
    return grp

# %%


def get_fg_edge_curve(ed, G):
    s = G.edges[ed]['size']
    node1 = G.node[ed[0]]
    node2 = G.node[ed[1]]
    x1, y1 = node1['pos']
    x2, y2 = node2['pos']
    start = x1*RIGHT + y1*UP
    end = x2*RIGHT + y2*UP

    # TODO: add default points for multiedges

    pnts = [x*RIGHT + y*UP for x, y in G.edges[ed].get('points', [])]

    edge = VMobject(stroke_width=np.sqrt(s)+1, color=BLACK)
    edge.set_points_smoothly([start, *pnts, end])

    return edge


def pos2d_to_np3d(pos):
    return np.array(list(pos)+[0])
# %%


def sum_node(n, mnG):
    assert mnG.graph.nodes[n]['type'] == 'variable', "Can't sum factor node"

    mnG.graph.nodes[n]['summed'] = True
    return Transform(mnG.nodes[mnG.graph.nodes[n]['mob_id']],
                     get_fg_node(n, mnG.graph))
# %%


def get_fg_edge_line(n1, n2, G):
    s = G[n1][n2]['size']
    node1 = G.node[n1]
    node2 = G.node[n2]
    x1, y1 = node1['pos']
    x2, y2 = node2['pos']
    start = x1*RIGHT + y1*UP
    end = x2*RIGHT + y2*UP
    edge = Line(start, end, stroke_width=s/10, color=BLACK)
    return edge

# %%


def get_closest_polygonal_point(n1, pos, G):
    deg = G.degree[n1]
    node = G.node[n1]
    phase = node.get('phase', 0)
    rad = node.get('radius', 0.4)
    pos = np.array(pos)
    centre = np.array(node['pos'])
    thetas = np.arange(deg) * 2*np.pi/deg + phase
    polyg = np.stack([np.cos(thetas), np.sin(thetas)], axis=-1)
    points = centre + polyg*rad
    dists = np.linalg.norm(points-pos, axis=1)
    return np.array(list(points[dists.argmin()])+[0])

# %%


def get_fg_edge_polygonal(n1, n2, G):
    s = G[n1][n2]['size']
    node1 = G.node[n1]
    node2 = G.node[n2]
    x1, y1 = node1['pos']
    x2, y2 = node2['pos']
    start = x1*RIGHT + y1*UP
    end = x2*RIGHT + y2*UP

    p1 = get_closest_polygonal_point(n1, (x2, y2), G)
    p2 = get_closest_polygonal_point(n2, (x1, y1), G)

    edge = VMobject(stroke_width=s/10, color=BLACK)
    edge.set_points_smoothly([start, p1, p2, end])

    # Line(start, end, stroke_width=s/10, color=BLACK)

    return edge


def combine_nodes(n1, n2, mnG):
    """Short summary.

    Parameters
    ----------
    n1 : type
        Description of parameter `n1`.
    n2 : type
        Description of parameter `n2`.
    mnG : type
        Description of parameter `mnG`.

    Returns
    -------
    type
        Description of returned object.

    """

    # straightforward assertions
    assert mnG.graph.nodes[n1]['type'] == mnG.graph.nodes[n2]['type'], \
        "cannot combine nodes of different types"

    t = mnG.graph.nodes[n1]['type']

    if t == 'variable':
        assert mnG.graph.nodes[n1]['summed'] == mnG.graph.nodes[n2]['summed'],\
            "cannot combine summed with non summed variable"

        assert mnG.graph.nodes[n1]['size'] == mnG.graph.nodes[n2]['size'],\
            "cannot combine variables of different sizes"

    # get initial positions
    pos1 = np.array(mnG.graph.nodes[n1]['pos'])
    pos2 = np.array(mnG.graph.nodes[n2]['pos'])

    # new position is midpoint by default
    new_pos = (pos1+pos2) / 2

    # name of the new combined node
    if t == 'variable':
        new_node_name = n1  # first node for variables
    else:
        new_node_name = n1+n2  # concatenate for factors

    # let's get all the edges which have to move
    n1_edges = []  # edges from n1
    n2_edges = []  # edges from n2
    for ed in mnG.graph.edges:
        if n1 in ed:
            n1_edges.append(ed)
        elif n2 in ed:
            n2_edges.append(ed)

    # before we can contract the two nodes using networkx, we need to make sure
    # that the axes of the combined factor is correct.
    if t == 'factor':

        # we simply increase the axis count of all dims of n2 by ndim of n1
        axis_increase = len(mnG.graph.nodes[n1]['factor'].shape)  # ndim of n1
        for a, b, k in n2_edges:
            # print(f"INCREASE ({n1_, n2_, k})")

            # all edges from n2 have their axis increased
            mnG.graph.edges[a, b, k]['axis'] += axis_increase

    # get new graph by contracting nodes.
    # This is where we need to enforce the graph to be a dirceted one, to force
    # consistent behavior by the networkx contract function for factor and
    # variable contractions
    new_graph = nx.contracted_nodes(mnG.graph, n1, n2)

    # note that we made the new graph after modifying the axis identifiers in
    # the original graph itself. this will matter later

    # relabel inplace
    nx.relabel_nodes(new_graph, {n1: new_node_name}, copy=False)

    # assign new position to the newly created node
    new_graph.nodes[new_node_name]['pos'] = tuple(new_pos)

    # we only create a new node mobject as a target for the transform,
    # we won't actually add this to the ManimGraph, but instead we will reuse
    # an already present mobject, namely the mobject of node n1
    new_node = get_fg_node(new_node_name, new_graph)

    # change n1 to the new_node, and keep it
    move1 = Transform(mnG.nodes[n1], new_node)

    # change n2 also to the new_node, but then remove it by fading out
    move2 = Succession(Transform(mnG.nodes[n2], new_node),
                       FadeOut(mnG.nodes[n2], darkness=0))
    mnG.remove(mnG.nodes[n2])  # remove from submobjects of ManimGraph

    # update the ManimGraph's copy of the node dict using the new name
    mnG.nodes[new_node_name] = mnG.nodes[n1]

    del mnG.nodes[n2]  # remove the node n2 from the ManimGraph dict

    if t == 'factor':
        # if we are combining factors, remove n1 as well, because new_node_name
        # is different from both n1 and n2
        del mnG.nodes[n1]

        # when combining factors, we actually need to perform some computation.
        # the basic computation is a hadamard product, but no dimensions are
        # reduced. So you can think of this as a fully broadcasted hadamard
        # product.
        a = mnG.graph.nodes[n1]['factor']
        b = mnG.graph.nodes[n2]['factor']

        # fully broadcasted hadamard product
        # a - (10, 20, 30), b - (40, 50) -> c - (10, 20, 30, 40, 50)
        c = a.reshape(*a.shape, *[1 for _ in b.shape]) * b

        new_graph.nodes[new_node_name]['factor'] = c

        # Note that this is actually inefficient, as in some cases
        # multiedges could be formed, and a diag indexing results, which can
        # actually save on significant computation, but implementing that is a
        # TODO

    # for e, v in new_graph.edges.items():
    #     print(e, v)

    # ------------- #
    # Now we create the edge animations and handle updating the ManimGraph's
    # copy of the edge mobject storage

    move_edges = []  # list of all anims

    # this will be the new edge_dict storage for the ManimGraph
    new_edges = mnG.edges.copy()

    # loop over all edges that need to move
    for n1_, n2_, k in n1_edges+n2_edges:

        # currently persist any points TODO: change points smartly (at least
        # for multiedges)
        pnts = mnG.graph.edges[n1_, n2_, k].get('points', [])

        if t == 'variable':
            # Since all the edges are directed (purely for consistency) from
            # factors to variables, the order of the new points depends on
            # what type of nodes we are combining

            # For variables, the new position is the end of the edge
            trans = ApplyMethod(mnG.edges[n1_, n2_][k].set_points_smoothly,
                                [pos2d_to_np3d(mnG.graph.nodes[n1_]['pos']),
                                 *[pos2d_to_np3d(p) for p in pnts],
                                 pos2d_to_np3d(new_pos)])
        else:
            # For factors, the new position is the start of the edge
            trans = ApplyMethod(mnG.edges[n1_, n2_][k].set_points_smoothly,
                                [pos2d_to_np3d(new_pos),
                                 *[pos2d_to_np3d(p) for p in pnts],
                                 pos2d_to_np3d(mnG.graph.nodes[n2_]['pos'])])

        move_edges.append(trans)  # add to list of anims

        # now, we delete this edge from the new_edges dict, and we will
        # add it back later with the changed key. The key changes due to the
        # node contraction.
        if (n1_, n2_) in new_edges.keys():
            # if check in case of multi edges
            del new_edges[n1_, n2_]

    # Now we add back the edge mobjects we transformed to the ManimGraph's
    # edge dict, but with the correct key. We use the consistent dirceted
    # storage of the edges (factor -> variable) to make this easier.
    for n1_, n2_, k in n1_edges+n2_edges:
        # we know the nodes between which the edges are, but in the case of
        # multi-edges, the indetified k will change
        if t == 'variable':
            # For a variable combination, we can uniquely identify an edge
            # that we moved by finding the axis it corresponded to
            ind = mnG.graph.edges[n1_, n2_, k]['axis']
            for key, v in new_graph[n1_][new_node_name].items():
                # find the value of k of that edge
                if v['axis'] == ind:
                    new_k = key
                    break

            # Adding back edges to ManimGraph edge dict keeping track of keys
            if (n1_, new_node_name) not in new_edges.keys():
                new_edges[n1_, new_node_name] = {}
            new_edges[n1_, new_node_name][new_k] = mnG.edges[n1_, n2_][k]

    # We need to do a slightly different procedure for factors, but essentially
    # the same use of the axis identifier
    if t == 'factor':
        for n1_, n2_, k in n1_edges+n2_edges:
            # Notice that the axis counts were updated in the original graph
            # this allows us to still use it to uniquely identify edges, even
            # though they will come from different factors, because the axis
            # updates made it so that the two factors being combined have
            # valid axis counts after the contraction
            ind = mnG.graph.edges[n1_, n2_, k]['axis']
            for key, v in new_graph[new_node_name][n2_].items():
                if v['axis'] == ind:
                    new_k = key
                    break

            # similar dict adding back as in variable case
            if (new_node_name, n2_) not in new_edges.keys():
                new_edges[new_node_name, n2_] = {}
            new_edges[new_node_name, n2_][new_k] = mnG.edges[n1_, n2_][k]

    mnG.graph = new_graph
    mnG.edges = new_edges

    return [move1, move2, *move_edges]
