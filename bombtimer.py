import cv2
import sys
import numpy as np
import tkinter as tk
from screeninfo import get_monitors
import pyscreenshot as ImageGrab # use pyscreenshot instead of PIL for Linux support
from PIL import ImageTk, Image

# Stuff you can customize
debugmode = True # True displays image processing in window
checkdelay = 0.1 # Time in seconds the
c4time = 40
miniscoreboard_position = "top" # not implemented yet
imagegrabwidth = 150 # How wide the image cut the script checks will be from left to right

redmask_threshold1 = [114,60,20] # lower threshold for the color mask
redmask_threshold2 = [140,255,255] # upper threshold for the color mask
blurintensity = (5,5) # intensity of the image blurring
edgedetect_threshold1 = 300
edgedetect_threshold2 = 450
histogram_threshold1 = 420
histogram_threshold2 = 520
# End

version = "0.2"

print(f"\nCSGO-Bombtimer v{version} by 3urobeat")
print("---------------------------\n")
print("This Bombtimer is based on image recognition and can be unprecise.")
print("You can go into the bombtimer.py file to customize values or enable debugmode which lets you see what the program sees.")

counterstarted = False
countdowntime = c4time
notdetectedcount = 0

# Get images the cut will be compared to
matchimage = cv2.imread("bomb.jpg", 0)
histogram1 = cv2.calcHist([matchimage], [0], None, [256], [0, 256]) # compare image

# Initialize tkinter window
root = tk.Tk()
root.title("Bombtimer")
root.minsize(300, 175)

# Define tkinter labels
if debugmode:
    # Display images and labels
    panellabel = tk.Label(root, text="Unprocessed")
    panel = tk.Label(root)
    panellabel.pack()
    panel.pack()

    panel2label = tk.Label(root, text="Masked")
    panel2 = tk.Label(root)
    panel2label.pack()
    panel2.pack()

    panel3label = tk.Label(root, text="Processed")
    panel3 = tk.Label(root)
    panel3label.pack()
    panel3.pack()
    
timernamelabel = tk.Label(root, text="Bombtimer")
timerdetectedlabel = tk.Label(root, text="No Bomb detected.", fg='#32CD32')
timerlabel = tk.Label(root, text=str(c4time))
timernamelabel.pack()
timerdetectedlabel.pack()
timerlabel.pack()

if not debugmode:
    debugmodelabel = tk.Label(root, text="Got problems? Enable debugmode to see what I'm seeing.")
    debugmodelabel.pack()

# Define each step in an own function
def refreshWindow(unprocessedimg, maskedimg, processedimg):
    if debugmode:
        unprocessedimg = ImageTk.PhotoImage(image=unprocessedimg)
        
        maskedimg = Image.fromarray(maskedimg)
        maskedimg = ImageTk.PhotoImage(image=maskedimg)
        
        processedimg = Image.fromarray(processedimg)
        processedimg = ImageTk.PhotoImage(image=processedimg)
        
        panel.configure(image=unprocessedimg)
        panel.image = unprocessedimg
        
        panel2.configure(image=maskedimg)
        panel2.image = maskedimg

        panel3.configure(image=processedimg)
        panel3.image = processedimg # keep a reference, otherwise the garbage collector will sweep it up
        
def countdown():
    global counterstarted
    global countdowntime
    
    if counterstarted and countdowntime > 0:
        countdowntime = countdowntime - 1
        timerlabel.configure(text = countdowntime)
        root.after(1000, countdown)
    
def analyseImage(img):
    # Thanks: https://www.geeksforgeeks.org/measure-similarity-between-images-using-python-opencv/
    histogram = cv2.calcHist([img], [0], None, [256], [0, 256]) # imagegrab image 
    
    c1, c2 = 0, 0
    
    # Euclidean Distace between imagegrab and compare img
    i = 0
    while i<len(histogram) and i<len(histogram1): 
        c1+=(histogram[i]-histogram1[i])**2
        i+= 1
    c1 = c1**(1 / 2)
    
    print(str(c1))
    with open("test.txt", "a") as myfile:
        myfile.write(str(c1) + "\n")

    
    global counterstarted
    global countdowntime
    global notdetectedcount
    
    if c1 > histogram_threshold1 and c1 < histogram_threshold2:
        notdetectedcount = 0
        
        if not counterstarted:
            counterstarted = True
            
            countdown()
            timerdetectedlabel.configure(text="Bomb detected!", fg='#ff1944')
    else:
        if notdetectedcount > 3: # only trigger a reset after 3 wrong values
            if counterstarted: # change stuff only once
                countdowntime = c4time
                timerdetectedlabel.configure(text="No Bomb detected.", fg='#32CD32')
                timerlabel.configure(text = countdowntime)
                
            counterstarted = False
        else:
            notdetectedcount = notdetectedcount + 1
    
def processImage(img):
    image = np.array(img)
    
    # Brighten image
    image = cv2.add(image, np.array([50.0])) 
    
    # Apply red & green mask
    result = image.copy() # Thanks: https://stackoverflow.com/a/58194879/12934162
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(image, np.array(redmask_threshold1), np.array(redmask_threshold2)) # red
    result = cv2.bitwise_and(result, result, mask=mask)
    
    # Blur image
    blurred = cv2.GaussianBlur(result, blurintensity, 0)
    
    # Outline objects
    outlinedimg = cv2.Canny(blurred, edgedetect_threshold1, edgedetect_threshold2)
       
    analyseImage(outlinedimg)
    refreshWindow(img, blurred, outlinedimg)

def grabImage():
    width = get_monitors()[0].width # get current width and height
    height = get_monitors()[0].height # check this every iteration to get resolution changes (16:9 desktop -> 4:3 stretched for example)

    img = ImageGrab.grab(bbox = ((width / 2) - (imagegrabwidth / 2), 2, (width / 2) + (imagegrabwidth / 2), 30), childprocess=False).convert("RGB") # Gets exactly the bomb when 0 CT's and 1 T is online
    processImage(img)

    root.after(int(checkdelay * 1000), grabImage) # delay
        
grabImage() # Start grabbing images

while True:
    root.update() # Keep tkinter window alive
    root.update_idletasks()