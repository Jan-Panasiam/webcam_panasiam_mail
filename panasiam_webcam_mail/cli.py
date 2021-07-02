"""
Panasiam Webcam Mail provides an easy solution for taking pictures with a
webcam and sending them per mail to a specified email location.

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
import tkinter as tk
from tkinter import ttk
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import date
from tkinter import messagebox
from PIL import ImageTk, Image
import cv2
import keyring
from loguru import logger
import subprocess #
import re #

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
    sections = {'PATH': ['pic_path'],
                'EMAIL': ['mail', 'smtp_server',
                          'smtp_port', 'receiver'],
                'VIDEOPORT': ['video_port']}
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
        self.customer_names = []
        self.picture_names = []
        self.current_picture = ''
        self.config = config
        self.server = None

        def on_closing():
            """
            Function to prevent the user from destroying the top_email window.
            """
            return

        self.top_email = tk.Toplevel(self)
        self.top_email.title('Ändere die Emfänger-email.')
        self.top_email.geometry('400x120')
        self.entry = tk.Entry(self.top_email)
        self.entry.grid(row=0, column=1, sticky='wens')
        self.label = tk.Label(self.top_email, text='Bitte Empfänger eintragen')
        self.label.grid(row=0, column=0, sticky='wens')
        self.button = tk.Button(
            self.top_email,
            text='Fertig',
            command=lambda: change_receiver()
        )
        self.button.grid(row=1, column=0, columnspan=2, sticky='wens')
        self.top_email.protocol("WM_DELETE_WINDOW", on_closing)
        self.top_email.withdraw()

        def open_change_receiver():
            """
            Opens the pop-up-window for changing the receiver e-mail.
            """
            self.top_email.deiconify()
            self.top_email.lift(self)
            self.entry.delete(0, 'end')

        def edit_config(section, key,  value):
            """
            Modify sections in the config and save the changes.

            Params:
                section         [str]   -   Section in the config
                key             [str]   -   Key in the config
                value           [str]   -   Value in the config
            """
            config.set(section, key, str(value))
            file = open(CONFIG_PATH, 'w')
            config.write(file)
            file.close

        def change_receiver():
            """
            Modify the receiver e-mail and change the label to show the new
            receiver email.
            """
            config.set('EMAIL', 'receiver', self.entry.get())
            file = open(CONFIG_PATH, 'w')
            config.write(file)
            file.close
            self.frames[Menu].label3['text']='Empfänger '+self.entry.get()
            self.top_email.withdraw()

        if sys.platform == 'linux':
            self.camera_index = []
            self.temp_index = []
            self.camera_string = subprocess.getstatusoutput(
                'v4l2-ctl --list-devices'
            )
            self.camera_string = self.camera_string[1].split("\n")

            count_list = []
            for count, ele in enumerate(self.camera_string):
                if ele == '':
                    count_list.append(count)
            count_list.pop()
            for count in count_list:
                self.camera_string.pop(count)

            for ele in self.camera_string:
                x = re.search('video', ele)
                if x:
                    vid = ele.split('video')
                    self.temp_index.append(int(vid[-1]))
                else:
                    if not self.temp_index == []:
                        self.camera_index.append(self.temp_index)
                    self.temp_index =[]
                    self.temp_index.append(ele)

            menubar = tk.Menu(self)

            camera_len = len(self.camera_index)

            camera_menu = tk.Menu(menubar, tearoff=0)

            if camera_len >= 1:
                camera_menu.add_command(
                    label=self.camera_index[0][0],
                    command=lambda: edit_config(
                        section='VIDEOPORT',
                        key='video_port',
                        value=min(self.camera_index[0][1:-1])
                    )
                )

            if camera_len >= 2:
                camera_menu.add_command(
                    label=self.camera_index[1][0],
                    command=lambda: edit_config(
                        section='VIDEOPORT',
                        key='video_port',
                        value=min(self.camera_index[1][1:-1])
                    )
                )

            if camera_len >= 3:
                camera_menu.add_command(
                    label=self.camera_index[2][0],
                    command=lambda: edit_config(
                        section='VIDEOPORT',
                        key='video_port',
                        value=min(self.camera_index[2][1:-1])
                    )
                )
            menubar.add_cascade(label="Kamera", menu=camera_menu)

            receiver_menu = tk.Menu(menubar, tearoff=0)
            receiver_menu.add_command(
                label='Ändere den Empfänger',
                command=lambda: open_change_receiver()
            )
            menubar.add_cascade(
                label="e-mail Einstellungen", menu=receiver_menu
            )

            self.configure(menu=menubar)

        container = tk.Frame(self, height=400, width=600)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (Menu, Listing, Details):
            frame = F(container, self)

            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Menu)
        self.frames[Menu].login(controller=self)

    def get_email_password(self, email: str, new_password = '') -> str:
        """
        Set up a new keyring instance for the email password or get the
        password from the instance.

        Parameters:
            reset           [bool]  -   Reset the password in case the
                                        incorrect password is saved in the
                                        keyring

        Return:
                            [str]   -   password as a string
        """
        email_identity = str(f"{self.config['EMAIL']['mail']}_password")
        password = keyring.get_password(email_identity, 'password')
        if new_password or not password:
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

    def take_picture(self, edit, lb_size, img, lb, description=None, name=None):
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
            description [tk.Entry]      -   Description of the product
            name[tk.Label]      -   subject name of the email
        """

        cap = cv2.VideoCapture(int(self.config['VIDEOPORT']['video_port']))
        if cap is None or not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(0)
        if cap is None or not cap.isOpened():
            messagebox.showerror(
                'Keine Kamera gefunden!',
                'Das Programm erkennt keine Kamera, bitte überprüfe ob die '
                'Kamera richtig angeschlossen ist.'
            )
            return

        if not description == None:
            if description.get() == '':
                messagebox.showerror(
                    'Keine Beschreibung eingegeben!',
                    'Bitte gebe zuerst eine Beschreibung ein.'
                )
                return
            if name.get() == '':
                messagebox.showerror(
                    'Keinen Auftragsnamen eingegeben!',
                    'Bitte gebe zuerst den Auftragsnamen ein.'
                )
                return
            if self.picture_names == []:
                description.config(state='disabled')
                name.config(state='disabled')

        self.current_picture = f'Auftrag_{edit}.jpg'
        self.customer_names.append(edit)
        self.picture_names.append(self.current_picture)

        while True:
            ret, frame = cap.read()
            if ret is False:
                break
            if len(set(self.picture_names)) != len(self.picture_names):
                self.picture_names.pop()
                self.customer_names.pop()
                messagebox.showerror(
                    'Bild existiert bereits',
                    str(f"{self.current_picture} ist bereits vorhanden, um den"
                        " Namen erneut zuverwenden, lösche das alte Bild."))
                return
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.imwrite(os.path.join(self.config['PATH']['pic_path'],
                                        self.current_picture),
                            frame)
                break

        load = Image.open(os.path.join(self.config['PATH']['pic_path'],
                          self.current_picture))
        render = ImageTk.PhotoImage(load)
        img.config(image=render)
        img.image = render

        cap.release()
        cv2.destroyAllWindows()
        lb.insert(lb_size, self.current_picture)

    def send_email(self, lb_size, lb, img, description=None, subject_name=None):
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
            img         [tk.Label]      -   Label where we delete the preview
                                            from
            description [tk.Entry]      -   Description of the product
            subject_name[tk.Label]      -   subject name of the email
        """
        today = date.today()

        message = MIMEMultipart('mixed')
        message['From'] = self.config['EMAIL']['mail']
        message['To'] = self.config['EMAIL']['receiver']

        if not description == None:
            message['Subject'] = f'Retour {subject_name.get()} Details'
            msg_content = description.get()
        else:
            message['Subject'] = f'Retouren {today}'
            msg_content = (
                'Anbei befinden sich alle heutigen Retouren. Der Kundenname steht '
                'in dem jeweiligem Titel der angehängten Datei. Die betreffenden '
                'Kundennamen sind folgende:' + str(self.customer_names)
            )
        body = MIMEText(msg_content, 'html')
        message.attach(body)

        for name in self.picture_names:
            attachment_path = os.path.join(self.config['PATH']['pic_path'], name)

            try:
                with open(attachment_path, "rb") as attachment:
                    p = MIMEApplication(attachment.read(), _subtype="jpg")
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
            os.remove(os.path.join(self.config['PATH']['pic_path'], name))
            lb.delete(0)

        self.picture_names.clear()
        self.customer_names.clear()

        img.image = None

        if not description == None:
            description.config(state='normal')
            description.delete(0, 'end')
            subject_name.config(state='normal')
            subject_name.delete(0, 'end')

    def full_reset(self, lb_size, lb, img, description, name):
        """
        Reset the whole page.

        Parameters:
            lb_size     [integer]       -   gives the current size of the
                                            listbox
            lb          [tk.Listbox]    -   The listbox where the picturenames
                                            are to be deleted from
            img         [tk.Label]      -   Label where we delete the preview
                                            from
            description [tk.Entry]      -   Description of the product that is
                                            to be deleted
            name[tk.Label]              -   subject name that is to be deleted
        """
        for pic_name in self.picture_names:
            os.remove(os.path.join(self.config['PATH']['pic_path'], pic_name))
            lb.delete(0)

        self.picture_names.clear()
        self.customer_names.clear()

        img.image = None

        description.config(state='normal')
        description.delete(0, 'end')
        name.config(state='normal')
        name.delete(0, 'end')

class Menu(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.top = tk.Toplevel(self)
        self.top.title('Fehler beim einloggen!')
        self.top.geometry('400x120')

        self.label = tk.Label(self, text="Menü")
        self.label.grid(row=0, column=0, columnspan=2)

        label1 = tk.Label(self.top, text='Bitte dein e-mail Passwort eingeben')
        label1.grid(row=1, column=0, sticky='wens')

        err = tk.Label(self.top, text="")
        err.grid(row=0, column=0, sticky='wens')

        label2 = tk.Label(self, text='')
        label2.grid(row=1, column=0, columnspan=2, sticky='wens')

        label2 = tk.Label(
            self, text="Sender: "+controller.config['EMAIL']['mail']
        )
        label2.grid(row=6, column=0, columnspan=2, sticky='wens')

        self.label3 = tk.Label(
            self, text="Empfänger: "+controller.config['EMAIL']['receiver']
        )
        self.label3.grid(row=7, column=0, columnspan=2, sticky='wens')

        self.edit1 = tk.Entry(self.top, show='*')
        self.edit1.grid(row=2, column=0, sticky='wens')

        self.switch_window_button1 = tk.Button(
            self,
            text="Retouren Auflisting",
            command=lambda: controller.show_frame(Listing),
            state='disabled'

        )
        self.switch_window_button1.grid(row=5, column=0, sticky='wens')

        self.switch_window_button2 = tk.Button(
            self,
            text="Retouen Details",
            command=lambda: controller.show_frame(Details),
            state='disabled'
        )
        self.switch_window_button2.grid(row=5, column=1, sticky='wens')

        login_button = tk.Button(
            self.top, text='Login',
            command=lambda: self.login(controller=controller))
        login_button.grid(row=3, column=0, sticky='wens')

        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.top.withdraw()

    def on_closing(self):
        """
        Function to prevent the user from closing the login window by pressing
        the "x" of the window.
        """
        return

    def login(self, controller):
        """
        We check if the current password in the keyring is valid for the user
        configured e-mail, if so we direct the user to the menu page. If this
        is not the case, the user gets a pop-up window where we ask the user to
        enter the password for his e-mail adress and then redo the check.
        """
        context = ssl.create_default_context()

        controller.server = smtplib.SMTP(
            controller.config['EMAIL']['smtp_server'],
            controller.config['EMAIL']['smtp_port'])

        controller.server.starttls(context=context)
        controller.server.ehlo()
        email = controller.config['EMAIL']['mail']

        while True:
            password = controller.get_email_password(
                email=email, new_password=self.edit1.get())
            try:
                controller.server.login(email, password)
                self.edit1.delete(0, 'end')
                self.top.withdraw()
            except smtplib.SMTPAuthenticationError:
                self.top.deiconify()
                self.top.lift(controller)
                self.edit1.delete(0, 'end')
                return
            self.label['text'] = 'Du bist eingeloggt'
            self.switch_window_button1['state'] = 'normal'
            self.switch_window_button2['state'] = 'normal'
            return


class Listing(tk.Frame):
    def __init__(self, parent, controller):
        def img_selection(*args):
            """
            This nested function allows the user to get a preview of the
            selected picture in the listbox.
            """
            selection = listbox1.curselection()
            if not selection:
                return
            filen = os.path.join(controller.config['PATH']['pic_path'],
                controller.picture_names[selection[0]])
            load = Image.open(filen)
            render = ImageTk.PhotoImage(load)
            img.config(image=render)
            img.image = render

        def reset():
            """
            This function allows the user to delete the selected picture in the
            listbox and everything that is referring to it.
            """
            selection = listbox1.curselection()
            if not selection:
                return
            os.remove(os.path.join(controller.config['PATH']['pic_path'],
                      controller.picture_names[selection[0]]))
            controller.picture_names.pop(selection[0])
            controller.customer_names.pop(selection[0])
            listbox1.delete(selection)
            if not listbox1.size():
                img.image = None

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Retouren Auflistung")
        label.grid(row=0, column=0, columnspan=4, sticky="wens")

        label1 = tk.Label(self, text='Bitte Kundenname eintragen -->')
        label1.grid(row=1, column=0, sticky="wens")

        label2 = tk.Label(self, text='Bilder die versendet werden:')
        label2.grid(row=4, column=0, sticky="we")

        img = tk.Label(self)
        img.grid(row=5, column=1, columnspan=3, sticky="wens")

        edit1 = tk.Entry(self)
        edit1.grid(row=1, column=1, columnspan=3, sticky="wens")

        listbox1 = tk.Listbox(self, width=35)
        listbox1.bind('<<ListboxSelect>>', img_selection)
        listbox1.grid(row=4, column=1, columnspan=3, sticky="wens")

        picture_btn = tk.Button(self, text="Schieße ein Foto",
                                command=lambda: controller.take_picture(
                                    edit=edit1.get(),
                                    lb_size=listbox1.size(),
                                    img=img, lb=listbox1))
        picture_btn.grid(row=2, column=1, sticky="wens")

        send_btn = tk.Button(self, text="Versende die Bilder per e-Mail",
                             command=lambda: controller.send_email(
                                 lb_size=listbox1.size(), lb=listbox1, img=img))
        send_btn.grid(row=2, column=3, sticky="wens")

        reset_btn = tk.Button(
            self, text="Lösche das ausgewählte Bild",
            command=lambda: reset())
        reset_btn.grid(row=2, column=2, sticky="wens")

        switch_window_button = ttk.Button(
            self,
            text="Zurück zum Menü",
            command=lambda: controller.show_frame(Menu),
        )
        switch_window_button.grid(
            row=6, column=0, columnspan=4, sticky="wens")


class Details(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        def img_selection(*args):
            """
            This nested function allows the user to get a preview of the
            selected picture in the listbox.
            """
            selection = listbox.curselection()
            if not selection:
                return
            filen = os.path.join(controller.config['PATH']['pic_path'],
                controller.picture_names[selection[0]])
            load = Image.open(filen)
            render = ImageTk.PhotoImage(load)
            img.config(image=render)
            img.image = render

        def reset():
            """
            This function allows the user to delete the selected picture in the
            listbox and everything that is referring to it.
            """
            selection = listbox.curselection()
            if not selection:
                return
            os.remove(os.path.join(controller.config['PATH']['pic_path'],
                      controller.picture_names[selection[0]]))
            controller.picture_names.pop(selection[0])
            controller.customer_names.pop(selection[0])
            listbox.delete(selection)
            if not listbox.size():
                img.image = None

        label = tk.Label(self, text="Retouren Details")
        label.grid(row=0, column=0, columnspan=4, sticky='wens')

        name = tk.Entry(self)
        name.grid(row=1, column=1, columnspan=2, sticky='wens')

        name_label = tk.Label(self,text='Bitte den Auftragsnamen eintragen:')
        name_label.grid(row=1, column=0, sticky='wens')

        pic_name = tk.Entry(self)
        pic_name.grid(row=2, column=1, columnspan=2, sticky='wens')

        pic_name_label = tk.Label(self,text='Bitte den Bildnamen eintragen:')
        pic_name_label.grid(row=2, column=0, sticky='wens')

        description = tk.Entry(self)
        description.grid(row=3, column=1, columnspan=2, sticky='wens')

        description_label = tk.Label(self,
                                     text='Bitte die Beschreibung eintragen:')
        description_label.grid(row=3, column=0, sticky='wens')

        listbox = tk.Listbox(self)
        listbox.bind('<<ListboxSelect>>', img_selection)
        listbox.grid(row=1, column=3, rowspan=5, sticky='wens')

        img = tk.Label(self)
        img.grid(row=7, column=0, columnspan=4, sticky="wens")

        picture_btn = tk.Button(self, text="Schieße ein Foto",
                                    command=lambda: controller.take_picture(
                                        edit=pic_name.get(),
                                        lb_size=listbox.size(),
                                        img=img, lb=listbox,
                                        description=description,
                                        name=name
                                    )
                                )
        picture_btn.grid(row=4, column=0, sticky="wens")

        send_btn = tk.Button(self, text="Versende die Bilder per e-Mail",
                             command=lambda: controller.send_email(
                                 lb_size=listbox.size(), lb=listbox, img=img,
                                 description=description, subject_name=name
                             ))
        send_btn.grid(row=4, column=2, sticky="wens")

        reset_btn = tk.Button(
            self, text="Lösche das ausgewählte Bild",
            command=lambda: reset())
        reset_btn.grid(row=4, column=1, sticky="wens")

        full_reset = tk.Button(self, text='Setze alles zurück!',
                               command=lambda: controller.full_reset(
                                   lb_size=listbox.size(), lb=listbox, img=img,
                                   description=description, name=name
                               ))
        full_reset.grid(row=5, column=0, columnspan=3, sticky='wens')

        seperator = tk.Label(
            self,
            text=4*'------------------------------------------------'
        )
        seperator.grid(row=6, column=0, columnspan=4, sticky='wens')

        switch_window_button = tk.Button(
            self, text="Zurück zum Menü",
            command=lambda: controller.show_frame(Menu)
        )
        switch_window_button.grid(
            row=8, column=0, columnspan=4, sticky='wens'
        )


def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if not validate_configuration(config=config):
        logger.error("Die Konfiguration muss angepasst werden.")
        sys.exit(1)

    gui = Windows(config=config)
    gui.mainloop()
