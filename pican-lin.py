from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial
import os
import time
import subprocess
import RPi.GPIO as GPIO
import tkinter as tk
from threading import Thread

ser = serial.Serial()
mclr = 26

root = tk.Tk()
root.title('PiCAN LIN v1.0 skpang.co.uk 2022')
root.geometry("650x550")
saved_secondary_color = "#D3D3D3"
saved_primary_color = "#D3D3D3"

send_status = 0
stop_cont_thread  = False

def crc_check(crc_str, length, pid,crc_int):
      
    if calculate_crc(crc_str,length-2,0) == crc_int:
#         print('classic')
        res = 'Classic'
    elif calculate_crc(crc_str,length-2,pid) == crc_int:
        #print('enhance')
        res = 'Enhanced'
    else:
        #print('error')
        res = 'Error'
        
    return res

def calculate_crc(data, size, sum):
      
        array_bin = bytearray()
        len_str = ""
      
        for i in range(size):
            len_str = chr(data[i*2]) + chr(data[(i*2)+1])
         
            len_int=int(len_str,base=16)
           
            array_bin.append(len_int)
              
        for i in range(size):
            sum = sum + array_bin[i]
            
            if sum >= 256:
                sum = sum-255
        sum = (-sum-1) & 0xff
        return sum

    
def rx_task():
    print('rx task stared')
    while True:
                   
#        try:
                rc_ch = 0
                telegram_string = b''
                bytecount = 0
                while (not rc_ch == b'\r') and bytecount < 120:
                    rc_ch = ser.read()
                    if(not rc_ch == b'\r'):
                        telegram_string = telegram_string + rc_ch
                        bytecount+=1
                if bytecount > 110:
                    bytecount = 0
                
                #telegram_received_ascii  = bytearray(telegram_string)
                print('Received:', telegram_string)
                #telegram_received_ascii =telegram_received_ascii.decode('utf-8')
                #M 4d m 6d  v 76  V 56 
                if telegram_string[0] == 0x4d: # M
                    print('m received')
                    len_str = chr(telegram_string[1]) + chr(telegram_string[2])   # Extract length from 2bytes
                    print(len_str)
                    len_int=int(len_str,base=16)
                    
                    if len(telegram_string)>6:
                        pid_str = chr(telegram_string[3])+chr(telegram_string[4])     # Extract PID
                        pid_int = int(pid_str,base=16)
                        
                        if bytecount > len_int:
                            crc_str = chr(telegram_string[(len_int*2)+1])+chr(telegram_string[(len_int*2)+2]) # Extract checksum
                            crc_int = int(crc_str,base=16)
                            print('crc = {:x}'.format(crc_int))
                            data_str = ''
                            dataraw_str = b''
                            for i in range(len_int -2):
                                 data_str = data_str+chr(telegram_string[5+(i*2)])+chr(telegram_string[6+(i*2)])+' '
                                 dataraw_str = dataraw_str +bytearray(chr(telegram_string[5+(i*2)])+chr(telegram_string[6+(i*2)]),encoding='utf-8')
                          
                            print(dataraw_str)
                            crc_status = crc_check(dataraw_str,len_int,pid_int,crc_int)   # Find the checksum type
                            
                            my_tree.insert('',tk.END,values=( time.process_time(),chr(telegram_string[3])+chr(telegram_string[4]),data_str,chr(telegram_string[(len_int*2)-1+2])+chr(telegram_string[(len_int*2)+2]),crc_status))
                            #tree.insert('',tk.END,values=( time.process_time(),chr(telegram_string[3])+chr(telegram_string[4]),data_str,chr(telegram_string[(len_int*2)-1+2])+chr(telegram_string[(len_int*2)+2]),crc_status))
                            my_tree.yview_moveto(1)
                elif telegram_string[0] == 0x56: # V
                    status_var.set(telegram_string)
                elif telegram_string[0] == 0x76: # v
                    status_var.set(telegram_string)
                elif telegram_string[0] == 0x00: # 
                    status_var.set(telegram_string)                    

#NCV7430 status read 3C t3c88081C0FFFFFFFFFF      
def connect():
    
    try:
        
        #index = listbox_usb_ports.curselection()[0] 
        acm = '/dev/ttyS0'  # + listbox_usb_ports.get(index)
        print('port selected = ', acm)
        #ser.close()
        #ser = (serial.Serial(acm ,baudrate=9600,timeout=0.1,bytesize = 8, stopbits = 2,dsrdtr= False))
        ser.baudrate = 115200  
        ser.port = acm
        if ser.isOpen() == False:
            print('open port')
            ser.open()
            t = Thread(target = rx_task)
            t.start()
            time.sleep(0.1)
    
    except:
        print('can not open port')
        
        
    try:
        
     #   t = Thread(target = rx_task)
     #   t.start()
        telegram_bin = bytearray()
        telegram_ascii_tx = b'V\r' 
        
        print('telegram_tx = ', telegram_ascii_tx)
        ser.write(telegram_ascii_tx)
     #   time.sleep(0.1)	
      #  telegram_ascii_tx = b'O\r' 
        
       # print('telegram_tx = ', telegram_ascii_tx)
       # ser.write(telegram_ascii_tx)
        
    except:
        print('Can not start thread')

