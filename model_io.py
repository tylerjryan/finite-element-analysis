"""
model_io.py module provides inputs to the model, runs the model, and receives outputs.

.. moduleauthor:: Tyler Ryan <tyler.ryan@engineering.ucla.edu>
"""

import math

import numpy

import body
import constants
import frames
import materials
import model
import constitutive_models
import kinematics
import operations
import tests


def homework1_part1():
    """Curvilinear Kinematics: Uniaxial deformation of a cylinder"""
    # Position at which to evaluate
    radius = 10
    angle = math.pi / 16

    # Constants
    lambda1 = 2
    lambda2 = 3

    # Lab frame
    lab_vector1 = numpy.array([math.cos(angle), math.sin(angle), 0])
    lab_vector2 = numpy.array([-math.sin(angle), math.cos(angle), 0])
    lab_vector3 = numpy.array([0, 0, 1])
    lab_frame = frames.Basis(vector1=lab_vector1,
                             vector2=lab_vector2,
                             vector3=lab_vector3,
                             type=constants.LAB)

    # Reference configuration
    reference_vector1_covariant = numpy.array(lab_vector1)
    reference_vector2_covariant = numpy.array(radius * lab_vector2)
    reference_vector3_covariant = numpy.array(lab_vector3)
    reference_configuration_covariant = frames.Basis(vector1=reference_vector1_covariant,
                                                     vector2=reference_vector2_covariant,
                                                     vector3=reference_vector3_covariant,
                                                     type=constants.COVARIANT)
    reference_vector1_contravariant = numpy.array(lab_vector1)
    reference_vector2_contravariant = numpy.array(1 / radius * lab_vector2)
    reference_vector3_contravariant = numpy.array(lab_vector3)
    reference_configuration_contravariant = frames.Basis(vector1=reference_vector1_contravariant,
                                                         vector2=reference_vector2_contravariant,
                                                         vector3=reference_vector3_contravariant,
                                                         type=constants.CONTRAVARIANT)
    reference_configuration = frames.ReferenceConfiguration(covariant_basis=reference_configuration_covariant,
                                                            contravariant_basis=reference_configuration_contravariant)
    # Deformed configuration
    deformed_vector1_covariant = numpy.array(lambda1 * lab_vector1)
    deformed_vector2_covariant = numpy.array(lambda1 * radius * lab_vector2)
    deformed_vector3_covariant = numpy.array(lambda2 * lab_vector3)
    deformed_configuration_covariant = frames.Basis(vector1=deformed_vector1_covariant,
                                                    vector2=deformed_vector2_covariant,
                                                    vector3=deformed_vector3_covariant,
                                                    type=constants.COVARIANT)
    deformed_vector1_contravariant = numpy.array(1 / lambda1 * lab_vector1)
    deformed_vector2_contravariant = numpy.array(1 / (lambda1 * radius) * lab_vector2)
    deformed_vector3_contravariant = numpy.array(1 / lambda2 * lab_vector3)
    deformed_configuration_contravariant = frames.Basis(vector1=deformed_vector1_contravariant,
                                                        vector2=deformed_vector2_contravariant,
                                                        vector3=deformed_vector3_contravariant,
                                                        type=constants.CONTRAVARIANT)
    deformed_configuration = frames.DeformedConfiguration(covariant_basis=deformed_configuration_covariant,
                                                          contravariant_basis=deformed_configuration_contravariant)

    # Compute deformation gradient and other kinematic quantities
    deformation_gradient_matrix = kinematics.deformation_gradient(deformed_configuration_covariant,
                                                                  reference_configuration_contravariant)
    tests.check_deformation_gradient_physical(numpy.linalg.det(deformation_gradient_matrix))
    right_cauchy_green_deformation = kinematics.right_cauchy_green_deformation_tensor(
        deformation_gradient_matrix)
    left_cauchy_green_deformation = kinematics.left_cauchy_green_deformation_tensor(
        deformation_gradient_matrix)
    green_lagrange_strain = kinematics.green_lagrange_strain(right_cauchy_green_deformation)


