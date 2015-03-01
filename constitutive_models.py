"""
constitutive_models.py contains classes that define the relationship between stress and strain for the body,
as well as assumptions to be imposed on the analysis such as plane stress and plane strain.

.. moduleauthor:: Tyler Ryan <tyler.ryan@engineering.ucla.edu>
"""

import math

import numpy

import operations
import tests


class Neohookean:
    """A hyperelastic model with non-linear stress-strain behavior of materials undergoing large deformations
    and extended to the compressive range (volume can change).
    """

    @classmethod
    def calculate_all(cls, material, deformation_gradient, dimension=3, test=True):
        """Calculate and return the values of the first Piola-Kirchhoff stress, the tangent moduli, and the strain
        energy density.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        :param int dimension: desired dimension of the returned tensors
        :param bool test: whether to perform the verification test for the stress result
        :return numpy.ndarray numerical_differentiation_first_piola_kirchhoff_stress: 3x3 matrix representing the first Piola-Kirchhoff stress in the body
        :return numpy.ndarray numerical_differentiation_tangent_moduli: 3x3x3x3 tensor representing the tangent moduli of the body
        :return float strain_energy_density: the value of the strain energy density in the body
        """
        strain_energy_density = cls.strain_energy_density(material=material,
                                                          deformation_gradient=deformation_gradient)
        first_piola_kirchhoff_stress = cls.first_piola_kirchhoff_stress(material=material,
                                                                        deformation_gradient=deformation_gradient,
                                                                        dimension=dimension,
                                                                        test=test)
        tangent_moduli = cls.tangent_moduli(material=material,
                                            deformation_gradient=deformation_gradient,
                                            dimension=dimension,
                                            test=test)
        return strain_energy_density, first_piola_kirchhoff_stress, tangent_moduli

    @classmethod
    def first_piola_kirchhoff_stress(cls, material, deformation_gradient, dimension=3, test=True):
        """Compute the first Piola-Kirchhoff stress for the material from the deformation gradient under
        the specified assumptions.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        :param int dimension: desired dimension of the returned matrix
        :param bool test: whether to perform the verification test for the stress result
        """
        result = (
            (material.first_lame_parameter * math.log(numpy.linalg.det(deformation_gradient)) - material.shear_modulus)
            * operations.inverse_transpose(deformation_gradient)
            + material.shear_modulus * deformation_gradient)
        # Verify the correctness of this result by comparing to numerical differentiation
        if test:
            tests.numerical_differentiation_first_piola_kirchhoff_stress(constitutive_model=cls,
                                                                         material=material,
                                                                         deformation_gradient=deformation_gradient,
                                                                         first_piola_kirchhoff_stress=result)
        # Return a 2x2 matrix if requested for plane stress:
        if dimension == 2:
            return result[0:2, 0:2]
        # Otherwise return the full 3x3 matrix
        else:
            return result

    @classmethod
    def strain_energy_density(cls, material, deformation_gradient):
        """Compute the strain energy density for the material from the deformation gradient under
        the specified assumptions. Note that this value is the same in 2D and 3D.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        """
        J = numpy.linalg.det(deformation_gradient)
        result = (material.first_lame_parameter / 2 * ((math.log(J)) ** 2)
                  - material.shear_modulus * math.log(J)
                  + material.shear_modulus / 2 * (
                      numpy.trace(numpy.dot(deformation_gradient.T, deformation_gradient)) - 3))
        return result

    @classmethod
    def tangent_moduli(cls, material, deformation_gradient, dimension=3, test=True):
        """Compute the tangent moduli for the material from the deformation gradient under
        the specified assumptions.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        :param int dimension: desired dimension of the returned tensor
        :param bool test: whether to perform the verification test for the stress result
        """
        J = numpy.linalg.det(deformation_gradient)
        F_inverse = numpy.linalg.inv(deformation_gradient)
        # Initialize tangent moduli as an empty 4-dimensional array
        tangent_moduli = numpy.empty(shape=(3, 3, 3, 3), dtype=float)
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    for l in range(3):
                        tangent_moduli[i][j][k][l] = (material.first_lame_parameter * F_inverse[l][k] * F_inverse[j][i]
                                                      - (
                            material.first_lame_parameter * math.log(J) - material.shear_modulus)
                                                      * F_inverse[j][k] * F_inverse[l][i])
                        if i == k and j == l:
                            tangent_moduli[i][j][k][l] += material.shear_modulus
        # Verify the correctness of this result by comparing it to numerical differentiation
        if test:
            tests.numerical_differentiation_tangent_moduli(constitutive_model=cls, material=material,
                                                           deformation_gradient=deformation_gradient,
                                                           tangent_moduli=tangent_moduli)
        # If the requested dimension is 2, corrected the tangent moduli for plane stress
        if dimension == 2:
            return cls.tangent_moduli_two_dimensions(tangent_moduli)
        # Otherwise return the full tangent moduli
        return tangent_moduli

    @classmethod
    def tangent_moduli_two_dimensions(cls, tangent_moduli):
        """Calculate the two-dimensional tangent moduli by correcting for plane stress.

        :param tangent_moduli: a 3x3x3x3 tangent moduli to be condensed by accounting for plane stress
        """
        # Initialize tangent moduli as an empty 4-dimensional array
        corrected_tangent_moduli = numpy.empty(shape=(2, 2, 2, 2), dtype=float)
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    for d in range(2):
                        corrected_tangent_moduli[a][b][c][d] = (
                            tangent_moduli[a][b][c][d] - tangent_moduli[a][b][2][2]
                            * tangent_moduli[2][2][c][d] / tangent_moduli[2][2][2][2])
        return corrected_tangent_moduli


