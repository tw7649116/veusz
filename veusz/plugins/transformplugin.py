#    Copyright (C) 2016 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################

from __future__ import division, print_function
import numpy as N

from .. import qtall as qt4
from .datasetplugin import Dataset1D

def _(text, disambiguation=None, context='TransformPlugin'):
    """Translate text."""
    return qt4.QCoreApplication.translate(context, text, disambiguation)

# TODO
# filter
# moving average
# rebin
# divfrom, inv

transformpluginregistry = {}

def registerTransformPlugin(
        name, username, category='Base', description=None):

    def decorator(f):
        transformpluginregistry[name] = (
            f, username, category, description)
        return f

    return decorator

def isDataset1D(v):
    return isinstance(v, Dataset1D)

def dsCodeToIdx(code):
    """Convert code for dataset to internal index."""
    try:
        return {
            'x': 0,
            'y': 1,
            'l': 2,
            'label': 2,
            's': 3,
            'size': 3,
            'c': 4,
            'color': 4,
        }[code.lower()]
    except (KeyError, AttributeError):
        raise ValueError('Unknown dataset code %s' % code)

###############################################################################

## categories
catadd = _('Add')
catsub = _('Sub')
catmul = _('Multiply')
catdiv = _('Divide')
catrange = _('Range')
catlog = _('Exponential / Log')
catgeom = _('Geometry')
catfilt = _('Filtering')
catnorm = _('Normalisation')
catapply = _('Apply')

###############################################################################
# Add

def _addSubDataset(d1, d2, sub=False):
    minlen = min(len(d1.data), len(d2.data))

    # add/subtract data points
    if sub:
        d1.data = d1.data[:minlen] - d2.data[:minlen]
    else:
        d1.data = d1.data[:minlen] + d2.data[:minlen]

    # below, combine errors
    # note: if d1err and not d2err, keep existing errors
    # if no errors, do nothing

    d1err = d1.hasErrors()
    d2err = d2.hasErrors()
    if d2err and not d1err:
        # copy errors
        if d2.serr is not None:
            d1.serr = N.array(d2.serr[:minlen])
        if d2.perr is not None:
            d1.perr = N.array(d2.perr[:minlen])
        if d2.nerr is not None:
            d1.nerr = N.array(d2.nerr[:minlen])
    elif d1err and d2err:
        # combine errors square errors, add, sqrt
        # symmetrise errors
        if d1.serr is not None:
            d1err2 = d1.serr**2
        else:
            d1err2 = 0.5*(getattr(d1, 'perr', 0)**2 + getattr(d1, 'nerr', 0)**2)
        if d2.serr is not None:
            d2err2 = d2.serr**2
        else:
            d2err2 = 0.5*(getattr(d2, 'perr', 0)**2 + getattr(d2, 'nerr', 0)**2)
        d1.serr = N.sqrt(d1err2[:minlen] + d2err2[:minlen])
        d1.perr = d1.nerr = None

@registerTransformPlugin(
    'Add', _('Add to dataset'), category=catadd,
    description=_('Add value or dataset [val] to specified output dataset [outds]'))
def addAdd(dss):
    def Add(outds, val):
        idx = dsCodeToIdx(outds)
        if isDataset1D(val):
            _addSubDataset(dss[idx], val, sub=False)
        else:
            dss[idx].data += val
    return Add

@registerTransformPlugin(
    'AddX', _('Add to X'), category=catadd,
    description=_('Add value or dataset [val] to X dataset'))
def addAddX(dss):
    return lambda val: addAdd(dss)('x', val)

@registerTransformPlugin(
    'AddY', _('Add to Y'), category=catadd,
    description=_('Add value or dataset [val] to Y dataset'))
def addAddY(dss):
    return lambda val: addAdd(dss)('y', val)

## CumSum

