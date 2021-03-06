#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inkex, os, random, sys, subprocess, shutil

from outputpro import cmyk, cutmarks

from PyQt4 import QtGui
from PyQt4 import QtCore

import gettext
_ = gettext.gettext

reload(sys)
sys.setdefaultencoding("utf-8")

dirpathTempFolder = '/tmp/output-'
for i in range(5):
    dirpathTempFolder += str(random.randint(0,9))
os.mkdir(dirpathTempFolder)

null_dir = " > /dev/null"

dirpathSoftware = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'outputpro')

inkscape_config = open(os.getenv("HOME") + '/.config/inkscape/preferences.xml', 'r').read()

list_of_export_formats = ['JPEG']
list_of_format_tips = {'JPEG':'O formato de imagem JPEG sempre perde qualidade devido ao método de compressão. Embora suporte o modo de cores CMYK, não é recomendado para uso em gráfica impressa.'}
list_of_color_modes_jpeg = ['CMYK','RGB','Gray','CMY','HSB','HSL','HWB','Lab','Log', 'OHTA','Rec601Luma','Rec601YCbCr','Rec709Luma','Rec709YCbCr','sRGB','XYZ','YCbCr','YCC','YIQ','YPbPr','YUV']
list_of_interlacing_jpeg = {u'Nenhum':'none', u'Linha':'line', u'Plano':'plane', u'Particionamento':'partition'}
list_of_noise_jpeg = {u'Gaussiano':'Gaussian-noise', u'Impulso':'Impulse-noise', u'Laplace':'Laplacian-noise', u'Multiplicativo':'Multiplicative-noise', u'Peixe':'Poisson-noise', u'Uniforme':'Uniform-noise'}
list_of_subsampling_jpeg = ['1x1, 1x1, 1x1', '2x1, 1x1, 1x1', '1x2, 1x1, 1x1', '2x2, 1x1, 1x1']
list_of_dct_jpeg = {u'Inteiro':'int', u'Inteiro rápido':'fast', u'Ponto flutuante':'float'}
list_of_area_to_export = [_(u"Página"), _(u"Desenho"), _(u"Objeto")]#,  _(u"Área definida")]
list_of_profiles = os.listdir('/usr/share/color/icc/')

selected_screen_profile = inkscape_config.split('id="displayprofile"')[1].split('uri="')[1].split('" />')[0].split('/')[-1]
selected_print_profile = inkscape_config.split('id="softproof"')[1].split('uri="')[1].split('" />')[0].split('/')[-1]

rgb_profile = '"' + inkscape_config.split('id="displayprofile"')[1].split('uri="')[1].split('" />')[0] + '"'
#cmyk_profile = '"' + inkscape_config.split('id="softproof"')[1].split('uri="')[1].split('" />')[0] + '"'

