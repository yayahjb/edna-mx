#
#    Project: EDNA MXv1
#             http://www.edna-site.org
#
#    Copyright (C) 2008-2012 European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal author:       Olof Svensson (svensson@esrf.fr) 
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

__authors__ = [ "Olof Svensson" ]
__contact__ = "svensson@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os

from EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3             import EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3
from EDAssert import EDAssert

class EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3_withRotationRangeAndRadiationDamageModel(EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3):


    def __init__(self, _edStringTestName=None):
        EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3.__init__(self, "EDPluginControlInterfaceToMXCuBEv1_3")
        self.setDataInputFile(os.path.join(self.getPluginTestsDataHome(), "XSDataInputMXCuBE_withRotationRangeAndRadiationDamageModel.xml"))


    def preProcess(self):
        EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3.preProcess(self)
        self.loadTestImage([ "ref-testscale_1_001.img", "ref-testscale_1_002.img" ])


    def testExecute(self):
        self.run()




    def process(self):
        self.addTestMethod(self.testExecute)




if __name__ == '__main__':

    edTestCasePluginExecuteControlInterfaceToMXCuBEv1_3_withRotationRangeAndRadiationDamageModel = EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3("EDTestCasePluginExecuteControlInterfaceToMXCuBEv1_3_withRotationRangeAndRadiationDamageModel")
    edTestCasePluginExecuteControlInterfaceToMXCuBEv1_3_withRotationRangeAndRadiationDamageModel.execute()