def _cumsum(dataset, reverse=False):
    def calccum(v):
        v = N.array(v)
        if reverse:
            v = v[::-1]
        v[~N.isfinite(v)] = 0.
        c = N.cumsum(v)
        if reverse:
            c = c[::-1]
        return c

    dataset.data[:] = calccum(dataset.data)
    if dataset.serr is not None:
        dataset.serr[:] = N.sqrt(calccum(dataset.serr**2))
    if dataset.perr is not None:
        dataset.perr[:] = N.sqrt(calccum(dataset.perr**2))
    if dataset.nerr is not None:
        dataset.nerr[:] = -N.sqrt(calccum(dataset.nerr**2))

@registerTransformPlugin(
    'CumSumX', _('Cumulative sum of X dataset'), category=catadd,
    description=_('Calculate cumulative sum of X dataset. Sum is from '
                  'reverse end if [reverse] set'))
def addCumSumX(dss):
    def CumSumX(reverse=False):
        _cumsum(dss[0], reverse=reverse)
    return CumSumX

@registerTransformPlugin(
    'CumSumY', _('Cumulative sum of Y dataset'), category=catadd,
    description=_('Calculate cumulative sum of Y dataset. Sum is from '
                  'reverse end if [reverse] set'))
def addCumSumY(dss):
    def CumSumY(reverse=False):
        _cumsum(dss[1], reverse=reverse)
    return CumSumY

@registerTransformPlugin(
    'CumSum', _('Cumulative sum of output dataset'), category=catadd,
    description=_('Calculate cumulative sum of [outds] dataset. Sum is from '
                  'reverse end if [reverse] set'))
def addCumSum(dss):
    def CumSum(outds, reverse=False):
        _cumsum(dss[dsCodeToIdx(outds)], reverse=reverse)
    return CumSum

###############################################################################
# Subtract

@registerTransformPlugin(
    'Sub', _('Subtract from dataset'), category=catsub,
    description=_('Subtract value or dataset [val] from specified output dataset [outds]'))
def subSub(dss):
    def Sub(outds, val):
        idx = dsCodeToIdx(outds)
        if isDataset1D(val):
            _addSubDataset(dss[idx], val, sub=True)
        else:
            dss[idx].data -= val
    return Sub

@registerTransformPlugin(
    'SubX', _('Subtract from X'), category=catsub,
    description=_('Subtract value or dataset [val] from X dataset'))
def subSubX(dss):
    return lambda val: subSub(dss)('x', val)

@registerTransformPlugin(
    'SubY', _('Subtract from Y'), category=catsub,
    description=_('Subtract value or dataset [val] from Y dataset'))
def subSubY(dss):
    return lambda val: subSub(dss)('y', val)

def _subfn(ds, fn):
    data = ds.data
    findata = data[N.isfinite(data)]
    if len(findata) > 0:
        ds.data -= fn(findata)

## SubMin

@registerTransformPlugin(
    'SubMin', _('Subtract minimum value from dataset'), category=catsub,
    description=_('Subtract minimum value from [outds]'))
def subSubMin(dss):
    return lambda outds: _subfn(dss[dsCodeToIdx(outds)], N.min)

@registerTransformPlugin(
    'SubMinX', _('Subtract minimum value from X'), category=catsub,
    description=_('Subtract minimum value from dataset X'))
def subSubMinX(dss):
    return lambda: _subfn(dss[0], N.min)

@registerTransformPlugin(
    'SubMinY', _('Subtract minimum value from Y'), category=catsub,
    description=_('Subtract minimum value from dataset Y'))
def subSubMinY(dss):
    return lambda: _subfn(dss[1], N.min)

## SubMax

@registerTransformPlugin(
    'SubMax', _('Subtract maximum value from dataset'), category=catsub,
    description=_('Subtract maximum value from [outds]'))
def subSubMax(dss):
    return lambda outds: _subfn(dss[dsCodeToIdx(outds)], N.max)

@registerTransformPlugin(
    'SubMaxX', _('Subtract maximum value from X'), category=catsub,
    description=_('Subtract maximum value from dataset X'))
