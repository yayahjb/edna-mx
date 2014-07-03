#
#    Project: mxPluginExec
#             http://www.edna-site.org
#
#    Copyright (C) 2008-2013 European Synchrotron Radiation Facility
#                            Grenoble, France
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

__author__ = "Olof Svensson"
__contact__ = "svensson@esrf.fr"
__license__ = "LGPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "20130328"
__status__ = "production"


from EDTestSuite                                  import EDTestSuite

class EDTestSuitePluginControlAutoprocv1_0(EDTestSuite):


    def process(self):
        self.addTestCaseFromName("EDTestCasePluginControlFileConversionv1_0")
        self.addTestCaseFromName("EDTestCasePluginExecuteExecXscalev1_0")
        self.addTestCaseFromName("EDTestCasePluginParseXdsOutputv1_0")
        self.addTestCaseFromName("EDTestCasePluginResCutoffv1_0")
        self.addTestCaseFromName("EDTestCasePluginControlAutoprocv1_0_id29_20140505")
