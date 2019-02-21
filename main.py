#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets

from bufi                   import Bufi

from dialogs.yn             import show_yn_dialog
from dialogs.login          import LoginDialog
from dialogs.new_repository import NewRepositoryDialog
from dialogs.acl            import AclDialog

import designs.main as design

import os
import sys
import time

def get_module(name):
    split_name = name.split("_")
    if (len(split_name) < 3):
        return None
    return split_name[0]

class App:
    def __init__(self):
        self.window = design.Ui_Bufi()
        self.app = QtWidgets.QApplication(sys.argv)
        self.form = QtWidgets.QMainWindow()
        self.window.setupUi(self.form)
        self.form.show()
        self.is_repository_selected = True

        session = self.get_saved_session()
        remember_me = False

        if (session):
            login, password = session[0], session[1]
        else:
            (login, password, remember_me) = LoginDialog(self.form).show()
            if (not login or not password):
                exit(1)

        acl_table = self.window.acl_table
        acl_header = acl_table.horizontalHeader()
        acl_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        acl_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        sp = self.window.repository_properties_form.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.window.repository_properties_form.setSizePolicy(sp)
        self.window.search_input.setFocus()
        self.reset_repository_info()

        self.window.modules_dropdown.currentTextChanged.connect(self.on_filter_settings_changed)
        self.window.search_input.textChanged.connect(self.on_filter_settings_changed)

        self.window.new_repository_button.clicked.connect(self.on_new_repository_clicked)
        self.window.delete_repository_button.clicked.connect(self.on_delete_repository_clicked)
        self.window.repositories_list.currentItemChanged.connect(self.on_repository_chosen)
        self.window.acl_table.currentItemChanged.connect(self.on_acl_chosen)
        self.window.edit_acl_button.clicked.connect(self.on_edit_acl_click)
        self.window.remove_acl_button.clicked.connect(self.on_remove_acl_click)
        self.window.add_acl_button.clicked.connect(self.on_add_acl_click)

        self.window.ssh_keys_list.currentItemChanged.connect(self.on_ssh_key_chosen)
        self.window.new_ssh_key_button.clicked.connect(self.on_new_ssh_key_clicked)
        self.window.delete_ssh_key_button.clicked.connect(self.on_delete_ssh_key_clicked)

        user_names = login.split("@")[0].split(".")
        names_str = user_names[0].capitalize() + (" " + user_names[1].upper() if len(user_names) > 1 else "")
        self.window.user_name_label.setText(names_str)
        self.window.logout_button.clicked.connect(self.on_logout_click)

        self.bufi = Bufi(login, password, self.form, bool(session))
        if (not self.bufi.check_token()):
            self.clear_session()
            exit(1)
        if (remember_me):
            self.save_session()

        self.window.new_repository_button.setEnabled(True)
        self.update_repositories()
        self.update_ssh_keys()

    # Event handlers

    def on_filter_settings_changed(self):
        self.update_repositories(False)

    def on_new_repository_clicked(self):
        (repository_name, description, set_ramassage_acl, clone_path) = NewRepositoryDialog(self.form).show()

        if (not repository_name):
            return
        self.toggle_repositories_list_lock(False)
        self.bufi.create_repository(
            repository_name,
            description,
            set_ramassage_acl
        )
        if (clone_path):
            try:
                os.system(
                    "git clone git@git.epitech.eu:/" +
                    self.bufi.get_username() +
                    "/" + repository_name +
                    " " + clone_path + "/" + repository_name
                )
            except:
                print("Failed to clone repository, moving on...")
        self.update_repositories()

    def on_delete_repository_clicked(self):
        if (not self.chosen_repository):
            return
        if (not show_yn_dialog(self.form, "Are you sure you want to delete \"{}\"?".format(self.chosen_repository))):
            return
        self.reset_repository_info()
        self.toggle_repositories_list_lock(False)
        self.bufi.delete_repository(self.chosen_repository)
        self.chosen_repository = None
        self.update_repositories()

    def on_ssh_key_chosen(self, element):
        if (element):
            self.window.delete_ssh_key_button.setEnabled(True)
            self.window.ssh_key_info.setEnabled(True)
        self.chosen_ssh_key = element.text() if element else ""
        ssh_key_info = self.bufi.get_ssh_key(self.chosen_ssh_key)
        self.window.ssh_info_owner_label.setText(self.chosen_ssh_key)
        self.window.ssh_info_type_label.setText(ssh_key_info[0])
        self.window.key_contents_text.setPlainText(ssh_key_info[1])

    def on_new_ssh_key_clicked(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Upload SSH key",
            os.path.expanduser("~/.ssh"),
            "Public SSH key files (*.pub);;All files (*)"
        )[0]
        print(self.bufi.upload_ssh_key(filename))
        self.update_ssh_keys()

    def on_delete_ssh_key_clicked(self):
        if (not self.chosen_ssh_key):
            return
        if (not show_yn_dialog(
            self.form,
            "Are you sure you want to delete "\
            "the SSH key for \"{}\"?".format(self.chosen_ssh_key))):
            return
        self.reset_ssh_key_info()
        self.toggle_ssh_keys_list_lock(False)
        print(self.bufi.delete_ssh_key(self.chosen_ssh_key))
        self.chosen_ssh_key = None
        self.update_ssh_keys()

    def on_repository_chosen(self, element = None):
        self.is_repository_selected = False
        QtCore.QCoreApplication.processEvents()

        if (element):
            self.chosen_repository = element.text()
        else:
            return
        if (not self.chosen_repository in self.repositories):
            return

        self.window.repository_name_label.setText(self.chosen_repository)
        info = self.bufi.repository_info(self.chosen_repository)

        creation_time_rows = time.ctime(int(info["creation_time"])).split(" ")
        creation_time_rows = list(filter(None, creation_time_rows))
        self.window.info_created_on_label.setText(
            "{} {} {}\t{}".format(
                creation_time_rows[2] if len(creation_time_rows) > 2 else "",
                creation_time_rows[1] if len(creation_time_rows) > 1 else "",
                creation_time_rows[4] if len(creation_time_rows) > 4 else "",
                creation_time_rows[3] if len(creation_time_rows) > 3 else ""
            )
        )
        self.window.info_description_label.setText(info["description"])
        self.window.info_type_label.setText(
            "Public" if info["public"] == "True" else "Private"
        )
        self.acl = self.bufi.repository_acl(self.chosen_repository)
        self.update_acl()
        self.window.repository_properties_form.show()
        self.window.repository_info_widget.setEnabled(True)
        self.window.delete_repository_button.setEnabled(True)
        self.is_repository_selected = True

    def on_add_acl_click(self):
        if (not self.is_repository_selected):
            return
        (user_name, acl) = AclDialog("", "", self.form).show()
        if (not user_name):
            return

        if(self.bufi.set_repository_acl(self.chosen_repository, user_name, acl)):
            self.acl[user_name] = acl
            self.update_acl()

    def on_remove_acl_click(self):
        if (not self.is_repository_selected):
            return
        user_name = self.window.acl_table.item(self.window.acl_table.currentRow(), 0).text()
        if (user_name == "ramassage-tek" and
            not show_yn_dialog(
                self.form,
                "Hey, listen!\n\n"\
                "Removing ramassage-tek's acl will prevent Marvin from examining your repository.\n"\
                "Are you sure that's what you want?"
            )):
            return
        if(self.bufi.set_repository_acl(self.chosen_repository, user_name, "")):
            del self.acl[user_name]
            self.update_acl()

    def on_edit_acl_click(self):
        if (not self.is_repository_selected):
            return
        table = self.window.acl_table
        (user_name, acl) = AclDialog(
            table.item(self.window.acl_table.currentRow(), 0).text(),
            table.item(self.window.acl_table.currentRow(), 1).text(),
            self.form
        ).show()
        if (not user_name):
            return
        if(self.bufi.set_repository_acl(self.chosen_repository, user_name, acl)):
            self.acl[user_name] = acl
            self.update_acl()

    def on_acl_chosen(self, element):
        if (not element):
            return
        self.acl_user = element.text()
        self.window.remove_acl_button.setEnabled(True)
        self.window.edit_acl_button.setEnabled(True)

    def on_logout_click(self):
        session_file = open(".session", "w")
        session_file.write("")
        session_file.close()
        exit(0)

    # Auth

    def save_session(self):
        login       = self.bufi.get_username()
        token_hash  = self.bufi.get_token_hash()

        print("Saving session")
        session_file = open(".session", "w")
        session_file.write(login + "\n" + token_hash)
        session_file.close()

    def get_saved_session(self):
        try:
            session_file = open(".session", "r")
        except IOError:
            return None
        credentials = session_file.read().split("\n")
        session_file.close()
        if (len(credentials) != 2):
            return None
        return (credentials[0], credentials[1])

    def clear_session(self):
        session_file = open(".session", "w")
        session_file.write("")
        session_file.close()

    # Repositories management

    def toggle_repositories_list_lock(self, unlock = False):
        self.window.repositories_list.setEnabled(unlock)
        self.window.add_acl_button.setEnabled(unlock)
        self.window.new_repository_button.setEnabled(unlock)
        QtCore.QCoreApplication.processEvents()

    def reset_repository_info(self):
        self.window.repository_name_label.setText("No repository selected")
        self.window.acl_table.setRowCount(0)
        self.window.repository_properties_form.hide()
        self.window.repository_info_widget.setEnabled(False)
        self.window.delete_repository_button.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

    def check_repository_filter(self, name):
        filter = self.window.search_input.text()
        module = self.window.modules_dropdown.currentText()

        if (module == "All modules"):
            module = ""
        return not name.find(module) and name.upper().find(filter.upper()) != -1

    def update_repositories(self, update_request = True):
        if (update_request):
            self.repositories = self.bufi.list_repositories()
            self.window.modules_dropdown.clear()
            self.window.modules_dropdown.addItem("All modules")
            self.modules = []

        self.reset_repository_info()
        self.toggle_repositories_list_lock(False)
        self.window.repositories_list.clear()
        for repository in self.repositories:
            if (self.check_repository_filter(repository)):
                self.window.repositories_list.addItem(repository)
            if (update_request):
                mod = get_module(repository)
                if (mod and mod not in self.modules):
                    self.modules.append(mod)
        if (update_request):
            for module in self.modules:
                self.window.modules_dropdown.addItem(module)
        self.toggle_repositories_list_lock(True)

    def update_acl(self):
        self.window.remove_acl_button.setEnabled(False)
        self.window.edit_acl_button.setEnabled(False)
        self.window.acl_table.setRowCount(0)
        for key in self.acl.keys():
            table = self.window.acl_table
            row_pos = table.rowCount()
            table.insertRow(row_pos)
            table.setItem(row_pos , 0, QtWidgets.QTableWidgetItem(key))
            table.setItem(row_pos , 1, QtWidgets.QTableWidgetItem(self.acl[key]))

    # SSH Keys management

    def toggle_ssh_keys_list_lock(self, unlock = False):
        self.window.ssh_keys_list.setEnabled(unlock)
        self.window.new_ssh_key_button.setEnabled(unlock)
        QtCore.QCoreApplication.processEvents()

    def update_ssh_keys(self):
        self.window.delete_ssh_key_button.setEnabled(False)
        self.toggle_ssh_keys_list_lock(False)

        self.window.ssh_keys_list.clear()
        ssh_keys = self.bufi.list_ssh_keys()
        for ssh_key in ssh_keys:
            self.window.ssh_keys_list.addItem(ssh_key)
        self.toggle_ssh_keys_list_lock(True)
        self.window.delete_ssh_key_button.setEnabled(False)
        self.window.ssh_key_info.setEnabled(False)

    def reset_ssh_key_info(self):
        self.window.ssh_info_owner_label.setText("")
        self.window.ssh_info_type_label.setText("")
        self.window.key_contents_text.setPlainText("")
        self.window.ssh_key_info.setEnabled(False)

def main():
    app = App()
    sys.exit(app.app.exec_())

if __name__ == "__main__":
    main()