def subSubMaxX(dss):
    return lambda: _subfn(dss[0], N.max)

@registerTransformPlugin(
    'SubMaxY', _('Subtract maximum value from Y'), category=catsub,
    description=_('Subtract maximum value from dataset Y'))
def subSubMaxY(dss):
    return lambda: _subfn(dss[1], N.max)

## SubMean

@registerTransformPlugin(
    'SubMean', _('Subtract mean value from dataset'), category=catsub,
    description=_('Subtract mean value from [outds]'))
def subSubMean(dss):
    return lambda outds: _subfn(dss[dsCodeToIdx(outds)], N.mean)

@registerTransformPlugin(
    'SubMeanX', _('Subtract mean value from X'), category=catsub,
    description=_('Subtract mean value from dataset X'))
def subSubMeanX(dss):
    return lambda: _subfn(dss[0], N.mean)

@registerTransformPlugin(
    'SubMeanY', _('Subtract mean value from Y'), category=catsub,
    description=_('Subtract mean value from dataset Y'))
def subSubMeanY(dss):
    return lambda: _subfn(dss[1], N.mean)

## SubFrom

def _subfrom(ds, val):
    if isDataset1D(val):
        _addSubDataset(val, ds, sub=True)
    else:
        ds.data[:] = val - ds.data

@registerTransformPlugin(
    'SubFrom', _('Subtract output dataset from value or dataset'), category=catsub,
    description=_('Subtract output dataset [outds] from value or dataset [val]'))
def subSubFrom(dss):
    def SubFrom(outds, val):
        _subfrom(dss[dsCodeToIdx(outds)], val)
    return SubFrom

@registerTransformPlugin(
    'SubFromX', _('Subtract X dataset from value or dataset'), category=catsub,
    description=_('Subtract X dataset from value or dataset [val]'))
def subSubFromX(dss):
    def SubFromX(val):
        _subfrom(dss[0], val)
    return SubFromX

@registerTransformPlugin(
    'SubFromY', _('Subtract Y dataset from value or dataset'), category=catsub,
    description=_('Subtract Y dataset from value or dataset [val]'))
def subSubFromY(dss):
    def SubFromY(val):
        _subfrom(dss[1], val)
    return SubFromY

###############################################################################
# Multiply

def _multiplyDatasetScalar(ds, val):
    ds.data *= val
    if ds.serr is not None:
        ds.serr *= val
    if ds.perr is not None:
        ds.perr *= val
    if ds.nerr is not None:
        ds.nerr *= val

def _multiplyDatasetDataset(d1, d2):
    minlen = min(len(d1.data), len(d2.data))

    # below, combine errors
    # if no errors, do nothing

    d1err = d1.hasErrors()
    d2err = d2.hasErrors()
    if d2err and not d1err:
        d1av = N.abs(d1.data[:minlen])
        if d2.serr is not None:
            d1.serr = d2.serr[:minlen]*d1av
        if d2.perr is not None:
            d1.perr = d2.perr[:minlen]*d1av
        if d2.nerr is not None:
            d1.nerr = d2.nerr[:minlen]*d1av
    elif d1err and not d2err:
        d2av = N.abs(d2.data[:minlen])
        if d2.serr is not None:
            d1.serr = d1.serr[:minlen]*d2av
        if d2.perr is not None:
            d1.perr = d1.perr[:minlen]*d2av
        if d2.nerr is not None:
            d1.nerr = d1.nerr[:minlen]*d2av
    elif d1err and d2err:
        # combine errors square fractional errors, add, sqrt
        # (symmetrising)
        if d1.serr is not None:
            d1ferr2 = (d1.serr/d1.data)**2
        else:
            d1err2 = 0.5*(getattr(d1, 'perr', 0)**2 + getattr(d1, 'nerr', 0)**2)
            d1ferr2 = d1err2 / d1.data**2
        if d2.serr is not None:
            d2ferr2 = (d2.serr/d2.data)**2
        else:
            d2err2 = 0.5*(getattr(d2, 'perr', 0)**2 + getattr(d2, 'nerr', 0)**2)
            d2ferr2 = d2err2 / d2.data**2

        d1.serr = N.sqrt(d1ferr2[:minlen] + d2ferr2[:minlen]) * N.abs(
            d1.data[:minlen] * d2.data[:minlen])
        d1.perr = d1.nerr = None

    # multiply data points
    d1.data = d1.data[:minlen] * d2.data[:minlen]

