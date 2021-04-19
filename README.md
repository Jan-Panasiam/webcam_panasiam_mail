# panasiam_webcam_mail

Taking Pictures via Webcam and sending it via e-mail

## Installation

Either install with the installation script or seperatly with: `poetry install`

## Configuration

Before you can succesfully run the script u have to configure your system. To do that you have to go into the config.ini file located in the panasiam_webcam_mail folder in .config.
There u have to give following information:
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

panasiam_webcam_mail is a programm which u can use to take pictures via a connected camera device and send them to a specific e-mail. Furthermore the program gives you preview of the taken pictures right after they are taken or via selection in the listbox. You can also delete in the listbox selected pictures with the apropriate button. Before you run the programm please make sure you did the configuration part first.
```bash
python3 -m panasiam_webcam_mail
```