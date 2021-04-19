# panasiam_webcam_mail

Taking pictures via webcam and sending them via e-mail.

## Installation

In order to use the application, you require git, a running python3 installation, tkinter and poetry.  
You can install poetry using the pip package manager.  
Here is an example installation on a debian system:
```bash
# Install dependencies
sudo apt-get install python3-pip python3-tk git
python3 -m pip install poetry

# Get the project
git clone https://github.com/Jan-Panasiam/webcam_panasiam_mail.git
cd webcam_panasiam_mail
# This will install all other required dependencies
poetry install

# This will set up the configuration folder and a empty config.ini file.
python3 -m panasiam_webcam_mail
# Test if the configuration was created
ls ~/.config/panasiam_webcam_mail/config.ini
```

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