@registerTransformPlugin(
    'Mul', _('Multiply dataset'), category=catmul,
    description=_('Multiply output dataset [outds] by value or dataset [val]'))
def arithMul(dss):
    def Mul(outds, val):
        idx = dsCodeToIdx(outds)
        if isDataset1D(val):
            _multiplyDatasetDataset(dss[idx], val)
        else:
            _multiplyDatasetScalar(dss[idx], val)
    return Mul

@registerTransformPlugin(
    'MulX', _('Multiply X'), category=catmul,
    description=_('Multiply X dataset by value or dataset [val]'))
def arithMulX(dss):
    return lambda val: arithMul(dss)('x', val)

@registerTransformPlugin(
    'MulY', _('Multiply Y'), category=catmul,
    description=_('Multiply Y dataset by value or dataset [val]'))
def arithMulY(dss):
    return lambda val: arithMul(dss)('y', val)

###############################################################################
# Divide

def _divideDatasetDataset(d1, d2):
    minlen = min(len(d1.data), len(d2.data))

    # below, combine errors
    # if no errors, do nothing

    ratio = d1.data[:minlen] / d2.data[:minlen]

    d1err = d1.hasErrors()
    d2err = d2.hasErrors()
    if d2err and not d1err:
        # copy fractional error
        aratiodiv = N.abs(ratio / d2.data[:minlen])
        if d2.serr is not None:
            d1.serr = aratiodiv * d2.serr[:minlen]
        if d2.perr is not None:
            d1.serr = aratiodiv * d2.perr[:minlen]
        if d2.nerr is not None:
            d1.serr = aratiodiv * d2.nerr[:minlen]

    elif d1err and not d2err:
        # divide error by scalar
        if d2.serr is not None:
            d1.serr = d1.serr[:minlen] / N.abs(d2.data[:minlen])
        if d2.perr is not None:
            d1.perr = d1.perr[:minlen] / N.abs(d2.data[:minlen])
        if d2.nerr is not None:
            d1.nerr = d1.nerr[:minlen] / N.abs(d2.data[:minlen])

    elif d1err and d2err:
        # combine errors square fractional errors, add, sqrt
        # (symmetrising)
        if d1.serr is not None:
            d1ferr2 = (d1.serr/d1.data)**2
        else:
            d1err2 = 0.5*(getattr(d1, 'perr', 0)**2 + getattr(d1, 'nerr', 0)**2)
            d1ferr2 = d1err2 / d1.data**2
        if d2.serr is not None:
            d2ferr2 = (d2.serr/d2.data)**2
        else:
            d2err2 = 0.5*(getattr(d2, 'perr', 0)**2 + getattr(d2, 'nerr', 0)**2)
            d2ferr2 = d2err2 / d2.data**2

        d1.serr = N.sqrt(d1ferr2[:minlen] + d2ferr2[:minlen]) * N.abs(ratio)
        d1.perr = d1.nerr = None

    # the divided points
    d1.data = ratio

@registerTransformPlugin(
    'Div', _('Divide dataset'), category=catdiv,
    description=_('Divide output dataset [outds] by value or dataset [val]'))
def divDiv(dss):
    def Div(outds, val):
        idx = dsCodeToIdx(outds)
        if isDataset1D(val):
            _divideDatasetDataset(dss[idx], val)
        else:
            _multiplyDatasetScalar(dss[idx], 1./val)
    return Div

