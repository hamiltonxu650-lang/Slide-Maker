from PyQt6 import QtGui


APP_STYLE = """
QWidget {
    color: #17191F;
    background: transparent;
    font-family: ".AppleSystemUIFont", "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", "Helvetica Neue";
    font-size: 14px;
}
QMainWindow {
    background: #EFF0F4;
}
#WindowRoot {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EAF0FF, stop:0.42 #EFF0F4, stop:1 #EAF8F2);
}
#AppSurface {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EAF0FF, stop:0.48 #EFF0F4, stop:1 #EAF8F2);
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 20px;
}
#AppSurface[nativeMacChrome="true"] {
    border: none;
    border-radius: 0px;
}
#AppSurface[maximized="true"] {
    border: none;
    border-radius: 0px;
}
#TitleBar {
    background: #F7F8FB;
    border-bottom: 1px solid rgba(24, 27, 34, 0.08);
    border-top-left-radius: 20px;
    border-top-right-radius: 20px;
}
#TitleBar[maximized="true"] {
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
}
#TitleBrand {
    font-size: 16px;
    font-weight: 800;
    color: #17191F;
}
#TitleMeta {
    color: #7C828D;
    font-size: 11px;
}
#Sidebar {
    background: rgba(241, 239, 232, 0.72);
    border-right: 1px solid rgba(24, 27, 34, 0.08);
    border-bottom-left-radius: 20px;
}
#Sidebar[nativeMacChrome="true"] {
    border-bottom-left-radius: 0px;
}
#Sidebar[maximized="true"] {
    border-bottom-left-radius: 0px;
}
#SidebarBrand {
    font-size: 12px;
    font-weight: 800;
    color: #17191F;
}
#SidebarCaption {
    color: #7C828D;
    font-size: 11px;
}
#RailDock {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.04);
    border-radius: 32px;
}
QPushButton#RailButton {
    background: transparent;
    border: none;
    border-radius: 22px;
    padding: 0;
}
QPushButton#RailButton:hover {
    background: rgba(47, 120, 255, 0.08);
}
QPushButton#RailButton[active="true"] {
    background: #1B1F2C;
}
QPushButton#NavButton {
    color: #383D48;
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.06);
    border-radius: 18px;
    padding: 12px 10px;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#NavButton:hover {
    background: #F6F7FA;
    border-color: rgba(47, 120, 255, 0.16);
}
QPushButton#NavButton[active="true"] {
    color: #FFE75F;
    background: #1B1F2C;
    border-color: #1B1F2C;
}
QPushButton#WindowButton, QPushButton#CloseButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 0;
    color: #485160;
    font-size: 13px;
    font-weight: 800;
}
QPushButton#WindowButton:hover {
    background: rgba(24, 27, 34, 0.06);
}
QPushButton#CloseButton:hover {
    background: #E14A4A;
    color: #FFFFFF;
}
#SectionEyebrow {
    color: #7C828D;
    font-size: 12px;
    font-weight: 800;
}
#SectionTitle {
    color: #17191F;
    font-size: 30px;
    font-weight: 900;
}
#SectionCaption {
    color: #7C828D;
    font-size: 13px;
}
#WelcomeIcon {
    border-radius: 16px;
}
#DashboardTitle {
    color: #17191F;
    font-size: 28px;
    font-weight: 900;
}
#DashboardSubtitle {
    color: #7C828D;
    font-size: 14px;
}
#FuturePanel {
    background: rgba(255, 255, 255, 0.54);
    border: 1px solid rgba(255, 255, 255, 0.68);
    border-radius: 32px;
}
#FutureTitle {
    color: #17191F;
    font-size: 20px;
    font-weight: 900;
}
#AboutPage {
    background: transparent;
}
#AboutCenter {
    background: transparent;
}
#AboutIcon {
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.90);
    border-radius: 24px;
}
#AboutTitle {
    color: #17191F;
    font-size: 36px;
    font-weight: 900;
}
#AboutSubtitle {
    color: #7C828D;
    font-size: 17px;
    font-weight: 800;
}
#AboutVersionPill {
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.80);
    border-radius: 20px;
    padding: 0;
    color: #7C828D;
    font-size: 14px;
    font-weight: 800;
}
#AboutSlogan {
    color: #17191F;
    font-size: 17px;
    font-weight: 900;
}
#AboutDescription {
    color: #7C828D;
    font-size: 16px;
    font-weight: 700;
    line-height: 150%;
}
#AboutMeta {
    color: #7C828D;
    font-size: 15px;
    font-weight: 750;
}
QPushButton#AboutActionButton {
    background: rgba(255, 255, 255, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.82);
    border-radius: 27px;
    padding: 0 22px;
    color: #17191F;
    font-size: 15px;
    font-weight: 850;
}
QPushButton#AboutActionButton:hover {
    background: #FFFFFF;
}
#UpdateDialog {
    background: transparent;
    border-radius: 28px;
}
#UpdateDialogCard {
    background: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.82);
    border-radius: 28px;
}
#UpdateDialogTitle {
    color: #17191F;
    font-size: 22px;
    font-weight: 900;
}
#UpdateDialogVersion {
    background: rgba(239, 240, 244, 0.92);
    border-radius: 16px;
    padding: 7px 16px;
    color: #7C828D;
    font-size: 13px;
    font-weight: 850;
}
#UpdateDialogBody {
    color: #596171;
    font-size: 14px;
    line-height: 155%;
}
#UpdateDialogEmail {
    background: rgba(47, 120, 255, 0.08);
    border: 1px solid rgba(47, 120, 255, 0.12);
    border-radius: 18px;
    padding: 10px 16px;
    color: #2F78FF;
    font-size: 15px;
    font-weight: 850;
}
QPushButton#UpdateDialogHelpButton {
    background: rgba(239, 240, 244, 0.82);
    border: 1px solid rgba(24, 27, 34, 0.06);
    border-radius: 20px;
    padding: 0 16px;
    color: #17191F;
    font-size: 13px;
    font-weight: 850;
}
QPushButton#UpdateDialogHelpButton:hover {
    background: #FFFFFF;
}
QPushButton#UpdateDialogButton {
    background: #17191F;
    border: none;
    border-radius: 21px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 900;
}
QPushButton#UpdateDialogButton:hover {
    background: #2A2E39;
}
#ProgressColumn {
    background: #EEF4F3;
    border-left: 1px solid rgba(24, 27, 34, 0.08);
}
#StatusPanelShell {
    background: transparent;
    border: none;
}
#StatusColumnScroll {
    background: transparent;
    border: none;
}
#StatusColumnScroll QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 8px 0 8px 0;
}
#StatusColumnScroll QScrollBar::handle:vertical {
    background: rgba(122, 132, 153, 0.32);
    border-radius: 4px;
    min-height: 42px;
}
#StatusColumnScroll QScrollBar::add-line:vertical,
#StatusColumnScroll QScrollBar::sub-line:vertical {
    height: 0px;
}
#StatusPanel, #AreasCard, #InfoPageCard, #PreferencePanel, #SettingCard {
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.82);
    border-radius: 32px;
}
#SubtleCard {
    background: rgba(229, 231, 237, 0.86);
    border: 1px solid rgba(24, 27, 34, 0.06);
    border-radius: 20px;
}
#ConnectorCard {
    background: rgba(229, 231, 237, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.64);
    border-radius: 32px;
}
#ConnectorTitle {
    color: #17191F;
    font-size: 18px;
    font-weight: 900;
}
#ConnectorMeta {
    color: #7C828D;
    font-size: 13px;
}
#ConnectorIcon, QPushButton#ConnectorIconButton {
    background: #FFFFFF;
    border: none;
    border-radius: 21px;
}
QPushButton#ConnectorIconButton:hover {
    background: #F6F7FA;
}
#UploadPill {
    background: #FFFFFF;
    border: none;
    border-radius: 25px;
    padding: 0 24px;
    color: #17191F;
    font-size: 14px;
    font-weight: 900;
}
QPushButton#UploadPill:hover {
    background: #F6F7FA;
}
QPushButton#CircleIconButton {
    background: #FFFFFF;
    border: none;
    border-radius: 22px;
}
QPushButton#CircleIconButton:hover {
    background: #F6F7FA;
}
#StatusTitle, #SettingTitle {
    color: #17191F;
    font-size: 21px;
    font-weight: 900;
}
#StatusCaption, #SettingCaption {
    color: #7C828D;
    font-size: 14px;
}
#ProgressPercent {
    color: #17191F;
    font-size: 31px;
    font-weight: 900;
}
#ProgressStage {
    color: #7C828D;
    font-size: 13px;
    font-weight: 800;
}
#ProgressDetail {
    color: #596171;
    font-size: 15px;
}
#ProgressStepList {
    border-top: 1px solid rgba(24, 27, 34, 0.08);
    border-bottom: 1px solid rgba(24, 27, 34, 0.08);
}
#ProgressStep {
    border-bottom: 1px solid rgba(24, 27, 34, 0.08);
}
#ProgressStepNumber {
    color: #B8BFCC;
    font-weight: 900;
}
#ProgressStepTitle {
    color: #17191F;
    font-size: 15px;
    font-weight: 900;
}
#ProgressStepDetail {
    color: #7C828D;
    font-size: 13px;
}
#ProgressStep[state="active"] #ProgressStepNumber,
#ProgressStep[state="done"] #ProgressStepNumber {
    color: #2F78FF;
}
#ProgressStep[state="error"] #ProgressStepNumber {
    color: #FF6673;
}
#ProgressStep[state="pending"] #ProgressStepTitle,
#ProgressStep[state="pending"] #ProgressStepDetail {
    color: #9AA2B1;
}
#ToggleTitle {
    color: #17191F;
    font-size: 14px;
    font-weight: 900;
}
#ToggleDetail {
    color: #7C828D;
    font-size: 12px;
}
#TaskNoteEdit {
    background: #F6F7FA;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 18px;
    padding: 12px;
    color: #17191F;
    font-size: 13px;
}
#ParameterTitle {
    color: #17191F;
    font-size: 13px;
    font-weight: 850;
}
#ParameterValue {
    color: #596171;
    font-size: 13px;
    font-weight: 850;
}
QProgressBar#ParameterBar {
    background: #E7E9EF;
    border: none;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
}
QProgressBar#ParameterBar::chunk {
    background: #2F78FF;
    border-radius: 5px;
}
#MutedLabel {
    color: #7C828D;
    font-size: 12px;
    font-weight: 700;
}
#PathValue {
    color: #17191F;
    font-size: 12px;
    font-weight: 700;
}
#PathField {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 14px;
    padding: 8px 10px;
    color: #17191F;
    font-size: 12px;
    font-weight: 700;
    selection-background-color: rgba(47, 120, 255, 0.20);
}
#InlineBanner {
    background: rgba(47, 120, 255, 0.08);
    border: 1px solid rgba(47, 120, 255, 0.16);
    border-radius: 16px;
    padding: 12px;
    color: #2F78FF;
    font-weight: 800;
}
#MutedNotice {
    border-radius: 16px;
    padding: 12px;
    color: #485160;
    font-weight: 800;
}
QProgressBar {
    background: #E7E9EF;
    border: none;
    border-radius: 8px;
    min-height: 12px;
    max-height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    border-radius: 8px;
    background: #2F78FF;
}
QProgressBar#ParameterBar {
    background: #E7E9EF;
    border: none;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
}
QProgressBar#ParameterBar::chunk {
    background: #2F78FF;
    border-radius: 5px;
}
QPushButton#ActionButton {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 16px;
    padding: 12px 14px;
    color: #17191F;
    font-weight: 800;
}
QPushButton#ActionButton:hover {
    background: #F6F7FA;
}
QPushButton#PrimaryActionButton {
    background: #2F78FF;
    border: none;
    border-radius: 18px;
    padding: 12px 16px;
    color: #FFFFFF;
    font-weight: 900;
}
QPushButton#PrimaryActionButton:hover {
    background: #2369EA;
}
QPushButton#SecondaryTextButton {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 16px;
    padding: 10px 12px;
    color: #17191F;
    font-weight: 800;
}
QPushButton#SecondaryTextButton:hover {
    background: #F6F7FA;
}
QLabel#StageTitle {
    color: #17191F;
    font-weight: 800;
}
QLabel#StageDetail, #PreferenceHint {
    color: #7C828D;
    font-size: 12px;
}
QListWidget {
    background: transparent;
    border: none;
    color: #17191F;
}
QListWidget::item {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.08);
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
    background: #CBD0DA;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 0;
    margin: 0;
}
QScrollBar::handle:horizontal,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    height: 0;
}
QCheckBox, QRadioButton {
    color: #17191F;
    spacing: 10px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
}
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid #C8CDD7;
    background: #FFFFFF;
    border-radius: 9px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    border: 1px solid #2F78FF;
    background: #2F78FF;
    border-radius: 9px;
}
QLineEdit, QPlainTextEdit, QComboBox {
    background: #F6F7FA;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 16px;
    padding: 10px 12px;
    color: #17191F;
}
#TaskNoteEdit {
    background: #F6F7FA;
    border: 1px solid rgba(24, 27, 34, 0.08);
    border-radius: 18px;
    padding: 12px;
    color: #17191F;
    font-size: 13px;
}
QPlainTextEdit {
    padding-top: 12px;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid rgba(24, 27, 34, 0.08);
    selection-background-color: rgba(47, 120, 255, 0.14);
    color: #17191F;
}
#PreferenceChoice {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 30px;
}
#PreferenceChoice[active="true"] {
    background: rgba(255, 255, 255, 0.96);
    border-color: rgba(255, 255, 255, 0.92);
}
#PreferenceChoiceTitle {
    color: #17191F;
    font-size: 16px;
    font-weight: 900;
}
#PreferenceChoice[active="true"] QLabel {
    color: #17191F;
}
#PreferenceSegmentBar {
    background: rgba(226, 228, 234, 0.92);
    border: 1px solid rgba(24, 27, 34, 0.05);
    border-radius: 36px;
}
#PreferenceChoiceIcon {
    color: #17191F;
}
"""


def apply_theme(app):
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#EFF0F4"))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#17191F"))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#17191F"))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#2F78FF"))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLE)
