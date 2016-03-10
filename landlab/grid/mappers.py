#! /usr/bin/env python
"""Map values from one grid element to another.

Each link has a *tail* and *head* node. The *tail* nodes are located at the
start of a link, while the head nodes are located at end of a link.

Below, the numbering scheme for links in `RasterModelGrid` is illustrated
with an example of a four-row by five column grid (4x5). In this example,
each * (or X) is a node, the lines represent links, and the ^ and > symbols
indicate the direction and *head* of each link. Link heads in the
`RasterModelGrid` always point in the cardinal directions North (N) or East
(E).::

    *--27-->*--28-->*--29-->*--30-->*
    ^       ^       ^       ^       ^
   22      23      24      25      26
    |       |       |       |       |
    *--18-->*--19-->*--20-->*--21-->*
    ^       ^       ^       ^       ^
    13      14      15      16     17
    |       |       |       |       |
    *---9-->*--10-->X--11-->*--12-->*
    ^       ^       ^       ^       ^
    4       5       6       7       8
    |       |       |       |       |
    *--0--->*---1-->*--2--->*---3-->*

For example, node 'X' has four link-neighbors. From south and going clockwise,
these neighbors are [6, 10, 15, 11]. Both link 6 and link 10 have node 'X' as
their 'head' node, while links 15 and 11 have node 'X' as their tail node.
"""
from __future__ import division

import numpy as np


def map_link_head_node_to_link(grid, var_name, out=None):
    """Map values from a link head nodes to links.

    Iterate over a grid and identify the node at the *head*. For each link,
    the value of *var_name* at the *head* node is mapped to the corresponding
    link.

    In a RasterModelGrid, each one node has two adjacent "link heads". This
    means each node value is mapped to two corresponding links.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_link_head_node_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_node['z'] = np.array([ 0,  1,  2,  3,
    ...                               4,  5,  6,  7,
    ...                               8,  9, 10, 11])
    >>> map_link_head_node_to_link(rmg, 'z')
    array([  1.,   2.,   3.,   4.,   5.,   6.,   7.,   5.,   6.,   7.,   8.,
             9.,  10.,  11.,   9.,  10.,  11.])

    >>> values_at_links = rmg.empty(centering='link')
    >>> rtn = map_link_head_node_to_link(rmg, 'z', out=values_at_links)
    >>> values_at_links
    array([  1.,   2.,   3.,   4.,   5.,   6.,   7.,   5.,   6.,   7.,   8.,
             9.,  10.,  11.,   9.,  10.,  11.])
    >>> rtn is values_at_links
    True
    """
    values_at_nodes = grid.at_node[var_name]
    if out is None:
        out = grid.empty(centering='link')
    out[:] = values_at_nodes[grid.node_at_link_head]

    return out


def map_link_tail_node_to_link(grid, var_name, out=None):
    """Map values from a link tail nodes to links.

    map_link_tail_node_to_link iterates across the grid and
    identifies the node at the "tail", or the "from" node for each link. For
    each link, the value of 'var_name' at the "from" node is mapped to the
    corresponding link.

    In a RasterModelGrid, each one node has two adjacent "link tails". This
    means each node value is mapped to two corresponding links.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_link_tail_node_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_node['z'] = np.array([ 0,  1,  2,  3,
    ...                               4,  5,  6,  7,
    ...                               8,  9, 10, 11])
    >>> map_link_tail_node_to_link(rmg, 'z')
    array([  0.,   1.,   2.,   0.,   1.,   2.,   3.,   4.,   5.,   6.,   4.,
             5.,   6.,   7.,   8.,   9.,  10.])

    >>> values_at_links = rmg.empty(centering='link')
    >>> rtn = map_link_tail_node_to_link(rmg, 'z', out=values_at_links)
    >>> values_at_links
    array([  0.,   1.,   2.,   0.,   1.,   2.,   3.,   4.,   5.,   6.,   4.,
             5.,   6.,   7.,   8.,   9.,  10.])
    >>> rtn is values_at_links
    True
    """
    if out is None:
        out = grid.empty(centering='link')

    values_at_nodes = grid.at_node[var_name]
    out[:] = values_at_nodes[grid.node_at_link_tail]

    return out