@registerTransformPlugin(
    'DivX', _('Divide X'), category=catdiv,
    description=_('Divide X dataset by value or dataset [val]'))
def divDivX(dss):
    return lambda val: divDiv(dss)('x', val)

@registerTransformPlugin(
    'DivY', _('Divide Y'), category=catdiv,
    description=_('Divide Y dataset by value or dataset [val]'))
def divDivY(dss):
    return lambda val: divDiv(dss)('y', val)

# helper function for dividing by function of dataset
def _divfn(ds, fn):
    data = ds.data
    findata = data[N.isfinite(data)]
    f = 1./fn(findata) if len(findata)>0 else 1
    ds.data *= f
    if ds.serr is not None:
        ds.serr *= f
    if ds.perr is not None:
        ds.perr *= f
    if ds.nerr is not None:
        ds.nerr *= f

## DivMax

@registerTransformPlugin(
    'DivMax', _('Divide dataset by maximum value'), category=catdiv,
    description=_('Divide output dataset [outds] by its maximum value'))
def divDivMax(dss):
    return lambda outds: _divfn(dss[dsCodeToIdx(outds)], N.max)

@registerTransformPlugin(
    'DivMaxX', _('Divide X by maximum value'), category=catdiv,
    description=_('Divide dataset X by its maximum value'))
def divDivMaxX(dss):
    return lambda: _divfn(dss[0], N.max)

@registerTransformPlugin(
    'DivMaxY', _('Divide Y by maximum value'), category=catdiv,
    description=_('Divide datset Y by its maximum value'))
def divDivMaxY(dss):
    return lambda: _divfn(dss[1], N.max)

## DivMean

@registerTransformPlugin(
    'DivMean', _('Divide dataset by mean value'), category=catdiv,
    description=_('Divide output dataset [outds] by its mean value'))
def divDivMean(dss):
    return lambda outds: _divfn(dss[dsCodeToIdx(outds)], N.mean)

@registerTransformPlugin(
    'DivMeanX', _('Divide X by mean value'), category=catdiv,
    description=_('Divide dataset X by its mean value'))
def divDivMeanX(dss):
    return lambda: _divfn(dss[0], N.mean)

@registerTransformPlugin(
    'DivMeanY', _('Divide Y by mean value'), category=catdiv,
    description=_('Divide dataset Y by its mean value'))
def divDivMeanY(dss):
    return lambda: _divfn(dss[1], N.mean)

## DivStd

@registerTransformPlugin(
    'DivStd', _('Divide dataset by standard deviation'), category=catdiv,
    description=_('Divide dataset [outds] by its standard deviation'))
def divDivStd(dss):
    return lambda outds: _divfn(dss[dsCodeToIdx(outds)], N.std)

@registerTransformPlugin(
    'DivStdX', _('Divide X by standard deviation'), category=catdiv,
    description=_('Divide dataset X by its standard deviation'))
def divDivStdX(dss):
    return lambda: _divfn(dss[0], N.std)

@registerTransformPlugin(
    'DivStdY', _('Divide Y by standard deviation'), category=catdiv,
    description=_('Divide dataset Y by its standard deviation'))
def divDivStdY(dss):
    return lambda: _divfn(dss[1], N.std)


## DivSum

@registerTransformPlugin(
    'DivSum', _('Divide dataset by sum'), category=catdiv,
    description=_('Divide dataset [outds] by its sum'))
def divDivSum(dss):
    return lambda outds: _divfn(dss[dsCodeToIdx(outds)], N.sum)

@registerTransformPlugin(
    'DivSumX', _('Divide X by sum'), category=catdiv,
    description=_('Divide dataset X by its sum'))
def divDivSumX(dss):
    return lambda: _divfn(dss[0], N.sum)

@registerTransformPlugin(
    'DivSumY', _('Divide Y by sum'), category=catdiv,
    description=_('Divide dataset Y by its sum'))