def sendcont_task(interval):
    global stop_cont_thread 
    telegram_ascii_str = strvar_command.get()
    while True:
        
        t=bytearray()
        t=str.encode( telegram_ascii_str)   
   
        t=t+ b'\r'
        ser.write(t)
        time.sleep(interval)
        if stop_cont_thread:
            break
            
#   t248C0000010310000FF         
def set_sendcont():
    global send_status
    global stop_cont_thread 
    try:
            interval_int=int(strvar_interval.get())
            print("interval {:d}".format(interval_int))
            interval_int = interval_int/1000
    except:
            status_var.set("Interval must be a number")
            
    tcont = Thread(target = sendcont_task,args=[interval_int])
    
    if send_status == 0:
        stop_cont_thread = False
        tcont.start()
        send_status = 1
        sendcont_button['text'] ="Stop"

    else:
        
        send_status = 0
        sendcont_button['text'] ="Send Continuous"
        stop_cont_thread = True
        
        #tcont = Thread(target = sendcont_task,args=[1])
        #tcont.start()
        
def set_send():

    telegram_ascii_str = strvar_command.get()
    #telegram_ascii_str = telegram_ascii_str +b'\r'
    
    t=bytearray()
     
    t=str.encode( telegram_ascii_str)   
   
    t=t+ b'\r'
    
    print('telegram_tx = ',telegram_ascii_str)
  
    ser.write(t)
    
    
def set_clear():
    my_tree.delete(*my_tree.get_children())
    
    return

def set_reset():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(mclr,GPIO.OUT)
    GPIO.output(mclr,False)
    time.sleep(0.1)
    GPIO.output(mclr,True)


# Add Some Style
style = ttk.Style()

# Pick A Theme
style.theme_use('clam')
style.configure('Treeview.Heading',font =(None,8))
# Configure the Treeview Colors
style.configure("Treeview",
	background="#D3D3D3",
	foreground="black",
	rowheight=25,
	fieldbackground="#D3D3D3")

# Change Selected Color #347083
style.map('Treeview',
	background=[('selected', "#347083")])

# Create a Treeview Frame
tree_frame = Frame(root)
tree_frame.pack(pady=10)

# Create a Treeview Scrollbar
tree_scroll = Scrollbar(tree_frame)
tree_scroll.pack(side=RIGHT, fill=Y)

# Create The Treeview
my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode="extended")
my_tree.pack()

# Configure the Scrollbar
tree_scroll.config(command=my_tree.yview)

# Define Our Columns
my_tree['columns'] = ("time_stamp", "frame_id", "lin_data", "checksum", "cs_type")

# Format Our Columns
my_tree.column("#0", width=0, stretch=NO)
my_tree.column('time_stamp',width=105)
my_tree.column('frame_id',width=85)
my_tree.column('lin_data',width=220)
my_tree.column('checksum',width=80)
my_tree.column('cs_type',width=105)


# Create Headings
my_tree.heading("#0", text="", anchor=W)
my_tree.heading('time_stamp', text='Time stamp')
my_tree.heading('frame_id', text='Frame ID')
my_tree.heading('lin_data', text='Data')
my_tree.heading('checksum', text='Checksum')
my_tree.heading('cs_type', text='CS Type') 


# Create Striped Row Tags
my_tree.tag_configure('oddrow', background=saved_secondary_color)
my_tree.tag_configure('evenrow', background=saved_primary_color)

strvar_command = StringVar()
strvar_interval = StringVar()

# Commands frame
data_frame = LabelFrame(root, text="Commands")
data_frame.pack(fill="x", expand="yes", padx=20)



command_entry = Entry(data_frame, width = 64,textvariable = strvar_command)
command_entry.grid(row=0, column=0, columnspan=5, padx=10, pady=10)

send_button = Button(data_frame, text="Send Once", command = set_send)
send_button.grid(row=1, column=0, padx=10, pady=10)


interval_entry = Entry(data_frame, width =10, textvariable = strvar_interval)
interval_entry.grid(row=1, column=1, padx=1, pady=1, sticky ='e')

interval_label = Label(data_frame, text="Intveral (ms)")
interval_label.grid(row=1, column=2, padx=1, pady=1, sticky ='w')

sendcont_button = Button(data_frame, text="Send Continuous",width=12, command = set_sendcont)
sendcont_button.grid(row=1, column=3, padx=1, pady=1)


# Add Buttons
button_frame = LabelFrame(root, text="buttons")
button_frame.pack(fill="x", expand="yes", padx=20)

connect_button = Button(button_frame, text="Connect",command = connect)
connect_button.grid(row=0, column=0, padx=10, pady=10)

add_button = Button(button_frame, text="Reset",command = set_reset)
add_button.grid(row=0, column=1, padx=10, pady=10)

clear_button = Button(button_frame, text="Clear", command = set_clear)
clear_button.grid(row=0, column=2, padx=10, pady=10)

remove_one_button = Button(button_frame, text="Test")
remove_one_button.grid(row=0, column=3, padx=10, pady=10)


status_frame = LabelFrame(root, text="Status")
status_frame.pack(fill="x", expand="yes", padx=20)

status_var = StringVar()
status_var.set("Ready to connect")

status_label = Label(status_frame, textvariable=status_var)
status_label.grid(row=0, column=0, padx=10, pady=10)





root.mainloop()