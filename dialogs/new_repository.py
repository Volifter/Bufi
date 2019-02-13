from PyQt5 import QtWidgets

import designs.new_repository

class NewRepositoryDialog:
    def __init__(self, parent):
        self.saved = False
        self.window = designs.new_repository.Ui_Dialog()
        self.form = QtWidgets.QDialog(parent)
        self.window.setupUi(self.form)
        self.clone_path = ""

        self.window.clone_check.toggled.connect(self.on_clone_checked)
        self.window.select_clone_dir_button.clicked.connect(self.on_clone_dir_button_clicked)
        self.window.cancel_button.clicked.connect(self.cancel_button_clicked)
        self.window.create_button.clicked.connect(self.create_button_clicked)

    def show(self):
        self.form.show()
        self.form.exec_()
        if (self.saved):
            return (
                self.window.name_input.text(),
                self.window.description_input.toPlainText() or None,
                self.window.ramassage_acl_check.isChecked(),
                self.clone_path if self.window.clone_check.isChecked() else ""
            )
        return (None, None, None, None)

    def on_clone_checked(self, is_checked):
        self.window.select_clone_dir_button.setEnabled(is_checked)

    def on_clone_dir_button_clicked(self):
        self.clone_path = QtWidgets.QFileDialog.getExistingDirectory()
        if (self.clone_path):
            self.window.select_clone_dir_button.setText(self.clone_path)

    def cancel_button_clicked(self):
        self.form.close()

    def create_button_clicked(self):
        self.saved = True
        self.form.close()
