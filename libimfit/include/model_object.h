/** @file
 * \brief Class declaration for ModelObject
 */
/*   Abstract base class interface definition for model_object.cpp [imfit]
 *
 * This is the abstract base class for 1D and 2D "model" objects.
 * 
 */


// CLASS ModelObject [base class]:

#ifndef _MODEL_OBJ_H_
#define _MODEL_OBJ_H_

#include <vector>
#include <string>

#include "definitions.h"
#include "function_object.h"
#include "psf_interpolators.h"
#include "convolver.h"
#include "oversampled_region.h"
#include "psf_oversampling_info.h"
#include "param_struct.h"

using namespace std;


// assume that all methods are "common" to both 2D (base) and 1D (derived) versions,
// unless otherwise stated

/// \brief Main class holding data, model information, and code for generating
///        model images, computing chi^2, etc.
class ModelObject
{
  public:
    ModelObject( );

    virtual ~ModelObject();


    void SetVerboseLevel( int verbosity );

    void SetDebugLevel( int debuggingLevel );
    
    void SetMaxThreads( int maxThreadNumber );

    void SetOMPChunkSize( int chunkSize );
    
    
    // Adds a new FunctionObject pointer to the internal vector
    virtual int AddFunction( FunctionObject *newFunctionObj_ptr );
    
    // 2D only
    int SetupPsfInterpolation( int interpolationType=kInterpolator_bicubic );

    // common, but Specialized by ModelObject1D
    virtual void DefineFunctionBlocks( vector<int>& functionStartIndices );
    
    
    // 1D only
    virtual void AddDataVectors( int nDataValues, double *xValVector, 
    						double *yValVector, bool magnitudeData ) { nDataVals = nDataValues; };

    // Probably 1D only, but might be usable by 2D version later...
    virtual void SetZeroPoint( double zeroPointValue );


    // 2D only
    void AddParameterInfo( mp_par  *inputParameterInfo );
    void AddParameterInfo( vector<mp_par> inputParameterInfo );
 
	// 2D only
    int AddImageDataVector( double *pixelVector, int nImageColumns, int nImageRows );

	// 2D only
    void AddImageCharacteristics( double imageGain, double readoutNoise, double expTime, 
    							int nCombinedImages, double originalSkyBackground );
    
    // 2D only
    void AddImageOffsets( int offset_X0, int offset_Y0 );
    
    // 2D only [used by model_object_multimage.cpp]
    std::tuple<int, int> GetImageOffsets( );

	// 2D only
    int SetupModelImage( int nImageColumns, int nImageRows );
    
	// 2D only
    virtual void AddErrorVector( long nDataValues, int nImageColumns, int nImageRows,
                         double *pixelVector, int inputType );

    // 1D only
    virtual void AddErrorVector1D( int nDataValues, double *pixelVector, int inputType ) { ; };

    // 1D only
    virtual int AddMaskVector1D( long nDataValues, double *inputVector, int inputType ) { return 0; };
    
	// 2D only
    virtual int GenerateErrorVector( );

	// 2D only
    virtual void GenerateExtraCashTerms( );

	// 2D only
    virtual int AddMaskVector( long nDataValues, int nImageColumns, int nImageRows,
                         double *pixelVector, int inputType );

	// 2D only
    int AddPSFVector( long nPixels_psf, int nColumns_psf, int nRows_psf,
                         double *psfPixels, bool normalizePSF=true );

 	// 2D only [this will eventually replace AddOversampledPSFVector]
    int AddOversampledPsfInfo( PsfOversamplingInfo *oversampledPsfInfo );

    // 1D only
    virtual int AddPSFVector1D( int nPixels_psf, double *xValVector, double *yValVector ) { return 0; };
    
	// 2D only [1D maybe needs something similar, but with diff. interface]
    virtual void ApplyMask( );


    // common, but specialized by ModelObject1D
    virtual void CreateModelImage( double params[] );
    
    // 2D only
    void UpdateWeightVector( );

     // common, not specialized (currently not specialized or used by ModelObject1d)
    virtual double ComputePoissonMLRDeviate( long i, long i_model );

    // Specialized by ModelObject1D
    virtual void ComputeDeviates( double yResults[], double params[] );


    virtual int UseModelErrors( );

    virtual int UseCashStatistic( );

    virtual void UsePoissonMLR( );
 
    virtual int WhichFitStatistic( bool verbose=false );
 
    virtual double GetFitStatistic( double params[] );
    
    virtual double ChiSquared( double params[] );
    
    virtual double CashStatistic( double params[] );
    
    
    // common, but specialized by ModelObject1D
    virtual void PrintDescription( );

    // common, but specialized by ModelObject1D
    virtual int Dimensionality( ) { return 2;};

    void GetFunctionNames( vector<string>& functionNames );

    void  GetImageOffsets( double params[] );
    
