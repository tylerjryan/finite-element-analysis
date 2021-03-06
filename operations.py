"""
operations.py contains useful function that are commonly used in the model but are not pre-defined in existing
packages such as numpy.

.. moduleauthor:: Tyler Ryan <tyler.ryan@engineering.ucla.edu>
"""
import random

import numpy

import constants
import exceptions


def inverse_transpose(matrix):
    """
    Compute the inverse of the transpose of a matrix.

    :param numpy.ndarray matrix: matrix to be operated on
    :return: inverse-transpose of the matrix
    """
    return numpy.linalg.inv(matrix.T)


def calculate_lambda_from_E_and_G(E, G):
    """Calculate the value of the first lame parameter for a material, given values for Young's Modulus(E, in GPa)
    and the shear modulus (G, in GPa).

    :param float E: Young's Modulus of a material
    :param float G: Shear modulus of a material
    :return float first_lame_parameter: value for the first lame parameter (lambda)
    """
    first_lame_parameter = G * (E - 2 * G) / (3 * G - E)
    return first_lame_parameter


def generate_random_deformation_gradient(plane_stress=True, uniaxial=False, equibiaxial=False):
    """Generate and return a random deformation gradient that is physically valid (Jacobian > 0).
    Note that plane stress must be true for uniaxial or equibiaxial deformation to apply.

    :param bool plane_stress: whether to restructure the matrix for plane stress
    :param bool uniaxial: whether to restructure the matrix for uniaxial deformation
    :param bool equibiaxial: whether to restructure the matrix for equibiaxial deformation
    :return numpy.ndarray random_deformation: a random 3x3 deformation gradient matrix
    """
    det = -1
    while det < 0:
        random_deformation = numpy.eye(3) + numpy.random.rand(3, 3)
        det = numpy.linalg.det(random_deformation)
    # If plane stress is requested, restructure the matrix for plane stress
    if plane_stress:
        random_deformation[0][2] = 0
        random_deformation[1][2] = 0
        random_deformation[2][0] = 0
        random_deformation[2][1] = 0
        random_deformation[2][2] = 1
        if uniaxial:
            random_deformation[0][1] = 0
            random_deformation[1][0] = 0
            random_deformation[1][1] = 1
        elif equibiaxial:
            random_deformation[0][1] = 0
            random_deformation[1][0] = 0
            random_deformation[1][1] = random_deformation[0][0]
    return random_deformation


def generate_random_node_current_position(node):
    """Generate random current positions for the provided node of a 2D triangular element.
    Start with the previous deformed position and add a small perturbation as a random 2 element array with entries
    between 0 and 1 scaled by a factor of 0.1.

    :param node: node object to perturb
    """
    # node.current_position = node.current_position + .01 * numpy.random.rand(2)  # use for random deformation
    pass  # use for no deformation


def generate_random_node_reference_positions(element_nodes):
    """Generate random reference positions for the 3 corner nodes (and 3 midpoint nodes) of a 2D triangular element.
    Start with a equilateral triangular of side length 1 with bottom left corner at the origin, and add a small
    perturbation as a random 2 element array with entries between 0 and 1 scaled by factor of 0.2.

    :param list element_nodes: list of 3 or 6 node objects to which to assign positions
    """
    node_position_1 = numpy.array([0., 0., 0])  # + .2 * numpy.random.rand(2)
    node_position_2 = numpy.array([1., 0., 0])  # + .2 * numpy.random.rand(2)
    node_position_3 = numpy.array([0., 1., 0])  # + .2 * numpy.random.rand(2)
    node_position_4 = numpy.array([.5, 0., 0])  # + .2 * numpy.random.rand(2)
    node_position_5 = numpy.array([.5, .5, 0])  # + .2 * numpy.random.rand(2)
    node_position_6 = numpy.array([0., .5, 0])  # + .2 * numpy.random.rand(2)
    node_positions = [node_position_1, node_position_2, node_position_3, node_position_4, node_position_5,
                      node_position_6]
    for node_index in range(len(element_nodes)):
        element_nodes[node_index].reference_position = node_positions[node_index]
        # Assign the current position to equal the reference position because no deformation has occurred yet
        element_nodes[node_index].current_position = numpy.copy(node_positions[node_index])


def generate_random_rotation_matrix():
    """Generate and return a random rotation matrix.

    :return numpy.ndarray random_rotation: a random 3x3 rotation matrix.
    """
    # generate a random normalized vector
    random_vector = numpy.random.rand(3, 1)
    n = random_vector / numpy.linalg.norm(random_vector)
    # generate a random angle between 0 and pi
    angle = random.uniform(0, numpy.pi)
    # generate n_hat (see notes for structure)
    n_hat = numpy.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
    # compute random rotation using the given equation
    rotation_matrix = (numpy.eye(3) - numpy.sin(angle) * n_hat
                       + (1 - numpy.cos(angle)) * (numpy.outer(n, n) - numpy.eye(3)))
    return rotation_matrix


def newton_method_thickness_stretch_ratio(constitutive_model, material, deformation_gradient, max_iterations=15):
    """Use Newton's method to iteratively solve for stretch ratio.

    :param constitutive_model: constitutive model object described material behavior
    :param material: material model for the body
    :param numpy.ndarray deformation_gradient: 3x3 deformation gradient matrix
    :param max_iterations: maximum number of iterations to perform while solving
    :return float thickness_stretch_ratio: ratio of the initial thickness to the deformed thickness
    """
    # TODO function to make a good initial guess
    # Make an initial guess for the thickness stretch ratio
    stretch_ratio = 1
    # Initialize current iteration counter
    current_iteration = 0
    # Loop until the stress converges to within tolerance of zero, or max iterations is exceeded.
    while True:
        # Assign the 3-3 element of the deformation gradient to the current stretch ratio
        deformation_gradient[2][2] = stretch_ratio
        # tests.deformation_gradient_physical(numpy.linalg.det(deformation_gradient))
        P33 = constitutive_model.first_piola_kirchhoff_stress(material=material,
                                                              deformation_gradient=deformation_gradient)[2][2]
        error = abs(0 - P33)
        # If the error is less than the tolerance, the loop has converged, so break out
        if error < constants.NEWTON_METHOD_TOLERANCE:
            break
        # Compute a new value for the stretch ratio and try again
        C3333 = constitutive_model.tangent_moduli(material=material,
                                                  deformation_gradient=deformation_gradient)[2][2][2][2]
        # Compute correction to the stretch ratio
        delta_stretch = -(1 / C3333) * P33
        stretch_ratio += delta_stretch
        # If there is a negative (unphysical) stretch ratio, adjust it to be a very small positive value
        # to avoid negative jacobian errors and give the solver another chance to converge
        if stretch_ratio < 0:
            stretch_ratio = 1e-6
        # If the loop has reached the max number of iterations, raise an error
        if current_iteration == max_iterations:
            raise exceptions.NewtonMethodMaxIterationsExceededError(iterations=max_iterations,
                                                                    error=error,
                                                                    tolerance=constants.NEWTON_METHOD_TOLERANCE)
        # Increment the iteration counter
        else:
            current_iteration += 1
    return stretch_ratio

