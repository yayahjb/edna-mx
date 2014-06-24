#
#    Project: mxv1
#             http://www.edna-site.org
#
#    Copyright (C) ESRF
#
#    Principal author:        Olof Svensson
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__author__ = "Olof Svensson"
__license__ = "GPLv3+"
__copyright__ = "ESRF"
__date__ = "20120711"
__status__ = "production"


"""
This control plugin will launch in parallel indexing with Labelit (EDPluginControlIndexingLabelitv1_0) 
and the EDPluginControlImageQualityIndicators.

The idea is to run labelit.distl at the same time as the Labelit indexing in order to not loose time 
for obtaining the image quality indicators.
"""

import os

from EDPluginControl import EDPluginControl
from EDActionCluster import EDActionCluster

from XSDataCommon import XSDataImage
from XSDataCommon import XSDataBoolean

from XSDataMXv1 import XSDataCollection
from XSDataMXv1 import XSDataCrystal
from XSDataMXv1 import XSDataExperimentalCondition
from XSDataMXv1 import XSDataIndexingInput
from XSDataMXv1 import XSDataString
from XSDataMXv1 import XSDataInputControlImageQualityIndicators


class EDPluginControlIndexingIndicatorsv1_1(EDPluginControl):
    """
    This control plugin will launch in parallel indexing with Labelit (EDPluginControlIndexingLabelitv1_0) 
    and the EDPluginControlImageQualityIndicators.
    
    The idea is to run labelit.distl at the same time as the Labelit indexing in order to not loose time 
    for obtaining the image quality indicators.

    - Input (same as current XSDataIndexingInput) :
        * dataCollection (XSDataCollection) 1..1
        * crystal (XSDataCrystal) 0..1
        * refinedExperimentalCondition (XSDataExperimentalCondition) 0..1
    
    - Output :
        * indexingResult : XSDataIndexingResult 0..1
        * imageQualityIndicators (XSDataImageQualityIndicators) 0..*
    """


    def __init__(self):
        EDPluginControl.__init__(self)
        self.setXSDataInputClass(XSDataCollection, "dataCollection")
        self.setXSDataInputClass(XSDataCrystal, "crystal")
        self.setXSDataInputClass(XSDataExperimentalCondition, "refinedExperimentalCondition")
        self.strPluginControlIndexingLabelit = "EDPluginControlIndexingLabelitv10"
        self.edPluginControlIndexingLabelit = None
        self.strControlledIndicatorsPluginName = "EDPluginControlImageQualityIndicatorsv1_5"
        self.edPluginControlIndicators = None


    def checkParameters(self):
        """
        Checks the mandatory parameter dataCollection
        """
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.checkParameters")
        self.checkMandatoryParameters(self.getDataInput("dataCollection")[0], "dataCollection")


    def preProcess(self, _edObject=None):
        EDPluginControl.preProcess(self)
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.preProcess")
        # Load and prepare the execution plugin
        self.edPluginControlIndexingLabelit = self.loadPlugin(self.strPluginControlIndexingLabelit)
        self.edPluginControlIndexingLabelit.setUseWarningInsteadOfError(True)
        xsDataIndexingInput = XSDataIndexingInput()
        xsDataIndexingInput.setDataCollection(self.getDataInput("dataCollection")[0])
        if self.hasDataInput("crystal"):
            xsDataIndexingInput.setCrystal(self.getDataInput("crystal")[0])
        if self.hasDataInput("refinedExperimentalCondition"):
            xsDataIndexingInput.setExperimentalCondition(self.getDataInput("refinedExperimentalCondition")[0])
        else:
            xsDataIndexingInput.setExperimentalCondition(self.getDataInput("dataCollection")[0].getSubWedge()[0].getExperimentalCondition())
        self.edPluginControlIndexingLabelit.setDataInput(xsDataIndexingInput)
        self.edPluginControlIndicators = self.loadPlugin(self.strControlledIndicatorsPluginName)
        # Extract the images from the data collections
        xsDataSubWedgeList = self.getDataInput("dataCollection")[0].getSubWedge()
        xsDataInputControlImageQualityIndicators = XSDataInputControlImageQualityIndicators()
        for xsDataSubWedge in xsDataSubWedgeList:
            xsDataImageList = xsDataSubWedge.getImage()
            for xsDataImage in xsDataImageList:
                xsDataInputControlImageQualityIndicators.addImage(xsDataImage)
        self.edPluginControlIndicators.setDataInput(xsDataInputControlImageQualityIndicators)


    def process(self, _edObject=None):
        EDPluginControl.process(self)
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.process")
        edActionCluster = EDActionCluster()
        edActionCluster.addAction(self.edPluginControlIndexingLabelit)
        edActionCluster.addAction(self.edPluginControlIndicators)
        self.edPluginControlIndexingLabelit.connectSUCCESS(self.doSuccessLabelitIndexing)
        self.edPluginControlIndexingLabelit.connectFAILURE(self.doFailureLabelitIndexing)
        self.edPluginControlIndicators.connectSUCCESS(self.doSuccessControlIndicators)
        self.edPluginControlIndicators.connectFAILURE(self.doFailureControlIndicators)
        edActionCluster.execute()
        edActionCluster.synchronize()


    def postProcess(self, _edObject=None):
        EDPluginControl.postProcess(self)
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.postProcess")
        # Retrieve the image quality indicators
        if not self.edPluginControlIndicators.isFailure():
            if self.edPluginControlIndicators.hasDataOutput():
                for xsDataImageQualityIndicators in self.edPluginControlIndicators.getDataOutput().getImageQualityIndicators():
                    self.setDataOutput(xsDataImageQualityIndicators, "imageQualityIndicators")


    def doSuccessLabelitIndexing(self, _edPlugin=None):
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.doSuccessLabelitIndexing")
        self.synchronizeOn()
        xsDataIndexingResult = self.edPluginControlIndexingLabelit.getDataOutput()
        xsDataCollection = self.getDataInput("dataCollection")[0]
        xsDataListImage = self.generateImageList(xsDataCollection)
        xsDataIndexingResult.setImage(xsDataListImage)
        xsDataIndexingResult.setLabelitIndexing(XSDataBoolean(False))
        self.setDataOutput(xsDataIndexingResult, "indexingResult")
