import os
import sys
import hmac
import hashlib
import urllib.request
import json
import time
import re

from PyQt5.QtWidgets import QMessageBox

class Bufi:
    def __init__(self, username, token, parent, already_hashed = False):
        self.BASE_URL   = "https://blih.epitech.eu/"
        self.USER_AGENT = "bufi-1.0"
        self.username   = username
        self.token_hash = token if already_hashed else hashlib.sha512(bytes(token, "utf8")).hexdigest()
        self.parent     = parent
        self.ssh_keys   = {}

    def get_username(self):
        return self.username

    def get_token_hash(self):
        return self.token_hash

    def show_error_dialog(self, message, exit_after = False):
        msg_box = QMessageBox(self.parent)

        if (re.match("User .* doesn't exists", message)):
            message += "\n(Yeah, I know, there's a shocking grammar mistake in that sentence.\nBut hey, that's what the server returned ¯\_(ツ)_/¯)"
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec_()
        if (exit_after):
            exit(1)

    def request(self, url, data=None, method="GET",
        content_type="application/json", exit_on_error=False):
        hash = hmac.new(
            bytes(self.token_hash, "utf8"),
            bytes(self.username + (
                json.dumps(
                    data,
                    sort_keys=True,
                    indent=4,
                    separators=(",", ": ")
                ) if data else ""
            ), "utf8"),
            digestmod=hashlib.sha512
        ).hexdigest()

        request_data = {
            "user":         self.username,
            "signature":    hash
        }

        if (data):
            request_data["data"] = data
        request = urllib.request.Request(
            url=self.BASE_URL + url,
            headers={
                "Content-Type": content_type,
                "User-Agent":   self.USER_AGENT
            },
            data=bytes(json.dumps(request_data), "utf8"),
            method=method
        )
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            try:
                err = json.loads(error.read().decode('utf8'))["error"]
                if (err != "No ACLs"):
                    self.show_error_dialog(err, exit_on_error)
                return {}
            except:
                self.show_error_dialog(str(error), exit_on_error)
                return {}
        except:
            self.show_error_dialog(
                "Failed to connect to {}.\n"\
                    "Check your internet connection and try again.".format(self.BASE_URL),
                True
            )
        try:
            ret = json.loads(response.read().decode("utf8"))
        except json.decoder.JSONDecodeError:
            self.show_error_dialog("Failed to parse resonse JSON")
            print("Error: {}".format(response.read().decode("utf8")))
            return {}
        if ("error" in ret):
            self.show_error_dialog(ret["error"])
            return {}
        return ret

    def create_repository(self, name, description=None, apply_ramassage_acl=False):
        request_data = {"name": name, "type": "git"}

        if (description):
            request_data["description"] = description
        data = self.request("repositories", request_data, "POST")

        if (apply_ramassage_acl):
            self.set_repository_acl(name, "ramassage-tek", "r")
        if ("error" in data):
            self.show_error_dialog(data["error"])

    def delete_repository(self, name):
        data = self.request("repository/" + name, method="DELETE")
        print(data.get("message"))

    def check_token(self):
        data = self.request("repositories")
        return not "error" in data

    def list_repositories(self):
        data            = self.request("repositories")
        repositories    = list(data.get("repositories") or [])
        repositories.sort()
        return repositories

    def repository_info(self, name):
        data = self.request("repository/" + name)
        info = data["message"] if "message" in data else {}
        return info

    def repository_acl(self, name):
        acls = self.request(
            "repository/" + name + "/acls",
            exit_on_error=False
        )
        if ("error" in acls):
            acls = {}
        return acls

    def set_repository_acl(self, name, user, acl):
        request_data    = {"user" : user, "acl" : acl}
        data            = self.request("repository/" + name + "/acls", request_data, "POST")

        return "message" in json.dumps(data)

    def list_ssh_keys(self):
        self.ssh_keys = self.request("sshkeys")
        return list(self.ssh_keys)

    def get_ssh_key(self, name):
        key = self.ssh_keys.get(name)
        return key.split(" ") if key else ["", ""]

    def upload_ssh_key(self, filename):
        if (not filename):
            return {}
        try:
            ssh_key = open(filename, "r").read().strip("\n")
        except (PermissionError, FileNotFoundError):
            self.show_error_dialog("Couldn't open \"{}\"".format(filename))
            return {}
        if (ssh_key.find("-----BEGIN OPENSSH PRIVATE KEY-----") != -1):
            self.show_error_dialog("Hold up!\n\n"\
                "You're about to hand out your private SSH key "\
                "and you definitely don't wanna do that!\n"\
                "Did you mean to upload a public key instead?\n"\
                "(like {}.pub, perhaps?)".format(filename.split("/")[-1]))
            return {}
        return self.request("sshkeys", {"sshkey": urllib.parse.quote(ssh_key)}, "POST")

    def delete_ssh_key(self, name):
        return self.request("sshkey/" +  urllib.parse.quote(name), method="DELETE")