def map_min_of_link_nodes_to_link(grid, var_name, out=None):
    """Map the minimum of a link's nodes to the link.

    map_min_of_link_nodes_to_link iterates across the grid and
    identifies the node values at both the "head" and "tail" of a given link.
    This function evaluates the value of 'var_name' at both the "to" and
    "from" node. The minimum value of the two node values is then mapped to
    the link.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_min_of_link_nodes_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> _ = rmg.add_field('node', 'z',
    ...                   [[ 0,  1,  2,  3],
    ...                    [ 7,  6,  5,  4],
    ...                    [ 8,  9, 10, 11]])
    >>> map_min_of_link_nodes_to_link(rmg, 'z')
    array([  0.,   1.,   2.,   0.,   1.,   2.,   3.,   6.,   5.,   4.,   7.,
             6.,   5.,   4.,   8.,   9.,  10.])

    >>> values_at_links = rmg.empty(centering='link')
    >>> rtn = map_min_of_link_nodes_to_link(rmg, 'z', out=values_at_links)
    >>> values_at_links
    array([  0.,   1.,   2.,   0.,   1.,   2.,   3.,   6.,   5.,   4.,   7.,
             6.,   5.,   4.,   8.,   9.,  10.])
    >>> rtn is values_at_links
    True
    """
    if out is None:
        out = grid.empty(centering='link')

    values_at_nodes = grid.at_node[var_name]
    np.minimum(values_at_nodes[grid.node_at_link_head],
               values_at_nodes[grid.node_at_link_tail],
               out=out)

    return out


def map_max_of_link_nodes_to_link(grid, var_name, out=None):
    """Map the maximum of a link's nodes to the link.

    map_max_of_link_nodes_to_link iterates across the grid and
    identifies the node values at both the "head" and "tail" of a given link.
    This function evaluates the value of 'var_name' at both the "to" and
    "from" node. The maximum value of the two node values is then mapped to
    the link.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_max_of_link_nodes_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> _ = rmg.add_field('node', 'z',
    ...                   [[0, 1, 2, 3],
    ...                    [7, 6, 5, 4],
    ...                    [8, 9, 10, 11]])
    >>> map_max_of_link_nodes_to_link(rmg, 'z')
    array([  1.,   2.,   3.,   7.,   6.,   5.,   4.,   7.,   6.,   5.,   8.,
             9.,  10.,  11.,   9.,  10.,  11.])

    >>> values_at_links = rmg.empty(centering='link')
    >>> rtn = map_max_of_link_nodes_to_link(rmg, 'z', out=values_at_links)
    >>> values_at_links
    array([  1.,   2.,   3.,   7.,   6.,   5.,   4.,   7.,   6.,   5.,   8.,
             9.,  10.,  11.,   9.,  10.,  11.])
    >>> rtn is values_at_links
    True
    """
    if out is None:
        out = grid.empty(centering='link')

    values_at_nodes = grid.at_node[var_name]
    np.maximum(values_at_nodes[grid.node_at_link_head],
               values_at_nodes[grid.node_at_link_tail],
               out=out)

    return out


