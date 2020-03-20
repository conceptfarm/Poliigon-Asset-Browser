'''
	Demonstrates how to create a QWidget with PySide and attach it to the 3dsmax main window.
''' 

from PySide2 import QtWidgets
import MaxPlus


class _GCProtector(object):
	widgets = []

def make_cylinder():
	obj = MaxPlus.Factory.CreateGeomObject(MaxPlus.ClassIds.Cylinder)
	obj.ParameterBlock.Radius.Value = 10.0
	obj.ParameterBlock.Height.Value = 30.0
	node = MaxPlus.Factory.CreateNode(obj)
	time = MaxPlus.Core.GetCurrentTime()
	MaxPlus.ViewportManager.RedrawViews(time)
	return

app = QtWidgets.QApplication.instance()
if not app:
	app = QtWidgets.QApplication([])
	
def main():	 
	MaxPlus.FileManager.Reset(True)
	
	w = QtWidgets.QWidget()
	MaxPlus.AttachQWidgetToMax(w)
	_GCProtector.widgets.append( w )
	w.resize(250, 100)
	w.setWindowTitle('PySide Qt Window')

	main_layout = QtWidgets.QVBoxLayout()
	label = QtWidgets.QLabel("Click button to create a cylinder in the scene")
	main_layout.addWidget(label)

	cylinder_btn = QtWidgets.QPushButton("Cylinder")
	cylinder_btn.clicked.connect(make_cylinder)
	main_layout.addWidget(cylinder_btn)
	
	textEdit = QtWidgets.QLineEdit()
	textEdit.setText("Edit box")
	main_layout.addWidget(textEdit)
	
	w.setLayout( main_layout )
	w.show()

	
if __name__ == '__main__':
	main()