def divDivSumY(dss):
    return lambda: _divfn(dss[1], N.sum)


###############################################################################
## Normalise

@registerTransformPlugin(
    'NormRange', _('Normalise output dataset to be between 0 and 1'), category=catrange,
    description=_('Normalise dataset [outds] to be between 0 and 1'))
def rangeNormRange(dss):
    def NormRange(outds):
        idx = dsCodeToIdx(outds)
        data = dss[idx].data
        findata = data[N.isfinite(data)]
        if len(findata) > 0:
            minv = N.min(findata)
            maxv = N.max(findata)
            dss[idx].data[:] = (data-minv) * (1./(maxv-minv))
    return NormRange

@registerTransformPlugin(
    'NormRangeX', _('Normalise dataset X to be between 0 and 1'), category=catrange,
    description=_('Normalise dataset X to be between 0 and 1'))
def rangeNormX(dss):
    return lambda: rangeNormRange(dss)('x')

@registerTransformPlugin(
    'NormRangeY', _('Normalise dataset Y to be between 0 and 1'), category=catrange,
    description=_('Normalise dataset Y to be between 0 and 1'))
def rangeNormY(dss):
    return lambda: rangeNormRange(dss)('y')

###############################################################################
## Log10, Log, Exp, Pow

def _applyFn(ds, fun):
    prange = nrange = None
    if ds.serr is not None:
        prange = ds.data+ds.serr
        nrange = ds.data-ds.serr
    if ds.nerr is not None:
        nrange = ds.data+ds.nerr
    if ds.perr is not None:
        prange = ds.data+ds.perr

    ds.data = fun(ds.data)
    if prange is not None:
        ds.perr = fun(prange) - ds.data
    if nrange is not None:
        ds.nerr = fun(nrange) - ds.data
    ds.serr = None

## Log10

@registerTransformPlugin(
    'Log10X', _('Log10 of X'), category=catlog,
    description=_('Set X dataset to be log10 of input X'))
def logLog10X(dss):
    def Log10X():
        _applyFn(dss[0], N.log10)
    return Log10X

@registerTransformPlugin(
    'Log10Y', _('Log10 of Y'), category=catlog,
    description=_('Set Y dataset to be log10 of input Y'))
def logLog10Y(dss):
    def Log10Y():
        _applyFn(dss[1], N.log10)
    return Log10Y

@registerTransformPlugin(
    'Log10', _('Log10 of dataset'), category=catlog,
    description=_('Set output dataset [outds] to be log10 of input'))
def logLog10(dss):
    def Log10(outds):
        _applyFn(dss[dsCodeToIdx(outds)], N.log10)
    return Log10

## Log

@registerTransformPlugin(
    'LogX', _('Natural log of X'), category=catlog,
    description=_('Set X dataset to be natural log of input X'))
def logLogX(dss):
    def LogX():
        _applyFn(dss[0], N.log)
    return LogX

@registerTransformPlugin(
    'LogY', _('Natural log of Y'), category=catlog,
    description=_('Set Y dataset to be natural log of input Y'))
def logLogY(dss):
    def LogY():
        _applyFn(dss[1], N.log)
    return LogY

@registerTransformPlugin(
    'Log', _('Natural log of dataset'), category=catlog,
    description=_('Set output dataset [outds] to be natural log of input'))
def logLog(dss):
    def Log(outds):
        _applyFn(dss[dsCodeToIdx(outds)], N.log)
    return Log

## Exp

@registerTransformPlugin(
    'ExpX', _('Calculate exponential of X'), category=catlog,
    description=_('Set X dataset to be e^X'))
def logExpX(dss):
    def ExpX():
        _applyFn(dss[0], N.exp)
    return ExpX

@registerTransformPlugin(
    'ExpY', _('Calculate exponential of Y'), category=catlog,
    description=_('Set Y dataset to be e^Y'))
def logExpY(dss):
    def ExpY():
        _applyFn(dss[1], N.exp)
    return ExpY