class OutputProBitmap(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--title")
        #self.OptionParser.add_option("-n", "--noffset",
        #                action="store", type="float",
        #                dest="noffset", default=0.0, help="normal offset")
        #self.OptionParser.add_option("-t", "--toffset",
        #                action="store", type="float",
        #                dest="toffset", default=0.0, help="tangential offset")
        #self.OptionParser.add_option("-k", "--kind",
        #                action="store", type="string",
        #                dest="kind", default=True,
        #                help="choose between wave or snake effect")
        #self.OptionParser.add_option("-c", "--copymode",
        #                action="store", type="string",
        #                dest="copymode", default=True,
        #                help="repeat the path to fit deformer's length")
        #self.OptionParser.add_option("-p", "--space",
        #                action="store", type="float",
        #                dest="space", default=0.0)
        #self.OptionParser.add_option("-v", "--vertical",
        #                action="store", type="inkbool",
        #                dest="vertical", default=False,
        #                help="reference path is vertical")
        #self.OptionParser.add_option("-d", "--duplicate",
        #                action="store", type="inkbool",
        #                dest="duplicate", default=False,
        #                help="duplicate pattern before deformation")

    def effect(self):
        list_of_selected_objects = []
        for id, node in self.selected.iteritems():
            list_of_selected_objects.append(node.get('id'))
        if len(list_of_selected_objects) >= 1:
            selected_object = list_of_selected_objects[0]
        else:
            selected_object = 'layer1'

        resolution = '90'


        self.code = open(self.svg_file, 'r').read()
        open(dirpathTempFolder +  "/original.svg", 'w').write(self.code)

        svg = self.document.getroot()
        page_width  = inkex.unittouu(svg.get('width'))
        page_height = inkex.unittouu(svg.attrib['height'])

        class mainWindow(QtGui.QWidget):
            def __init__(self, parent=None):
                QtGui.QWidget.__init__(self, parent)
                self.resize(950, 600)
                self.setMaximumSize(QtCore.QSize(950, 600))
                self.setMinimumSize(QtCore.QSize(950, 600))
                self.setWindowTitle(_(u'Inkscape OUTPUT PRO Bitmap'))
                self.setWindowIcon(QtGui.QIcon('/usr/share/pixmaps/inkscape-outputpro.png'))
                self.move((QtGui.QDesktopWidget().screenGeometry().width()-self.geometry().width())/2, (QtGui.QDesktopWidget().screenGeometry().height()-self.geometry().height())/2)

                self.preview_zoom = 1.0

                self.top_title_bitmap = QtGui.QLabel(parent=self)
                self.top_title_bitmap.setGeometry(0, 0, 950, 60)
                self.top_title_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathSoftware, 'top.png')))

                self.preview_panel = QtGui.QWidget(parent=self)
                self.preview_panel.setGeometry(0, 0, 320, 600)

                self.preview_bitmap = QtGui.QLabel(parent=self.preview_panel)
                self.preview_bitmap.setGeometry(10, 70, 300, 300)
                self.preview_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathTempFolder, 'preview.png')))
                #self.preview_bitmap.setStyleSheet("QWidget { background: url(alpha.png)}")
                #self.preview_bitmap.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)

                self.preview_original_title = QtGui.QLabel(parent=self.preview_panel)
                self.preview_original_title.setText(_(u"Original").upper())
                self.preview_original_title.setGeometry(255, 355, 50, 10)
                self.preview_original_title.setAlignment(QtCore.Qt.AlignCenter)
                self.preview_original_title.setStyleSheet('QFrame{font:6pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')

                self.preview_result_title = QtGui.QLabel(parent=self.preview_panel)
                self.preview_result_title.setText(_(u"Resultado").upper())
                self.preview_result_title.setGeometry(15, 75, 50, 10)
                self.preview_result_title.setAlignment(QtCore.Qt.AlignCenter)
                self.preview_result_title.setStyleSheet('QFrame{font:6pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')

                self.zoom_out_button = QtGui.QPushButton(QtGui.QIcon.fromTheme("zoom-out"), '', parent=self.preview_panel)
                self.zoom_out_button.setGeometry(10, 371, 16, 16)
                self.zoom_out_button.setIconSize(QtCore.QSize(12,12))
                self.zoom_out_button.setFlat(True)
                self.zoom_out_button.clicked.connect(self.zoom_out)

                self.zoom_in_button = QtGui.QPushButton(QtGui.QIcon.fromTheme("zoom-in"), '', parent=self.preview_panel)
                self.zoom_in_button.setGeometry(26, 371, 16, 16)
                self.zoom_in_button.setIconSize(QtCore.QSize(12,12))
                self.zoom_in_button.setFlat(True)
                self.zoom_in_button.clicked.connect(self.zoom_in)

                self.preview_zoom_title = QtGui.QLabel(parent=self.preview_panel)
                self.preview_zoom_title.setGeometry(44, 371, 256, 16)
                self.preview_zoom_title.setText('100%')
                self.preview_zoom_title.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
                self.preview_zoom_title.setFont(QtGui.QFont('Ubuntu', 8))
                #self.preview_result_title.setStyleSheet('QFrame{font:7pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')

                self.view_c_button = QtGui.QPushButton('C', parent=self.preview_panel)
                self.view_c_button.setGeometry(246, 371, 16, 16)
                self.view_c_button.setIconSize(QtCore.QSize(12,12))
                self.view_c_button.setFlat(True)
                self.view_c_button.setCheckable(True)
                self.view_c_button.setChecked(True)
                self.view_c_button.setShown(False)
                self.view_c_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)

                self.view_m_button = QtGui.QPushButton('M', parent=self.preview_panel)
                self.view_m_button.setGeometry(262, 371, 16, 16)
                self.view_m_button.setIconSize(QtCore.QSize(12,12))
                self.view_m_button.setFlat(True)
                self.view_m_button.setCheckable(True)
                self.view_m_button.setChecked(True)
                self.view_m_button.setShown(False)
                self.view_m_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)

                self.view_y_button = QtGui.QPushButton('Y', parent=self.preview_panel)
                self.view_y_button.setGeometry(278, 371, 16, 16)
                self.view_y_button.setIconSize(QtCore.QSize(12,12))
                self.view_y_button.setFlat(True)
                self.view_y_button.setCheckable(True)
                self.view_y_button.setChecked(True)
                self.view_y_button.setShown(False)
                self.view_y_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)

                self.view_k_button = QtGui.QPushButton('K', parent=self.preview_panel)
                self.view_k_button.setGeometry(294, 371, 16, 16)
                self.view_k_button.setIconSize(QtCore.QSize(12,12))
                self.view_k_button.setFlat(True)
                self.view_k_button.setCheckable(True)
                self.view_k_button.setChecked(True)
                self.view_k_button.setShown(False)
                self.view_k_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)

                self.view_image_info = QtGui.QLabel(parent=self.preview_panel)
                self.view_image_info.setGeometry(10, 400, 300, 190)
                self.view_image_info.setFont(QtGui.QFont('Ubuntu', 8))
                self.view_image_info.setWordWrap(True)
                self.view_image_info.setAlignment(QtCore.Qt.AlignTop)

                #self.main_title = QtGui.QLabel(parent=self)
                #self.main_title.setText(_(u"BITMAPS").upper())
                #self.main_title.setGeometry(640, 30, 150, 30)
                #self.main_title.setFont(QtGui.QFont('Ubuntu', 16, 75))
                #self.main_title.setAlignment(QtCore.Qt.AlignRight)
                #self.main_title.setForegroundRole(QtGui.QPalette.ColorRole(2))

                self.format_title = QtGui.QLabel(parent=self)
                self.format_title.setText(_(u"Formato").upper())
                self.format_title.setGeometry(320, 70, 200, 15)
                self.format_title.setFont(QtGui.QFont('Ubuntu', 8, 75))

                self.format_choice = QtGui.QComboBox(parent=self)
                self.format_choice.setGeometry(320, 85, 200, 25)
                self.format_choice.addItems(list_of_export_formats)
                self.format_choice.activated.connect(self.change_format)

                self.format_preview_check = QtGui.QCheckBox(parent=self)
                self.format_preview_check.setGeometry(540, 85, 200, 25)
                self.format_preview_check.setText(_(u"Previsualizar"))
                self.format_preview_check.setChecked(True)
                self.format_preview_check.clicked.connect(self.format_preview_change)

                self.option_box = QtGui.QTabWidget(parent=self)
                self.option_box.setGeometry(320, 120, 620, 435)

                self.general_options_panel = QtGui.QWidget(parent=self)
                self.general_geometry_panel = QtGui.QWidget(parent=self)
                self.general_prepress_panel = QtGui.QWidget(parent=self)
                self.general_imposition_panel = QtGui.QWidget(parent=self)
                self.option_box.addTab(self.general_options_panel, _(u"Opções"))
                self.option_box.addTab(self.general_geometry_panel, _(u"Tamanho"))
                self.option_box.addTab(self.general_prepress_panel, _(u"Pré-impressão"))
                self.option_box.addTab(self.general_imposition_panel, _(u"Imposição"))

                self.option_box.currentChanged.connect(self.generate_preview)

                self.general_options_panel_jpeg = QtGui.QWidget(parent=self.general_options_panel)
                self.general_options_panel_jpeg.setShown(False)

                self.color_mode_title_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.color_mode_title_jpeg.setText(_(u"Modo de cores").upper())
                self.color_mode_title_jpeg.setGeometry(10, 10, 260, 15)
                self.color_mode_title_jpeg.setFont(QtGui.QFont('Ubuntu', 8))

                self.color_mode_choice_jpeg = QtGui.QComboBox(parent=self.general_options_panel_jpeg)
                self.color_mode_choice_jpeg.setGeometry(10, 25, 260, 25)
                self.color_mode_choice_jpeg.addItems(list_of_color_modes_jpeg)
                self.color_mode_choice_jpeg.activated.connect(self.change_color_mode_jpeg)

                self.color_mode_title_tip_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.color_mode_title_tip_jpeg.setGeometry(10, 50, 260, 15)
                self.color_mode_title_tip_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                #self.color_mode_title_tip.setAlignment(QtCore.Qt.AlignLeft)

                self.quality_title_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.quality_title_jpeg.setText(_(u"Qualidade").upper())
                self.quality_title_jpeg.setGeometry(285, 10, 100, 15)
                self.quality_title_jpeg.setFont(QtGui.QFont('Ubuntu', 8))

                self.quality_percent_title_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.quality_percent_title_jpeg.setText('50%')
                self.quality_percent_title_jpeg.setGeometry(505, 10, 100, 40)
                self.quality_percent_title_jpeg.setFont(QtGui.QFont('Ubuntu', 12, 75))
                self.quality_percent_title_jpeg.setAlignment(QtCore.Qt.AlignRight)

                self.quality_percent_title_left_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.quality_percent_title_left_jpeg.setText('Menos qualidade\nMenor tamanho de arquivo')
                self.quality_percent_title_left_jpeg.setGeometry(285, 40, 160, 25)
                self.quality_percent_title_left_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                self.quality_percent_title_left_jpeg.setAlignment(QtCore.Qt.AlignLeft)

                self.quality_percent_title_right_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.quality_percent_title_right_jpeg.setText('Mais qualidade<br>Maior tamanho de arquivo')
                self.quality_percent_title_right_jpeg.setGeometry(445, 40, 160, 25)
                self.quality_percent_title_right_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                self.quality_percent_title_right_jpeg.setAlignment(QtCore.Qt.AlignRight)

                self.quality_choice_dial_jpeg = QtGui.QDial(parent=self.general_options_panel_jpeg)
                self.quality_choice_dial_jpeg.setRange(1,100)
                self.quality_choice_dial_jpeg.setGeometry(415, 10, 60, 60)
                self.quality_choice_dial_jpeg.setNotchesVisible(True)
                self.quality_choice_dial_jpeg.setValue(50)
                self.quality_choice_dial_jpeg.sliderReleased.connect(self.generate_preview)
                self.quality_choice_dial_jpeg.valueChanged.connect(self.change_quality_live_jpeg)

                self.color_profile_choice_jpeg = QtGui.QCheckBox(_(u"Usar perfil de cores do Inkscape"), parent=self.general_options_panel_jpeg)
                self.color_profile_choice_jpeg.setChecked(False)
                self.color_profile_choice_jpeg.setGeometry(283, 150, 325, 25)
                self.color_profile_choice_jpeg.clicked.connect(self.generate_preview)

                self.document_color_profile_title_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.document_color_profile_title_jpeg.setGeometry(290, 175, 320, 30)
                self.document_color_profile_title_jpeg.setWordWrap(True)
                self.document_color_profile_title_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                self.document_color_profile_title_jpeg.setAlignment(QtCore.Qt.AlignLeft)

                if selected_print_profile == '':
                    self.document_color_profile_title_jpeg.setEnabled(False)
                    self.color_profile_choice_jpeg.setEnabled(False)
                    self.document_color_profile_title_jpeg.setText(_(u"Esse documento não está utilizando um perfil de cor."))
                else:
                    self.document_color_profile_title_jpeg.setText(_(u"O perfil que o Inkscape está utilizando é") + ' ' + selected_print_profile[:-4])

                self.jpeg_interlace_option_jpeg = QtGui.QCheckBox(_(u"Entrelaçar"), parent=self.general_options_panel_jpeg)
                self.jpeg_interlace_option_jpeg.setGeometry(10, 80, 120, 25)
                self.jpeg_interlace_option_jpeg.toggled.connect(self.jpeg_interlace_click_jpeg)

                self.jpeg_interlace_choice_jpeg = QtGui.QComboBox(parent=self.general_options_panel_jpeg)
                self.jpeg_interlace_choice_jpeg.setGeometry(130, 80, 140, 25)
                self.jpeg_interlace_choice_jpeg.addItems(list_of_interlacing_jpeg.keys())
                self.jpeg_interlace_choice_jpeg.setCurrentIndex(1)
                self.jpeg_interlace_choice_jpeg.setEnabled(False)
                self.jpeg_interlace_choice_jpeg.activated.connect(self.generate_preview)

                self.jpeg_optimize_option_jpeg = QtGui.QCheckBox(_(u"Otimizar"), parent=self.general_options_panel_jpeg)
                self.jpeg_optimize_option_jpeg.setGeometry(10, 115, 260, 25)
                self.jpeg_optimize_option_jpeg.setChecked(True)

                self.jpeg_noise_option_jpeg = QtGui.QCheckBox(_(u"Ruído"), parent=self.general_options_panel_jpeg)
                self.jpeg_noise_option_jpeg.setGeometry(10, 150, 120, 25)
                self.jpeg_noise_option_jpeg.toggled.connect(self.jpeg_noise_click_jpeg)

                self.jpeg_noise_choice_jpeg = QtGui.QComboBox(parent=self.general_options_panel_jpeg)
                self.jpeg_noise_choice_jpeg.setGeometry(130, 150, 140, 25)
                self.jpeg_noise_choice_jpeg.addItems(list_of_noise_jpeg.keys())
                self.jpeg_noise_choice_jpeg.setCurrentIndex(1)
                self.jpeg_noise_choice_jpeg.setEnabled(False)
                self.jpeg_noise_choice_jpeg.activated.connect(self.generate_preview)

                self.jpeg_noise_ammount_jpeg = QtGui.QSlider(QtCore.Qt.Horizontal, parent=self.general_options_panel_jpeg)
                self.jpeg_noise_ammount_jpeg.setGeometry(15, 175, 260, 25)
                self.jpeg_noise_ammount_jpeg.setRange(0,100)
                self.jpeg_noise_ammount_jpeg.setEnabled(False)
                self.jpeg_noise_ammount_jpeg.setValue(0.0)
                self.jpeg_noise_ammount_jpeg.sliderReleased.connect(self.generate_preview)

                self.jpeg_subsampling_option_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.jpeg_subsampling_option_jpeg.setText(_(u"Sub-amostragem"))
                self.jpeg_subsampling_option_jpeg.setGeometry(10, 210, 140, 25)

                self.jpeg_subsampling_choice_jpeg = QtGui.QComboBox(parent=self.general_options_panel_jpeg)
                self.jpeg_subsampling_choice_jpeg.setGeometry(150, 210, 120, 25)
                self.jpeg_subsampling_choice_jpeg.addItems(list_of_subsampling_jpeg)
                self.jpeg_subsampling_choice_jpeg.setCurrentIndex(0)
                self.jpeg_subsampling_choice_jpeg.activated.connect(self.generate_preview)

                self.jpeg_dct_option_jpeg = QtGui.QLabel(parent=self.general_options_panel_jpeg)
                self.jpeg_dct_option_jpeg.setText(_(u"Método DCT"))
                self.jpeg_dct_option_jpeg.setGeometry(10, 245, 120, 25)

                self.jpeg_dct_choice_jpeg = QtGui.QComboBox(parent=self.general_options_panel_jpeg)
                self.jpeg_dct_choice_jpeg.setGeometry(130, 245, 140, 25)
                self.jpeg_dct_choice_jpeg.addItems(list_of_dct_jpeg.keys())
                self.jpeg_dct_choice_jpeg.activated.connect(self.generate_preview)

                self.cmyk_advanced_manipulation_option_jpeg = QtGui.QCheckBox(_(u"Manipulação apurada de cores"), parent=self.general_options_panel_jpeg)
                self.cmyk_advanced_manipulation_option_jpeg.setGeometry(283, 80, 325, 25)
                self.cmyk_advanced_manipulation_option_jpeg.clicked.connect(self.cmyk_advanced_manipulation_click_jpeg)

                self.cmyk_overblack_jpeg = QtGui.QCheckBox(_(u"Sobrepôr o preto"), parent=self.general_options_panel_jpeg)
                self.cmyk_overblack_jpeg.setGeometry(283, 115, 325, 25)
                self.cmyk_overblack_jpeg.setEnabled(False)
                self.cmyk_overblack_jpeg.clicked.connect(self.cmyk_advanced_manipulation_click_jpeg)

                self.area_to_export_title = QtGui.QLabel(parent=self.general_geometry_panel)
                self.area_to_export_title.setText(_(u"Área a exportar").upper())
                self.area_to_export_title.setGeometry(10, 20, 250, 15)
                self.area_to_export_title.setFont(QtGui.QFont('Ubuntu', 8))

                self.area_to_export_choice = QtGui.QComboBox(parent=self.general_geometry_panel)
                self.area_to_export_choice.setGeometry(10, 35, 250, 25)
                self.area_to_export_choice.addItems(list_of_area_to_export)
                self.area_to_export_choice.activated.connect(self.change_area_to_export)

                self.dpi_title = QtGui.QLabel(parent=self.general_geometry_panel)
                self.dpi_title.setText(_(u"Pontos por Polegada").upper())
                self.dpi_title.setGeometry(270, 20, 200, 15)
                self.dpi_title.setFont(QtGui.QFont('Ubuntu', 8))

                self.dpi_choice = QtGui.QSpinBox(parent=self.general_geometry_panel)
                self.dpi_choice.setValue(90)
                self.dpi_choice.setGeometry(270, 35, 100, 25)
                self.dpi_choice.setRange(1, 99999)
                self.dpi_choice.editingFinished.connect(self.change_area_to_export)

                self.dpi_text_title = QtGui.QLabel(parent=self.general_geometry_panel)
                self.dpi_text_title.setText('dpi')
                self.dpi_text_title.setGeometry(380, 35, 80, 25)
                self.dpi_text_title.setFont(QtGui.QFont('Ubuntu', 8))

                self.x0_value = QtGui.QSpinBox(parent=self.general_geometry_panel)
                self.x0_value.setGeometry(10, 100, 80, 25)
                self.x0_value.setRange(1, 2147483647)
                self.x0_value.editingFinished.connect(self.change_area_to_export)

                self.y0_value = QtGui.QSpinBox(parent=self.general_geometry_panel)
                self.y0_value.setGeometry(100, 130, 80, 25)
                self.y0_value.setRange(1, 2147483647)
                self.y0_value.editingFinished.connect(self.change_area_to_export)

                self.x1_value = QtGui.QSpinBox(parent=self.general_geometry_panel)
                self.x1_value.setGeometry(100, 70, 80, 25)
                self.x1_value.setRange(1, 2147483647)
                self.x1_value.editingFinished.connect(self.change_area_to_export)

                self.y1_value = QtGui.QSpinBox(parent=self.general_geometry_panel)
                self.y1_value.setGeometry(190, 100, 80, 25)
                self.y1_value.setRange(1, 2147483647)
                self.y1_value.editingFinished.connect(self.change_area_to_export)

                self.area_to_export_id_title = QtGui.QLabel(parent=self.general_geometry_panel)
                self.area_to_export_id_title.setText(_(u"Objeto a exportar").upper())
                self.area_to_export_id_title.setGeometry(10, 70, 300, 15)
                self.area_to_export_id_title.setFont(QtGui.QFont('Ubuntu', 8))

                self.area_to_export_id_name = QtGui.QLineEdit(parent=self.general_geometry_panel)
                self.area_to_export_id_name.setGeometry(10, 85, 300, 25)

                self.area_to_export_idonly_check = QtGui.QCheckBox(parent=self.general_geometry_panel)
                self.area_to_export_idonly_check.setGeometry(10, 120, 400, 25)
                self.area_to_export_idonly_check.setText(_(u"Exportar apenas o objeto"))

                self.prepress_paper_settings_label = QtGui.QLabel(parent=self.general_prepress_panel)
                self.prepress_paper_settings_label.setGeometry(10, 10, 300, 15)
                self.prepress_paper_settings_label.setText(_(u"Cofiguração do Papel ou filme").upper())
                self.prepress_paper_settings_label.setFont(QtGui.QFont('Ubuntu', 8))

                self.prepress_paper_settings_invert = QtGui.QCheckBox(parent=self.general_prepress_panel)
                self.prepress_paper_settings_invert.setGeometry(10, 25, 300, 25)
                self.prepress_paper_settings_invert.setText(_(u"Inverter"))
                self.prepress_paper_settings_invert.setChecked(False)
                self.prepress_paper_settings_invert.clicked.connect(self.generate_preview)

                self.prepress_paper_settings_mirror = QtGui.QCheckBox(parent=self.general_prepress_panel)
                self.prepress_paper_settings_mirror.setGeometry(10, 50, 300, 25)
                self.prepress_paper_settings_mirror.setText(_(u"Espelhar"))
                self.prepress_paper_settings_mirror.setChecked(False)
                self.prepress_paper_settings_mirror.clicked.connect(self.generate_preview)

                self.prepress_paper_cutmarks_label = QtGui.QLabel(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_label.setGeometry(10, 85, 300, 15)
                self.prepress_paper_cutmarks_label.setText(_(u"Marcas de corte").upper())
                self.prepress_paper_cutmarks_label.setFont(QtGui.QFont('Ubuntu', 8))

                self.prepress_paper_cutmarks_check = QtGui.QCheckBox(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_check.setGeometry(10, 100, 300, 25)
                self.prepress_paper_cutmarks_check.setText(_(u"Inserir marcas de corte"))
                self.prepress_paper_cutmarks_check.setChecked(False)
                self.prepress_paper_cutmarks_check.clicked.connect(self.cut_marks_insert_change)

                self.prepress_paper_cutmarks_strokewidth_label = QtGui.QLabel(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_strokewidth_label.setGeometry(10, 125, 200, 25)
                self.prepress_paper_cutmarks_strokewidth_label.setText(_(u"Espessura da marca:"))
                self.prepress_paper_cutmarks_strokewidth_label.setEnabled(False)

                self.prepress_paper_cutmarks_strokewidth_value = QtGui.QLineEdit(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_strokewidth_value.setGeometry(210, 125, 50, 25)
                self.prepress_paper_cutmarks_strokewidth_value.setText('1')
                self.prepress_paper_cutmarks_strokewidth_value.setEnabled(False)
                self.prepress_paper_cutmarks_strokewidth_value.editingFinished.connect(self.generate_preview)

                self.prepress_paper_cutmarks_strokewidth_choice = QtGui.QComboBox(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_strokewidth_choice.setGeometry(260,125,50,25)
                self.prepress_paper_cutmarks_strokewidth_choice.addItems(inkex.uuconv.keys())
                self.prepress_paper_cutmarks_strokewidth_choice.setCurrentIndex(5)
                self.prepress_paper_cutmarks_strokewidth_choice.activated.connect(self.generate_preview)
                self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(False)

                self.prepress_paper_cutmarks_bleedsize_label = QtGui.QLabel(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_bleedsize_label.setGeometry(10, 150, 200, 25)
                self.prepress_paper_cutmarks_bleedsize_label.setText(_(u"Sangria:"))
                self.prepress_paper_cutmarks_bleedsize_label.setEnabled(False)

                self.prepress_paper_cutmarks_bleedsize_value = QtGui.QLineEdit(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_bleedsize_value.setGeometry(210, 150, 50, 25)
                self.prepress_paper_cutmarks_bleedsize_value.setText('5')
                self.prepress_paper_cutmarks_bleedsize_value.setEnabled(False)
                self.prepress_paper_cutmarks_bleedsize_value.editingFinished.connect(self.generate_preview)

                self.prepress_paper_cutmarks_bleedsize_choice = QtGui.QComboBox(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_bleedsize_choice.setGeometry(260,150,50,25)
                self.prepress_paper_cutmarks_bleedsize_choice.addItems(inkex.uuconv.keys())
                self.prepress_paper_cutmarks_bleedsize_choice.setCurrentIndex(5)
                self.prepress_paper_cutmarks_bleedsize_choice.activated.connect(self.generate_preview)
                self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(False)

                self.prepress_paper_cutmarks_marksize_label = QtGui.QLabel(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_marksize_label.setGeometry(10, 175, 200, 25)
                self.prepress_paper_cutmarks_marksize_label.setText(_(u"Tamanho da marca:"))
                self.prepress_paper_cutmarks_marksize_label.setEnabled(False)

                self.prepress_paper_cutmarks_marksize_value = QtGui.QLineEdit(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_marksize_value.setGeometry(210, 175, 50, 25)
                self.prepress_paper_cutmarks_marksize_value.setText('5')
                self.prepress_paper_cutmarks_marksize_value.setEnabled(False)
                self.prepress_paper_cutmarks_marksize_value.editingFinished.connect(self.generate_preview)

                self.prepress_paper_cutmarks_marksize_choice = QtGui.QComboBox(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_marksize_choice.setGeometry(260,175,50,25)
                self.prepress_paper_cutmarks_marksize_choice.addItems(inkex.uuconv.keys())
                self.prepress_paper_cutmarks_marksize_choice.setCurrentIndex(5)
                self.prepress_paper_cutmarks_marksize_choice.activated.connect(self.generate_preview)
                self.prepress_paper_cutmarks_marksize_choice.setEnabled(False)

                self.prepress_paper_cutmarks_inside_check = QtGui.QCheckBox(parent=self.general_prepress_panel)
                self.prepress_paper_cutmarks_inside_check.setGeometry(10, 200, 300, 25)
                self.prepress_paper_cutmarks_inside_check.setText(_(u"Sem marcas internas"))
                self.prepress_paper_cutmarks_inside_check.setChecked(False)
                self.prepress_paper_cutmarks_inside_check.setEnabled(False)
                self.prepress_paper_cutmarks_inside_check.clicked.connect(self.generate_preview)

                self.imposition_label = QtGui.QLabel(parent=self.general_imposition_panel)
                self.imposition_label.setGeometry(10, 10, 300, 15)
                self.imposition_label.setText(_(u"Quantidade de imposições").upper())
                self.imposition_label.setFont(QtGui.QFont('Ubuntu', 8))

                self.imposition_vertical_number_label = QtGui.QLabel(parent=self.general_imposition_panel)
                self.imposition_vertical_number_label.setGeometry(10, 25, 200, 25)
                self.imposition_vertical_number_label.setText(_(u"Linhas:"))

                self.imposition_vertical_number_value = QtGui.QSpinBox(parent=self.general_imposition_panel)
                self.imposition_vertical_number_value.setGeometry(210, 25, 50, 25)
                self.imposition_vertical_number_value.setValue(1)
                self.imposition_vertical_number_value.setRange(1, 999)
                self.imposition_vertical_number_value.editingFinished.connect(self.generate_preview)

                self.imposition_horizontal_number_label = QtGui.QLabel(parent=self.general_imposition_panel)
                self.imposition_horizontal_number_label.setGeometry(10, 60, 200, 25)
                self.imposition_horizontal_number_label.setText(_(u"Colunas:"))

                self.imposition_horizontal_number_value = QtGui.QSpinBox(parent=self.general_imposition_panel)
                self.imposition_horizontal_number_value.setGeometry(210, 60, 50, 25)
                self.imposition_horizontal_number_value.setValue(1)
                self.imposition_horizontal_number_value.setRange(1, 999)
                self.imposition_horizontal_number_value.editingFinished.connect(self.generate_preview)

                self.imposition_space_label = QtGui.QLabel(parent=self.general_imposition_panel)
                self.imposition_space_label.setGeometry(10, 90, 200, 25)
                self.imposition_space_label.setText(_(u"Espaço entre as marcas:"))

                self.imposition_space_value = QtGui.QLineEdit(parent=self.general_imposition_panel)
                self.imposition_space_value.setGeometry(210, 90, 50, 25)
                self.imposition_space_value.setText('5')
                self.imposition_space_value.editingFinished.connect(self.generate_preview)

                self.imposition_space_choice = QtGui.QComboBox(parent=self.general_imposition_panel)
                self.imposition_space_choice.setGeometry(260,90,50,25)
                self.imposition_space_choice.addItems(inkex.uuconv.keys())
                self.imposition_space_choice.setCurrentIndex(5)
                self.imposition_space_choice.activated.connect(self.generate_preview)

                self.export_button = QtGui.QPushButton(QtGui.QIcon.fromTheme("document-export"), _("Exportar"), parent=self)
                self.export_button.setGeometry(740, 560, 200, 30)
                self.export_button.setIconSize(QtCore.QSize(20,20))
                self.export_button.clicked.connect(self.export)

                self.change_area_to_export()
                self.change_format()

            def generate_preview(self):
                if self.format_preview_check.isChecked():
                    self.generate_final_file()

                    if self.option_box.currentIndex() == 0:
                        self.preview_original_title.setVisible(True)
                        self.preview_result_title.setVisible(True)

                        final_command = ['convert']
                        final_command.append(dirpathTempFolder +  '/result-imp.' + list_of_export_formats[self.format_choice.currentIndex()].lower())

                        if self.color_profile_choice_jpeg.isChecked():
                            final_command.append('-profile')
                            final_command.append('/usr/share/color/icc/' + selected_screen_profile)

                        final_command.append(dirpathTempFolder +  '/result.png')

                        subprocess.Popen(final_command).wait()

                        file_info = subprocess.Popen(['identify', dirpathTempFolder +  '/source.png'], stdout=subprocess.PIPE).communicate()[0]

                        image_width = int(file_info.split(' ')[2].split('x')[0])
                        image_height = int(file_info.split(' ')[2].split('x')[1])

                        marksize = (self.dpi_choice.value() / 90) * inkex.unittouu(str(self.prepress_paper_cutmarks_marksize_value.text()) + str(self.prepress_paper_cutmarks_marksize_choice.currentText()))
                        imposition_space = (self.dpi_choice.value() / 90) * inkex.unittouu(str(self.imposition_space_value.text()) + str(self.imposition_space_choice.currentText()))

                        file_info = subprocess.Popen(['identify', '-verbose',dirpathTempFolder +  '/result-imp.' + list_of_export_formats[self.format_choice.currentIndex()].lower()], stdout=subprocess.PIPE).communicate()[0]

                        file_info_final = ''
                        for line in file_info.split('\n'):
                            if '  Format: ' in line:
                                file_info_final += 'Formato da imagem: <strong>' + line.replace('  Format: ', '') + '</strong><br>'
                            if '  Geometry: ' in line:
                                file_info_final += 'Largura e altura: <strong>' + line.replace('  Geometry: ', '').split('+')[0] + '</strong><br>'
                            if '  Resolution: ' in line:
                                file_info_final += 'Resolução: <strong>' + line.replace('  Resolution: ', '')
                            if '  Units: ' in line:
                                file_info_final += ' ' + line.replace('  Units: ', '').replace('Per', ' por ').replace('Pixels', 'pixels').replace('Centimeter', 'centímetro').replace('Inch', 'polegada') + '</strong><br>'
                            if '  Colorspace: ' in line:
                                file_info_final += 'Modo de cores: <strong>' + line.replace('  Colorspace: ', '') + '</strong><br>'
                            if '  Depth: ' in line:
                                file_info_final += 'Profundidade: <strong>' + line.replace('  Depth: ', '') + '</strong><br>'
                            if '  Quality: ' in line:
                                file_info_final += 'Qualidade: <strong>' + line.replace('  Quality: ', '') + '%</strong><br>'
                            if '  Filesize: ' in line:
                                file_info_final += 'Tamanho do arquivo: <strong>' + line.replace('  Filesize: ', '') + '</strong><br>'
                            if '    jpeg:sampling-factor: ' in line:
                                file_info_final += 'Amostragem: <strong>' + line.replace('    jpeg:sampling-factor: ', '') + '</strong><br>'

                        if self.prepress_paper_cutmarks_check.isChecked():
                            margin = marksize
                        else:
                            margin = imposition_space

                        if image_width < 300 or image_height < 300:
                            what_show = '-extent ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '-' + str(int(150 * self.preview_zoom) - int(image_width / 2)) + '-' + str(int(150 * self.preview_zoom) - int(image_height / 2))
                        else:
                            what_show = '-crop ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '+' + str(int(image_width / 2) - int(150 * self.preview_zoom)) + '+' + str(int(image_height / 2) - int(150 * self.preview_zoom))

                        os.system('convert "' + dirpathTempFolder +  '/source.png" ' + what_show + ' "' + dirpathTempFolder +  '/original.png"' )

                        if image_width < 300 or image_height < 300:
                            what_show = '-extent ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '-' + str(int(150 * self.preview_zoom) - int(image_width / 2) - margin) + '-' + str(int(150 * self.preview_zoom) - int(image_height / 2) - margin)
                        else:
                            what_show = '-crop ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '+' + str(int(image_width / 2) - int(150 * self.preview_zoom) + margin) + '+' + str(int(image_height / 2) - int(150 * self.preview_zoom) + margin)

                        os.system('convert "' + dirpathTempFolder +  '/result.png" ' + what_show + ' "' + dirpathTempFolder +  '/result.png"' )

                        if not self.preview_zoom == 1:
                            os.system('convert "' + dirpathTempFolder +  '/original.png" -filter box -resize 300x300 "' + dirpathTempFolder +  '/original.png"' )
                            os.system('convert "' + dirpathTempFolder +  '/result.png" -filter box -resize 300x300 "' + dirpathTempFolder +  '/result.png"' )

                        os.system('convert "' + dirpathTempFolder +  '/original.png" "' + dirpathTempFolder +  '/result.png" "' + dirpathSoftware + '/preview_mask.png" -composite "' + dirpathTempFolder +  '/preview.png"' )

                        self.view_image_info.setText(unicode(file_info_final + '<br><small>' + list_of_format_tips[list_of_export_formats[self.format_choice.currentIndex()]] + '</small>', 'utf-8'))

                    elif self.option_box.currentIndex() == 1:
                        self.preview_original_title.setVisible(False)
                        self.preview_result_title.setVisible(False)

                        subprocess.Popen(['convert', dirpathTempFolder +  '/result-imp.' + list_of_export_formats[self.format_choice.currentIndex()].lower(), '-resize', '300x300', os.path.join(dirpathTempFolder, 'preview.png')]).wait()

                    elif self.option_box.currentIndex() == 2:
                        None

                    elif self.option_box.currentIndex() == 3:
                        None

                    self.preview_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathTempFolder, 'preview.png')))

            def generate_final_file(self):
                if list_of_export_formats[self.format_choice.currentIndex()] == 'JPEG':
                    jpeg_command = ['convert']

                    if not self.cmyk_advanced_manipulation_option_jpeg.isChecked():
                        pre_command = ['convert']
                        pre_command.append(dirpathTempFolder +  '/source.tiff')

                        if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMYK' or list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                            if self.color_profile_choice_jpeg.isChecked():
                                pre_command.append('-profile')
                                pre_command.append('/usr/share/color/icc/' + selected_screen_profile)
                                pre_command.append('-profile')
                                pre_command.append('/usr/share/color/icc/' + selected_print_profile)

                            if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                                pre_command.append(dirpathTempFolder +  '/result.tiff')
                                subprocess.Popen(pre_command).wait()
                                del pre_command[:]
                                pre_command.append('convert')
                                pre_command.append(dirpathTempFolder +  '/result.tiff')
                                pre_command.append('-profile')
                                pre_command.append('/usr/share/color/icc/' + selected_screen_profile)

                        pre_command.append(dirpathTempFolder +  '/result.tiff')
                        subprocess.Popen(pre_command).wait()

                    else:
                        if self.color_profile_choice_jpeg.isChecked():
                            pre_command = ['convert']
                            pre_command.append(dirpathTempFolder +  '/result.tiff')
                            pre_command.append('-profile')
                            pre_command.append('/usr/share/color/icc/' + selected_print_profile)
                            pre_command.append(dirpathTempFolder +  '/result.tiff')
                            subprocess.Popen(pre_command).wait()

                    file_info = subprocess.Popen(['identify', dirpathTempFolder +  '/source.png'], stdout=subprocess.PIPE).communicate()[0]

                    if self.prepress_paper_cutmarks_check.isChecked():
                        bleedsize = (self.dpi_choice.value() / 90) * inkex.unittouu(str(self.prepress_paper_cutmarks_bleedsize_value.text()) + str(self.prepress_paper_cutmarks_bleedsize_choice.currentText()))
                        marksize = (self.dpi_choice.value() / 90) * inkex.unittouu(str(self.prepress_paper_cutmarks_marksize_value.text()) + str(self.prepress_paper_cutmarks_marksize_choice.currentText()))
                    else:
                        bleedsize = 0
                        marksize = 0

                    imposition_space = (self.dpi_choice.value() / 90) *inkex.unittouu(str(self.imposition_space_value.text()) + str(self.imposition_space_choice.currentText()))

                    image_width = []
                    for i in range(self.imposition_vertical_number_value.value()):
                        image_width.append(int(file_info.split(' ')[2].split('x')[0]))

                    image_height = []
                    for i in range(self.imposition_horizontal_number_value.value()):
                        image_height.append(int(file_info.split(' ')[2].split('x')[1]))

                    imposition_command = ['convert']
                    imposition_command.append(dirpathTempFolder + '/result.tiff')
                    imposition_command.append('-extent')
                    imposition_command.append(str(sum(image_width) + (marksize*2) + (imposition_space * (len(image_width) -1))) + 'x' + str(sum(image_height) + (marksize*2) + (imposition_space * (len(image_height) -1))) + '-' + str(marksize) + '-' + str(marksize))
                    imposition_command.append(dirpathTempFolder + '/result-imp.tiff')
                    subprocess.Popen(imposition_command).wait()

                    last_width = 0
                    last_height = 0
                    last_marksize = marksize
                    for width in image_width:
                        for height in image_height:
                            if not (last_width == 0 and last_height == 0):
                                imposition_command = ['composite']
                                imposition_command.append('-geometry')
                                imposition_command.append('+'  + str(last_width + marksize) + '+' + str(last_height + marksize))
                                imposition_command.append(dirpathTempFolder + '/result.tiff')
                                imposition_command.append(dirpathTempFolder + '/result-imp.tiff')
                                imposition_command.append(dirpathTempFolder + '/result-imp.tiff')
                                subprocess.Popen(imposition_command).wait()

                            last_height += height + imposition_space
                            last_marksize = 0
                        last_width += width + imposition_space
                        last_height = 0

                    if self.prepress_paper_cutmarks_check.isChecked():
                        cutmarks.generate_final_file(False, self.prepress_paper_cutmarks_inside_check.isChecked(),list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()], image_width, image_height, imposition_space,inkex.unittouu(str(self.prepress_paper_cutmarks_strokewidth_value.text()) + str(self.prepress_paper_cutmarks_strokewidth_choice.currentText())), bleedsize, marksize, dirpathTempFolder)

                        cut_marks_command = ['composite']
                        cut_marks_command.append('-compose')
                        cut_marks_command.append('Multiply')
                        cut_marks_command.append('-gravity')
                        cut_marks_command.append('center')
                        cut_marks_command.append(dirpathTempFolder + '/cut_mark.tiff')
                        cut_marks_command.append(dirpathTempFolder + '/result-imp.tiff')
                        cut_marks_command.append(dirpathTempFolder + '/result-imp.tiff')
                        subprocess.Popen(cut_marks_command).wait()

                    jpeg_command.append(dirpathTempFolder +  '/result-imp.tiff')

                    if self.prepress_paper_settings_invert.isChecked():
                        jpeg_command.append('-negate')

                    if self.prepress_paper_settings_mirror.isChecked():
                        jpeg_command.append('-flop')

                    jpeg_command.append('-quality')
                    jpeg_command.append(str(self.quality_choice_dial_jpeg.value()))

                    jpeg_command.append('-colorspace')
                    jpeg_command.append(list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()])

                    if self.jpeg_interlace_option_jpeg.isChecked():
                        jpeg_command.append('-interlace')
                        jpeg_command.append(list_of_interlacing_jpeg[unicode(self.jpeg_interlace_choice_jpeg.currentText(), 'utf-8')])

                    if self.jpeg_optimize_option_jpeg.isChecked():
                        jpeg_command.append('-type')
                        jpeg_command.append('optimize')

                    if self.jpeg_noise_option_jpeg.isChecked():
                        jpeg_command.append('-evaluate')
                        jpeg_command.append(list_of_noise_jpeg[unicode(self.jpeg_noise_choice_jpeg.currentText(), 'utf-8')])
                        jpeg_command.append(str(self.jpeg_noise_ammount_jpeg.value()))

                    jpeg_command.append('-sampling-factor')
                    jpeg_command.append(self.jpeg_subsampling_choice_jpeg.currentText())

                    jpeg_command.append('-define')
                    jpeg_command.append('jpeg:dct-method=' + list_of_dct_jpeg[unicode(self.jpeg_dct_choice_jpeg.currentText(), 'utf-8')])

                    jpeg_command.append(dirpathTempFolder +  '/result-imp.jpeg')

                    subprocess.Popen(jpeg_command).wait()

            def change_format(self):
                self.general_options_panel_jpeg.setShown(False)

                if list_of_export_formats[self.format_choice.currentIndex()] == 'JPEG':
                    self.general_options_panel_jpeg.setShown(True)

                self.generate_preview()

            def change_color_mode_jpeg(self):
                if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMYK':
                    self.color_mode_title_tip_jpeg.setText(u'Recomendado para impressão gráfica')
                    self.cmyk_advanced_manipulation_option_jpeg.setChecked(False)
                    self.cmyk_advanced_manipulation_option_jpeg.setEnabled(True)
                    self.cmyk_overblack_jpeg.setEnabled(False)
                    self.cmyk_overblack_jpeg.setChecked(False)
                    self.color_profile_choice_jpeg.setEnabled(True)
                    self.color_profile_choice_jpeg.setChecked(False)
                    self.document_color_profile_title_jpeg.setEnabled(True)
                    self.general_prepress_panel.setEnabled(True)
                else:
                    self.cmyk_advanced_manipulation_option_jpeg.setEnabled(False)
                    self.cmyk_overblack_jpeg.setEnabled(False)
                    self.cmyk_overblack_jpeg.setChecked(False)
                    #self.color_profile_choice_jpeg.setEnabled(False)
                    self.color_profile_choice_jpeg.setChecked(False)
                    self.document_color_profile_title_jpeg.setEnabled(False)
                    self.general_prepress_panel.setEnabled(False)
                if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMY':
                    self.color_mode_title_tip_jpeg.setText(u'Recomendado para casos específicos de impressão')
                elif list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                    self.color_mode_title_tip_jpeg.setText(u'Recomendado para uso em telas')
                elif list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'Gray':
                    self.color_mode_title_tip_jpeg.setText(u'Imagem em tons de cinza')

                self.generate_preview()

            def change_quality_live_jpeg(self):
                self.quality_percent_title_jpeg.setText(str(self.quality_choice_dial_jpeg.value()) + '%')

            def jpeg_interlace_click_jpeg(self):
                if self.jpeg_interlace_option_jpeg.isChecked():
                    self.jpeg_interlace_choice_jpeg.setEnabled(True)
                else:
                    self.jpeg_interlace_choice_jpeg.setEnabled(False)
                self.generate_preview()

            def jpeg_noise_click_jpeg(self):
                if self.jpeg_noise_option_jpeg.isChecked():
                    self.jpeg_noise_choice_jpeg.setEnabled(True)
                    self.jpeg_noise_ammount_jpeg.setEnabled(True)
                else:
                    self.jpeg_noise_choice_jpeg.setEnabled(False)
                    self.jpeg_noise_ammount_jpeg.setEnabled(False)
                self.generate_preview()

            def cmyk_advanced_manipulation_click_jpeg(self):
                if self.cmyk_advanced_manipulation_option_jpeg.isChecked():
                    self.cmyk_overblack_jpeg.setEnabled(True)
                    self.view_c_button.setShown(True)
                    self.view_m_button.setShown(True)
                    self.view_y_button.setShown(True)
                    self.view_k_button.setShown(True)
                    self.cmyk_overprint_black()
                    self.cmyk_advanced_manipulation()

                else:
                    self.cmyk_overblack_jpeg.setEnabled(False)
                    self.cmyk_overblack_jpeg.setChecked(False)
                    self.view_c_button.setShown(False)
                    self.view_m_button.setShown(False)
                    self.view_y_button.setShown(False)
                    self.view_k_button.setShown(False)
                    self.generate_preview()

            def cmyk_overprint_black(self):
                if self.cmyk_overblack_jpeg.isChecked():
                    cmyk.generate_svg_separations(dirpathTempFolder +  '/', open(dirpathTempFolder +  '/original.svg').read(), True)
                else:
                    cmyk.generate_svg_separations(dirpathTempFolder +  '/', open(dirpathTempFolder +  '/original.svg').read(), False)

            def cmyk_advanced_manipulation(self):
                area_to_export = self.area_to_export()
                cmyk.generate_png_separations(dirpathTempFolder + '/', self.area_to_export(), self.dpi_choice.value(), False)

                for color in ['C', 'M', 'Y', 'K']:
                    subprocess.Popen(['convert', dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + color + ".png", '-colorspace', 'CMYK', '-channel', color, '-separate', dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + color + ".png"]).wait()

                self.cmyk_advanced_manipulation_view_separations()

            def cmyk_advanced_manipulation_view_separations(self):
                area_to_export = self.area_to_export()

                file_info = subprocess.Popen(['identify', dirpathTempFolder +  '/source.png'], stdout=subprocess.PIPE).communicate()[0]

                image_size = file_info.split(' ')[2]

                subprocess.Popen(['convert', '-size', image_size, 'xc:black', dirpathTempFolder +  '/empty.png']).wait()

                final_command = ['convert']

                if self.view_c_button.isChecked():
                    final_command.append(dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + 'C' + ".png")
                else:
                    final_command.append(dirpathTempFolder + '/' + "empty.png")

                if self.view_m_button.isChecked():
                    final_command.append(dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + 'M' + ".png")
                else:
                    final_command.append(dirpathTempFolder + '/' + "empty.png")

                if self.view_y_button.isChecked():
                    final_command.append(dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + 'Y' + ".png")
                else:
                    final_command.append(dirpathTempFolder + '/' + "empty.png")

                if self.view_k_button.isChecked():
                    final_command.append(dirpathTempFolder + '/' + "separated" + area_to_export.replace(' ', '') + 'K' + ".png")
                else:
                    final_command.append(dirpathTempFolder + '/' + "empty.png")

                final_command.extend(['-set', 'colorspace', 'cmyk'])
                final_command.extend(['-combine', dirpathTempFolder + '/' + 'result.tiff'])
                subprocess.Popen(final_command).wait()

                self.generate_preview()

            def area_to_export(self):
                if self.area_to_export_choice.currentIndex() == 1:
                    return ' -D '

                elif self.area_to_export_choice.currentIndex() == 2:
                    if self.area_to_export_idonly_check.isChecked():
                        return ' --export-id=' + str(self.area_to_export_id_name.text()) + ' --export-id-only '
                    else:
                        return ' --export-id=' + str(self.area_to_export_id_name.text())

                elif self.area_to_export_choice.currentIndex() == 3:
                    return ' --export-area=' + str(self.x0_value.value()) + ':' + str(self.y0_value.value()) + ':' + str(self.x1_value.value()) + ':' + str(self.y1_value.value())

                else:
                    return ' -C '

            def change_area_to_export(self):
                self.x0_value.setShown(False)
                self.y0_value.setShown(False)
                self.x1_value.setShown(False)
                self.y1_value.setShown(False)
                self.area_to_export_id_title.setShown(False)
                self.area_to_export_id_name.setShown(False)
                self.area_to_export_idonly_check.setShown(False)

                if self.area_to_export_choice.currentIndex() == 2:
                    self.area_to_export_id_name.setText(selected_object)
                    self.area_to_export_id_title.setShown(True)
                    self.area_to_export_id_name.setShown(True)
                    self.area_to_export_idonly_check.setShown(True)

                elif self.area_to_export_choice.currentIndex() == 3:
                    self.x0_value.setShown(True)
                    self.y0_value.setShown(True)
                    self.x1_value.setShown(True)
                    self.y1_value.setShown(True)

                os.system('inkscape' + ' -z --file="' + dirpathTempFolder +  '/original.svg" ' + self.area_to_export() + ' --export-dpi=' + str(self.dpi_choice.value()) + ' --export-background-opacity=1 --export-png="' + dirpathTempFolder + '/source.png"' + null_dir)
                subprocess.Popen(['convert', dirpathTempFolder + '/source.png', dirpathTempFolder + '/source.tiff']).wait()

                self.generate_preview()

            def zoom_out(self):
                self.preview_zoom += 0.1
                self.generate_preview()

                if int(self.preview_zoom * 100) == 200:
                    self.zoom_out_button.setEnabled(False)
                self.zoom_in_button.setEnabled(True)

                self.preview_zoom_title.setText(str(int(self.preview_zoom * 100)) + '%')

            def zoom_in(self):
                self.preview_zoom -= 0.1
                self.generate_preview()

                if int(self.preview_zoom * 100) == 10:
                    self.zoom_in_button.setEnabled(False)
                self.zoom_out_button.setEnabled(True)

                self.preview_zoom_title.setText(str(int(self.preview_zoom * 100)) + '%')

            def cut_marks_insert_change(self):
                if self.prepress_paper_cutmarks_check.isChecked():
                    self.prepress_paper_cutmarks_strokewidth_label.setEnabled(True)
                    self.prepress_paper_cutmarks_strokewidth_value.setEnabled(True)
                    self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(True)
                    self.prepress_paper_cutmarks_bleedsize_label.setEnabled(True)
                    self.prepress_paper_cutmarks_bleedsize_value.setEnabled(True)
                    self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(True)
                    self.prepress_paper_cutmarks_marksize_label.setEnabled(True)
                    self.prepress_paper_cutmarks_marksize_value.setEnabled(True)
                    self.prepress_paper_cutmarks_marksize_choice.setEnabled(True)
                    self.prepress_paper_cutmarks_inside_check.setEnabled(True)

                else:
                    self.prepress_paper_cutmarks_strokewidth_label.setEnabled(False)
                    self.prepress_paper_cutmarks_strokewidth_value.setEnabled(False)
                    self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(False)
                    self.prepress_paper_cutmarks_bleedsize_label.setEnabled(False)
                    self.prepress_paper_cutmarks_bleedsize_value.setEnabled(False)
                    self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(False)
                    self.prepress_paper_cutmarks_marksize_label.setEnabled(False)
                    self.prepress_paper_cutmarks_marksize_value.setEnabled(False)
                    self.prepress_paper_cutmarks_marksize_choice.setEnabled(False)
                    self.prepress_paper_cutmarks_inside_check.setEnabled(False)

                self.generate_preview()

            def format_preview_change(self):
                if self.format_preview_check.isChecked():
                    self.resize(950, 600)
                    self.setMaximumSize(QtCore.QSize(950, 600))
                    self.setMinimumSize(QtCore.QSize(950, 600))
                    self.preview_panel.setShown(True)
                    self.option_box.setGeometry(320, 120, 620, 435)
                    self.format_title.setGeometry(320, 70, 200, 15)
                    self.format_choice.setGeometry(320, 85, 200, 25)
                    self.export_button.setGeometry(740, 560, 200, 30)
                    self.format_preview_check.setGeometry(540, 85, 200, 25)
                else:
                    self.resize(640, 600)
                    self.setMaximumSize(QtCore.QSize(640, 600))
                    self.setMinimumSize(QtCore.QSize(640, 600))
                    self.preview_panel.setShown(False)
                    self.option_box.setGeometry(10, 120, 620, 435)
                    self.format_title.setGeometry(10, 70, 200, 15)
                    self.format_choice.setGeometry(10, 85, 200, 25)
                    self.export_button.setGeometry(430, 560, 200, 30)
                    self.format_preview_check.setGeometry(230, 85, 200, 25)

                self.move((QtGui.QDesktopWidget().screenGeometry().width()-self.geometry().width())/2, (QtGui.QDesktopWidget().screenGeometry().height()-self.geometry().height())/2)

            def export(self):
                self.location_path = QtGui.QFileDialog.getSaveFileName(self, _(u"Salvar imagem"), os.environ.get('HOME', None), list_of_export_formats[self.format_choice.currentIndex()]).toUtf8()

                if not self.format_preview_check.isChecked():
                    self.generate_final_file()

                if not str(self.location_path) == '':
                    shutil.copy2(dirpathTempFolder +  '/result-imp.' + list_of_export_formats[self.format_choice.currentIndex()].lower(), self.location_path)



        app = QtGui.QApplication(sys.argv)
        app.main = mainWindow()
        app.main.show()

        sys.exit(app.exec_())


if __name__ == '__main__':
    e = OutputProBitmap()
    e.affect()
