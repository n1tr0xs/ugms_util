import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import *
from PIL import Image, ImageDraw, ImageFont

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
        
        edit_validator = QRegExpValidator(QRegExp('\d+'))
        self.region_edit = {}
        for i, region in enumerate(regions):
            label = QLabel(region) # laber for region
            self.layout.addWidget(label, i, 0)
            
            edit = QLineEdit() # edit for region
            edit.setValidator(edit_validator)
            self.layout.addWidget(edit, i, 1)
            self.region_edit[region] = edit
        
        self.buttonSubmit = QPushButton('Сгенерировать картинку')
        self.buttonSubmit.clicked.connect(self.drawPicture)
        self.layout.addWidget(self.buttonSubmit, i+1, 0, 1, 2)

        self.progressLabel = QLabel()
        self.layout.addWidget(self.progressLabel, i+2, 0, 1, 2)

    def drawPicture(self):
        self.progressLabel.setText(f'Прогресс: 0/{len(regions)}')
        QApplication.processEvents()
        
        region_value = {}
        for region, edit in self.region_edit.items():
            try: region_value[region] = int(edit.text())
            except ValueError: region_value[region] = 0
        
        image = Image.open('0.png')
        os.system('del "Карта пожароопасности.png"')

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('times.ttf', 42)
        draw.font = font

        text_color = (0, 0, 0)
        
        for i, region in enumerate(regions, start=1):
            # filling area with color
            x, y = region_coords[region]
            ImageDraw.floodfill(
                image,
                (x, y),
                value_to_color(region_value[region])
            )

            # printing name of region
            w, h1 = font.font.getsize(region)[0]
            draw.text(
                (x - w//2, y - h1//2),
                region,
                fill=text_color
            )

            # printing fire danger factor
            text = str(region_value[region])
            w, h = font.font.getsize(text)[0]
            draw.text(
                (x - w//2, y+h1 - h//2),
                text,
                fill=text_color
            )

            # printing fire danger class
            text = value_to_class(region_value[region])
            w, h = font.font.getsize(text)[0]
            draw.text(
                (x - w//2, y+h1*2 - h//2),
                text,
                fill=text_color
            )

            self.progressLabel.setText(f'Прогресс: {i}/{len(regions)}')
            QApplication.processEvents()
            
        self.progressLabel.setText('Все области обработаны!')
        QApplication.processEvents()
        image.save('Карта пожароопасности.png', 'PNG')            
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
