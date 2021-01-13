import tkinter as tk
from tkinter import filedialog
import speech_recognition as sr
from pynput.keyboard import Controller,Key
import threading
import subprocess


class StatusBar:
    def __init__(self, master):
        self.status = tk.StringVar()
        self.status.set('VoiceCoding')

        label = tk.Label(master.root, textvariable=self.status,fg='black' ,bg ='light grey',anchor='se')
        label.pack(side=tk.BOTTOM, fill=tk.BOTH)



    def update_status(self, *args):
        if isinstance(args[0], bool):
            self.status.set('Saved Successfully!')
        else:
            self.status.set('VoiceCoding')


class Menu:
    def __init__(self,master):
        # Menu Bar
        menu_bar = tk.Menu(master.root)
        master.root.config(menu=menu_bar)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=master.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=master.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=master.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=master.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=master.root.destroy)

        #Edit Menu
        edit_menu = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=lambda : master.cut_text(False), accelerator='Ctrl+X')
        edit_menu.add_command(label="Copy", command=lambda : master.copy_text(False), accelerator='Ctrl+C')
        edit_menu.add_command(label="Paste", command=lambda : master.paste_text(False), accelerator='Ctrl+V')
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=master.select_all, accelerator='Ctrl+A')
        edit_menu.add_command(label="Delete All", command=master.delete_all)
        edit_menu.add_command(label="Delete", command=master.delete_text)
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=master.undo, accelerator='Ctrl+Z')
        edit_menu.add_command(label="Redo", command=master.redo, accelerator='Ctrl+Y')

        #Run menu
        run_menu = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run File", command=master.run_file, accelerator='Ctrl+F12')


class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.text_widget = None

    def attach(self, text_widget):
        self.text_widget = text_widget

    def redraw(self, *args):
        self.delete("all")

        i = self.text_widget.index("@0,0")
        while True :
            d_line= self.text_widget.dlineinfo(i)
            if d_line is None: break
            y = d_line[1]
            line_num = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=line_num,font=("Helvetica",12))
            i = self.text_widget.index("%s+1line" % i)


class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"

        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # let the actual widget perform the requested action
        cmd = (self._orig,) + args
        try:
            result = self.tk.call(cmd)
        except Exception as e:
            print(e)
            result = None

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "replace", "delete") or
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("xview", "scroll") or
            args[0:2] == ("yview", "moveto") or
            args[0:2] == ("yview", "scroll")
        ):
            self.event_generate("<<Change>>", when="tail")

        # return what the actual widget returned
        return result


