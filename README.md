# panasiam_webcam_mail

Taking pictures via webcam and sending them via e-mail.

## Installation

Either install with the installation script or seperatly with: `poetry install`

## Configuration

Before you can succesfully run the script, you have to configure your system. To do that you have to go into the config.ini file located in the panasiam_webcam_mail folder in .config.
There you have to give the following information:
```
[PATH]
pic_path = (your path where u want to save your pictures)

[EMAIL]
password = (your e-mail password)
mail = (your e-mail adress)
smtp_server = (your smtp-server)
smtp_port = (your smtp_port)
receiver = (the e-mail adress where the e-mail will be send to)
```

## Usage

panasiam_webcam_mail is a program which you can use to take pictures via a connected camera device and send them to a specific e-mail. Furthermore the program gives you a preview of the taken pictures right after they are taken or via a selection in the listbox. You can also delete a selected picture within the listbox with the appropriate button. Before you run the program please make sure you did the configuration part first.
```bash
python3 -m panasiam_webcam_mail
```
