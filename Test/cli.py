"""
{BRIEF PROJECT DESCRIPTION}

Copyright (C) 2021  Jan Sallermann, Panasiam

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import sys
import configparser
import getpass
import keyring
from loguru import logger
import tkinter as tk
from tkinter import ttk
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import cv2
from PIL import ImageTk, Image
from datetime import date
from tkinter import messagebox


PROG_NAME = 'panasiam_webcam_mail'
USER = os.getlogin()
if sys.platform == 'linux':
    BASE_PATH = os.path.join(
        '/', 'home', str(f'{USER}'), '.config', PROG_NAME
    )
elif sys.platform == 'win32':
    BASE_PATH = os.path.join(
        'C:\\', 'Users', str(f'{USER}'), '.config', PROG_NAME
    )
if not os.path.exists(BASE_PATH):
    os.mkdir(BASE_PATH)

CONFIG_PATH = os.path.join(BASE_PATH, 'config.ini')

if not os.path.exists(CONFIG_PATH):
    open(CONFIG_PATH, 'a').close()


def validate_configuration(config):
    """
    Check if the config contains the required sections and options.

    Parameters:
        config              [dict]  -   Configuration of @CONFIG_PATH

    Return:
                            [bool]
    """
    sections = {'PATH': ['pic_path'], 'EMAIL': ['mail', 'smtp_server',
                                                'smtp_port', 'receiver']}
    for section in sections:
        if not config.has_section(section=section):
            logger.error(f"Inkorrekte Konfiguration benötigt eine {section} "
                         "Sektion.")
            return False
        for option in sections[section]:
            if not config.has_option(section=section, option=option):
                logger.error(f"Inkorrekte Konfiguration benötigt eine {option}"
                             f" Option in der {section} Sektion.")
                return False
            if not config[section][option]:
                logger.error("Inkorrekte Konfiguration kein Wert in der "
                             f"{option} Option unter der {section} Sektion.")
                return False
    return True


class Windows(tk.Tk):
    def __init__(self, config):
        tk.Tk.__init__(self)
        self.wm_title("Webcam Panasiam")
        self.geometry('1000x770')
        self.order_numbers = []
        self.picture_names = []
        self.current_picture = ''
        self.config = config

        container = tk.Frame(self, height=400, width=600)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MainPage, SidePage, CompletionScreen):
            frame = F(container, self)

            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

    def get_email_password(self, email: str, new_password = '') -> str:
        """
        Set up a new keyring instance for the email password or get the
        password from the instance.

        Parameters:
            email           [str]   -   Email of the sender
            reset           [bool]  -   Reset the password in case the
                                        incorrect password is saved in the
                                        keyring

        Return:
                            [str]   -   password as a string
        """
        email_identity = str(f"{email}_password")
        password = keyring.get_password(email_identity, 'password')
        if new_password:
            keyring.set_password(email_identity, 'password', new_password)
            return new_password
        return password

    def show_frame(self, cont):
        """
        This function brings the specified frame to the top of the GUI
        so it is the only one to be seen and to be used

        Parameters:
            cont        [tk.Frame]      -       Frame that is to be brought up
        """
        frame = self.frames[cont]
        frame.tkraise()

    def take_picture(self, edit, lb_size, img, lb):
        """
        This function allows the user to take pictures with a connected camera
        device and saves it in a path specified by the config. The picture
        name is stored in a listbox and a preview of the picture is shown to
        the user

        Parameters:
            edit        [tk.Entry]      -   entry window where we take the name
                                            of the picture from
            lb_size     [integer]       -   gives the current size of the
                                            listbox
            img         [tk.Label]      -   gives the label where the picture
                                            is to be shown
            lb          [tk.Listbox]    -   The listbox where the picturename
                                            is to be inserted
        """
        self.current_picture=f'Auftrag_{edit}.jpg'
        self.order_numbers.append(edit)
        self.picture_names.append(self.current_picture)
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret == False:
                break
            if not len(set(self.picture_names)) == len(self.picture_names):
                self.picture_names.pop()
                self.order_numbers.pop()
                messagebox.showerror(
                    'Picture already exists',
                    str(f"{self.current_picture} already exists please delete {self.current_picture}"))
                return
            cv2.imwrite(self.config['PATH']['pic_path'] + self.current_picture,
                        frame)
            break

        load = Image.open(self.config['PATH']['pic_path'] +
                          self.current_picture)
        render = ImageTk.PhotoImage(load)
        img.config(image = render)
        img.image = render

        cap.release()
        cv2.destroyAllWindows()
        lb.insert(lb_size, self.current_picture)

    def login(self, edit, page1, page2, log_btn, label, top, err):
        context = ssl.create_default_context()

        self.server = smtplib.SMTP(self.config['EMAIL']['smtp_server'],
                                   self.config['EMAIL']['smtp_port'])
        
        self.server.starttls(context=context)
        self.server.ehlo()
        email = self.config['EMAIL']['mail']
        password = self.get_email_password(email=email, new_password = 'abcd')

        while True:
            password = self.get_email_password(email=email, new_password = edit.get())
            try:
                self.server.login(email, password)
                edit.delete(0, 'end')
                top.withdraw()
            except smtplib.SMTPAuthenticationError:
                top.deiconify()
                top.lift(self)
                err['text'] = str(
                    f"'{password}': \nist das falsche Passwort für {email}"
                )
                edit.delete(0, 'end')
                return
            label['text'] = 'Du bist eingeloggt'
            page1['state'] = 'normal'
            page2['state'] = 'normal'
            return

    def on_closing(self):
        return

    def send_email(self, lb_size, lb) -> None:
        """
        This function allows the user to send the taken pictures via email to
        another email specified in the config. After the sending process has
        completed the function deletes all the pictures that have been sent
        and clears the listbox with all variables referring to the deleted
        pictures.

        Parameters:
            lb_size     [integer]       -   gives the current size of the
                                            listbox
            lb          [tk.Listbox]    -   The listbox where the picturenames
                                            are to be deleted from
        """
        today = date.today()

        message = MIMEMultipart('mixed')
        message['From'] = self.config['EMAIL']['mail']
        message['To'] = self.config['EMAIL']['receiver']
        message['Subject'] = f'Retouren {today}'

        msg_content = (
            'Anbei befinden sich alle heutigen Retouren. Auftragsnummer steht'
            'in dem jeweiligem Titel der angehängten Datei. Die betreffenden'
            'Auftragsnummern sind folgende:' + str(self.order_numbers)
        )
        body = MIMEText(msg_content, 'html')
        message.attach(body)

        for name in self.picture_names:
            attachment_path = self.config['PATH']['pic_path'] + name

            try:
                with open(attachment_path, "rb") as attachment:
                    p = MIMEApplication(attachment.read(),_subtype="jpg")
                    p.add_header('Content-Disposition',
                                "attachment; filename= %s"
                                % attachment_path.split("/")[-1])
                    message.attach(p)
            except Exception as e:
                print(str(e))

        msg_full = message.as_string()


        self.server.sendmail(self.config['EMAIL']['mail'],
                        message['To'].split(";"),
                        msg_full)

        for name in self.picture_names:
            os.remove(self.config['PATH']['pic_path'] + name)
            lb.delete(0)

        self.picture_names.clear()
        self.order_numbers.clear()

    def reset(self, lb):
        """
        This function allows the user to delete the selected picture in the
        listbox and everything that is referring to it.

        Parameters:
            lb          [tk.Listbox]    -   The listbox where the picturename
                                            is to be deleted from
        """
        selection = lb.curselection()
        os.remove(self.config['PATH']['pic_path'] +
                  self.picture_names[selection[0]])
        self.picture_names.pop(selection[0])
        self.order_numbers.pop(selection[0])
        lb.delete(selection)




class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        top = tk.Toplevel(self)
        top.title('Fehler beim einloggen!')
        top.geometry('400x120')
        
        label = tk.Label(self, text="Main Page")
        label.grid(row = 0, column = 0, columnspan = 2)

        label1 = tk.Label(top, text = 'Bitte dein e-mail Passwort eingeben')
        label1.grid(row = 1, column = 0, sticky='wens')

        err = tk.Label(top, text = "")
        err.grid(row = 0, column = 0, sticky='wens')

        label2 = tk.Label(self, text = '')
        label2.grid(row = 1, column = 0, columnspan = 2, sticky='wens')
        
        edit1 = tk.Entry(top, show = '*')
        edit1.grid(row = 2, column = 0, sticky='wens')

        switch_window_button1 = tk.Button(
            self,
            text="Seite 1",
            command = lambda: controller.show_frame(SidePage),
            state = 'disabled'

        )
        switch_window_button1.grid(row = 5, column = 0, sticky='wens')

        switch_window_button2 = tk.Button(
            self,
            text="Seite 2",
            command = lambda: controller.show_frame(CompletionScreen),
            state = 'disabled'
        )
        switch_window_button2.grid(row = 5, column = 1, sticky='wens')

        login_button = tk.Button(
            top,
            text = 'Login',
            command = lambda: controller.login(
                edit1, switch_window_button1,
                switch_window_button2, login_button,
                label2, top, err
            )

        )
        login_button.grid(row = 3, column = 0, sticky='wens')

        top.protocol("WM_DELETE_WINDOW", controller.on_closing)
        top.withdraw()

        self.after(0, controller.login(
            edit1, switch_window_button1,
            switch_window_button2, login_button,
            label2, top, err
        ))

class SidePage(tk.Frame):
    def __init__(self, parent, controller):
        def img_selection(self):
            """
            This function allows the user to get a preview of the selected
            picture in the listbox.
            """
            selection = listbox1.curselection()
            if not selection:
                return
            filen = controller.config['PATH']['pic_path'] +\
                controller.picture_names[selection[0]]
            load = Image.open(filen)
            render = ImageTk.PhotoImage(load)
            img.config(image = render)
            img.image = render

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Retouren Auflistung")
        label.grid(row = 0, column = 0, columnspan = 4, sticky = "wens")

        label1 = tk.Label(self, text = 'Bitte Auftragsnummer eintragen -->')
        label1.grid(row = 1, column = 0, sticky="wens")

        label2 = tk.Label(self, text = 'Bilder die versendet werden:')
        label2.grid(row = 4, column = 0, sticky="we")

        img = tk.Label(self)
        img.grid( row = 5, column = 1, columnspan = 3, sticky = "wens")

        edit1 = tk.Entry(self)
        edit1.grid(row = 1, column = 1, columnspan = 3, sticky = "wens")

        listbox1 = tk.Listbox(self, width = 35)
        listbox1.bind('<<ListboxSelect>>', img_selection)
        listbox1.grid(row = 4, column = 1, columnspan = 3, sticky = "wens")

        picture_btn = tk.Button(self, text = "Schieße ein Foto",
                                command = lambda : controller.take_picture(
                                edit = edit1.get(),
                                lb_size = listbox1.size(),
                                img = img, lb = listbox1))
        picture_btn.grid(row = 2, column = 1, sticky = "wens")

        send_btn = tk.Button(self, text = "Versende die Bilder per e-Mail",
                             command = lambda : controller.send_email(
                             lb_size = listbox1.size(), lb = listbox1))
        send_btn.grid(row = 2, column = 3, sticky = "wens")

        reset_btn = tk.Button(
            self, text = "Lösche das ausgewählte Bild",
            command = lambda : controller.reset(lb = listbox1))
        reset_btn.grid(row = 2, column = 2, sticky = "wens")

        switch_window_button = tk.Button(
            self,
            text="Zurück zum Menü",
            command=lambda: controller.show_frame(MainPage),
        )
        switch_window_button.grid(
            row = 6, column = 0, columnspan = 4, sticky = "wens")

class CompletionScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Seite 2")
        label.pack(padx=10, pady=10)
        switch_window_button = ttk.Button(
            self, text="Zurück zum Menü",
            command=lambda: controller.show_frame(MainPage)
        )
        switch_window_button.pack(side="bottom", fill=tk.X)


def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if not validate_configuration(config=config):
        logger.error("Die Konfiguration muss angepasst werden.")
        sys.exit(1)

    testObj = Windows(config=config)
    testObj.mainloop()
