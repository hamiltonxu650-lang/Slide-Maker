from PyQt6 import QtGui


APP_STYLE = """
QWidget {
    color: #F5F2FF;
    background: transparent;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 14px;
}
QMainWindow {
    background: transparent;
}
#WindowRoot {
    background: transparent;
}
#AppSurface {
    background: #12111A;
    border: 1px solid #2A2638;
    border-radius: 20px;
}
#AppSurface[maximized="true"] {
    border: none;
    border-radius: 0px;
}
#TitleBar {
    background: #15131C;
    border-bottom: 1px solid #242131;
    border-top-left-radius: 20px;
    border-top-right-radius: 20px;
}
#TitleBar[maximized="true"] {
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
}
#TitleBrand {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
}
#TitleMeta {
    color: #B8B1D6;
    font-size: 11px;
}
#Sidebar {
    background: #100F17;
    border-right: 1px solid #242131;
    border-bottom-left-radius: 20px;
}
#Sidebar[maximized="true"] {
    border-bottom-left-radius: 0px;
}
#SidebarBrand {
    font-size: 18px;
    font-weight: 700;
    color: #FFFFFF;
}
#SidebarCaption {
    color: #9F98BE;
    font-size: 12px;
}
QPushButton#NavButton {
    text-align: left;
    color: #C7C1E4;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 16px;
    padding: 14px 16px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#NavButton:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: #2B2840;
}
QPushButton#NavButton[active="true"] {
    color: #FFFFFF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D3EF6, stop:1 #FF6B3D);
}
QPushButton#WindowButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px;
}
QPushButton#WindowButton:hover {
    background: rgba(255, 255, 255, 0.08);
}
QPushButton#CloseButton:hover {
    background: #D24A44;
}
#SectionEyebrow {
    color: #FFB56D;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}
#SectionTitle {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 800;
}
#SectionCaption {
    color: #A8A1C6;
    font-size: 13px;
}
#StatusPanel, #InfoPageCard, #PreferencePanel, #SettingCard {
    background: #171522;
    border: 1px solid #29253A;
    border-radius: 24px;
}
#SubtleCard {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
}
#StatusTitle, #SettingTitle {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 800;
}
#StatusCaption, #SettingCaption {
    color: #A39BBC;
    font-size: 13px;
}
#MutedLabel {
    color: #A39BBC;
    font-size: 12px;
}
#PathValue {
    color: #F2EFFF;
    font-size: 12px;
    font-weight: 600;
}
#PathField {
    background: #0E0D14;
    border: 1px solid #252137;
    border-radius: 12px;
    padding: 8px 10px;
    color: #F2EFFF;
    font-size: 12px;
    font-weight: 600;
    selection-background-color: #3B3656;
}
#InlineBanner {
    background: rgba(255, 176, 109, 0.12);
    border: 1px solid rgba(255, 176, 109, 0.28);
    border-radius: 14px;
    padding: 12px;
    color: #FFD8AC;
    font-weight: 700;
}
#MutedNotice {
    border-radius: 14px;
    padding: 12px;
    color: #F3E7D9;
    font-weight: 700;
}
QProgressBar {
    background: #0F0E15;
    border: 1px solid #2A2740;
    border-radius: 12px;
    min-height: 14px;
    max-height: 14px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    border-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF4F6A, stop:1 #FF8B3D);
}
QPushButton#ActionButton {
    background: #232036;
    border: 1px solid #342F4B;
    border-radius: 14px;
    padding: 12px 14px;
    color: #F4F0FF;
    font-weight: 700;
}
QPushButton#ActionButton:hover {
    background: #2C2741;
}
QPushButton#PrimaryActionButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF4F6A, stop:1 #FF8B3D);
    border: none;
    border-radius: 14px;
    padding: 12px 16px;
    color: #FFFFFF;
    font-weight: 800;
}
QPushButton#PrimaryActionButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6A80, stop:1 #FF9D58);
}
QPushButton#SecondaryTextButton {
    background: transparent;
    border: 1px solid #302C42;
    border-radius: 12px;
    padding: 10px 12px;
    color: #E8E3FF;
    font-weight: 700;
}
QPushButton#SecondaryTextButton:hover {
    background: rgba(255,255,255,0.04);
}
QLabel#StageTitle {
    color: #ECE8FF;
    font-weight: 700;
}
QLabel#StageDetail, #PreferenceHint {
    color: #938BAE;
    font-size: 12px;
}
QListWidget {
    background: transparent;
    border: none;
    color: #F4F0FF;
}
QListWidget::item {
    background: #171522;
    border: 1px solid #29253A;
    border-radius: 18px;
    padding: 12px;
    margin-bottom: 10px;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 10px 0 10px 0;
}
QScrollBar::handle:vertical {
    background: #343048;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QCheckBox, QRadioButton {
    color: #F5F2FF;
    spacing: 10px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
}
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid #544C70;
    background: #151320;
    border-radius: 9px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    border: 1px solid #FF8B3D;
    background: #FF8B3D;
    border-radius: 9px;
}
QLineEdit, QPlainTextEdit, QComboBox {
    background: #0E0D14;
    border: 1px solid #252137;
    border-radius: 14px;
    padding: 10px 12px;
    color: #F2EFFF;
}
QPlainTextEdit {
    padding-top: 12px;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #171522;
    border: 1px solid #2A2740;
    selection-background-color: #2C2741;
    color: #F2EFFF;
}
#PreferenceChoice {
    background: rgba(255,255,255,0.03);
    border: 1px solid #2B2840;
    border-radius: 18px;
}
"""


def apply_theme(app):
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#12111A"))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#12111A"))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#F5F2FF"))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#F5F2FF"))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#FF7C4C"))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLE)
