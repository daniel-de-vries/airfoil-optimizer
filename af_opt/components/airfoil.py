#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains the definition of the generic Airfoil OpenMDAO Component and its helper functions.
"""
import numpy as np
import openmdao.api as om

from cst import cst, fit

from ..util import cosspace


def coords2cst(x, y_u, y_l, n_ca, n_th):
    """
    Convert airfoil upper/lower curve coordinates to camber line/thickness distribution CST coefficients.

    Parameters
    ----------
    x : array_like
        X-Coordinates
    y_u, y_l : array_like
        Y-Coordinates of the upper and lower curves, respectively
    n_ca, n_th : int
        Number of CST coefficients to use for the camber line and thickness distribution of the airfoil

    Returns
    -------
    a_ca, a_th : np.ndarray
        CST coefficients describing the camber line and thickness distribution of the airfoil
    t_te : float
        Airfoil trailing edge thickness
    """
    y_c = (y_u + y_l) / 2
    t = y_u - y_l

    a_ca, _ = fit(x, y_c, n_ca, delta=(0.0, 0.0), n1=1)
    a_th, t_te = fit(x, t, n_th)

    return a_ca, a_th, t_te[1]


def cst2coords(a_ca, a_th, t_te, n_coords=100):
    """
    Convert airfoil camber line/thickness distribution CST coefficients to upper/lower curve coordinates.

    Parameters
    ----------
    a_ca, a_th : array_like
        CST coefficients describing the camber line and thickness distribution of the airfoil
    t_te : float
        Airfoil trailing edge thickness
    n_coords : int, optional
        Number of x-coordinates to use. 100 by default

    Returns
    -------
    x : np.ndarray
        Airfoil x-coordinates
    y_u, y_l : np.ndarray
        Airfoil upper and lower curves y-coordinates
    y_c, t : np.ndarray
        Airfoil camber line and thickness distribution
    """
    x = cosspace(0, 1, n_coords)
    y_c = cst(x, a_ca, n1=1)
    t = cst(x, a_th, delta=(0, t_te))

    y_u = y_c + t / 2
    y_l = y_c - t / 2
    return x, y_u, y_l, y_c, t


class AirfoilComponent(om.ExplicitComponent):
    """
    Basic Aifoil specified by CST coefficients for its camber line and thickness distribution and a TE thickness.
    """

    def initialize(self):
        self.options.declare("n_ca", default=6, types=int)
        self.options.declare("n_th", default=6, types=int)

        self.options.declare("n_coords", default=100, types=int)

    def setup(self):
        # Number of CST coefficients
        n_ca = self.options["n_ca"]
        n_th = self.options["n_th"]

        # Inputs
        self.add_input("a_ca", shape=n_ca)
        self.add_input("a_th", shape=n_th)
        self.add_input("t_te", shape=1)

    def compute_coords(self, inputs, precision=None, n_coords=None):
        """
        Compute airfoil coordinates from the set of OpenMDAO inputs.
        """
        x, y_u, y_l, y_c, t = cst2coords(
            inputs["a_ca"],
            inputs["a_th"],
            inputs["t_te"][0],
            self.options["n_coords"] if n_coords is None else n_coords,
        )
        if precision is not None:
            return (
                np.round(x, precision),
                np.round(y_u, precision),
                np.round(y_l, precision),
                np.round(y_c, precision),
                np.round(t, precision),
            )
        return x, y_u, y_l, y_c, t
