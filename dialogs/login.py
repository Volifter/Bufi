from PyQt5 import QtWidgets

import designs.login

class LoginDialog:
    def __init__(self, parent):
        self.submitted = False
        self.window = designs.login.Ui_Dialog()
        self.form = QtWidgets.QDialog(parent)
        self.window.setupUi(self.form)

        self.window.ok_button.clicked.connect(self.ok_button_clicked)

    def show(self):
        self.form.show()
        self.form.exec_()
        if (not self.submitted):
            return (None, None, None)
        return (
            self.window.login_input.text(),
            self.window.password_input.text(),
            self.window.remember_me_check.isChecked()
        )

    def ok_button_clicked(self):
        self.submitted = True
        if (self.window.login_input.text() and self.window.password_input.text()):
            self.form.close()