class MyThread(threading.Thread):

    def __init__(self,master, *args, **kwargs):
        self.parent=master
        super(MyThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()

    # create a method to stop thread
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        print('Recording...')
        while True:
            if self.stopped():
                print('Recording Stopped')
                return
            self.parent.record_start()


class VoiceCoding(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        master.title("Untitled - VoiceCoder")
        master.geometry("1200x680")
        tk.Frame.__init__(self, *args, **kwargs)
        self.root = master
        self.filename = None

        self.text_box = CustomText(self)
        self.text_box.config(undo=True, font="Courier 12")
        self.vsb = tk.Scrollbar(orient="vertical", command=self.text_box.yview)
        self.text_box.config(yscrollcommand=self.vsb.set,undo=True)


        self.line_numbers = TextLineNumbers(self, width=50)
        self.line_numbers.attach(self.text_box)
        self.line_numbers.pack(side="left", fill="y")

        self.vsb.pack(side="right", fill="y")
        self.text_box.pack(side="right", fill="both", expand=True)
        self.text_box.bind("<<Change>>", self._on_change)
        self.text_box.bind("<Configure>", self._on_change)
        self.keyboard = Controller()

        self.status = StatusBar(self)
        self.menu_bar = Menu(self)

        self.key_bindings()

        self.toolbar = tk.Frame(master)
        self.toolbar.pack(fill=tk.X)


        #Creating a thread for speech recognition
        self.t1 = MyThread(self)
        self.t1.setDaemon(True)
        # Creating Buttons

        # Record Start Button
        record_button = tk.Button(self.toolbar, text="Start Recording", command=lambda : self.t1.start())

        # Record Stop Button


        #the stop recording function works after few seconds ,because we have to wait for the thread to complete
        stop_record_button = tk.Button(self.toolbar, text="Stop Recording", command=self.record_stop)


        stop_record_button.pack(side=tk.RIGHT)
        record_button.pack(side=tk.RIGHT)

        # Run Button
        run_button = tk.Button(self.toolbar, text="Run", command=self.run_file)
        run_button.pack(side=tk.RIGHT)

        #Display the voice command in command box
        self.command_box = tk.Text(self.toolbar)
        self.command_box.config(width=40, height=1,font=("Helvetica",10))
        self.command_box.insert(0.0, "Your command will be shown here")
        self.command_box.pack(side=tk.RIGHT,padx=10)

        self.save_button = tk.Button(self.toolbar, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT)
        self.open_button = tk.Button(self.toolbar, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT)

    def record_stop(self):
        #Stopping the thread here
        self.t1.stop()

        #A Thread can be called only once
        #So we re_assume the same thread as a new thread
        self.t1 = MyThread(self)


    def record_start(self):
        command = self.take_voice_command()
        self.process_command(command)

    def _on_change(self, event):
        self.line_numbers.redraw()

    def cut_text(self,e, *args):
        if e:
            self.clipboard = self.clipboard_get()
        else:
            if self.text_box.selection_get():
                self.clipboard = self.text_box.selection_get()
                self.text_box.delete('sel.first','sel.last')
                self.clipboard_clear()
                self.clipboard_append(self.clipboard)


    def copy_text(self, *args):
        if self.text_box.selection_get():
            self.clipboard_clear()
            self.clipboard = self.text_box.get('sel.first','sel.last')
            self.clipboard_append(self.clipboard)

    def paste_text(self,e, *args):
        if e:
            self.clipboard = self.clipboard_get()
        else:
            if self.clipboard:
                pos = self.text_box.index(tk.INSERT)
                self.text_box.insert(pos,self.clipboard)

    def select_all(self):
        self.text_box.tag_add('sel',1.0,tk.END)
    def delete_all(self):
        self.text_box.delete(1.0,tk.END)
    def delete_text(self):
        if self.text_box.selection_get():
            self.text_box.delete('sel.first','sel.last')
    def undo(self, *args):
        self.text_box.edit_undo()


    def redo(self, *args):
        self.text_box.edit_redo()


    def window_title(self, name=None):
        if name:
            self.root.title(name+" - VoiceCoder")
        else:
            self.root.title("Untitled - VoiceCoder")


    # Creating a New File Function
    def new_file(self, *args):
        # Delete Previous Text
        self.text_box.delete("1.0", tk.END)
        self.filename = None
        self.window_title()


    # Open File
    def open_file(self, *args):
        # Get File Name
        self.filename = filedialog.askopenfilename(defaultextension="*.py", title="Open File",
                                                filetypes=(("Python Files", "*.py"), ("All Files", "*.*")))
        if self.filename:
            # Delete Previous Text
            self.text_box.delete("1.0", tk.END)
            # Open the file
            with open(self.filename, 'r') as f:
                self.text_box.insert(tk.END, f.read())
                self.window_title(self.filename)


    def save_as_file(self, *args):
        try:
            #get file name
            new_file = filedialog.asksaveasfilename(initialfile='Untitled.py', defaultextension=".py", title="Save File",
                                                 filetypes=(("Python Files", "*.py"), ("All Files", "*.*")))
            #save the file
            with open(new_file, 'w') as f:
                f.write(self.text_box.get(1.0, tk.END))
            self.filename = new_file
            self.window_title(self.filename)
            self.status.update_status(True)
        except Exception as e:
            print(e)


    def save_file(self, *args):
        if self.filename:
            try:
                with open(self.filename, 'w') as f:
                    f.write(self.text_box.get(1.0, tk.END))
                    self.status.update_status(True)
            except Exception as e:
                print(e)

        else:
            self.save_as_file()


    def key_bindings(self):
        self.text_box.bind('<Control-n>', self.new_file)
        self.text_box.bind('<Control-o>', self.open_file)
        self.text_box.bind('<Control-s>', self.save_file)
        self.text_box.bind('<Control-x>', self.cut_text)
        self.text_box.bind('<Control-c>', self.copy_text)
        self.text_box.bind('<Control-v>', self.paste_text)
        self.text_box.bind('<Control-a>', self.select_all)
        self.text_box.bind('<Control-S>', self.save_as_file)
        self.text_box.bind('<Key>', self.status.update_status)
        self.text_box.bind('<Control-z>', self.undo)
        self.text_box.bind('<Control-y>', self.redo)
        self.text_box.bind('<Control-F12>', self.run_file)



    # Run Program
    def run_file(self, *args):
        self.save_file()
        output = subprocess.check_output('python '+self.filename,shell=True)
        outputwindow =tk.Toplevel(width='680',height='400')
        outputwindow.title("Console")
        outputtext = tk.Text(outputwindow,bg='black',fg='white',insertbackground='white',font=("Helvetica",12))
        outputtext.pack(expand=True,fill='both')
        outputtext.insert(tk.END,output)

    def add_function_command(self,command):
        self.command = command.replace('function', '')
        if 'add two number' in self.command:
            self.text_box.insert(tk.INSERT, "def add2num():")
            self.text_box.insert(tk.INSERT, "\n    num1 =")
            self.text_box.insert(tk.INSERT, "\n    num2 =")
            self.text_box.insert(tk.INSERT, "\n\n    print(num1+num2)")
        elif 'subtract two number' in self.command:
            self.text_box.insert(tk.INSERT, "def sub2num():")
            self.text_box.insert(tk.INSERT, "\n    num1 =")
            self.text_box.insert(tk.INSERT, "\n    num2 =")
            self.text_box.insert(tk.INSERT, "\n\n    print(num1-num2)")
        elif 'multiply two number' in self.command:
            self.text_box.insert(tk.INSERT, "def multiply2num():")
            self.text_box.insert(tk.INSERT, "\n    num1 =")
            self.text_box.insert(tk.INSERT, "\n    num2 =")
            self.text_box.insert(tk.INSERT, "\n\n    print(num1*num2)")
        elif 'divide two number' in self.command:
            self.text_box.insert(tk.INSERT, "def divide2num():")
            self.text_box.insert(tk.INSERT, "\n    num1 =")
            self.text_box.insert(tk.INSERT, "\n    num2 =")
            self.text_box.insert(tk.INSERT, "\n\n    print(num1/num2)")
        else:
            self.command.strip()
            self.text_box.insert(tk.INSERT,"def "+self.command.split().strip()+"():\n    pass")

    def call_function_command(self):
        self.command.replace('call function', '')
        if 'add two number' in self.command:
            self.text_box.insert(tk.INSERT, "add2num()")
        elif 'subtract two number' in self.command:
            self.text_box.insert(tk.INSERT, "sub2num()")
        elif 'multiply two number' in self.command:
            self.text_box.insert(tk.INSERT, "multiply2num()")
        elif 'divide two number' in self.command:
            self.text_box.insert(tk.INSERT, "divide2num()")
        else:
            self.text_box.insert(tk.INSERT, self.command.strip()+"()")

    # Creating a method to get voice input and return the command
    def take_voice_command(self):
        listener = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                listener.adjust_for_ambient_noise(source, 0.5)
                voice = listener.listen(source)
                command = listener.recognize_google(voice)
                command = command.lower()
                self.command_box.delete(1.0, tk.END)
                self.command_box.insert(1.0, command)
                print(command)
                return command
        except Exception as e :
            print(e)


    # Processing the commands
    def process_command(self, command):
        self.command = command
        if self.command:
            if self.command == 'exit':
                self.root.destroy()
            elif self.command == 'stop recording':
                self.record_stop()
            elif self.command == 'create new file':
                self.new_file()
            elif self.command == 'open file':
                self.open_file()
            elif self.command == 'save file':
                self.save_file()
            elif self.command == 'run program':
                self.run_file()
            elif self.command == 'undo':
                self.text_box.edit_undo()
            elif self.command == 'tab':
                self.text_box.insert(tk.INSERT,"    ")
            elif self.command == 'next line':
                self.text_box.insert(tk.INSERT,"\n")
            elif self.command == 'space':
                self.text_box.insert(tk.INSERT," ")
            # Move Cursor to left
            elif self.command == 'cursor move left':
                self.keyboard.press(Key.left)
                self.keyboard.release(Key.left)

            # Move Cursor to right
            elif self.command == 'cursor move right':
                self.keyboard.press(Key.right)
                self.keyboard.release(Key.left)

            # Move Cursor to up
            elif self.command == 'cursor move up':
                self.keyboard.press(Key.up)
                self.keyboard.release(Key.up)

            # Move Cursor to down
            elif self.command == 'cursor move down':
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)

            elif 'go to line number' in self.command:
                for i in self.command.split():
                    if i.isdigit():
                        res = i
                        self.text_box.mark_set(tk.INSERT,"%s.%s" % (int(res),tk.END))

            elif 'call function' in self.command:
                self.call_function_command()

            elif 'create' in self.command:
                command = self.command.replace("create ",'')
                if 'function' in command:
                    self.add_function_command(command)
                elif 'while loop' in command:
                    self.text_box.insert(tk.INSERT,"count=1\ni=1\nwhile(i<=count)\n    pass\n    i++\n")
                elif 'variable' in command:
                    command2 = command.replace('variable ','').strip()
                    if command2 :
                        self.text_box.insert(tk.INSERT, command2+"=")

            elif 'set'in self.command:
                if 'set number' in self.command:
                    command3 = self.command.replace('set number', '')
                    self.text_box.insert(tk.INSERT, command3)
                if 'set string' in self.command:
                    command3 = self.command.replace('set string', '')
                    self.text_box.insert(tk.INSERT, "'" + command3 + "'")
                else:
                    self.command.replace("set ","")
                    self.text_box.insert(tk.INSERT,self.command)

            elif 'delete'in self.command:
                command= self.command.replace("delete ",'')
                print(command)
                start = '1.0'
                while 1:
                    idx = self.text_box.search(command, start,
                                      stopindex=tk.END)
                    if not idx:
                        break
                    lastidx = '%s+%dc' % (idx, len(command))
                    self.text_box.tag_add('found', idx, lastidx)
                    start = lastidx
                    self.text_box.tag_config("found")
                self.text_box.delete("found.first","found.last")

            elif 'print' in self.command:
                command1 = self.command.replace("print ",'')
                if 'variable' in command1:
                    command2 =command1.replace('variable ','')
                    self.text_box.insert(tk.INSERT, "print(" + command2 + ")\n")
                else:
                    self.text_box.insert(tk.INSERT,"print('"+command1+"')\n")

            else:
                self.text_box.insert(tk.INSERT,self.command)

if __name__ == "__main__":
    root = tk.Tk()
    VoiceCoding(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
