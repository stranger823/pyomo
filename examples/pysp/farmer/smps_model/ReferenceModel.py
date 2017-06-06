#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and 
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain 
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________
#
# Farmer: Annotated with location of stochastic matrix entries
#         for use with pysp2smps conversion tool.
#
# Imports
#

from pyomo.core import *
from pyomo.pysp.annotations import (PySP_ConstraintStageAnnotation,
                                    PySP_StochasticMatrixAnnotation)

#
# Model
#

model = AbstractModel()

#
# Sets
#

model.CROPS = Set(initialize=['WHEAT', 'CORN', 'SUGAR_BEETS'],
                  ordered=True)

#
# Parameters
#

model.TOTAL_ACREAGE = Param(within=PositiveReals)

model.PriceQuota = Param(model.CROPS, within=PositiveReals)

model.SubQuotaSellingPrice = Param(model.CROPS, within=PositiveReals)

def super_quota_selling_price_validate (model, value, i):
    return model.SubQuotaSellingPrice[i] >= model.SuperQuotaSellingPrice[i]

model.SuperQuotaSellingPrice = Param(model.CROPS,
                                     validate=super_quota_selling_price_validate)

model.CattleFeedRequirement = Param(model.CROPS, within=NonNegativeReals)

model.PurchasePrice = Param(model.CROPS, within=PositiveReals)

model.PlantingCostPerAcre = Param(model.CROPS, within=PositiveReals)

model.Yield = Param(model.CROPS, within=NonNegativeReals)

#
# Variables
#

model.DevotedAcreage = Var(model.CROPS,
                           bounds=(0.0, model.TOTAL_ACREAGE))
model.QuantitySubQuotaSold = Var(model.CROPS,
                                 bounds=(0.0, None))
model.QuantitySuperQuotaSold = Var(model.CROPS,
                                   bounds=(0.0, None))
model.QuantityPurchased = Var(model.CROPS,
                              bounds=(0.0, None))

#
# First-Stage Constraints
#

def ConstrainTotalAcreage_rule(model):
    return summation(model.DevotedAcreage) <= model.TOTAL_ACREAGE
model.ConstrainTotalAcreage = \
    Constraint(rule=ConstrainTotalAcreage_rule)

#
# Second-Stage Constraints
#

def EnforceQuotas_rule(model, i):
    return (0.0, model.QuantitySubQuotaSold[i], model.PriceQuota[i])
model.EnforceQuotas = Constraint(model.CROPS,
                                 rule=EnforceQuotas_rule)

#
# Second-Stage Constraints With Stochastic Data
#

def EnforceCattleFeedRequirement_rule(model, i):
    return model.CattleFeedRequirement[i] <= (model.Yield[i] * model.DevotedAcreage[i]) + model.QuantityPurchased[i] - model.QuantitySubQuotaSold[i] - model.QuantitySuperQuotaSold[i]
model.EnforceCattleFeedRequirement = \
    Constraint(model.CROPS, rule=EnforceCattleFeedRequirement_rule)

def LimitAmountSold_rule(model, i):
    return model.QuantitySubQuotaSold[i] + model.QuantitySuperQuotaSold[i] - (model.Yield[i] * model.DevotedAcreage[i]) <= 0.0
model.LimitAmountSold = \
    Constraint(model.CROPS, rule=LimitAmountSold_rule)

#
# Stage-specific cost computations
#

def ComputeFirstStageCost_rule(model):
    return summation(model.PlantingCostPerAcre, model.DevotedAcreage)
model.FirstStageCost = Expression(rule=ComputeFirstStageCost_rule)

def ComputeSecondStageCost_rule(model):
    expr = summation(model.PurchasePrice, model.QuantityPurchased)
    expr -= summation(model.SubQuotaSellingPrice, model.QuantitySubQuotaSold)
    expr -= summation(model.SuperQuotaSellingPrice, model.QuantitySuperQuotaSold)
    return expr
model.SecondStageCost = Expression(rule=ComputeSecondStageCost_rule)

#
# PySP Auto-generated Objective
#
# minimize: sum of StageCosts
#
# An active scenario objective equivalent to that generated by PySP is
# included here for informational purposes.
def total_cost_rule(model):
    return model.FirstStageCost + model.SecondStageCost
model.Total_Cost_Objective = Objective(rule=total_cost_rule,
                                       sense=minimize)

def declare_annotations_rule(model):
    #
    # Annotate constraint stages
    #
    model.constraint_stage = PySP_ConstraintStageAnnotation()
    # first-stage constraints
    model.constraint_stage.declare(model.ConstrainTotalAcreage, 1)
    # second-stage constraints
    model.constraint_stage.declare(model.EnforceQuotas, 2)
    model.constraint_stage.declare(model.EnforceCattleFeedRequirement, 2)
    model.constraint_stage.declare(model.LimitAmountSold, 2)

    #
    # Annotate stochastic constraint matrix coefficients
    #
    model.stoch_matrix = PySP_StochasticMatrixAnnotation()
    # DevotedAcreage[i] has a stochastic coefficient in two constraints
    for i in model.CROPS:
        model.stoch_matrix.declare(model.EnforceCattleFeedRequirement[i],
                               variables=[model.DevotedAcreage[i]])
        model.stoch_matrix.declare(model.LimitAmountSold[i],
                                   variables=[model.DevotedAcreage[i]])
model.declare_annotations = BuildAction(rule=declare_annotations_rule)
