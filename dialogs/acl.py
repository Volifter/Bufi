from PyQt5 import QtCore, QtWidgets

from dialogs.yn import show_yn_dialog

class AclDialog:
    def __init__(self, username, rights, parent):
        self.parent = parent
        self.saved = False
        self.dialog = QtWidgets.QDialog(parent)
        self.dialog.setObjectName("dialog")
        self.dialog.resize(400, 100)
        self.dialog.setMaximumSize(QtCore.QSize(1280, 720))
        vertical_layout = QtWidgets.QVBoxLayout()
        horizontal_info_layout = QtWidgets.QHBoxLayout()
        horizontal_buttons_layout = QtWidgets.QHBoxLayout()
        self.username = QtWidgets.QLineEdit(username)
        self.r_cb = QtWidgets.QCheckBox("r")
        self.w_cb = QtWidgets.QCheckBox("w")
        self.a_cb = QtWidgets.QCheckBox("a")
        self.r_cb.setChecked("r" in rights)
        self.w_cb.setChecked("w" in rights)
        self.a_cb.setChecked("a" in rights)
        ok_button = QtWidgets.QPushButton("Ok")
        cancel_button = QtWidgets.QPushButton("Cancel")
        horizontal_info_layout.addWidget(self.username)
        horizontal_info_layout.addWidget(self.r_cb)
        horizontal_info_layout.addWidget(self.w_cb)
        horizontal_info_layout.addWidget(self.a_cb)
        horizontal_buttons_layout.addWidget(ok_button)
        horizontal_buttons_layout.addWidget(cancel_button)
        vertical_layout.addLayout(horizontal_info_layout)
        vertical_layout.addLayout(horizontal_buttons_layout)
        self.dialog.setLayout(vertical_layout)
        ok_button.clicked.connect(self.on_ok_button_click)
        cancel_button.clicked.connect(self.on_cancel_button_click)

    def show(self):
        self.dialog.exec_()
        acl = ""
        if (self.r_cb.isChecked()):
            acl += "r"
        if (self.w_cb.isChecked()):
            acl += "w"
        if (self.a_cb.isChecked()):
            acl += "a"
        if (self.saved):
            return (self.username.text(), acl)
        return (None, None)

    def on_ok_button_click(self):
        if (not self.r_cb.isChecked() and
            not self.w_cb.isChecked() and
            not self.a_cb.isChecked()):
            return
        if (self.username.text() == "ramassage-tek" and
            not self.r_cb.isChecked() and
            not show_yn_dialog(
            self.parent,
            "Hey, listen!\n\n"\
            "Since ramassage-tek will not be given the \"r\" permission, Marvin will not be able to examine your repository.\n"\
            "Save anyway?"
        )):
            return
        self.saved = True
        self.dialog.close()

    def on_cancel_button_click(self):
        self.dialog.close()