def map_mean_of_link_nodes_to_link(grid, var_name, out=None):
    """Map the mean of a link's nodes to the link.

    map_mean_of_link_nodes_to_link iterates across the grid and
    identifies the node values at both the "head" and "tail" of a given link.
    This function takes the sum of the two values of 'var_name' at both the
    "to" and "from" node. The average value of the two node values of
    'var_name' is then mapped to the link.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_mean_of_link_nodes_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_node['z'] = np.array([ 0,  1,  2,  3,
    ...                               4,  5,  6,  7,
    ...                               8,  9, 10, 11])
    >>> map_mean_of_link_nodes_to_link(rmg, 'z')
    array([  0.5,   1.5,   2.5,   2. ,   3. ,   4. ,   5. ,   4.5,   5.5,
             6.5,   6. ,   7. ,   8. ,   9. ,   8.5,   9.5,  10.5])

    >>> values_at_links = rmg.empty(centering='link')
    >>> rtn = map_mean_of_link_nodes_to_link(rmg, 'z', out=values_at_links)
    >>> values_at_links
    array([  0.5,   1.5,   2.5,   2. ,   3. ,   4. ,   5. ,   4.5,   5.5,
             6.5,   6. ,   7. ,   8. ,   9. ,   8.5,   9.5,  10.5])
    >>> rtn is values_at_links
    True
    """
    if out is None:
        out = grid.empty(centering='link')

    values_at_nodes = grid.at_node[var_name]
    out[:] = 0.5 * (values_at_nodes[grid.node_at_link_head] +
                    values_at_nodes[grid.node_at_link_tail])

    return out


def map_value_at_min_node_to_link(grid, control_name, value_name, out=None):
    """
    Map the the value found in one field of nodes to a link, based on the
    minimum value found in a second node field.

    map_value_at_min_node_to_link iterates across the grid and
    identifies the node values at both the "head" and "tail" of a given link.
    This function evaluates the value of 'control_name' at both the "to" and
    "from" node. The value of 'value_name' at the node with the minimum value
    of the two values of 'control_name' is then mapped to the link.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    control_name : str
        Name of field defined at nodes that dictates which end of the link to
        draw values from.
    value_name : str
        Name of field defined at nodes from which values are drawn, based on
        control_name.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_value_at_min_node_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> _ = rmg.add_field('node', 'z',
    ...                   [[0, 1, 2, 3],
    ...                    [7, 6, 5, 4],
    ...                    [8, 9, 10, 11]])
    >>> _ = rmg.add_field('node', 'vals_to_map',
    ...                   [[0, 10, 20, 30],
    ...                    [70, 60, 50, 40],
    ...                    [80, 90, 100, 110]])
    >>> map_value_at_min_node_to_link(rmg, 'z', 'vals_to_map')
    array([   0.,   10.,   20.,    0.,   10.,   20.,   30.,   60.,   50.,
             40.,   70.,   60.,   50.,   40.,   80.,   90.,  100.])
    """
    if out is None:
        out = grid.empty(centering='link')

    controlling_values_at_nodes = grid.at_node[control_name]
    head_control = controlling_values_at_nodes[grid.node_at_link_head]
    tail_control = controlling_values_at_nodes[grid.node_at_link_tail]
    head_vals = grid.at_node[value_name][grid.node_at_link_head]
    tail_vals = grid.at_node[value_name][grid.node_at_link_tail]

    out[:] = np.where(tail_control < head_control, tail_vals, head_vals)
    return out


def map_value_at_max_node_to_link(grid, control_name, value_name, out=None):
    """
    Map the the value found in one field of nodes to a link, based on the
    maximum value found in a second node field.

    map_value_at_max_node_to_link iterates across the grid and
    identifies the node values at both the "head" and "tail" of a given link.
    This function evaluates the value of 'control_name' at both the "to" and
    "from" node. The value of 'value_name' at the node with the maximum value
    of the two values of 'control_name' is then mapped to the link.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    control_name : str
        Name of field defined at nodes that dictates which end of the link to
        draw values from.
    value_name : str
        Name of field defined at nodes from which values are drawn, based on
        control_name.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at links.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_value_at_max_node_to_link
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> _ = rmg.add_field('node', 'z',
    ...                   [[0, 1, 2, 3],
    ...                    [7, 6, 5, 4],
    ...                    [8, 9, 10, 11]])
    >>> _ = rmg.add_field('node', 'vals_to_map',
    ...                   [[0, 10, 20, 30],
    ...                    [70, 60, 50, 40],
    ...                    [80, 90, 100, 110]])
    >>> map_value_at_max_node_to_link(rmg, 'z', 'vals_to_map')
    array([  10.,   20.,   30.,   70.,   60.,   50.,   40.,   70.,   60.,
             50.,   80.,   90.,  100.,  110.,   90.,  100.,  110.])
    """
    if out is None:
        out = grid.empty(centering='link')

    controlling_values_at_nodes = grid.at_node[control_name]
    head_control = controlling_values_at_nodes[grid.node_at_link_head]
    tail_control = controlling_values_at_nodes[grid.node_at_link_tail]
    head_vals = grid.at_node[value_name][grid.node_at_link_head]
    tail_vals = grid.at_node[value_name][grid.node_at_link_tail]

    out[:] = np.where(tail_control > head_control, tail_vals, head_vals)
    return out


