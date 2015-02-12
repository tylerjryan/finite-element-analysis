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

    def __init__(self, plane_stress=False, plane_strain=False):
        # Assumptions
        self.plane_stress = plane_stress
        self.plane_strain = plane_strain

    def calculate_all(self, material, deformation_gradient, test=True):
        """Calculate and return the values of the first Piola-Kirchhoff stress, the tangent moduli, and the strain
        energy density.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        :param bool test: whether to perform the verification test for the stress result
        :return numpy.ndarray first_piola_kirchhoff_stress: 3x3 matrix representing the first Piola-Kirchhoff stress in the body
        :return numpy.ndarray tangent_moduli: 3x3x3x3 tensor representing the tangent moduli of the body
        :return float strain_energy_density: the value of the strain energy density in the body
        """
        strain_energy_density = self.strain_energy_density(material=material,
                                                           deformation_gradient=deformation_gradient)
        first_piola_kirchhoff_stress = self.first_piola_kirchhoff_stress(material=material,
                                                                         deformation_gradient=deformation_gradient,
                                                                         test=test)
        tangent_moduli = self.tangent_moduli(material=material, deformation_gradient=deformation_gradient, test=test)
        return strain_energy_density, first_piola_kirchhoff_stress, tangent_moduli

    def first_piola_kirchhoff_stress(self, material, deformation_gradient, test=True):
        """Compute the first Piola-Kirchhoff stress for the material from the deformation gradient under
        the specified assumptions.

        :param material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        :param bool test: whether to perform the verification test for the stress result
        """
        result = (
            (material.first_lame_parameter * math.log(numpy.linalg.det(deformation_gradient)) - material.shear_modulus)
            * operations.inverse_transpose(deformation_gradient)
            + material.shear_modulus * deformation_gradient)
        # Verify the correctness of this result by comparing to numerical differentiation
        if test:
            tests.verify_first_piola_kirchhoff_stress(constitutive_model=self,
                                                      material=material,
                                                      deformation_gradient=deformation_gradient,
                                                      first_piola_kirchhoff_stress=result)
        return result

    def strain_energy_density(self, material, deformation_gradient):
        """Compute the strain energy density for the material from the deformation gradient under
        the specified assumptions.

        :param model.Material material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
        """
        J = numpy.linalg.det(deformation_gradient)
        result = (material.first_lame_parameter / 2 * ((math.log(J)) ** 2)
                  - material.shear_modulus * math.log(J)
                  + material.shear_modulus / 2 * (
                      numpy.trace(numpy.dot(deformation_gradient.T, deformation_gradient)) - 3))
        return result

    def tangent_moduli(self, material, deformation_gradient, test=True):
        """Compute the tangent moduli for the material from the deformation gradient under
        the specified assumptions.

        :param model.Material material: material to which the deformation gradient applies
        :param numpy.ndarray deformation_gradient: 3x3 matrix describing the deformation of the body
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
                        entry = (material.first_lame_parameter * F_inverse[l][k] * F_inverse[j][i]
                                 - (material.first_lame_parameter * math.log(J) - material.shear_modulus)
                                 * F_inverse[j][k] * F_inverse[l][i])
                        if i == k and j == l:
                            entry += material.shear_modulus
                        tangent_moduli[i][j][k][l] = entry
        # Verify the correctness of this result by comparing it to numerical differentiation
        if test:
            tests.verify_tangent_moduli(constitutive_model=self, material=material,
                                        deformation_gradient=deformation_gradient,
                                        tangent_moduli=tangent_moduli)
        return tangent_moduli


