"""
Modification of Andre's "config.py" (originally created 19 Sep 2013).
"""

from .model import ParameterDescription, FunctionDescription, FunctionSetDescription, ModelDescription

__all__ = ['parse_config_file', 'parse_config']


commentChar = '#'
x0_str = 'X0'
y0_str = 'Y0'
function_str = 'FUNCTION'
fixed_str = 'fixed'

# The following are the currently recognized config-file image options (see
# imfit_main.cpp) and the functions for transforming string values from a
# config file:
recognizedOptions = {"GAIN": float, "READNOISE": float, "EXPTIME": float,
                    "NCOMBINED": int, "ORIGINAL_SKY": float}
recognizedOptionNames = list(recognizedOptions.keys())



#FIXME: (PE) Need to handle case of optional image-function parameters


def parse_config_file( fname ):
    """
    Read an Imfit model configuration file.

    Parameters
    ----------
    fname : string
        Path to the model configuration file.

    Returns
    -------
    model : :class:`~imfit.ModelDescription`
        A model description object.

    See also
    --------
    parse_config
    """
    with open(fname) as fd:
        return parse_config(fd.readlines())




def parse_config( lines ):
    """
    Parses an Imfit model configuration from a list of strings.

    Parameters
    ----------
    lines : list of strings
        String representantion of Imfit model configuration.

    Returns
    -------
    model : :class:`~imfit.ModelDescription`
        A model description object.

    See also
    --------
    parse_config_file
    """
    lines = clean_lines(lines)

    model = ModelDescription()

    block_start = 0
    id_fs = 0   # number of current function block ("function set")
    for i in range(block_start, len(lines)):
        if lines[i].startswith(x0_str):
            if block_start == 0:
                options = read_options(lines[block_start:i])
                model.options.update(options)
            else:
                funcSetName = "fs{0:d}".format(id_fs)
                model.addFunctionSet(read_function_set(funcSetName, lines[block_start:i]))
                id_fs += 1
            block_start = i
    funcSetName = "fs{0:d}".format(id_fs)
    model.addFunctionSet(read_function_set(funcSetName, lines[block_start:i + 1]))
    return model




def clean_lines( lines ):
    clean = []
    for line in lines:
        # Clean the comments.
        line = line.split(commentChar, 1)[0]
        # Remove leading and trailing whitespace.
        line = line.strip()
        # Skip the empty lines.
        if line == '':
            continue
        clean.append(line)
    return clean




def read_options( lines ):
    """
    Parse the lines from an Imfit configuration file which contain image-description
    parameters (GAIN, READ_NOISE, etc.).

    Parameters
    ----------
    lines : list of strings
        String representantion of Imfit model configuration.

    Returns
    -------
    config : dict mapping parameter names to numerical values
        e.g, {"GAIN": 4.56, "ORIGINAL_SKY": 233.87}
    """
    config = {}
    for line in lines:
        # Options are key-value pairs.
        pieces = line.split()
        if len(pieces) < 2:
            msg = "Expected image-description parameter and value"
            raise ValueError(msg)
        k, val = pieces[0], pieces[1]
        if k in [x0_str, y0_str, function_str]:
            msg = "Expected image-description parameter name, but got {0:s} instead.".format(k)
            raise ValueError(msg)
        if k in recognizedOptionNames:
            val = recognizedOptions[k](val)
            config[k] = val
        else:
            print("Ignoring unrecognized image-description parameter \"{0}\"".format(k))

    return config




def read_function_set( name, lines ):
    """
    Reads in lines of text corresponding to a function block (or 'set') containing
    X0,Y0 coords and one or more image functions with associated parameter settings.

    Parameters
    ----------
    name : string
    
    lines : list of string
        lines from configuration file
    
    Returns
    -------
    fs : FunctionSetDescription
        Contains extracted information about function block, functions, and their parameters
    """
    # A function set starts with X0 and Y0 parameters.
    x0 = read_parameter(lines[0])
    y0 = read_parameter(lines[1])
    if x0.name != x0_str or y0.name != y0_str:
        raise ValueError('A function set must begin with the parameters X0 and Y0.')
    fs = FunctionSetDescription(name)
    fs.x0 = x0
    fs.y0 = y0
    block_start = 2
    for i in range(block_start, len(lines)):
        # Functions for a given set start with FUNCTION.
        if i == block_start or not lines[i].startswith(function_str):
            continue
        fs.addFunction(read_function(lines[block_start:i]))
        block_start = i
    # Add the last function in the set.
    fs.addFunction(read_function(lines[block_start:i + 1]))
    return fs




def read_function( lines ):
    """
    Reads in lines of text corresponding to a function declaration and
    initial values, ranges, etc. for its parameters.

    Parameters
    ----------
    lines : list of string
        lines from configuration file; initial line is of form 'FUNCTION <func-name>'
        with subsequent lines (assumed to be in correct order) describing
        parameter values and (optionally) 'fixed' or lower,upper limits
    
    Returns
    -------
    func : FunctionDescription
        Contains extracted information about function and its parameters
    """
    # First line contains the function name.
    pieces = lines[0].split()
    test_function_str = pieces[0]
    if test_function_str != function_str:
        raise ValueError('Function definition must begin with FUNCTION.')
    if len(pieces) <= 1:
        raise ValueError('No function name was supplied.')
    name  = pieces[1].strip()
    func = FunctionDescription(name)
    # Read the function parameters.
    for i in range(1, len(lines)):
        func.addParameter(read_parameter(lines[i]))

    # FIXME: check function and parameters.
    return func




def read_parameter( line ):
    """
    Reads in a single text line containing parameter info, parses it, and
    returns a ParameterDescription object with the parameter info.

    Parameters
    ----------
    line : string
        line from configuration file specifying parameter name, initial value,
        and (optionally) 'fixed' or lower,upper limits
    
    Returns
    -------
    ParameterDescription instance
        Contains extracted information about parameter
    """
    llimit = None
    ulimit = None
    fixed = False

    # Format:
    # PAR_NAME	  VALUE	  [ "fixed" | LLIMIT,ULIMIT ] [# comments]
    goodLine = line.split("#")[0]
    pieces = goodLine.split()
    if len(pieces) <= 1:
        raise ValueError("Line must have at least two elements (parameter name, value).")
    name = pieces[0]
    value = float(pieces[1])
    if len(pieces) > 2:
        predicate = pieces[2]
        if predicate == fixed_str:
            fixed = True

        elif ',' in predicate:
            llimit, ulimit = predicate.split(',')
            llimit = float(llimit)
            ulimit = float(ulimit)
            if llimit > ulimit:
                raise ValueError('lower limit ({0:f}) is larger than upper limit ({1:f})'.format(llimit, ulimit))
        else:
            raise ValueError("Malformed limits on parameter line.")

    return ParameterDescription(name, value, llimit, ulimit, fixed)

