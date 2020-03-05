from PyQt5 import QtCore, QtGui, QtWidgets

class PixmapItem(QtWidgets.QGraphicsWidget):
	def __init__(self, image, scale, parent=None):
		super(PixmapItem, self).__init__(parent)
		self.s = scale
		self.pic = QtGui.QPixmap(image).scaledToWidth(self.s)

	def boundingRect(self):
		return QtCore.QRectF(self.pic.rect())

	def sizeHint(self, which, constraint=QtCore.QSizeF()):
		return self.boundingRect().size()

	def paint(self, painter, option, widget):
		painter.drawPixmap(QtCore.QPoint(), self.pic.scaledToWidth(self.s))

class GraphicsScene(QtWidgets.QGraphicsScene):
	def drawBackground(self, painter, rect):
		bg_brush = QtGui.QBrush(QtGui.QColor(255, 255, 255), QtCore.Qt.SolidPattern)
		painter.fillRect(rect, bg_brush)
		#Red bar on top
		painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
		brush = QtGui.QBrush(QtGui.QColor(139, 0, 0), QtCore.Qt.SolidPattern)
		r = QtCore.QRectF(rect)
		r.setY(0)
		r.setHeight(30)
		painter.fillRect(r, brush)

class GraphicsView(QtWidgets.QGraphicsView):
	def adjust_scene(self):
		if self.scene() is None: return
		r = self.scene().itemsBoundingRect()
		view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
		w = max(r.size().width(), view_rect.size().width())
		h = max(r.size().height(), view_rect.size().height())
		self.scene().setSceneRect(QtCore.QRectF(QtCore.QPointF(), QtCore.QSizeF(w, h)))
		#print(w)

	def resizeEvent(self, event):
		super(GraphicsView, self).resizeEvent(event)
		self.adjust_scene()
		

class Widget(QtWidgets.QWidget):
	def __init__(self, parent=None):
		super(Widget, self).__init__(parent)
		self.load_button = QtWidgets.QPushButton(text="Load")
		self.load_button.clicked.connect(self.load)
		self.column_spinbox = QtWidgets.QSpinBox(
			value=4,
			minimum=1,
			maximum=25,
			enabled=False
		)
		self.column_spinbox.valueChanged[int].connect(self.set_columns)
		self.scene = GraphicsScene()
		self.view = GraphicsView(self.scene)
		lay = QtWidgets.QVBoxLayout(self)
		hlay = QtWidgets.QHBoxLayout()
		hlay.addWidget(self.load_button)
		hlay.addWidget(self.column_spinbox)
		lay.addLayout(hlay)
		lay.addWidget(self.view)

	@QtCore.pyqtSlot()
	def load(self):
		self.imglist = ["py.png", "py.png","py.png","py.png","py.png","py.png",
			"py.png","py.png","py.png","py.png","py.png","py.png"]
		self.set_columns(self.column_spinbox.value())
		self.column_spinbox.setEnabled(True)

	@QtCore.pyqtSlot(int)
	def set_columns(self, column):
		self.view.scene().clear()
		item = self.scene.addText("Some Sample Text.", QtGui.QFont("Arial", 16, QtGui.QFont.Light))
		item.setDefaultTextColor(QtGui.QColor(255, 255, 255))

		top = item.mapToScene(item.boundingRect().bottomLeft())
		self.graphics_widget = QtWidgets.QGraphicsWidget()
		graphics_layout = QtWidgets.QGraphicsGridLayout(self.graphics_widget)
		self.view.scene().addItem(self.graphics_widget)
		self.graphics_widget.setPos(top)
		
		print(self.view.width())
		
		for i, img in enumerate(self.imglist):
			item = PixmapItem(img, ((self.view.width()/column)-15))
			row, col = divmod(i, column)
			graphics_layout.addItem(item, row, col)
			graphics_layout.setColumnSpacing(column, 15)
			graphics_layout.setRowSpacing(row, 15)
		QtCore.QTimer.singleShot(0, self.view.adjust_scene)

if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication(sys.argv)
	w = Widget()
	w.show()
	sys.exit(app.exec_())