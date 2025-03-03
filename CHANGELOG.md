# Change Log for PyImfit

(Formatting and design based on Olivier Lacan's [Keep a CHANGELOG](http://keepachangelog.com/))

**NOTE:** PyImfit is currently in a state of rapid development; minor-version-number
changes may contain significant changes to the API.


## 0.8.8 -- 2019-08-25
## Added
Imfit objects now return a FitResult object containing summary information about the
fit when the doFit method is called.

Added MakePsfOversampler() convenience function to create PsfOversampling objects
(automatically applies FixImage to oversampled PSF image array).
    
### Changed
Added automatic conversion (via FixImage) of input PSF images when instantiating Imfit objects.


## 0.8.7 -- 2019-08-20
### Added
Imfit.runBootstrap can now optionally return a list of parameter names (annotated by function-set
number for X0,Y0 and by function number for function parameters) along with the numpy array
of bootstrap results.

### Changed
The FunctionSetDescription and ModelDescription classes now have both
functionList and functionNameList methods; the former returns a list of FunctionDescription
objects, while the latter returns a list of function *names* (strings).

### Fixed
Boolean mask images (including boolean masks that are part of a numpy MaskedArray) are
now properly handled.




## 0.8.6 -- 2019-08-09
### Added
User can now specify verbosity level of fit via `verbose` keyword in Imfit.doFit().

Data, PSF, mask, and error images added to an Imfit instance are automatically processed
by the FixImage function, so it is no longer necessary to do this prior to adding them
to an Imfit instance.

### Changed

### Fixed
The (limited) API documentation is now available on readthedocs.org! (After insane kludging with
post-processed HTML...)



## 0.8.5 -- 2019-08-07

Initial public release of PyImfit.