    virtual string GetParamHeader( );

    // common, but Specialized by ModelObject1D
    virtual int PrintModelParamsToStrings( vector<string> &stringVector, double params[], 
									double errs[], const char *prefix="", bool printLimits=false );

    virtual string PrintModelParamsHorizontalString( const double params[], const string& separator="\t" );

    // 2D only
    void PrintImage( double *pixelVector, int nColumns, int nRows );

    // 1D only
    virtual void PrintVector( double *theVector, int nVals ) { ; };

    virtual void PrintInputImage( );

    virtual void PrintModelImage( );

    virtual void PrintWeights( );

    virtual void PrintMask( );


    // common, but specialized by ModelObject1D
    virtual void PopulateParameterNames( );

    // common, but specialized by ModelObject1D
    virtual int FinalSetupForFitting( );

    string& GetParameterName( int i );

    int GetNFunctions( );

    int GetNParams( );

    // Returns total number of data values
    long GetNDataValues( );

    // Returns total number of *non-masked* data values
    virtual long GetNValidPixels( );

	// 2D only
    bool HasPSF( );
    bool HasOversampledPSF( );
    bool HasMask( );

	// 2D only
    virtual double * GetModelImageVector( );

	// 2D only
    double * GetExpandedModelImageVector( );

	// 2D only
    double * GetResidualImageVector( );

	// 2D only
    double * GetWeightImageVector( );

	// 2D only
    double * GetDataVector( );

	// 2D only
    double FindTotalFluxes(double params[], int xSize, int ySize, 
    											double individualFluxes[] );

    // Generate a model image using *one* of the FunctionObjects (the one indicated by
    // functionIndex) and the input parameter vector; returns pointer to modelVector.
    double * GetSingleFunctionImage( double params[], int functionIndex );

    // 1D only
    virtual int GetModelVector( double *profileVector ) { return -1; };


    // mainly for use by ModelObjectMultImage
    virtual int GetNImages( ) { return 1; };


    virtual int UseBootstrap( );
    
    virtual int MakeBootstrapSample( );


  protected:
    bool CheckParamVector( int nParams, double paramVector[] );
    
    bool CheckWeightVector( );
    
    bool VetDataVector( );



  private:
    Convolver  *psfConvolver;
  
  protected:  // same as private, except accessible to derived classes
    long  nDataVals, nValidDataVals, nModelVals;
    int  nDataColumns, nDataRows, nCombined;
    int  nModelColumns, nModelRows, nPSFColumns, nPSFRows;
	double  zeroPoint;
	double  gain, readNoise, exposureTime, originalSky, effectiveGain;
	double  readNoise_adu_squared;
    int  debugLevel, verboseLevel;
    int  maxRequestedThreads, ompChunkSize;
    bool  dataValsSet;
    bool  modelVectorAllocated, weightVectorAllocated, maskVectorAllocated;
    bool  standardWeightVectorAllocated;
    bool  residualVectorAllocated, outputModelVectorAllocated;
    bool  fblockStartFlags_allocated;
    bool  modelImageSetupDone;
    bool  modelImageComputed;
    bool  weightValsSet, maskExists, doBootstrap, bootstrapIndicesAllocated;
    bool  doConvolution, pointSourcesPresent;
    bool  modelErrors, dataErrors, externalErrorVectorSupplied;
    bool  useCashStatistic, poissonMLR;
    bool  deviatesVectorAllocated;   // for chi-squared calculations
    bool  extraCashTermsVectorAllocated;
    bool  localPsfPixels_allocated;
    bool  zeroPointSet;
    int  nFunctions, nFunctionBlocks, nFunctionParams, nParamsTot;
    double  *dataVector;
    double  *weightVector, *standardWeightVector;
    double  *maskVector;
    double  *modelVector;
    double  *deviatesVector;
    double  *residualVector;
    double  *outputModelVector;
    double  *extraCashTermsVector;
    double  *localPsfPixels;
    long  *bootstrapIndices;
    bool  *fblockStartFlags;
    vector<FunctionObject *> functionObjects;
    vector<int> paramSizes;
    vector<string>  parameterLabels;
    vector<SimpleParameterInfo> parameterInfoVect;
    int  imageOffset_X0, imageOffset_Y0;
    
    PsfInterpolator *psfInterpolator;
    bool  psfInterpolator_allocated;
    
    // stuff for ovsersampled PSF convolution
    Convolver  *psfConvolver_osamp;
    int  nPSFColumns_osamp, nPSFRows_osamp;
    int  nOversampledModelColumns, nOversampledModelRows;
    long  nOversampledModelVals;
    bool  oversampledRegionsExist;
    int  nOversampledRegions;
    vector<OversampledRegion *>oversampledRegionsVect;

  
};

#endif   // _MODEL_OBJ_H_
