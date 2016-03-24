# coding: utf8
#
#    Project: EDNAproc
#             http://www.edna-site.org
#
#    File: "$Id$"
#
#    Copyright (C) ESRF
#
#    Principal author: Thomas Boeglin
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

__author__ = "Thomas Boeglin"
__license__ = "GPLv3+"
__copyright__ = "ESRF"

import sys
import os.path
import shutil

from EDPluginControl import EDPluginControl
from EDVerbose import EDVerbose
from EDFactoryPlugin import edFactoryPlugin

from XSDataCommon import XSDataFile, XSDataString

edFactoryPlugin.loadModule('XSDataXDSv1_0')

from XSDataXDSv1_0 import XSDataMinimalXdsIn
from XSDataXDSv1_0 import XSDataXdsOutput
from XSDataXDSv1_0 import XSDataXdsOutputFile
from XSDataXDSv1_0 import XSDataRange

from xdscfgparser import parse_xds_file

class EDPluginControlRunXdsFastProcv1_0(EDPluginControl):
    """
    Run XDS up to three times, extending the SPOT_RANGE after each
    failure.
    """


    def __init__(self):
        EDPluginControl.__init__(self)
        self.setXSDataInputClass(XSDataMinimalXdsIn)
        self.setDataOutput(XSDataXdsOutput())
        self.controlled_plugin_name = 'EDPluginExecMinimalXdsv1_0'
        self.first_run = None
        self.second_run = None
        self.third_run = None

        # to hold a ref to the successful plugin
        self.successful_run = None

    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginControlRunXdsFastProcv1_0.checkParameters")
        self.checkMandatoryParameters(self.dataInput, "Data Input is None")
        self.checkMandatoryParameters(self.dataInput.input_file, "No XDS input file")


    def preProcess(self, _edObject=None):
        EDPluginControl.preProcess(self)
        self.DEBUG("EDPluginControlRunXdsFastProcv1_0.preProcess")
        # Load the execution plugin
        self.first_run = self.loadPlugin(self.controlled_plugin_name)

        cfg = parse_xds_file(self.dataInput.input_file.value)
        spot_range = cfg.get('SPOT_RANGE=')
        if spot_range is None:
            strErrorMessage = "No SPOT_RANGE parameter"
            self.addErrorMessage(strErrorMessage)
            self.ERROR(strErrorMessage)
            self.setFailure()
        else:
            self.spot_range = spot_range

        # we will use this value to constrain the upper bound of
        # spot_range so it does not get past the last image number, so
        # we use a default value that cannot be a constraint in case
        # we cannot find it in the xds input file
        self.end_image_no = sys.maxint

        data_range = cfg.get('DATA_RANGE=')
        if data_range is not None:
            self.start_image_no = data_range[0]
            self.end_image_no = data_range[1]

    def process(self, _edObject=None):
        EDPluginControl.process(self)
        self.DEBUG("EDPluginControlRunXdsFastProcv1_0.process")
        # First run is vanilla without any modification
        params = XSDataMinimalXdsIn()
        params.input_file = self.dataInput.input_file
        params.spacegroup = self.dataInput.spacegroup
        params.unit_cell = self.dataInput.unit_cell
        # Fix for 'SPOT_RANGE 0 100' problem
        for srange in self.spot_range:
            if srange[0] > 0:
                xsDataRange = XSDataRange()
                xsDataRange.begin = srange[0]
                xsDataRange.end = srange[1]
                params.addSpot_range(xsDataRange)
        # Gleb on Mon Aug  4 18:54:36 CEST 2014: set jobs parameters in order to prevent
        # params.job = XSDataString('XYCORR INIT COLSPOT IDXREF')
        self.first_run.dataInput = params
        self.first_run.executeSynchronous()
        self.retrieveFailureMessages(self.first_run, "First XDS run")

        EDVerbose.DEBUG('first run completed...')

        if self.first_run.dataOutput is not None and self.first_run.dataOutput.succeeded.value:
            EDVerbose.DEBUG('... and it worked')
            self.successful_run = self.first_run
        else:
            EDVerbose.DEBUG('... and it failed')


        if not self.successful_run:
            self.second_run = self.loadPlugin(self.controlled_plugin_name)
            self.screen('Retrying with increased SPOT_RANGE')
            self.DEBUG('copying previously generated files to the new plugin dir')
            copy_xds_files(self.first_run.getWorkingDirectory(),
                           self.second_run.getWorkingDirectory())
            params = XSDataMinimalXdsIn()
            params.input_file = self.dataInput.input_file
            # params.job = XSDataString('DEFPIX INTEGRATE CORRECT')
            params.spacegroup = self.dataInput.spacegroup
            params.unit_cell = self.dataInput.unit_cell

            # Extended spot range
            if self.end_image_no <= 300:
                # All data as spot range
                xsDataRangeLimited = XSDataRange()
                xsDataRangeLimited.begin = 1
                xsDataRangeLimited.end = self.end_image_no
                params.addSpot_range(xsDataRangeLimited)
            else:
                # Start spot range
                xsDataRangeLimited = XSDataRange()
                xsDataRangeLimited.begin = 1
                xsDataRangeLimited.end = 100
                params.addSpot_range(xsDataRangeLimited)
                # Start spot range
                middleImageNumber = int(self.end_image_no / 2)
                xsDataRangeLimited = XSDataRange()
                xsDataRangeLimited.begin = middleImageNumber - 49
                xsDataRangeLimited.end = middleImageNumber + 50
                params.addSpot_range(xsDataRangeLimited)
                # End spot range
                xsDataRangeLimited = XSDataRange()
                xsDataRangeLimited.begin = self.end_image_no - 99
                xsDataRangeLimited.end = self.end_image_no
                params.addSpot_range(xsDataRangeLimited)


            self.second_run.dataInput = params
            self.second_run.executeSynchronous()
            self.retrieveFailureMessages(self.second_run, "Second XDS run")

            EDVerbose.DEBUG('second run completed')
            if self.second_run.dataOutput is not None and self.second_run.dataOutput.succeeded.value:
                EDVerbose.DEBUG('... and it worked')
                self.successful_run = self.second_run
            else:
                EDVerbose.DEBUG('... and it failed')

        if not self.successful_run:
            self.third_run = self.loadPlugin(self.controlled_plugin_name)
            self.screen('Retrying with reduced SPOT_RANGE')
            self.DEBUG('copying previously generated files to the new plugin dir')
            copy_xds_files(self.first_run.getWorkingDirectory(),
                           self.third_run.getWorkingDirectory())
            params = XSDataMinimalXdsIn()
            params.input_file = self.dataInput.input_file
            # params.job = XSDataString('DEFPIX INTEGRATE CORRECT')
            params.spacegroup = self.dataInput.spacegroup
            params.unit_cell = self.dataInput.unit_cell

            # Limited spot range: 1 to 20 or max no data points

            xsDataRangeLimited = XSDataRange()
            xsDataRangeLimited.begin = 1
            xsDataRangeLimited.end = 20 if self.end_image_no > 20 else self.end_image_no

            params.addSpot_range(xsDataRangeLimited)

            self.third_run.dataInput = params
            self.third_run.executeSynchronous()
            self.retrieveFailureMessages(self.third_run, "Second XDS run")

            EDVerbose.DEBUG('second run completed')
            if self.third_run.dataOutput is not None and self.third_run.dataOutput.succeeded.value:
                EDVerbose.DEBUG('... and it worked')
                self.successful_run = self.third_run
            else:
                EDVerbose.DEBUG('... and it failed')



        if not self.successful_run:
        # all runs failed so bail out ...
            strErrorMessage = "All three XDS runs failed"
            self.addErrorMessage(strErrorMessage)
            self.ERROR(strErrorMessage)
            self.setFailure()
        else:
            # use the xds parser plugin to parse the xds output file...
            parser = self.loadPlugin("EDPluginParseXdsOutputv1_0")
            wd = self.successful_run.getWorkingDirectory()
            parser_input = XSDataXdsOutputFile()
            correct_lp_path = XSDataFile()
            correct_lp_path.path = XSDataString(os.path.join(wd, 'CORRECT.LP'))
            parser_input.correct_lp = correct_lp_path
            gxparm_path = os.path.join(wd, 'GXPARM.XDS')
            if os.path.isfile(gxparm_path):
                gxparm = XSDataFile()
                gxparm.path = XSDataString(os.path.join(wd, 'GXPARM.XDS'))
                parser_input.gxparm = gxparm

            parser.dataInput = parser_input
            parser.executeSynchronous()

            if parser.isFailure():
                # that should not happen
                strErrorMessage = "Parser failure in XDS fast proc"
                self.ERROR(strErrorMessage)
                self.addErrorMessage(strErrorMessage)
                self.setFailure()
                return
            self.dataOutput = parser.dataOutput

    def postProcess(self, _edObject=None):
        EDPluginControl.postProcess(self)
        self.DEBUG("EDPluginControlRunXdsFastProcv1_0.postProcess")
        # XXX: maybe move the XDS output parsing there?

def copy_xds_files(source_dir, dest_dir):
    # those files are generated by the first steps of XDS. When we try
    # a re-run with JOB= DEFPIX INTEGRATE CORRECT we need them to be
    # available in the current directory
    FILES = [ 'X-CORRECTIONS.cbf',
              'Y-CORRECTIONS.cbf',
              'BKGINIT.cbf',
              'XPARM.XDS',
              'BLANK.cbf',
              'GAIN.cbf',
              'REMOVE.HKL',
              'XPARM.XDS',
              ]
    for f in FILES:
        try:
            shutil.copyfile(os.path.join(source_dir, f),
                            os.path.join(dest_dir, f))
        except IOError:
            # file not found
            pass