#! /usr/env/python
from __future__ import print_function

import warnings

import numpy as np
from six.moves import range

from landlab import Component, FieldError
from landlab.core.model_parameter_dictionary import MissingKeyError
from landlab.grid.base import BAD_INDEX_VALUE
from landlab.utils.decorators import make_return_array_immutable

from .cfuncs import (sed_flux_fn_gen_genhump, sed_flux_fn_gen_lindecl,
                     sed_flux_fn_gen_almostparabolic, sed_flux_fn_gen_const,
                     iterate_sde_downstream)

WAVE_STABILITY_PREFACTOR = 0.2

# NB: The inline documentation of this component freely (& incorrectly!)
# interchanges "flux" and "discharge". Almost always, "discharge" is intended
# in place of "flux", including in variable names.

# NB: Stability problems persist when m_sp>0.5 & m_t>1.5. Presumably this is
# a problem with the derivation of the stability.
# NB: ALSO, there are odd outcomes when m_sp != m_t-1. Analysis shows that the
# steady state form should converge on the TL st st form, but it does not -
# abnormally flat profiles seem to result.




# Note: DOES SHEAR STRESS GET UPDATED?????
# Think about NotImplementedErrors for other things




class SedDepEroder(Component):
    """
    This module implements sediment flux dependent channel incision
    following::

        E = f(Qs, Qc) * [a stream power-like term],

    where E is the bed erosion rate, Qs is the volumetric sediment discharge
    into a node, and Qc is the volumetric sediment transport capacity (as a
    discharge) at that node.

    The details of the implementation are a function of the two key
    arguments, *sed_dependency_type* and *Qc*. The former controls the
    shape of the sediment dependent response function f(Qs, Qc), the
    latter controls the way in which sediment transport capacities are
    calculated.

    For Qc, 'power_law' broadly follows the assumptions in Gasparini et
    al. 2006, 2007. Note however that these equations in this instance
    calculate DISCHARGE, not the more common FLUX, since resolving fluxes on
    grid diagonals is nontrivial in Landlab but necessary for this
    implementation. At the present time, only 'power_law' is permitted as a
    parameter for Qc, but it is anticipated that in the future other
    formulations will be implemented.

    If ``Qc == 'power_law'``::

        E  = K_sp * f(Qs, Qc) * A ** m_sp * S ** n_sp;
        Qc = K_t * A ** m_t * S ** n_t

    where Qs is volumetric sediment discharge, Qc is volumetric sediment
    discharge capacity, A is upstream drainage area, S is local topographic
    slope, m_sp, n_sp, m_t, and n_t are constants, and K_sp and K_t are
    (spatially constant) prefactors.

    The component uses the field channel_sediment__depth as the record of the
    sediment on the bed at any given time. This may be set and/or freely
    modified by the user, but will be created by the component if not found.
    However, under some conditions, modification of this field "manually" may
    induce model instability, i.e., the component is not unconditionally
    stable.
    Tools-driven bedrock erosion is permitted only when this layer thickness
    is reduced to zero. The sediment recorded in channel_sediment__depth is
    considered loose, and freely transportable by clearwater flow.
    Note that the topography tracked by 'topographic__elevation' is the true
    surface topography, not the bedrock topography (...as is consistent with
    that field name). The bedrock topography can be found from the
    topographic__elevation less the channel_sediment__depth.

    The component is able to handle flooded nodes, if created by a lake
    filler. It assumes the flow paths found in the fields already reflect
    any lake routing operations, and then requires the optional argument
    *flooded_nodes* be passed to the run method. A flooded depression
    acts as a perfect sediment trap, and will be filled sequentially
    from the inflow points towards the outflow points.

    Examples
    --------
    >>> from six.moves import range
    >>> import numpy as np
    >>> from landlab import RasterModelGrid, CLOSED_BOUNDARY
    >>> from landlab.components import FlowAccumulator, SedDepEroder

    >>> mg = RasterModelGrid((10, 3), 200.)
    >>> for edge in (mg.nodes_at_left_edge, mg.nodes_at_top_edge,
    ...              mg.nodes_at_right_edge):
    ...     mg.status_at_node[edge] = CLOSED_BOUNDARY

    >>> z = mg.add_zeros('node', 'topographic__elevation')
    >>> th = mg.add_zeros('node', 'channel_sediment__depth')
    >>> th += 0.0007

    >>> fr = FlowAccumulator(mg, flow_director='D8')
    >>> sde = SedDepEroder(mg, K_sp=1.e-4,
    ...                    sed_dependency_type='almost_parabolic',
    ...                    Qc='power_law', K_t=1.e-4)

    >>> z[:] = mg.node_y/10000.

    >>> initz = z.copy()

    >>> dt = 100.
    >>> up = 0.05

    >>> for i in range(1):
    ...     fr.run_one_step()
    ...     sde.run_one_step(dt)

    Where TL conditions predominate, the incision is linked only to movement
    of the sediment layer:

    >>> TLs = mg.core_nodes[sde.is_it_TL[mg.core_nodes]]
    >>> np.allclose(th[TLs] + (initz - z)[TLs], 0.0007)
    True

    Otherwise, incision procedes in the naked nodes according to the sediment
    dependent bedrock incision rules:

    >>> incising_nodes = mg.core_nodes[
    ...     np.logical_not(sde.is_it_TL)[mg.core_nodes]]
    >>> np.all((initz - z)[incising_nodes] > 0.0007)
    True

    The component will dump all sediment in transit if it encounters flooded
    nodes:

    >>> from landlab.components import DepressionFinderAndRouter
    >>> mg.at_node.clear()
    >>> z = mg.add_zeros('node', 'topographic__elevation')
    >>> th = mg.add_zeros('node', 'channel_sediment__depth')
    >>> z[:] = mg.node_y/10000.
    >>> fr = FlowAccumulator(mg, flow_director='D8')
    >>> sde = SedDepEroder(mg, K_sp=1.e-5,
    ...                    sed_dependency_type='generalized_humped',
    ...                    Qc='power_law', K_t=1.e-5)
    >>> myflood = mg.zeros('node', dtype=bool)
    >>> myflood[mg.node_y < 500.] = True  # 1st 3 nodes are flooded
    >>> for i in range(1):
    ...     fr.run_one_step()
    ...     sde.run_one_step(100., flooded_nodes=myflood)
    >>> z[7] > mg.node_y[7]/10000.  # sed ends up here
    True
    >>> np.isclose(z[4], mg.node_y[4]/10000.)  # ...but not here
    True

    Pleasingly, the solution for a constant f(Qs) is very close to the stream
    power solution:

    >>> from landlab.components import FastscapeEroder
    >>> mg = RasterModelGrid((10, 3), 200.)
    >>> for edge in (mg.nodes_at_left_edge, mg.nodes_at_top_edge,
    ...              mg.nodes_at_right_edge):
    ...     mg.status_at_node[edge] = CLOSED_BOUNDARY

    >>> z = mg.add_zeros('node', 'topographic__elevation')

    >>> fr = FlowAccumulator(mg, flow_director='D8')
    >>> sde = SedDepEroder(mg, K_sp=1.e-4,
    ...                    sed_dependency_type='None',
    ...                    Qc='power_law', K_t=1.e-4)

    >>> z[:] = mg.node_y/10000.

    >>> dt = 100.
    >>> up = 0.01

    >>> for i in range(50):
    ...     z[mg.core_nodes] += up * dt
    ...     fr.run_one_step()
    ...     sde.run_one_step(dt)

    >>> z_sde = z.copy()

    >>> fsc = FastscapeEroder(mg, K_sp=1.e-4)

    >>> z[:] = mg.node_y/10000.

    >>> for i in range(50):
    ...     z[mg.core_nodes] += up * dt
    ...     fr.run_one_step()
    ...     fsc.run_one_step(dt)

    The difference is less that 3 per cent at maximum:

    >>> ((z.reshape((10, 3))[1:-1, 1] -
    ...   z_sde.reshape((10, 3))[1:-1, 1])/(
    ...       z.reshape((10, 3))[1:-1, 1])).max() < 0.03
    True

    A visual comparison of these solutions will confirm this closeness.
    """

    _name = "SedDepEroder"

    _input_var_names = (
        "topographic__elevation",
        "drainage_area",
        "flow__receiver_node",
        "flow__upstream_node_order",
        "topographic__steepest_slope",
        "flow__link_to_receiver_node",
        "flow__sink_flag",
        "channel_sediment__depth",
    )

    _output_var_names = (
        "topographic__elevation",
        "channel__bed_shear_stress",
        "channel_sediment__volumetric_transport_capacity",
        "channel_sediment__volumetric_discharge",
        "channel_sediment__relative_flux",
        "channel__discharge",
    )

    _optional_var_names = ("channel__width", "channel__depth")

    _var_units = {
        "topographic__elevation": "m",
        "drainage_area": "m**2",
        "flow__receiver_node": "-",
        "topographic__steepest_slope": "-",
        "flow__upstream_node_order": "-",
        "flow__link_to_receiver_node": "-",
        "flow__sink_flag": "-",
        "channel_sediment__depth": "m",
        "channel__bed_shear_stress": "Pa",
        "channel_sediment__volumetric_transport_capacity": "m**3/s",
        "channel_sediment__volumetric_discharge": "m**3/s",
        "channel_sediment__relative_flux": "-",
        "channel__discharge": "m**3/s",
    }

    _var_mapping = {
        "topographic__elevation": "node",
        "drainage_area": "node",
        "flow__receiver_node": "node",
        "topographic__steepest_slope": "node",
        "flow__upstream_node_order": "node",
        "flow__link_to_receiver_node": "node",
        "flow__sink_flag": "node",
        "channel_sediment__depth": "node",
        "channel__bed_shear_stress": "node",
        "channel_sediment__volumetric_transport_capacity": "node",
        "channel_sediment__volumetric_discharge": "node",
        "channel_sediment__relative_flux": "node",
        "channel__discharge": "node",
    }

    _var_type = {
        "topographic__elevation": float,
        "drainage_area": float,
        "flow__receiver_node": int,
        "topographic__steepest_slope": float,
        "flow__upstream_node_order": int,
        "flow__link_to_receiver_node": int,
        "flow__sink_flag": bool,
        "channel_sediment__depth": float,
        "channel__bed_shear_stress": float,
        "channel_sediment__volumetric_transport_capacity": float,
        "channel_sediment__volumetric_discharge": float,
        "channel_sediment__relative_flux": float,
        "channel__discharge": float,
    }

    _var_doc = {
        "topographic__elevation": "Land surface topographic elevation",
        "drainage_area": (
            "Upstream accumulated surface area contributing to the node's " +
            "discharge"
        ),
        "flow__receiver_node": (
            "Node array of receivers (node that receives flow from current " +
            "node)"
        ),
        "topographic__steepest_slope": (
            "Node array of steepest *downhill* slopes"
        ),
        "flow__upstream_node_order": (
            "Node array containing downstream-to-upstream ordered list of " +
            "node IDs"
        ),
        "flow__link_to_receiver_node": ("ID of link downstream of each " +
            "node, which carries the discharge"
        ),
        "flow__sink_flag": "Boolean array, True at local lows",
        "channel_sediment__depth": (
            "Loose fluvial sediment at each node. Can be " +
            "freely entrained by the flow, and must be to permit erosion. " +
            "Note that the sediment is assumed to be distributed across the" +
            " whole cell area."
        ),
        "channel__bed_shear_stress": (
            "Shear exerted on the bed of the channel, assuming all "
            + "discharge travels along a single, self-formed channel"
        ),
        "channel_sediment__volumetric_transport_capacity": (
            "Volumetric transport capacity of a channel carrying all runoff"
            + " through the node, assuming the Meyer-Peter Muller transport "
            + "equation"
        ),
        "channel_sediment__volumetric_discharge": (
            "Total volumetric fluvial sediment flux brought into the node "
            + "from upstream"
        ),
        "channel_sediment__relative_flux": (
            "The channel_sediment__volumetric_discharge divided by the " +
            "channel_sediment__volumetric_transport_capacity"
        ),
        "channel__discharge": (
            "Volumetric water flux of the a single channel carrying all "
            + "runoff through the node"
        ),
    }

    def __init__(
        self,
        grid,
        K_sp=1.e-6,
        g=9.81,
        rock_density=2700.,
        sediment_density=2700.,
        fluid_density=1000.,
        runoff_rate=1.,
        sed_dependency_type="generalized_humped",
        kappa_hump=13.683,
        nu_hump=1.13,
        phi_hump=4.24,
        c_hump=0.00181,
        Qc="power_law",
        m_sp=0.5,
        n_sp=1.,
        K_t=1.e-4,
        m_t=1.5,
        n_t=1.,
        # params for model numeric behavior:
        pseudoimplicit_repeats=50,
        **kwds
    ):
        """Constructor for the class.

        Parameters
        ----------
        grid : a ModelGrid
            A grid.
        K_sp : float (time unit must be *years*)
            K in the stream power equation; the prefactor on the erosion
            equation (units vary with other parameters).
        g : float (m/s**2)
            Acceleration due to gravity.
        rock_density : float (Kg m**-3)
            Bulk intact rock density.
        sediment_density : float (Kg m**-3)
            Typical density of loose sediment on the bed.
        fluid_density : float (Kg m**-3)
            Density of the fluid. Currently redundant, but will become
            necessary in a future version using e.g. MPM for the transport
            law.
        runoff_rate : float, array or field name (m/s)
            The rate of excess overland flow production at each node (i.e.,
            rainfall rate less infiltration).
        pseudoimplicit_repeats : int
            Maximum number of loops to perform with the pseudoimplicit
            iterator, seeking a stable solution. Convergence is typically
            rapid. The component counts the total number of times it "maxed
            out" the loop to seek a stable solution (error in sed flux fn <1%)
            with the internal variable "_pseudoimplicit_aborts".
        sed_dependency_type : {'generalized_humped', 'None', 'linear_decline',
                               'almost_parabolic'}
            The shape of the sediment flux function. For definitions, see
            Hobley et al., 2011. 'None' gives a constant value of 1.
            NB: 'parabolic' is currently not supported, due to numerical
            stability issues at channel heads.
        Qc : {'power_law', }
            At present, only `power_law` is supported.

        If ``sed_dependency_type == 'generalized_humped'``...

        kappa_hump : float
            Shape parameter for sediment flux function. Primarily controls
            function amplitude (i.e., scales the function to a maximum of 1).
            Default follows Leh valley values from Hobley et al., 2011.
        nu_hump : float
            Shape parameter for sediment flux function. Primarily controls
            rate of rise of the "tools" limb. Default follows Leh valley
            values from Hobley et al., 2011.
        phi_hump : float
            Shape parameter for sediment flux function. Primarily controls
            rate of fall of the "cover" limb. Default follows Leh valley
            values from Hobley et al., 2011.
        c_hump : float
            Shape parameter for sediment flux function. Primarily controls
            degree of function asymmetry. Default follows Leh valley values
            from Hobley et al., 2011.

        If ``Qc == 'power_law'``...

        m_sp : float
            Power on drainage area in the erosion equation.
        n_sp : float
            Power on slope in the erosion equation.
        K_t : float (time unit must be in *years*)
            Prefactor in the transport capacity equation.
        m_t : float
            Power on drainage area in the transport capacity equation.
        n_t : float
            Power on slope in the transport capacity equation.
        """
        if "flow__receiver_node" in grid.at_node:
            if grid.at_node["flow__receiver_node"].size != grid.size("node"):
                msg = (
                    "A route-to-multiple flow director has been "
                    "run on this grid. The landlab development team has not "
                    "verified that SedDepEroder is compatible with "
                    "route-to-multiple methods. Please open a GitHub Issue "
                    "to start this process."
                )
                raise NotImplementedError(msg)
        self._grid = grid
        self._pseudoimplicit_repeats = pseudoimplicit_repeats

        self._K_unit_time = K_sp / 31557600.
        # ^...because we work with dt in seconds
        # set gravity
        self._g = g
        self._rock_density = rock_density
        self._sed_density = sediment_density
        # self._fluid_density = fluid_density
        # at present this is redundant, but this is retained in comments
        # pending future code enhancement.
        # self._relative_weight = (
        #     (self._sed_density - self._fluid_density) /
        #     self._fluid_density * self.g
        # )
        # self.rho_g = self._fluid_density * self.g
        # ^to accelerate MPM calcs
        self._porosity = self._sed_density / self._rock_density
        self.type = sed_dependency_type
        assert self.type in (
            'generalized_humped',
            'None',
            'linear_decline',
            'almost_parabolic',
        )
        # now conditional inputs
        if self.type == 'generalized_humped':
            self.kappa = kappa_hump
            self.nu = nu_hump
            self.phi = phi_hump
            self.c = c_hump
            self.norm = None
        else:
            self.kappa = 0.
            self.nu = 0.
            self.phi = 0.
            self.c = 0.
            self.norm = 0.
        # set the sed flux fn for later on:
        self.set_sed_flux_fn_gen()

        self.Qc = Qc
        if type(runoff_rate) in (float, int):
            self.runoff_rate = float(runoff_rate)
        elif type(runoff_rate) is str:
            self.runoff_rate = self.grid.at_node[runoff_rate]
        else:
            self.runoff_rate = np.array(runoff_rate)
            assert runoff_rate.size == self.grid.number_of_nodes

        if self.Qc == 'MPM':
            raise NameError('MPM is no longer a permitted value for Qc!')
        elif self.Qc == 'power_law':
            self._m = m_sp
            self._n = n_sp
            self._Kt = K_t / 31557600.  # in sec
            self._mt = m_t
            self._nt = n_t
        elif self.Qc == 'Voller_generalized':
            raise NameError('Voller_generalized not yet supported!')
            # self._m = m_sp
            # self._n = n_sp
            # self._Kt = K_t/31557600.  # in sec
            # self._mt = m_t
            # self._nt = n_t
            # self._bt = b_t
            # self._Scrit = S_crit
        else:
            msg = (
                "Supplied transport law form, Qc, not recognised. Use " +
                "Qc='power_law'."
            )
            raise NameError(msg)

        self._hillslope_sediment_flux_wzeros = self.grid.zeros('node',
                                                               dtype=float)
        try:
            self._hillslope_sediment = self.grid.at_node[
                'channel_sediment__depth']  # a field was present
        except FieldError:
            self._hillslope_sediment = self.grid.add_zeros(
                'node', 'channel_sediment__depth')

        self.cell_areas = np.empty(grid.number_of_nodes)
        self.cell_areas.fill(np.mean(grid.area_of_cell))
        self.cell_areas[grid.node_at_cell] = grid.area_of_cell
        self._pseudoimplicit_aborts = 0
        self._total_DL_calls = 0
        self._error_at_abort = []

        # set up the necessary fields:
        self.initialize_output_fields()

    def set_sed_flux_fn_gen(self):
        """
        Sets the property self._sed_flux_fn_gen that controls which sed flux
        function to use elsewhere in the component.
        """
        if self.type == 'generalized_humped':
            # work out the normalization param:
            max_val = 0.
            for i in np.arange(0., 1.001, 0.001):
                # ...1.001 as fn is defined at 1.
                sff = sed_flux_fn_gen_genhump(
                    i, self.kappa, self.nu, self.c, self.phi, 1.)
                max_val = max((sff, max_val))
            self.norm = 1./max_val
            self._sed_flux_fn_gen = sed_flux_fn_gen_genhump
        elif self.type == 'None':
            self._sed_flux_fn_gen = sed_flux_fn_gen_const
        elif self.type == 'linear_decline':
            self._sed_flux_fn_gen = sed_flux_fn_gen_lindecl
        elif self.type == 'almost_parabolic':
            self._sed_flux_fn_gen = sed_flux_fn_gen_almostparabolic

    def erode(self, dt, flooded_nodes=None, **kwds):
        """Erode and deposit on the channel bed for a duration of *dt*.

        Erosion occurs according to the sediment dependent rules specified
        during initialization.

        Parameters
        ----------
        dt : float (years, only!)
            Timestep for which to run the component.
        flooded_nodes : ndarray, field name, or None
            If an array, either the IDs of nodes that are flooded and should
            have no erosion, or an nnodes boolean array of flooded nodes.
            If a field name, a boolean field at nodes of flooded nodes. If not
            provided but flow has still been routed across depressions, erosion
            and deposition may still occur beneath the apparent water level.
        """
        if (
            self._grid.at_node["flow__receiver_node"].size !=
            self._grid.size("node")
        ):
            msg = (
                "A route-to-multiple flow director has been "
                "run on this grid. The landlab development team has not "
                "verified that SedDepEroder is compatible with "
                "route-to-multiple methods. Please open a GitHub Issue "
                "to start this process."
            )
            raise NotImplementedError(msg)
        grid = self.grid
        node_z = grid.at_node['topographic__elevation']
        node_A = grid.at_node['drainage_area']
        flow_receiver = grid.at_node['flow__receiver_node']
        s_in = grid.at_node['flow__upstream_node_order']
        node_S = grid.at_node['topographic__steepest_slope']
        elev_less_sed = node_z - self._hillslope_sediment

        dt_secs = dt * 31557600.

        if type(flooded_nodes) is str:
            flooded_nodes = self.grid.at_node[flooded_nodes]
            is_flooded = flooded_nodes
        elif type(flooded_nodes) is np.ndarray:
            assert (flooded_nodes.size == self.grid.number_of_nodes or
                    flooded_nodes.dtype == np.integer)
            is_flooded = flooded_nodes
            # need an *updateable* record of the pit depths
        else:
            # if None, handle in loop
            is_flooded = np.array([], dtype=bool)
        steepest_link = 'flow__link_to_receiver_node'
        link_length = np.empty(grid.number_of_nodes, dtype=float)
        link_length.fill(np.nan)
        draining_nodes = np.not_equal(
            grid.at_node[steepest_link], BAD_INDEX_VALUE
        )
        core_draining_nodes = np.intersect1d(
            np.where(draining_nodes)[0], grid.core_nodes, assume_unique=True
        )
        link_length[core_draining_nodes] = grid.length_of_d8[
            grid.at_node[steepest_link][core_draining_nodes]
        ]

        # calc fluxes from hillslopes into each node:
        # we're going to budget the sediment coming IN as part of the fluvial
        # budget, on the basis this flux will be higher than the out-flux in
        # a convergent flow node
        # ...worst that can happen is that the river can't move it, and dumps
        # it in the first node
        # Take care to add this sed to the cover, but not to actually move it.
        # turn depth into a supply flux:
        sed_in_cells = self._hillslope_sediment[self.grid.node_at_cell]
        flux_in_cells = sed_in_cells * self.grid.area_of_cell / dt_secs
        self._hillslope_sediment_flux_wzeros[
            self.grid.node_at_cell] = flux_in_cells
        self._voldroprate = self.grid.zeros('node', dtype=float)
        self._hillslope_sediment.fill(0.)
        # ^ this will get refilled below. For now, the sed has been "fully
        # mobilised" off the bed; at the end of the step it can resettle.

        if self.Qc == 'power_law':
            transport_capacity_prefactor_withA = self._Kt * node_A ** self._mt
            erosion_prefactor_withA = self._K_unit_time * node_A ** self._m
            # ^doesn't include S**n*f(Qc/Qc)
            downward_slopes = node_S.clip(np.spacing(0.))
            # for the stability condition:
            if np.isclose(self._n, 1.):
                wave_stab_cond_denominator = erosion_prefactor_withA
            else:
                wave_stab_cond_denominator = (
                    erosion_prefactor_withA * downward_slopes**(self._n - 1.))
                # this is a bit cheeky; we're basically assuming the slope
                # won't change much as the tstep evolves
                # justifiable as the -1 suppresses the sensitivity to S
                # small n will be problematic: the machine precision calc
                # ensures it won't crash, but it's not going to be right
                # for now, we're going to be conservative and just exclude the
                # role of the value of the sed flux fn in modifying the calc;
                # i.e., we assume f(Qs,Qc) = 1 in the stability calc.

            max_tstep_wave = WAVE_STABILITY_PREFACTOR * np.nanmin(
                link_length / wave_stab_cond_denominator
            )
            # ^adding additional scaling per CHILD; CHILD uses 0.2
            # This should now be redundant, as we're using machine precision
            # if np.isclose(self._n, 0.):
            #     # janky special condition to enable code to still run for the
            #     # limiting case of n_sp == 0 -> this throws the stability cond
            #     # entirely onto the diffusive aspect, so be very careful!!
            #     max_tstep_wave = 100000000000.
            self.wave_denom = wave_stab_cond_denominator
            self.link_length = link_length
            self.max_tstep_wave = max_tstep_wave

            t_elapsed_internal = 0.
            break_flag = False
            rel_sed_flux = np.empty_like(node_A)

            dzbydt = np.zeros(grid.number_of_nodes, dtype=float)
            self._loopcounter = 0
            while 1:
                flood_node = None  # int if timestep is limited by flooding
                conv_factor = 0.3
                flood_tstep = dt_secs
                slopes_tothen = downward_slopes**self._n
                slopes_tothen[is_flooded] = 0.
                slopes_tothent = downward_slopes**self._nt
                slopes_tothent[is_flooded] = 0.
                transport_capacities = (
                    transport_capacity_prefactor_withA * slopes_tothent
                )
                erosion_prefactor_withS = (
                    erosion_prefactor_withA * slopes_tothen
                )  # no time, no fqs

                river_volume_flux_into_node = np.zeros(grid.number_of_nodes,
                                                       dtype=float)
                dzbydt.fill(0.)
                cell_areas = self.cell_areas

                self._is_it_TL = np.zeros(
                    self.grid.number_of_nodes, dtype=np.int8)

                iterate_sde_downstream(s_in, cell_areas,
                                       self._hillslope_sediment_flux_wzeros,
                                       self._porosity,
                                       river_volume_flux_into_node,
                                       transport_capacities,
                                       erosion_prefactor_withS,
                                       rel_sed_flux, self._is_it_TL,
                                       self._voldroprate, flow_receiver,
                                       self._pseudoimplicit_repeats,
                                       dzbydt, self._sed_flux_fn_gen,
                                       self.kappa, self.nu, self.c,
                                       self.phi, self.norm)

                # now perform a CHILD-like convergence-based stability test:
                ratediff = dzbydt[flow_receiver] - dzbydt
                # if this is +ve, the nodes are converging
                downstr_vert_diff = node_z - node_z[flow_receiver]
                # ^+ve when dstr is lower
                botharepositive = np.logical_and(ratediff > 0.,
                                                 downstr_vert_diff > 0.)
                try:
                    t_to_converge = np.amin(
                        downstr_vert_diff[botharepositive] /
                        ratediff[botharepositive])
                except ValueError:  # no node pair converges
                    t_to_converge = dt_secs
                t_to_converge *= conv_factor
                # ^arbitrary safety factor; CHILD uses 0.3
                # check this is a more restrictive condition than Courant:
                t_to_converge = min((t_to_converge, max_tstep_wave))
                if t_to_converge < 3600. and flood_node is not None:
                    t_to_converge = 3600.  # forbid tsteps < 1hr; a bit hacky
                # without this, it's possible for the component to get stuck in
                # a loop, presumably when the gradient is "supposed" to level
                # out. We make exception got nodes that need to be filled in
                # "just so"
                # the new handling of flooded nodes as of 25/10/16 should make
                # this redundant, but retained to help ensure stability
                this_tstep = min((t_to_converge, dt_secs))
                t_elapsed_internal += this_tstep
                if t_elapsed_internal >= dt_secs:
                    break_flag = True
                    t_to_converge = dt_secs - t_elapsed_internal + this_tstep
                    self.t_to_converge = t_to_converge
                    this_tstep -= t_elapsed_internal - dt_secs

                # back-calc the sed budget in the nodes, as appropriate:
                self._hillslope_sediment[self.grid.node_at_cell] = (
                    self._voldroprate[self.grid.node_at_cell] /
                    self.grid.area_of_cell * this_tstep)
                # modify elevs; both sed & rock:
                # note dzbydt applies only to the ROCK surface
                elev_less_sed[grid.core_nodes] += (
                    dzbydt[grid.core_nodes] * this_tstep
                )
                node_z[grid.core_nodes] = (
                    elev_less_sed[grid.core_nodes] +
                    self._hillslope_sediment[grid.core_nodes]
                )

                if break_flag:
                    break
                else:
                    self._loopcounter += 1
                # do we need to reroute the flow/recalc the slopes here?
                # -> NO, slope is such a minor component of Diff we'll be OK
                # BUT could be important not for the stability, but for the
                # actual calc. So YES.
                node_S = np.zeros_like(node_S)
                # print link_length[core_draining_nodes]
                node_S[core_draining_nodes] = (node_z-node_z[flow_receiver])[
                    core_draining_nodes
                ]/link_length[core_draining_nodes]
                downward_slopes = node_S.clip(0.)
        else:
            raise TypeError  # should never trigger

        grid.at_node['channel_sediment__volumetric_transport_capacity'][
            :] = transport_capacities
        grid.at_node['channel_sediment__volumetric_discharge'][
            :] = river_volume_flux_into_node
        # ^note this excludes the hillslope fluxes now, i.e., it's the
        # incoming sed flux to the node. Including the local flux in would
        # make little sense as it could easily exceed capacity.
        grid.at_node['channel_sediment__relative_flux'][:] = rel_sed_flux
        # elevs set automatically to the name used in the function call.

        return grid, grid.at_node["topographic__elevation"]

    def run_one_step(self, dt, flooded_nodes=None, **kwds):
        """Run the component across one timestep increment, dt.

        Erosion occurs according to the sediment dependent rules specified
        during initialization. Method is fully equivalent to the :func:`erode`
        method.

        Parameters
        ----------
        dt : float (years, only!)
            Timestep for which to run the component.
        flooded_nodes : ndarray, field name, or None
            If an array, either the IDs of nodes that are flooded and should
            have no erosion, or an nnodes boolean array of flooded nodes.
            If a field name, a boolean field at nodes of flooded nodes. If not
            provided but flow has still been routed across depressions, erosion
            and deposition may still occur beneath the apparent water level.
        """
        self.erode(dt=dt, flooded_nodes=flooded_nodes, **kwds)

    def show_sed_flux_function(self, **kwds):
        """
        This is a helper function to visualize the sediment flux function
        chosen during component instantiation. Plots to current figure
        f(Qs/Qc) vs Qs/Qc. Call show() to print to screen after calling this
        method.
        """
        from matplotlib.pyplot import plot, xlim, ylim, xlabel, ylabel
        xvals = np.linspace(0., 1., 101)
        yvals = []
        for xval in xvals:
            yval = self._sed_flux_fn_gen(
                xval, self.kappa, self.nu, self.c, self.phi, self.norm)
            yvals.append(yval)
        yvals = np.array(yvals)
        plot(xvals, yvals, **kwds)
        xlim((0, 1))
        ylim((0, 1))
        xlabel('Relative sediment flux (Qs/Qc)')
        ylabel('Relative erosional efficiency')

    @property
    def is_it_TL(self):
        """Return a map of where erosion is purely transport-limited.
        """
        return self._is_it_TL.view(dtype=np.bool)
