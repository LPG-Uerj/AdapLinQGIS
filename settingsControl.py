import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils
from qgis.core.contextmanagers import qgisapp

from .settingsModel import settingsModel
from .settingsView import settingsView

from .utils import *

class settingsControl(object):
	"""docstring for settingsControl"""

	_instance = None

	def __new__(self):

		if not self._instance:

			self._instance = super(settingsControl, self).__new__(self)
			self.model = settingsModel()
			self.view = settingsView()
			
		return self._instance		

	def control(self):

		load = self.model.load()
		if (load):

			self.view.setValues(load)

		if (self.view.showDialog()):

			info = self.view.getValues()
			self.model.save(info)

			QSettings().setValue(SETTINGS_NAME + "/stride", info[0])
			QSettings().setValue(SETTINGS_NAME + "/vertices", info[1])
			QSettings().setValue(SETTINGS_NAME + "/snapperDistence", info[2])
			QSettings().setValue(SETTINGS_NAME + "/snapperMode", info[3])