from utils import scrape_image_paths
from segments import group_into_segments

import os
from paddleocr import PaddleOCR
import random
import time
import cv2
import numpy as np
import pyperclip  
import tkinter as tk
from PIL import Image, ImageTk
import threading

ocr = None

def load_ocr():
    global ocr
    ocr = PaddleOCR(lang="en", enable_mkldnn=False, use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False,)

ocr_thread = threading.Thread(target=load_ocr, daemon=True)
ocr_thread.start()



def popup_text(image, x, y, text):
    lines = text.split("\n")

    font = cv2.FONT_HERSHEY_COMPLEX_SMALL
    font_scale = 1
    thickness = 1
    padding = 5
    margin_abv_bel = 5
    line_sizes = [cv2.getTextSize(line, font, font_scale, thickness)[0] for line in lines]
    text_width = max(size[0] for size in line_sizes)
    text_height = max(size[1] for size in line_sizes)
    baseline = cv2.getTextSize(lines[0], font, font_scale, thickness)[-1]


    line_height = text_height + baseline
    block_size = (line_height*len(lines)) + (margin_abv_bel*2)
    # if enough space above
    rect_x1 = x
    rect_x2 = x + text_width + padding*2
    if y >= block_size + margin_abv_bel:
        rect_y1 = y - block_size - margin_abv_bel
        rect_y2 = y - margin_abv_bel
    # pop below
    else:
        rect_y1 = y + text_height + margin_abv_bel
        rect_y2 = rect_y1 + block_size 
        
    cv2.rectangle(image, (rect_x1, rect_y1), (rect_x2, rect_y2), (0,100,0), -1)

    text_x = x + padding
    text_y = rect_y1 + padding + text_height
    for line in lines:
        cv2.putText(image, line, (text_x, text_y), font, font_scale, (255,255,255), thickness)
        text_y += line_height



def mouse_callback(event, x, y, flags, param):
    window_name, image, segments, hovered_segment = param
    if event == cv2.EVENT_MOUSEMOVE:
        hovered_segment["segment"] = None
        for segment in segments:
            if point_in_rect(x,y, segment["rect"]):
                hovered_segment["segment"] = segment
                break                
        
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"clicked at {x}, {y}")
        cv2.circle(image, (x,y), 4, (0,255,0), -1)
        cv2.imshow("image", image)



def point_in_rect(px,py, rect):
    x,y,w,h = rect
    return x<=px<=x+w and y<=py<=y+h



def run_detection(image_path):
    if ocr is None:
        print("Model is still loading, please wait")
        return
    

    print("_"*20, f"{image_path.split('/')[-1]}", "_"*20)
    image = cv2.imread(image_path)
    result = ocr.predict(image_path)

    res = result[0]

    polys = res.get("dt_polys")
    texts = res.get("rec_texts")

    boxes = []
    for poly, text in zip(polys, texts):
        pts = np.array(poly, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(pts)
        boxes.append({"pts": pts, "rect": (x, y, w, h), "text": text})

    segments = group_into_segments(boxes, y_gap_ratio=0.6, min_x_overlap_ratio=0.3)
    print(f"found {len(segments)} segments")

    image = cv2.imread(image_path)
    copy_image = image.copy()

    for segment in segments:
        x,y,w,h = segment["rect"]
        cv2.rectangle(copy_image,  (x,y), (x+w,y+h), (0,255,0), 2)

    hovered_segment = {"segment":None}

    window_name = f"{(image_path.split('/')[-1]).split('.')[0]}"
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", mouse_callback, (window_name, copy_image, segments, hovered_segment))

    while True:
        temp_image = copy_image.copy()

        segment = hovered_segment["segment"]
        if segment is not None:
            rx, ry, rw, rh = segment["rect"]
            cv2.rectangle(temp_image, (rx,ry), (rx+rw, ry+rh), (0,0,0), 2)
            popup_text(temp_image, rx, ry, segment["text"])
        cv2.imshow("image", temp_image)

        key = cv2.waitKey(100) & 0xFF
        if key == ord("c"):
            pyperclip.copy(segment["text"])
            print("targated text copied.")
        elif key == ord("q"):
            cv2.destroyAllWindows()
            break




def process_image(image_path):
    run_detection(image_path)




def image_portal(image_paths, process_image):
    root = tk.Tk()
    root.title("Selection Portal")
    root.geometry("1000x1700")

    def key_call(event):
        if event.keysym == "q":
            root.destroy()

    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    frame = tk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0),window=frame,anchor="nw")
    def update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", update_scrollregion)
    def update_frame_width(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", update_frame_width)
    canvas.configure(yscrollcommand=scrollbar.set)
    thumbnails = []
    columns = 4
    for i, image_path in enumerate(image_paths):
        image = Image.open(image_path)
        image.thumbnail((200, 150))
        photo = ImageTk.PhotoImage(image)
        thumbnails.append(photo)
        row = i // columns
        column = i % columns
        button = tk.Button(frame, image=photo, command=lambda path=image_path: process_image(path))
        button.image = photo
        button.grid(row=row, column=column, padx=10, pady=10)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    root.bind("<Key>", key_call)
    root.mainloop()


dir_path = os.path.join("media", "input")
image_paths = scrape_image_paths(dir_path)
print(len(image_paths))
image_portal(image_paths, process_image)

