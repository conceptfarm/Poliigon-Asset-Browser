import sys
import configparser

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PoliigonBrowserConfigDialog(QDialog):
	def __init__(self, _appIcon, _windowWidth, parent = None):
		super().__init__(parent)
		
		self.verticalLayout = QVBoxLayout(self)
		self.gridLayoutControlls = QGridLayout()

		self.lbl1 = QLabel()
		self.lbl1.setText('Select poliigon Thumbnail Folder')
		self.gridLayoutControlls.addWidget(self.lbl1, 0, 0, 1, 1)
		
		self.btn1 = QPushButton("...")
		self.btn1.setFixedWidth(35)
		self.btn1.clicked.connect(lambda: self.getDir(self.le1))
		self.le1 = QLineEdit()
		self.le1.setReadOnly(True)
		self.gridLayoutControlls.addWidget(self.btn1, 1, 1)
		self.gridLayoutControlls.addWidget(self.le1, 1, 0)

		self.lbl2 = QLabel()
		self.lbl2.setText('Select poliigon Maps Folder')
		self.gridLayoutControlls.addWidget(self.lbl2, 2, 0, 1, 1)

		self.btn2 = QPushButton("...")
		self.btn2.setFixedWidth(35)
		self.btn2.clicked.connect(lambda: self.getDir(self.le2))
		self.le2 = QLineEdit()
		self.le2.setReadOnly(True)
		self.gridLayoutControlls.addWidget(self.btn2, 3, 1)
		self.gridLayoutControlls.addWidget(self.le2, 3, 0)
		
		self.gridLayoutOKCancel = QGridLayout()
		self.okCancel = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		self.okButton = self.okCancel.button(QDialogButtonBox.Ok)
		self.okButton.setEnabled(False)
		self.okCancel.accepted.connect(self.okPressed)
		self.okCancel.rejected.connect(self.cancelPressed)
		self.gridLayoutOKCancel.addWidget(self.okCancel, 0, 0)

		self.spacerItem = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.gridLayoutOKCancel.addItem(self.spacerItem, 1, 0)

		self.verticalLayout.addLayout(self.gridLayoutControlls)
		self.verticalLayout.addLayout(self.gridLayoutOKCancel)

		self.setWindowTitle("poliigon Browser Configuration")
		self.setModal(True)
		self.setFixedWidth(_windowWidth)
		self.setWindowIcon(_appIcon)
		self.adjustSize()
		self.setFixedHeight(self.height())
		
	@pyqtSlot()
	def getDir(self, _widget):
		#QFileDialog(parent, caption = QString(), QString &directory, QString &filter = QString())
		dirPath = QFileDialog.getExistingDirectory(self, 'Select a directory', QDir.home().dirName(), QFileDialog.ShowDirsOnly)
		
		if dirPath:
			_widget.setText(dirPath)

		if self.le1.text() != '' and self.le2.text() != '':
			self.okButton.setEnabled(True)

	@pyqtSlot()
	def okPressed(self):
		config = configparser.ConfigParser()
		config['poliigonBrowserSettings'] = {'poliigonThumbsPath':self.le1.text(),'poliigonMapsPath':self.le2.text()}
		
		with open('poliigonBrowser.ini', 'w') as configfile:
			config.write(configfile)

		self.accept()

	@pyqtSlot()
	def cancelPressed(self):
		self.reject()

'''
#use
def main(): 
	app = QApplication(sys.argv)
	ex = PoliigonBrowserConfigDialog()
	var = ex.exec()
	if var == 1:
		print(var)
		print(ex.le2.text())
		print(ex.le1.text())
	sys.exit(app.exec_())
	
if __name__ == '__main__':
	main()
'''