#        self.generateExecutiveSummaryLabelit(_edPlugin)
        self.addExecutiveSummarySeparator()
        self.addExecutiveSummaryLine("Summary of indexing with %s :" % self.strControlledIndicatorsPluginName)
        self.addExecutiveSummaryLine("")
        self.appendExecutiveSummary(self.edPluginControlIndexingLabelit, "Labelit : ", _bAddSeparator=False)
        self.generateIndexingShortSummary(xsDataIndexingResult)
        self.synchronizeOff()


    def doFailureLabelitIndexing(self, _edPlugin=None):
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.doFailureLabelitIndexing")
        self.synchronizeOn()
        self.retrieveFailureMessages(_edPlugin, "EDPluginControlIndexingIndicatorsv1_1.doFailureLabelitIndexing")
        self.addErrorWarningMessagesToExecutiveSummary("Labelit indexing failure! Error messages: ")
        #self.generateExecutiveSummaryLabelit(_edPlugin)
        self.synchronizeOff()

    def doSuccessControlIndicators(self, _edPlugin=None):
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.doSuccessControlIndicators")
        self.synchronizeOn()
        self.generateExecutiveSummaryIndicators(self.edPluginControlIndicators)
        self.generateIndicatorsShortSummary(self.edPluginControlIndicators)
        self.synchronizeOff()


    def doFailureControlIndicators(self, _edPlugin=None):
        self.DEBUG("EDPluginControlIndexingIndicatorsv1_1.doFailureControlIndicators")
        self.synchronizeOn()
        self.retrieveFailureMessages(_edPlugin, "EDPluginControlIndexingIndicatorsv1_1.doFailureControlIndicators")
        self.addErrorWarningMessagesToExecutiveSummary("Image quality indicator failure! Error messages: ")
        self.generateExecutiveSummaryIndicators(_edPlugin)
        self.synchronizeOff()


    def generateExecutiveSummaryLabelit(self, _edPlugin):
        """
        Generates a summary of the execution of the Labelit plugin.
        """
        self.verboseDebug("EDPluginControlIndexingIndicatorsv1_1.generateExecutiveSummaryLabelit")
        if self.edPluginLabelitIndexing is not None and not self.edPluginLabelitIndexing.isFailure():
            self.addExecutiveSummarySeparator()
            self.addExecutiveSummaryLine("Summary of indexing with %s :" % self.strLabelitIndexingPluginName)
            self.addExecutiveSummaryLine("")
            self.appendExecutiveSummary(self.edPluginLabelitIndexing, "Labelit : ", _bAddSeparator=False)


    def generateExecutiveSummaryIndicators(self, _edPlugin):
        """
        Generates a summary of the execution of the indicator plugin.
        """
        self.verboseDebug("EDPluginControlIndexingIndicatorsv1_1.generateExecutiveSummaryIndicators")
        if self.edPluginControlIndicators is not None:
            self.addExecutiveSummarySeparator()
            self.appendExecutiveSummary(self.edPluginControlIndicators, "")


    def generateImageList(self, _xsDataCollection):
        """
        Make a list of all images in the subwedges
        """
        self.verboseDebug("EDPluginControlIndexingIndicatorsv1_1.generateImageList")
        listImage = None
        if (_xsDataCollection is not None):
            listImage = []
            xsDataSubWedgeList = _xsDataCollection.getSubWedge()
            for xsDataSubWedge in xsDataSubWedgeList:
                xsDataImageList = xsDataSubWedge.getImage()
                for xsDataImage in xsDataImageList:
                    listImage.append(XSDataImage.parseString(xsDataImage.marshal()))
        return listImage


    def generateIndexingShortSummary(self, _xsDataIndexingResult):
        """
        Generates a very short summary of the indexing
        """
        strIndexingShortSummary = ""
        if self.hasDataInput("crystal"):
            xsDataCrystal = self.getDataInput("crystal")[0]
            if xsDataCrystal.getSpaceGroup() is not None:
                strForcedSpaceGroup = xsDataCrystal.getSpaceGroup().getName().getValue().upper()
                if xsDataCrystal.getSpaceGroup().getName().getValue() != "":
                    strIndexingShortSummary += "Forced space group: %s\n" % strForcedSpaceGroup
        if _xsDataIndexingResult is not None:
            # Indexing solution
            xsDataSelectedSolution = _xsDataIndexingResult.getSelectedSolution()
            xsDataCrystal = xsDataSelectedSolution.getCrystal()
            # Refined cell parameters
            xsDataCell = xsDataCrystal.getCell()
            fA = xsDataCell.getLength_a().getValue()
            fB = xsDataCell.getLength_b().getValue()
            fC = xsDataCell.getLength_c().getValue()
            fAlpha = xsDataCell.getAngle_alpha().getValue()
            fBeta = xsDataCell.getAngle_beta().getValue()
            fGamma = xsDataCell.getAngle_gamma().getValue()
            # Estimated mosaicity
            fEstimatedMosaicity = xsDataCrystal.getMosaicity().getValue()
            # Space group
            strSpaceGroup = xsDataCrystal.getSpaceGroup().getName().getValue()
            # Spot deviation
            xsDataStatisticsIndexing = xsDataSelectedSolution.getStatistics()
            fSpotDeviationPositional = xsDataStatisticsIndexing.getSpotDeviationPositional().getValue()
            strIndexingShortSummary += "Indexing: laue/space group %s, mosaicity %.2f [degree], " % (strSpaceGroup, fEstimatedMosaicity)
            strIndexingShortSummary += "RMS dev pos %.2f [mm]" % fSpotDeviationPositional
            if xsDataStatisticsIndexing.getSpotDeviationAngular() is not None:
                fSpotDeviationAngular = xsDataStatisticsIndexing.getSpotDeviationAngular().getValue()
                strIndexingShortSummary += " ang %.2f [degree]" % fSpotDeviationAngular
            strIndexingShortSummary += "\n"
            strIndexingShortSummary += "Indexing: refined Cell: %7.2f %7.2f %7.2f %7.2f %7.2f %7.2f\n" % (fA, fB, fC, fAlpha, fBeta, fGamma)
        else:
            strIndexingShortSummary += "Indexing failed."
        for strLine in strIndexingShortSummary.split("\n"):
            self.screen(strLine)
        self.setDataOutput(XSDataString(strIndexingShortSummary), "indexingShortSummary")


    def generateIndicatorsShortSummary(self, _edPlugin):
        """
        Generates a very short summary of the image quality indicator processing
        """
        strIndicatorsShortSummary = ""
        if _edPlugin.hasDataOutput():
            for xsDataQualityIndicators in _edPlugin.getDataOutput().getImageQualityIndicators():
                strImageName = os.path.basename(xsDataQualityIndicators.getImage().getPath().getValue())
                strIndicatorsShortSummary += "ImageQualityIndicators: %s: " % strImageName
                iNoGoodBraggCandidates = xsDataQualityIndicators.getGoodBraggCandidates().getValue()
                strIndicatorsShortSummary += "good bragg %d, " % iNoGoodBraggCandidates
                fResMethod1 = xsDataQualityIndicators.getMethod1Res().getValue()
                strIndicatorsShortSummary += "r1 %.1f [A], " % fResMethod1