def homework1_part2():
    """Plane Stress Nonlinear Elasticity:

    In this part of the assignment you will derive the stress response and tangent moduli for a nonlinear
    hyperelastic constitutive law subject to the assumption of plane stress, and write a program using
    these results to compute the response of a planar sheet made of this material."""
    # Initialize a new finite element model
    fem = model.FEM()
    # Select constitutive model and state assumptions
    fem.constitutive_model = constitutive_models.Neohookean()
    # Create a material for the body
    fem.material = materials.Custom(name='custom material', first_lame_parameter=1, shear_modulus=1)
    # Make a set of elements to add to model
    for i in range(10):
        # Make a new element and add it to the model
        element = model.Element()
        fem.elements.append(element)
        # Make a new quadrature point and add it to the element
        quadrature_point = model.QuadraturePoint()
        element.quadrature_points.append(quadrature_point)
        # Initialize a random deformation gradient (with positive determinant) from which to compute other quantities
        random_deformation = operations.generate_random_deformation_gradient()
        quadrature_point.deformation_gradient = body.DeformationGradient(deformation_gradient=random_deformation,
                                                                         material=fem.material,
                                                                         constitutive_model=fem.constitutive_model)
        (quadrature_point.strain_energy_density,
         quadrature_point.first_piola_kirchhoff_stress,
         quadrature_point.tangent_moduli) = fem.constitutive_model.calculate_all(material=fem.material,
                                                                                 deformation_gradient=random_deformation)


def error_testing():
    for i in range(10):
        deformation_gradient = operations.generate_random_deformation_gradient()
        material = materials.Custom(name='custom material', first_lame_parameter=5, shear_modulus=3)
        constitutive_model = constitutive_models.Neohookean()
        first_piola_kirchhoff_stress = constitutive_model.first_piola_kirchhoff_stress(material, deformation_gradient)
        w = constitutive_model.strain_energy_density(material, deformation_gradient)
        c = constitutive_model.tangent_moduli(material, deformation_gradient)


def plane_stress():
    fem = model.FEM()
    fem.constitutive_model = constitutive_models.Neohookean()
    fem.material = materials.Custom(name='test', first_lame_parameter=5, shear_modulus=3)
    random_deformation = operations.generate_random_deformation_gradient(plane_stress=True)
    deformation_gradient = body.DeformationGradient(deformation_gradient=random_deformation,
                                                    material=fem.material,
                                                    constitutive_model=fem.constitutive_model,
                                                    plane_stress=True)


def uniaxial_deformation():
    fem = model.FEM()
    fem.constitutive_model = constitutive_models.Neohookean()
    fem.material = materials.AluminumAlloy
    # random_deformation = operations.generate_random_deformation_gradient(plane_stress=True,
    # uniaxial=True)
    random_deformation = numpy.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    # For a range of F11 values, compute the first Piola-Kirchhoff stress
    f11_values = numpy.arange(.1, 10, .5)
    p11_values = []
    # TODO what values do I plot here for P?
    for f11_value in f11_values:
        random_deformation[0][0] = f11_value
        deformation_gradient = body.DeformationGradient(deformation_gradient=random_deformation,
                                                        material=fem.material,
                                                        constitutive_model=fem.constitutive_model,
                                                        plane_stress=True)
        first_piola_kirchhoff_stress = fem.constitutive_model.first_piola_kirchhoff_stress(
            material=fem.material,
            deformation_gradient=deformation_gradient.F,
            test=True)
        p11_values.append(first_piola_kirchhoff_stress[0][0])





def run():
    """Create and run finite element model"""
    # homework1_part1()
    # homework1_part2()
    # error_testing()
    # tests.material_frame_indifference()
    # tests.material_symmetry()
    # plane_stress()
    uniaxial_deformation()


run()
