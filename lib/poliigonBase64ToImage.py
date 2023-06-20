from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import QByteArray
import base64

class Base64ToImage():
	def __init__(self):
		pass

	def qIconFromBase64(self, base64, base64isBytes=False):
		if base64isBytes:
			base64 = bytes(base64,'utf-8')
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(base64))
		_icon = QIcon(pixmap)
		return _icon
	
	def readChachedQIcon(self, _bytes):
		_icon = QIcon()
		base64 = bytes(_bytes,'utf-8')
		buffer = QByteArray.fromBase64(base64)
		read_stream = QDataStream(buffer, QIODevice.ReadOnly)
		read_stream >> _icon
		return _icon
	
	def writeChachedObject(self, obj):
		buffer = QByteArray()
		write_stream = QDataStream(buffer, QIODevice.WriteOnly)
		write_stream << obj
		return base64.b64encode(buffer).decode('UTF-8')

	def qImageFromBase64(self, base64, base64isBytes=False):
		if base64isBytes:
			base64 = bytes(base64,'utf-8')
		_image = QImage()
		_image.loadFromData(QByteArray.fromBase64(base64))
		return _image

	def qPixmapFromBase64(self, base64, base64isBytes=False):
		if base64isBytes:
			base64 = bytes(base64,'utf-8')
		_image = QPixmap()
		_image.loadFromData(QByteArray.fromBase64(base64))
		return _image
'''
class QPixmapQDatastream():
	#QDataStream <<>> QPixmap

	def __init__(self):
		self.source_pixmap = QPixmap(100, 100)
		self.source_pixmap.fill(Qt.red)
		self.output_pixmap = QPixmap()
		self.buffer = QByteArray()
		self.read_stream = QDataStream(self.buffer, QIODevice.ReadOnly)
		self.write_stream = QDataStream(self.buffer, QIODevice.WriteOnly)

	def testStream(self):
		self.write_stream << self.source_pixmap

		self.read_stream >> self.output_pixmap

		image = self.output_pixmap.toImage()
		pixel = image.pixel(10,10)
		self.astertEqual(pixel, QColor(Qt.red).rgba())
		self.astertEqual(self.source_pixmap.toImage(), self.output_pixmap.toImage())
'''