@registerTransformPlugin(
    'Exp', _('Calculate exponential of dataset'), category=catlog,
    description=_('Calculate exponential of output dataset [outds]'))
def logExp(dss):
    def Exp(outds):
        _applyFn(dss[dsCodeToIdx(outds)], N.exp)
    return Exp

## Exp10

@registerTransformPlugin(
    'Exp10X', _('Raise 10 to the power of X'), category=catlog,
    description=_('Set X dataset to be 10^X'))
def logExp10X(dss):
    def Exp10X():
        _applyFn(dss[0], lambda x: 10**x)
    return Exp10X

@registerTransformPlugin(
    'Exp10Y', _('Raise 10 to the power of Y'), category=catlog,
    description=_('Set Y dataset to be 10^Y'))
def logExp10Y(dss):
    def Exp10Y():
        _applyFn(dss[1], lambda x: 10**x)
    return Exp10Y

@registerTransformPlugin(
    'Exp10', _('Raise 10 to the power of dataset'), category=catlog,
    description=_('Raise 10 to the power of output dataset [outds]'))
def logExp10(dss):
    def Exp10(outds):
        _applyFn(dss[dsCodeToIdx(outds)], lambda x: 10**x)
    return Exp10

## ExpV

@registerTransformPlugin(
    'ExpVX', _('Raise value to the power of X dataset'), category=catlog,
    description=_('Raise value [val] to the power of X dataset'))
def logExpVX(dss):
    def ExpVX(val):
        _applyFn(dss[0], lambda x: val**x)
    return ExpVX

@registerTransformPlugin(
    'ExpVY', _('Raise value to the power of Y dataset'), category=catlog,
    description=_('Raise value [val] to the power of Y dataset'))
def logExpVY(dss):
    def ExpVY(val):
        _applyFn(dss[1], lambda x: val**x)
    return ExpVY

@registerTransformPlugin(
    'ExpV', _('Raise value to the power of dataset'), category=catlog,
    description=_('Raise value [val] to the power of output dataset [outds]'))
def logExpV(dss):
    def ExpV(val, outds):
        _applyFn(dss[dsCodeToIdx(outds)], lambda x: val**x)
    return ExpV

## Pow

@registerTransformPlugin(
    'PowX', _('Raise X dataset to power'), category=catmul,
    description=_('Raise X dataset to power [val]'))
def mulPowX(dss):
    def PowX(val):
        _applyFn(dss[0], lambda x: x**val)
    return PowX

@registerTransformPlugin(
    'PowY', _('Raise Y dataset to power'), category=catmul,
    description=_('Raise Y dataset to power [val]'))
def mulPowY(dss):
    def PowY(val):
        _applyFn(dss[1], lambda x: x**val)
    return PowY

@registerTransformPlugin(
    'Pow', _('Raise dataset to power'), category=catmul,
    description=_('Raise dataset [outds] to power [val]'))
def mulPowX(dss):
    def Pow(outds, val):
        _applyFn(dss[dsCodeToIdx(outds)], lambda x: x**val)
    return Pow

## Apply

@registerTransformPlugin(
    'ApplyX', _('Apply function to X dataset'), category=catapply,
    description=_('Apply function [fn] to X dataset'))
def applyApplyX(dss):
    def ApplyX(fn):
        _applyFn(dss[0], fn)
    return ApplyX

@registerTransformPlugin(
    'ApplyY', _('Apply function to Y dataset'), category=catapply,
    description=_('Apply function [fn] to Y dataset'))
def applyApplyY(dss):
    def ApplyY(fn):
        _applyFn(dss[1], fn)
    return ApplyY

@registerTransformPlugin(
    'Apply', _('Apply function to dataset'), category=catapply,
    description=_('Apply function [fn] to output dataset [outds]'))
def applyApply(dss):
    def Apply(outds, fn):
        _applyFn(dss[dsCodeToIdx(outds)], fn)
    return Apply