#                if xsDataQualityIndicators.getMethod2Res() is not None:
#                    fResMethod2 = xsDataQualityIndicators.getMethod2Res().getValue()
#                    strIndicatorsShortSummary += "r2 %.1f [A], " % fResMethod2
                if xsDataQualityIndicators.getMaxUnitCell() is not None:
                    fMaxCell = xsDataQualityIndicators.getMaxUnitCell().getValue()
                    strIndicatorsShortSummary += "max cell %.1f [A], " % fMaxCell
                iIceRings = xsDataQualityIndicators.getIceRings().getValue()
                strIndicatorsShortSummary += "ice rings %d" % iIceRings
                if xsDataQualityIndicators.getTotalIntegratedSignal() is not None:
                    fTotalIntegratedSignal = xsDataQualityIndicators.getTotalIntegratedSignal().getValue()
                    strIndicatorsShortSummary += ", TIS %.0f" % fTotalIntegratedSignal
                if xsDataQualityIndicators.getDozor_score() is None:
                    strIndicatorsShortSummary += "\n"
                else:
                    fDozorScore = xsDataQualityIndicators.getDozor_score().getValue()
                    strIndicatorsShortSummary += ", Dozor %.1f\n" % fDozorScore
            for strLine in strIndicatorsShortSummary.split("\n"):
                self.screen(strLine)
            self.setDataOutput(XSDataString(strIndicatorsShortSummary), "indicatorsShortSummary")