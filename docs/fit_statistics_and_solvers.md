# Fitting an Image (Choosing Fit Statistics and Solvers)

In the example code below, we assume that an instance of the fitting.Imfit class has
already been created and supplied with the necessary ModelDescription.

For example,

    imfit_fitter = pyimfit.Imfit(someModelDescription)
    

## Finding the best-fit solution by minimizing a fit statistic

Fitting a model to an image in PyImfit involves calculating a model image and then
comparing it pixel-by-pixel with a data image to derive a summary "fit statistic" (based
on some total likelihood value). The goal is to *minimize* the fit statistic (which corresponds
to maximizing the likelihood). This is done
by iteratively adjusting the parameters of the model and recomputing the fit statistic
until convergence is achieved; the algorithm which oversees this process is called
a "minimizer" or "solver".


## Fit statistics (chi^2 and all that)

Which fit statistic to use depends in part on your data source, and so is determined as part
of the `loadData` method of the Imfit class.

1. Chi^2 Statistics

   A. Sigmas estimated from the data values
   
   B. Sigmas estimated from the model values
   
   C. Sigmas from a pre-existing error/uncertainty/variance image


To specify model-based chi^2 as the fit statistic

    imfit_fitter.loadData(imageData, ..., use_model_for_errors=True)

To supply your own error/uncertainty map

    imfit_fitter.loadData(imageData, error=errorImageData, ...)
    imfit_fitter.loadData(imageData, error=errorImageData, error_type="variance", ...)

**TBD:** Gain; sky background; read noise


2. Pure Poisson Statistics


To specify Poisson-MLR as the fit statistic

    imfit_fitter.loadData(imageData, ..., use_poisson_mlr=True)



## Minimizers/Solvers

To actually find the best fit, you tell the Imfit object to find the minimum fit-statistic
value, using a particular minimization algorithm.

PyImfit has three minimizers (a.k.a. solvers):

   - Levenberg-Marquardt: This is the default, and is by far the fastest; it has the
   drawback of being the most prone to being trapped in local minima in the fit-statistic
   landscape. It requires initial guesses for each parameter value.
   
         imfit_fitter.DoFit()
         imfit_fitter.DoFit(solver="LM")
   
   - Nelder-Mead Simplex: This is a slower algorithm, generally held to be less likely to
   be trapped in local fit-statistic minima. Like Levenberg-Marquardt, it
   requires initial guesses for each parameter value.

    imfit_fitter.DoFit(solver="NM")

   - Differential Evolution: This is a genetic-algorithms approach, and is the
   slowest of all the algorithms. Unlike the other two solvers, it requires lower
   and upper parameter *limits* for all non-fixed parameters. Initial guesses
   for the non-fixed parameter values are *ignored*.

    imfit_fitter.DoFit(solver="DE")

Roughly speaking, the Nelder-Mead simplex minimizer is about an order of magnitude slower
than Levenberg-Marquardt, and Differential Evolution is itself about an order of magnitude
slower than Nelder-Mead simplex.


## More Information

For more information:

   - [Section 4](https://iopscience.iop.org/article/10.1088/0004-637X/799/2/226#apj506756s4) of Erwin (2015) [(ADS link)](https://ui.adsabs.harvard.edu/abs/2015ApJ...799..226E/abstract)

   - Chapter 9 of [the Imfit manual (PDF)](https://www.mpe.mpg.de/~erwin/resources/imfit/imfit_howto.pdf)
