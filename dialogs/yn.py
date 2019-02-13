from PyQt5 import QtWidgets

def show_yn_dialog(parent, question = "Are you sure?"):
    dialog = QtWidgets.QMessageBox(parent)
    dialog.setWindowTitle("Dialog")
    dialog.setText(question)
    dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    dialog.setDefaultButton(QtWidgets.QMessageBox.No)
    return dialog.exec_() == QtWidgets.QMessageBox.Yes
