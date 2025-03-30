How to compile and Execute GingaPlayer- using PyInstaller.

Download the project at [my GitHub
Repository](https://github.com/icePain12/GingaPlayer-/blob/main/musicplayer.py)
in case you haven't.

You can do it executing the comand

git clone
https://github.com/icePain12/GingaPlayer-/blob/main/musicplayer.py

Then you need to make sure you have installed the following libraries:
pyinstaller, pygame, readchar, and rich.

You can execute:

*pip install pyinstaller pygame readchar rich*

to make sure of it.

You should make sure you have the musicplayer.spec that I provide you on
my repository. (I guess, I'm not really sure it is really mandatory but
just in case)

Finally execute the following instruction:

*pyinstaller \--onefile \--collect-all readchar musicplayer.py*

After it you should have a musicPlayer.exe file on project/dist

Enjoy It!
