#!/usr/bin/python

import argparse
import collections
import sys

import numpy
from scipy import stats

class Symbol(object):
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return 'Symbol({!r})'.format(self._name)

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self._name == other._name
        else:
            return False

CONFIDENCE_WINDOW = 'confidence'


PARSER = argparse.ArgumentParser(description='Utility to work our various running averages')
PARSERS = PARSER.add_subparsers(dest='method')
subparser = PARSERS.add_parser('confidence', help='Include a window of values before the point until we are confidence of the value')


AverageResult = collections.namedtuple('AverageResult', 'estimate')

CONFIDENCE_WINDOW_PARAMS = dict(
    required_confidence=0.95,
    required_threshold=0.95,
)


def main():
    result = run(sys.argv[1:], sys.stdin)
    if result is not None:
        print result
        sys.stdout.flush()

def run(args, in_file):
    args = PARSER.parse_args(args)
    values = map(float, in_file.readlines())
    result = []
    for average in running_average(values, args.method):
        result.append(str(average.estimate))
    return '\n'.join(result)

def running_average(values, method, **params):
    "Work out a running average using a particular method"
    if method == CONFIDENCE_WINDOW:
        unknown_params = set(params) - set(CONFIDENCE_WINDOW_PARAMS)
        params = fill_in_dict(params, CONFIDENCE_WINDOW_PARAMS)
        if unknown_params:
           raise Exception('CONFIDENCE WINDOW does not accept unknown parameters: {!r}'.format(unknown_params))
        return _confidence_average(values, **params)
    else:
        raise ValueError(method)

def _confidence_average(values, required_confidence, required_threshold):
    # This should really be using some sort of view
    # to avoid n**2 copying
    for i in range(len(values)):
        yield recent_confidence_interval(
            values[:i],
            required_confidence=required_confidence,
            required_threshold=required_threshold)

def recent_confidence_interval(values, required_confidence, required_threshold):
    for n in range(2, len(values) -1):
        # this probably doesn't want to be a view because it's normally small
        subset = values[len(values) - n:]
        upper, lower = confidence_interval(required_confidence, subset)
        mean = float(numpy.mean(subset))
        if required_threshold:
            return  AverageResult(estimate=mean)
    else:
        return AverageResult(estimate=None)

def confidence_interval(confidence, values):
    return stats.t.interval(confidence, len(values)-1, loc=numpy.mean(values), scale=stats.sem(values))

# Utility functions

def fill_in_dict(initial, default_values):
    result = initial.copy()
    for k, v in default_values.items():
        if k not in list(result.keys()):
            result[k] = v
    return result

if __name__ == '__main__':
	main()