def map_node_to_cell(grid, var_name, out=None):
    """Map values for nodes to cells.

    map_node_to_cell iterates across the grid and
    identifies the all node values of 'var_name'.

    This function takes node values of 'var_name' and mapes that value to the
    corresponding cell area for each node.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at nodes.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at cells.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_node_to_cell
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> _ = rmg.add_field('node', 'z', np.arange(12.))
    >>> map_node_to_cell(rmg, 'z')
    array([ 5.,  6.])

    >>> values_at_cells = rmg.empty(centering='cell')
    >>> rtn = map_node_to_cell(rmg, 'z', out=values_at_cells)
    >>> values_at_cells
    array([ 5.,  6.])
    >>> rtn is values_at_cells
    True
    """
    if out is None:
        out = grid.empty(centering='cell')

    values_at_nodes = grid.at_node[var_name]
    out[:] = values_at_nodes[grid.node_at_cell]

    return out


def map_min_of_node_links_to_node(grid, var_name, out=None):
    """Map the minimum value of a nodes' links to the node.

    map_min_of_node_links_to_node iterates across the grid and
    identifies the link values at each link connected to  a node.
    This function finds the minimum value of 'var_name' of each set
    of links, and then maps this value to the node. Note no attempt is made
    to honor the directionality of the links.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_min_of_node_links_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.arange(rmg.number_of_links)
    >>> map_min_of_node_links_to_node(rmg, 'grad')
    array([  0.,   0.,   1.,   2.,
             3.,   4.,   5.,   6.,
            10.,  11.,  12.,  13.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_min_of_node_links_to_node(rmg, 'grad', out=values_at_nodes)
    >>> values_at_nodes
    array([  0.,   0.,   1.,   2.,
             3.,   4.,   5.,   6.,
            10.,  11.,  12.,  13.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_linksX = np.empty(grid.number_of_links+1, dtype=float)
    values_at_linksX[-1] = np.finfo(dtype=float).max
    values_at_linksX[:-1] = grid.at_link[var_name]
    np.amin(values_at_linksX[grid.links_at_node], axis=1, out=out)

    return out


def map_max_of_node_links_to_node(grid, var_name, out=None):
    """Map the maximum value of a nodes' links to the node.

    map_max_of_node_links_to_node iterates across the grid and
    identifies the link values at each link connected to  a node.
    This function finds the maximum value of 'var_name' of each set
    of links, and then maps this value to the node. Note no attempt is made
    to honor the directionality of the links.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_max_of_node_links_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.arange(rmg.number_of_links)
    >>> map_max_of_node_links_to_node(rmg, 'grad')
    array([  3.,   4.,   5.,   6.,
            10.,  11.,  12.,  13.,
            14.,  15.,  16.,  16.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_max_of_node_links_to_node(rmg, 'grad', out=values_at_nodes)
    >>> values_at_nodes
    array([  3.,   4.,   5.,   6.,
            10.,  11.,  12.,  13.,
            14.,  15.,  16.,  16.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_linksX = np.empty(grid.number_of_links+1, dtype=float)
    values_at_linksX[-1] = np.finfo(dtype=float).min
    values_at_linksX[:-1] = grid.at_link[var_name]
    np.amax(values_at_linksX[grid.links_at_node], axis=1, out=out)

    return out


def map_upwind_node_link_max_to_node(grid, var_name, out=None):
    """
    Map the largest magnitude of the links bringing flux into the node to the
    node.

    map_upwind_node_link_max_to_node iterates across the grid and identifies
    the link values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links bringing flux into the
    node, then maps the maximum magnitude of 'var_name' found on these links
    onto the node. If no upwind link is found, the value will be recorded as
    zero.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_upwind_node_link_max_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.])
    >>> map_upwind_node_link_max_to_node(rmg, 'grad')
    array([ 0.,  1.,  2.,  1.,
            0.,  1.,  2.,  1.,
            0.,  1.,  2.,  1.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_upwind_node_link_max_to_node(rmg, 'grad',
    ...                                        out=values_at_nodes)
    >>> values_at_nodes
    array([ 0.,  1.,  2.,  1.,
            0.,  1.,  2.,  1.,
            0.,  1.,  2.,  1.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    np.amax(-values_at_links, axis=1, out=out)

    return out


def map_downwind_node_link_max_to_node(grid, var_name, out=None):
    """
    Map the largest magnitude of the links carrying flux from the node to the
    node.

    map_downwind_node_link_max_to_node iterates across the grid and identifies
    the link values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links carrying flux out of the
    node, then maps the maximum magnitude of 'var_name' found on these links
    onto the node. If no downwind link is found, the value will be recorded as
    zero.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_downwind_node_link_max_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.])
    >>> map_downwind_node_link_max_to_node(rmg, 'grad')
    array([ 1.,  2.,  1.,  0.,
            1.,  2.,  1.,  0.,
            1.,  2.,  1.,  0.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_downwind_node_link_max_to_node(rmg, 'grad',
    ...                                        out=values_at_nodes)
    >>> values_at_nodes
    array([ 1.,  2.,  1.,  0.,
            1.,  2.,  1.,  0.,
            1.,  2.,  1.,  0.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    steepest_links_at_node = np.amax(values_at_links, axis=1)
    np.fabs(steepest_links_at_node, out=out)

    return out


def map_upwind_node_link_mean_to_node(grid, var_name, out=None):
    """
    Map the mean magnitude of the links bringing flux into the node to the
    node.

    map_upwind_node_link_mean_to_node iterates across the grid and identifies
    the link values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links bringing flux into the
    node, then maps the mean magnitude of 'var_name' found on these links
    onto the node. Links with zero values are not included in the means,
    and zeros are returned if no upwind links are found.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_upwind_node_link_mean_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> map_upwind_node_link_mean_to_node(rmg, 'grad')
    array([ 0. ,  1. ,  2. ,  1. ,
            2. ,  2. ,  3. ,  3. ,
            1. ,  1.5,  2.5,  2.5])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_upwind_node_link_mean_to_node(rmg, 'grad',
    ...                                         out=values_at_nodes)
    >>> values_at_nodes
    array([ 0. ,  1. ,  2. ,  1. ,
            2. ,  2. ,  3. ,  3. ,
            1. ,  1.5,  2.5,  2.5])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    vals_in_positive = -values_at_links
    vals_above_zero = vals_in_positive > 0.
    total_vals = np.sum(vals_in_positive*vals_above_zero, axis=1)
    link_count = np.sum(vals_above_zero, axis=1)
    np.divide(total_vals, link_count, out=out)
    out[np.isnan(out)] = 0.

    return out


def map_downwind_node_link_mean_to_node(grid, var_name, out=None):
    """
    Map the mean magnitude of the links carrying flux out of the node to the
    node.

    map_downwind_node_link_mean_to_node iterates across the grid and identifies
    the link values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links carrying flux out of the
    node, then maps the mean magnitude of 'var_name' found on these links
    onto the node. Links with zero values are not included in the means,
    and zeros are returned if no upwind links are found.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_downwind_node_link_mean_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> map_downwind_node_link_mean_to_node(rmg, 'grad')
    array([ 1.5,  2.5,  2.5,  5. ,
            1. ,  2. ,  2. ,  4. ,
            1. ,  2. ,  1. ,  0. ])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_downwind_node_link_mean_to_node(rmg, 'grad',
    ...                                         out=values_at_nodes)
    >>> values_at_nodes
    array([ 1.5,  2.5,  2.5,  5. ,
            1. ,  2. ,  2. ,  4. ,
            1. ,  2. ,  1. ,  0. ])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    vals_in_positive = values_at_links
    vals_above_zero = vals_in_positive > 0.
    total_vals = np.sum(vals_in_positive*vals_above_zero, axis=1)
    link_count = np.sum(vals_above_zero, axis=1)
    np.divide(total_vals, link_count, out=out)
    out[np.isnan(out)] = 0.

    return out


def map_value_at_upwind_node_link_max_to_node(grid, control_name,
                                              value_name, out=None):
    """
    Map the the value found in one field of links to a node, based on the
    largest magnitude value of links bringing fluxes into the node,
    found in a second node field.

    map_upwind_node_link_max_to_node iterates across the grid and identifies
    the link control_values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links bringing flux into the
    node, then identifies the link with the maximum magnitude. The value of the
    second field 'value_name' at these links is then mapped onto the node.
    If no upwind link is found, the value will be recorded as zero.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    control_name : str
        Name of field defined at nodes that dictates which end of the link to
        draw values from.
    value_name : str
        Name of field defined at nodes from which values are drawn, based on
        control_name.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_value_at_upwind_node_link_max_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.])
    >>> rmg.at_link['vals'] = np.arange(rmg.number_of_links, dtype=float)
    >>> map_value_at_upwind_node_link_max_to_node(rmg, 'grad', 'vals')
    array([  0.,   0.,   1.,   2.,
             0.,   7.,   8.,   9.,
             0.,  14.,  15.,  16.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_value_at_upwind_node_link_max_to_node(rmg, 'grad', 'vals',
    ...                                                 out=values_at_nodes)
    >>> values_at_nodes
    array([  0.,   0.,   1.,   2.,
             0.,   7.,   8.,   9.,
             0.,  14.,  15.,  16.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_nodes = (grid.at_link[control_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    which_link = np.argmax(-values_at_nodes, axis=1)
    invalid_links = values_at_nodes >= 0.
    link_vals_without_invalids = grid.at_link[value_name][grid.links_at_node]
    link_vals_without_invalids[invalid_links] = 0.
    out[:] = link_vals_without_invalids[np.arange(grid.number_of_nodes),
                                        which_link]

    return out


def map_value_at_downwind_node_link_max_to_node(grid, control_name,
                                                value_name, out=None):
    """
    Map the the value found in one field of links to a node, based on the
    largest magnitude value of links carrying fluxes out of the node,
    found in a second node field.

    map_downwind_node_link_max_to_node iterates across the grid and identifies
    the link control_values at each link connected to a node. It then uses the
    link_dirs_at_node data structure to identify links carrying flux out of the
    node, then identifies the link with the maximum magnitude. The value of the
    second field 'value_name' at these links is then mapped onto the node.
    If no downwind link is found, the value will be recorded as zero.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    control_name : str
        Name of field defined at nodes that dictates which end of the link to
        draw values from.
    value_name : str
        Name of field defined at nodes from which values are drawn, based on
        control_name.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.

    Returns
    -------
    ndarray
        Mapped values at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import map_value_at_downwind_node_link_max_to_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.,
    ...                                  0.,  0.,  0.,  0.,
    ...                                 -1., -2., -1.])
    >>> rmg.at_link['vals'] = np.arange(rmg.number_of_links, dtype=float)
    >>> map_value_at_downwind_node_link_max_to_node(rmg, 'grad', 'vals')
    array([  0.,   1.,   2.,   0.,
             7.,   8.,   9.,   0.,
            14.,  15.,  16.,   0.])

    >>> values_at_nodes = rmg.add_empty('node', 'z')
    >>> rtn = map_value_at_downwind_node_link_max_to_node(rmg, 'grad', 'vals',
    ...                                                   out=values_at_nodes)
    >>> values_at_nodes
    array([  0.,   1.,   2.,   0.,
             7.,   8.,   9.,   0.,
            14.,  15.,  16.,   0.])
    >>> rtn is values_at_nodes
    True
    """
    if out is None:
        out = grid.empty(centering='node')

    values_at_nodes = (grid.at_link[control_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    which_link = np.argmax(values_at_nodes, axis=1)
    invalid_links = values_at_nodes <= 0.
    link_vals_without_invalids = grid.at_link[value_name][grid.links_at_node]
    link_vals_without_invalids[invalid_links] = 0.
    out[:] = link_vals_without_invalids[np.arange(grid.number_of_nodes),
                                        which_link]

    return out


def link_at_node_is_upwind(grid, var_name, out=None):
    """
    Return a boolean the same shape as :func:`links_at_node` which flags
    links which are upwind of the node as True.

    link_at_node_is_upwind iterates across the grid and identifies the link
    values at each link connected to a node. It then uses the link_dirs_at_node
    data structure to identify links bringing flux into the node. It then
    return a boolean array the same shape as links_at_node flagging these
    links. e.g., for a raster, the returned array will be shape (nnodes, 4).

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.
        Must be correct shape and boolean dtype.

    Returns
    -------
    ndarray
        Boolean of which links are upwind at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import link_at_node_is_upwind
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> link_at_node_is_upwind(rmg, 'grad')
    array([[False, False, False, False],
           [False, False,  True, False],
           [False, False,  True, False],
           [False, False,  True, False],
           [False, False, False,  True],
           [False, False,  True,  True],
           [False, False,  True,  True],
           [False, False,  True,  True],
           [False, False, False,  True],
           [False, False,  True,  True],
           [False, False,  True,  True],
           [False, False,  True,  True]], dtype=bool)
    """
    if out is None:
        out = np.empty_like(grid.links_at_node, dtype=bool)
    else:
        assert out.shape is grid.links_at_node.shape
        assert out.dtype is bool

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    np.less(values_at_links, 0., out=out)

    return out


def link_at_node_is_downwind(grid, var_name, out=None):
    """
    Return a boolean the same shape as :func:`links_at_node` which flags
    links which are downwind of the node as True.

    link_at_node_is_downwind iterates across the grid and identifies the link
    values at each link connected to a node. It then uses the link_dirs_at_node
    data structure to identify links carrying flux out of the node. It then
    return a boolean array the same shape as links_at_node flagging these
    links. e.g., for a raster, the returned array will be shape (nnodes, 4).

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.
    out : ndarray, optional
        Buffer to place mapped values into or `None` to create a new array.
        Must be correct shape and boolean dtype.

    Returns
    -------
    ndarray
        Boolean of which links are downwind at nodes.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import link_at_node_is_downwind
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> link_at_node_is_downwind(rmg, 'grad')
    array([[ True,  True, False, False],
           [ True,  True, False, False],
           [ True,  True, False, False],
           [False,  True, False, False],
           [ True,  True, False, False],
           [ True,  True, False, False],
           [ True,  True, False, False],
           [False,  True, False, False],
           [ True, False, False, False],
           [ True, False, False, False],
           [ True, False, False, False],
           [False, False, False, False]], dtype=bool)
    """
    if out is None:
        out = np.empty_like(grid.links_at_node, dtype=bool)
    else:
        assert out.shape is grid.links_at_node.shape
        assert out.dtype is bool

    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    np.greater(values_at_links, 0., out=out)

    return out


def upwind_links_at_node(grid, var_name, bad_index=-1):
    """
    Return an (nnodes, X) shape array of link IDs of which links are upwind
    of each node, according to the field 'var_name'.

    X is the maximum upwind links at any node. Nodes with fewer upwind links
    than this have additional slots filled with *bad_index*. Links are ordered
    anticlockwise from east.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.

    Returns
    -------
    ndarray
        Array of upwind link IDs

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import upwind_links_at_node
    >>> from landlab import RasterModelGrid

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> upwind_links_at_node(rmg, 'grad', bad_index=-1)
    array([[-1, -1],
           [ 0, -1],
           [ 1, -1],
           [ 2, -1],
           [ 3, -1],
           [ 7,  4],
           [ 8,  5],
           [ 9,  6],
           [10, -1],
           [14, 11],
           [15, 12],
           [16, 13]])
    """
    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    unordered_IDs = np.where(values_at_links < 0., grid.links_at_node,
                             bad_index)
    bad_IDs = unordered_IDs == bad_index
    nnodes = grid.number_of_nodes
    flat_sorter = (np.argsort(bad_IDs, axis=1) + grid.links_at_node.shape[1] *
                   np.arange(nnodes).reshape((nnodes, 1)))
    big_ordered_array = unordered_IDs.ravel()[flat_sorter].reshape(
                            grid.links_at_node.shape)
    cols_to_cut = int(bad_IDs.sum(axis=1).min())

    return big_ordered_array[:, :-cols_to_cut]


def downwind_links_at_node(grid, var_name, bad_index=-1):
    """
    Return an (nnodes, X) shape array of link IDs of which links are downwind
    of each node, according to the field 'var_name'.

    X is the maximum downwind links at any node. Nodes with fewer downwind
    links than this have additional slots filled with *bad_index*. Links are
    ordered anticlockwise from east.

    Parameters
    ----------
    grid : ModelGrid
        A landlab ModelGrid.
    var_name : str
        Name of variable field defined at links.

    Returns
    -------
    ndarray
        Array of upwind link IDs

    Examples
    --------
    >>> import numpy as np
    >>> from landlab.grid.mappers import downwind_links_at_node
    >>> from landlab import RasterModelGrid, BAD_INDEX_VALUE

    >>> rmg = RasterModelGrid((3, 4))
    >>> rmg.at_link['grad'] = np.array([-1., -2., -1.,
    ...                                 -2., -3., -4., -5.,
    ...                                 -1., -2., -1.,
    ...                                 -1., -2., -3., -4.,
    ...                                 -1., -2., -1.])
    >>> downwind_links_at_node(rmg, 'grad', bad_index=BAD_INDEX_VALUE)
    array([[         0,          3],
           [         1,          4],
           [         2,          5],
           [         6, 2147483647],
           [         7,         10],
           [         8,         11],
           [         9,         12],
           [        13, 2147483647],
           [        14, 2147483647],
           [        15, 2147483647],
           [        16, 2147483647],
           [2147483647, 2147483647]])
    """
    values_at_links = (grid.at_link[var_name][grid.links_at_node] *
                       grid.link_dirs_at_node)
    # this procedure makes incoming links NEGATIVE
    unordered_IDs = np.where(values_at_links > 0., grid.links_at_node,
                             bad_index)
    bad_IDs = unordered_IDs == bad_index
    nnodes = grid.number_of_nodes
    flat_sorter = (np.argsort(bad_IDs, axis=1) + grid.links_at_node.shape[1] *
                   np.arange(nnodes).reshape((nnodes, 1)))
    big_ordered_array = unordered_IDs.ravel()[flat_sorter].reshape(
                            grid.links_at_node.shape)
    cols_to_cut = int(bad_IDs.sum(axis=1).min())

    return big_ordered_array[:, :-cols_to_cut]
