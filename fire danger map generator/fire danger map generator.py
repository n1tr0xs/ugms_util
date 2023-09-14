import sys
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import *
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageQt import ImageQt

try:
    Image.open('blank.png')
except FileNotFoundError:
    with open('log.txt', 'a') as log:
        log.write('blank.png not found')
    exit(1)

regions = [
    u"Троицкий",
    u"Белокуракинский",
    u"Новопсковский",
    u"Марковский",
    u"Меловской",
    u"Сватовский",
    u"Старобельский",
    u"Беловодский",
    u"Кременской",
    u"Новоайдарский",
    u"Станично-Луганский",
    u"Попаснянский",
    u"Славяносербский",
    u"Перевальский",
    u"Лутугинский",
    u"Краснодонский",
    u"Антрацитовский",
    u"Свердловский",
]

region_coords = {
    u"Троицкий": (415, 323),
    u"Белокуракинский": (710, 557),
    u"Новопсковский": (1060, 465),
    u"Марковский": (1440, 557),
    u"Меловской": (1760, 660),
    u"Сватовский": (300, 815),
    u"Старобельский": (945, 950),
    u"Беловодский": (1500, 917),
    u"Кременской": (490, 1160),
    u"Новоайдарский": (1081, 1313),
    u"Станично-Луганский": (1530, 1440),
    u"Попаснянский": (700, 1630),
    u"Славяносербский": (1110, 1680),
    u"Перевальский": (960, 1985),
    u"Лутугинский": (1370, 1975),
    u"Краснодонский": (1750, 1923),
    u"Антрацитовский": (1277, 2307),
    u"Свердловский": (1800, 2355),
}

def value_to_color(value):
    if value > 10000:
        return (255, 0, 0)
    if value > 4000:
        return (192, 0, 0)
    if value > 1000:
        return (255, 255, 0)
    if value > 300:
        return (0, 112, 192)
    return (146, 208, 80)

def value_to_class(value):
    if value > 10000:
        return 'V'
    if value > 4000:
        return 'IV'
    if value > 1000:
        return 'III'
    if value > 300:
        return 'II'
    return 'I'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
        self.setFont(QFont('Times New Roman', 16))
        self.setWindowTitle('Генератор карты пожароопасности')
        self.setWindowIcon(QIcon('icon.png'))

        self.image = None
        
        label = QLabel('Район')
        label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(label, 0, 0)

        label = QLabel('Показатель гориморсти')
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label, 0, 1)

        label = QLabel('Предпросмотр')
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label, 0, 3, 1, 2)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(line, 1, 0, 1, 5)
        
        edit_validator = QRegExpValidator(QRegExp('\d+'))
        self.region_edit = {}
        for i, region in enumerate(regions, start=2):
            # label for region
            label = QLabel(region) 
            self.layout.addWidget(label, i, 0)

            # edit for region
            edit = QLineEdit() 
            edit.setValidator(edit_validator)
            self.layout.addWidget(edit, i, 1)
            self.region_edit[region] = edit
        
        self.buttonSubmit = QPushButton('Сгенерировать картинку')
        self.buttonSubmit.clicked.connect(self.drawPicture)
        self.layout.addWidget(self.buttonSubmit, i+1, 0, 1, 2)

        self.buttonShowImage = QPushButton('Перейти к картинке')
        self.buttonShowImage.setEnabled(False)
        self.buttonShowImage.clicked.connect(lambda x: subprocess.Popen(r'explorer /select,"Карта пожароопасности.png"'))
        self.layout.addWidget(self.buttonShowImage, i+2, 0, 1, 2)

        self.preview_image_height = 650
        self.imageLabel = QLabel('')
        self.layout.addWidget(self.imageLabel, 2, 3, len(regions)+2, 1)
        self.imageLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                ImageQt(Image.open("blank.png")).scaledToHeight(self.preview_image_height)
            )
        )

    def drawPicture(self):
        self.buttonShowImage.setEnabled(False)
        
        region_value = {}
        for region, edit in self.region_edit.items():
            try: region_value[region] = int(edit.text())
            except ValueError: region_value[region] = 0
        
        self.image = Image.open('blank.png')
        draw = ImageDraw.Draw(self.image)
        font = ImageFont.truetype('times.ttf', 42)
        draw.font = font

        text_color = (0, 0, 0)
        y_padding = 10 # vertical spacing between text
        
        for i, region in enumerate(regions, start=1):
            # filling area with color
            x, y = region_coords[region]
            fill_color = value_to_color(region_value[region])
            ImageDraw.floodfill(
                self.image,
                (x, y),
                fill_color
            )
            # printing name of region
            y = self.draw_text(
                draw,
                x, y,
                text=str(region),
                fill=text_color
            )
            # printing fire danger factor
            y = self.draw_text(
                draw,
                x, y + y_padding,
                text=str(region_value[region]),
                fill=text_color
            )
            # printing fire danger class
            y = self.draw_text(
                draw,
                x, y + y_padding,
                text=str(value_to_class(region_value[region])),
                fill=text_color
            )

            self.imageLabel.setPixmap(
                QtGui.QPixmap.fromImage(
                    ImageQt(self.image).scaledToHeight(self.preview_image_height)
                )
            )
            QApplication.processEvents()
        
        self.image.save('Карта пожароопасности.png', 'PNG')
        self.image.close()
        self.buttonShowImage.setEnabled(True)

    def draw_text(self, draw, x, y, text='', fill=None):
        w, h = draw.font.font.getsize(text)[0]
        draw.text(
            (x - w//2, y - h//2),
            str(text),
            fill=fill
        )
        return y+h

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