###############################################################################
## Clip

def _clip_dataset(d, minv, maxv):
    """Internal dataset clip range."""
    data = d.data
    if d.serr is not None:
        prange = d.data+d.serr
        nrange = d.data-d.serr
    else:
        prange = d.perr+d.data if d.perr is not None else None
        nrange = d.nerr+d.data if d.nerr is not None else None

    d.data = N.clip(data, minv, maxv)
    if prange is not None:
        d.perr = N.clip(prange, minv, maxv) - d.data
    if nrange is not None:
        d.nerr = N.clip(nrange, minv, maxv) - d.data
    d.serr = None

@registerTransformPlugin(
    'Clip', _('Clip dataset'), category=catrange,
    description=_('Clip output dataset [outds] to lie within range [minv to maxv]'))
def rangeClip(dss):
    def Clip(outds, minv=-N.inf, maxv=N.inf):
        idx = dsCodeToIdx(outds)
        _clip_dataset(dss[idx], minv, maxv)
    return Clip

@registerTransformPlugin(
    'ClipX', _('Clip X dataset'), category=catrange,
    description=_('Clip X dataset values to lie within range [minv to maxv]'))
def rangeClip(dss):
    def ClipX(minv=-N.inf, maxv=N.inf):
        _clip_dataset(dss[0], minv, maxv)
    return ClipX

@registerTransformPlugin(
    'ClipY', _('Clip Y dataset'), category=catrange,
    description=_('Clip Y dataset values to lie within range [minv to maxv]'))
def rangeClip(dss):
    def ClipY(minv=-N.inf, maxv=N.inf):
        _clip_dataset(dss[1], minv, maxv)
    return ClipY

###############################################################################
# Geometry

@registerTransformPlugin(
    'Rotate', _('Rotate coordinates'), category=catgeom,
    description=_('Rotate coordinates by angle in radians [angle_rad], with '
                  'optional centre [cx,cy]'))
def geometryRotate(dss):
    def Rotate(angle_rad, cx=0, cy=0):
        xvals = dss[0].data - cx
        yvals = dss[1].data - cy

        nx = N.cos(angle_rad)*xvals - N.sin(angle_rad)*yvals + cx
        ny = N.sin(angle_rad)*xvals + N.cos(angle_rad)*yvals + cy

        dss[0].data = nx
        dss[1].data = ny
        dss[0].serr = dss[0].perr = dss[0].nerr = None
        dss[1].serr = dss[1].perr = dss[1].nerr = None
    return Rotate

@registerTransformPlugin(
    'Translate', _('Translate coordinates'), category=catgeom,
    description=_('Translate coordinates by given shifts [dx,dy]'))
def geometryTranslate(dss):
    def Translate(dx, dy):
        dss[0].data += dx
        dss[1].data += dy
    return Translate

###############################################################################
# Filter

@registerTransformPlugin(
    'Thin', _('Thin values'), category=catfilt,
    description=_('Thin values by step [step] and optional starting index ([start] from 0)'))
def filteringThin(dss):
    def Thin(step, start=0):
        for ds in dss:
            if ds is None:
                continue
            for attr in 'data', 'serr', 'perr', 'nerr':
                if getattr(ds, attr, None) is not None:
                    setattr(ds, attr, getattr(ds, attr)[start::step])
    return Thin

@registerTransformPlugin(
    'IndexRange', _('Select index range'), category=catfilt,
    description=_(
        'Select values between index ranges from start [start], '
        'with optional end index [end] and step '
        '[step] (Python-style indexing from 0)'))
def filteringRange(dss):
    def IndexRange(start, end=None, step=None):
        for ds in dss:
            if ds is None:
                continue
            for attr in 'data', 'serr', 'perr', 'nerr':
                if getattr(ds, attr, None) is not None:
                    setattr(ds, attr, getattr(ds, attr)[start:end:step])
    return IndexRange