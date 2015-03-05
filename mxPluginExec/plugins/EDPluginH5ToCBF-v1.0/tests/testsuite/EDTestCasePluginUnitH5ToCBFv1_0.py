#
#    Project: mxPluginExec
#             http://www.edna-site.org
#
#    Copyright (C) 2012 European Synchrotron Radiation Facility
#                       Grenoble, France
#
#    Principal authors:      Olof Svensson (svensson@esrf.fr) 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    and the GNU Lesser General Public License  along with this program.  
#    If not, see <http://www.gnu.org/licenses/>.
#


__authors__ = [ "Olof Svensson" ]
__contact__ = "svensson@esrf.fr"
__license__ = "LGPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "20150304"
__status__ = "beta"

import os

from EDAssert                        import EDAssert
from EDTestCasePluginUnit            import EDTestCasePluginUnit

from XSDataH5ToCBFv1_0 import XSDataInputH5ToCBF
from XSDataH5ToCBFv1_0 import XSDataResultH5ToCBF

class EDTestCasePluginUnitH5ToCBFv1_0(EDTestCasePluginUnit):


    def __init__(self, _strTestName=None):
        EDTestCasePluginUnit.__init__(self, "EDPluginH5ToCBFv1_0")
        self.strDataPath = self.getPluginTestsDataHome()
        self.strReferenceInputFile = os.path.join(self.strDataPath, "XSDataInputH5ToCBF_reference.xml")


    def testGenerateCommands(self):
        edPluginH5ToCBF = self.createPlugin()
        xsDataInputH5ToCBF = XSDataInputH5ToCBF.parseFile(self.strReferenceInputFile)
        strCommandLine = edPluginH5ToCBF.generateCommands(xsDataInputH5ToCBF)
        print(strCommandLine)

    def testGenerateMiniCBFHeader(self):
        edPluginH5ToCBF = self.createPlugin()
        xsDataInputH5ToCBF = XSDataInputH5ToCBF.parseFile(self.strReferenceInputFile)
        miniCBFHeader = edPluginH5ToCBF.generateMiniCBFHeader(xsDataInputH5ToCBF)
        print miniCBFHeader

    def process(self):
#        self.addTestMethod(self.testGenerateCommands)
        self.addTestMethod(self.testGenerateMiniCBFHeader)
