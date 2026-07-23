#!/usr/bin/env python3
from __future__ import annotations
import json, math

OBS=[29,30,30,30,30,30,30,30,30,30]  # Pisces..Sagittarius, Aries/Taurus halves summed

def neglog2(p):
    return -math.log2(max(p,1e-300))

# Fixed 30 slots with one independent omission across 300 slots; MLE epsilon=1/300.
eps=1/300
p_exact_one=300*eps*((1-eps)**299)
fixed_cost=neglog2(p_exact_one)+0.5*math.log2(300)  # one fitted Bernoulli parameter

# Simple lunar 29/30 model: each sign independently 29 or 30 with equal probability.
lunar_balanced_cost=10.0

# Alternating 29/30 model with best of two phases; four observed panels disagree with best phase.
# Encode phase (1 bit) and mismatch mask among 10 positions.
alt_mismatches=4
lunar_alternating_cost=1+math.log2(math.comb(10,alt_mismatches))

# 28-mansion exact count with absolute-error universal code.
mansions28_cost=sum(math.log2(1+abs(x-28)) for x in OBS)

# 30/31 civil-month family, best case maps every observed 30 to a 30-day month but must pay mapping;
# four 30-day months exist in a 12-month Julian year, so nine observed 30s cannot be explained without reuse/exceptions.
calendar_lower_bound=math.log2(12)+math.log2(math.comb(9,5))

result={
 'observed_sign_totals':OBS,
 'observed_total':sum(OBS),
 'models':{
   'FIXED_30_WITH_ONE_OMISSION':{'description_bits':fixed_cost,'status':'SURVIVES'},
   'LUNAR_29_30_IID_P_EQ_0_5':{'description_bits':lunar_balanced_cost,'status':'DISFAVORED_EXACT_MODEL'},
   'LUNAR_29_30_STRICT_ALTERNATION':{'description_bits':lunar_alternating_cost,'status':'DISFAVORED_EXACT_MODEL'},
   'MANSIONS_28_EXACT_COUNT':{'description_bits':mansions28_cost,'status':'FAIL_EXACT_MODEL'},
   'CIVIL_MONTH_30_31_SIMPLE_MAPPING_LOWER_BOUND':{'description_bits':calendar_lower_bound,'status':'DISFAVORED_EXACT_MODEL'},
 },
 'count_only_verdict':'INCONCLUSIVE_BETWEEN_M_FORMAT_M_DEGREE_M_DECAN',
 'next_test':'BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01'
}
print(json.dumps(result,indent=2,ensure_ascii=False))
