
from tkinter import ttk
import math
from tkinter import messagebox, colorchooser
from tkinter import simpledialog
from tkinter import filedialog
from decimal import Decimal, ROUND_HALF_UP
from PIL import Image
import numpy as np
import tkinter as tk
from PIL import ImageGrab
import json
import os
from PIL.PngImagePlugin import PngInfo
from PIL import Image
from functools import partial
import pdb
import time
import threading
from reportlab.pdfgen import canvas
from reportlab.platypus import Table
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import datetime

class DrawingApp:
    def __init__(self):
        self.lines = []
        self.current_line = []
        self.unit_flag = False
        self.drawing = False
        self.edit_state = False
        self.drawing_enabled = True
        self.previous_angle = 0.0
        self.selected_line_index = None
        self.background_color = "white"
        self.border_color = "#f0f0f0"
        self.line_color = "black"
        self.unit = "mm"
        self.angle = 180
        self.line_width = 2
        self.scale = 1
        # self.current_order = 0
        self.animate_array = []
        self.animate_line_array = []
        self.current_animate_number = 0
        self.order = []
        self.angle_check = []
        self.angle_array = []
        self.animation_id = None
        self.order_arg = []

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title("Drawing App")
        
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        # Create the File menu
        file_menu = tk.Menu(menu_bar, tearoff=False) 
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Print", command=self.edit_pdf)

        draw_menu = tk.Menu(menu_bar, tearoff=False)
        draw_menu.add_command(label="draw", command=self.toggle_to_drawing_state)

        setting_menu = tk.Menu(menu_bar, tearoff=False)
        setting_menu.add_command(label="Edit", command=self.edit_handle)
        # setting_menu.add_command(label="Read", command=self.read_handle)

        setup_menu = tk.Menu(menu_bar, tearoff=False)
        setup_menu.add_command(label="Background-Color", command=self.open_background_color_picker)
        setup_menu.add_command(label="Border-Color", command=self.open_border_color_picker)

        unit_menu = tk.Menu(menu_bar, tearoff=False)
        unit_menu.add_command(label="Unit(mm)", command=self.select_mili)
        unit_menu.add_command(label="Unit(inch)", command=self.select_inch)

        line_info = tk.Menu(menu_bar, tearoff=False)
        line_info.add_command(label="Color", command=self.open_line_color_picker)
        line_info.add_command(label="Width", command=self.open_line_width_setup)

        animation_menu = tk.Menu(menu_bar, tearoff=False)
        animation_menu.add_command(label="Setting", command=self.open_modal)
        animation_menu.add_command(label="Auto", command=self.auto_animate)
        animation_menu.add_command(label="Step", command=self.handle_step)

        menu_bar.add_cascade(label="File", menu=file_menu)        
        menu_bar.add_cascade(label="Draw", menu=draw_menu)     
        menu_bar.add_cascade(label="Edit", menu=setting_menu)
        menu_bar.add_cascade(label="Setup", menu=setup_menu)
        menu_bar.add_cascade(label="Unit", menu=unit_menu)
        menu_bar.add_cascade(label="Animation", menu=animation_menu)

        setup_menu.add_cascade(label="Line", menu=line_info)        
        
       
        
        self.matrix=np.array([[1, 0, 0],
                              [0, 1, 0],
                              [0, 0, 1]])
        self.start_x = None
        self.start_y = None
        self.current_line = None
        self.edit_mode = False
        # Create the frame for the status table and buttons
        left_frame = tk.Frame(self.root, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        # left_frame.pack_propagate(0)        
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # Create the status table
        status_table = ttk.Treeview(left_frame, columns=("Seq","Length", "Angle", "Total_Length","Bal"))
        status_table.heading("#0", text="Line")
        status_table.heading("Seq", text="Seq")
        status_table.heading("Angle", text="Angle")
        status_table.heading("Length", text="Len")  
        status_table.heading("Total_Length", text="Total")
        status_table.heading("Bal", text="Bal")
          
        status_table.column("#0", width=50, stretch=tk.NO)  # Adjust the width of the "Line" column
        status_table.column("Seq", width=50, stretch=tk.NO)
        status_table.column("Angle", width=50, stretch=tk.NO)  # Adjust the width of the "Angle with Previous Line" column
        status_table.column("Length", width=50, stretch=tk.NO)  # Adjust the width of the "Length" column 
        status_table.column("Total_Length", width=50, stretch=tk.NO)  # Adjust the width of the "Total_Length" column 
        status_table.column("Bal", width=50, stretch=tk.NO)
          
        status_table.pack(fill=tk.Y)
        # status_table.pack(fill=tk.BOTH, expand=True)
        status_table.bind("<Double-1>", self.handle_double_click)
        self.status_table = status_table
        

        # Create the frame for the canvas
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, width = 800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_drawing)
        self.canvas.bind("<Button-3>", self.toggle_drawing_enabled)
        self.canvas.bind("<Double-Button-1>", self.select_line)
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        self.canvas.configure(bg=self.background_color)
        self.canvas.tag_raise("oval")
        self.canvas.tag_raise("text")

        self.toolbar = self.create_toolbar(bottom_frame)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        status_table.pack(fill=tk.BOTH, expand=True)

        # self.create_grid(self.canvas, 800, 600, 20)
        self.root.mainloop()
        
    def handle_step(self):
        self.edit_mode == False
        self.fit_button.configure(state="disabled")
        self.zoom_in_button.configure(state="disabled")
        self.zoom_out_button.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.backup_btn.configure(state="disabled")
        self.drawing_status_label.config(text="Drawing Disabled")

        self.canvas.delete("all")
        self.animate_array = []
        self.angle_array = []
        count = len(self.lines)
        # print(count)
        
        for i, line in enumerate(self.lines):
            if i + 1 < count:
                angle1 = math.atan2(line[1] - line[3], line[0] - line[2])
                angle2 = math.atan2(self.lines[i+1][3] - line[3], self.lines[i+1][2] - line[2])
                # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle  
                self.angle_array.append(round(abs(angle),1))


        self.matrix=np.array([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]])        
        self.scale=1
        self.canvas.delete("all")   

        total_length = 0  
        for i, line in enumerate(self.lines):            
            x1, y1 = self.calculate_transform_coordinate(self.lines[i][0], self.lines[i][1])
            x2, y2 = self.calculate_transform_coordinate(self.lines[i][2], self.lines[i][3]) 
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)/self.scale
            total_length += length
            self.animate_array.append(length)            
            # print(x1)
        x_init = self.canvas.winfo_width()/2 - total_length/2
        x1 = x_init
        # print(self.animate_array)        
        for i in range(len(self.animate_array)):           
             
            x2 = x1 + self.animate_array[i]
            y = self.canvas.winfo_height()/2
            # print(x1)
            # self.animate_line_array 
            # self.draw_line(x1, y, x2, y, "line")                      
            self.animate_line_array.append([x1,y,x2,y])               
            x1 = x2 
        self.order_arg = np.argsort(self.order) 
        self.draw_animate_lines()        
        self.implement_step_animate(self.current_animate_number)
        # Calculate the current bounding box of the drawing
        bbox = self.canvas.bbox("line")
        if bbox is not None:
            min_x, min_y, max_x, max_y = bbox
        else:
            # print("Test")
            return
        # Calculate the dimensions of the bounding box
        width = max_x - min_x
        height = max_y - min_y

        # Calculate the scaling factor to fit the drawing in the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width / width, canvas_height / height)*0.8

        # Move the drawing up by a specified amount
        move_up_amount = 0  # Adjust this value as needed
        dx = (canvas_width - width * scale) / 2 - min_x * scale
        dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
        self.scale = self.scale*scale
        
        self.canvas.delete("all")
        
        matrix2 = np.array([[scale,  0,       dx],
                            [0,      scale,   dy],
                            [0,      0,       1]])
        
        self.matrix = np.matmul(self.matrix, matrix2) 
        self.draw_animate_lines()
        self.current_animate_number +=1

    def auto_animate(self):  
        self.edit_mode == False
        self.fit_button.configure(state="disabled")
        self.zoom_in_button.configure(state="disabled")
        self.zoom_out_button.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.backup_btn.configure(state="disabled")
        self.drawing_status_label.config(text="Drawing Disabled")

        self.canvas.delete("all")
        self.animate_array = []
        self.angle_array = []
        count = len(self.lines)
        # print(count)
        self.matrix=np.array([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]]) 
        
        for i, line in enumerate(self.lines):
            if i + 1 < count:
                angle1 = math.atan2(line[1] - line[3], line[0] - line[2])
                angle2 = math.atan2(self.lines[i+1][3] - line[3], self.lines[i+1][2] - line[2])
                # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle  
                self.angle_array.append(round(abs(angle),1))


               
        self.scale=1
        self.canvas.delete("all")     
        
        total_length = 0  
        for i, line in enumerate(self.lines):            
            x1, y1 = self.calculate_transform_coordinate(self.lines[i][0], self.lines[i][1])
            x2, y2 = self.calculate_transform_coordinate(self.lines[i][2], self.lines[i][3]) 
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)/self.scale
            total_length += length
            self.animate_array.append(length)            
            # print(x1)
        x_init = self.canvas.winfo_width()/2 - total_length/2
        x1 = x_init
        # print(self.animate_array)        
        for i in range(len(self.animate_array)):           
             
            x2 = x1 + self.animate_array[i]
            y = self.canvas.winfo_height()/2
            # print(x1)
            self.animate_line_array 
            # self.draw_line(x1, y, x2, y, "line")                      
            self.animate_line_array.append([x1,y,x2,y])               
            x1 = x2 
        self.order_arg = np.argsort(self.order)        
        # self.canvas.after(10, partial(self.implement_animate, 0))
        # print(order_arg)
        # for i in range(0, len(order_arg)):
            # self.root.after(3500, self.implement_animate(i))
        self.draw_animate_lines()        
        self.implement_animate(self.current_animate_number)
        # Calculate the current bounding box of the drawing
        bbox = self.canvas.bbox("line")
        if bbox is not None:
            min_x, min_y, max_x, max_y = bbox
        else:
            print("Test")
            return
        # Calculate the dimensions of the bounding box
        width = max_x - min_x
        height = max_y - min_y

        # Calculate the scaling factor to fit the drawing in the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width / width, canvas_height / height)*0.8

        # Move the drawing up by a specified amount
        move_up_amount = 0  # Adjust this value as needed
        dx = (canvas_width - width * scale) / 2 - min_x * scale
        dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
        self.scale = self.scale*scale
        
        self.canvas.delete("all")
        
        matrix2 = np.array([[scale,  0,       dx],
                            [0,      scale,   dy],
                            [0,      0,       1]])
        
        self.matrix = np.matmul(self.matrix, matrix2) 
        self.draw_animate_lines()

    def implement_step_animate(self, index):
        self.canvas.delete("all")
        
        # print(self.animate_line_array)
        self.draw_animate_lines()            

        self.angle -= 0.1
        if self.current_animate_number > len(self.angle_array):
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:
                # print("Test")
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2) 
            self.draw_animate_lines()
            self.angle = 180
            return
        if index >= len(self.angle_array):
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:
                # print("Test")
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2) 
            self.draw_animate_lines()
            self.angle = 180
            return  # Animation has reached the end, exit the method
        
        if self.angle < self.angle_array[self.order_arg[index]]:
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:
                # print("Test")
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2) 
            self.draw_animate_lines()
            self.angle = 180
             
            # Calculate the current bounding box of the drawing
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:            
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2)   
            self.draw_animate_lines()                    
            return  # Terminate the current animation

        for i in range(self.order_arg[index], len(self.angle_array)):
            self.animate_line_array[i+1][0], self.animate_line_array[i+1][1] = self.rotate_point(self.animate_line_array[self.order_arg[index]][2], self.animate_line_array[self.order_arg[index]][3], self.animate_line_array[i+1][0], self.animate_line_array[i+1][1], self.angle_check[self.order_arg[index]]*0.1)
            self.animate_line_array[i+1][2], self.animate_line_array[i+1][3] = self.rotate_point(self.animate_line_array[self.order_arg[index]][2], self.animate_line_array[self.order_arg[index]][3], self.animate_line_array[i+1][2], self.animate_line_array[i+1][3], self.angle_check[self.order_arg[index]]*0.1)

        self.animation_id = self.canvas.after(1, partial(self.implement_step_animate, index))
    def open_modal(self):
        dialog = OrderEditDialog(self.root, self.order)
        result = dialog.result
        if result:
            # Handle the modified array
            self.order = result
            self.update_table_for_edit()
            # print(self.order)

    def implement_animate(self, index):
        self.canvas.delete("all")
               
        self.draw_animate_lines()        

        if index >= len(self.angle_array):
            self.angle = 180
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:
                # print("Test")
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2) 
            self.draw_animate_lines()
            return  # Animation has reached the end, exit the method

        self.angle -= 0.1

        if self.angle < self.angle_array[self.order_arg[index]]:
            # Calculate the current bounding box of the drawing
            bbox = self.canvas.bbox("line")
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
            else:
                # print("Test")
                return
            # Calculate the dimensions of the bounding box
            width = max_x - min_x
            height = max_y - min_y

            # Calculate the scaling factor to fit the drawing in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)*0.8

            # Move the drawing up by a specified amount
            move_up_amount = 0  # Adjust this value as needed
            dx = (canvas_width - width * scale) / 2 - min_x * scale
            dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
            self.scale = self.scale*scale
            
            self.canvas.delete("all")
            
            matrix2 = np.array([[scale,  0,       dx],
                                [0,      scale,   dy],
                                [0,      0,       1]])
            
            self.matrix = np.matmul(self.matrix, matrix2) 
            self.draw_animate_lines()
            self.angle = 180
            print("Animation stopped")

            if index + 1 < len(self.angle_array):
                # Start a new animation with the next index
                self.animation_id = self.canvas.after(1, partial(self.implement_animate, index+1))
            else:
                print("All animations complete")

            return  # Terminate the current animation

        for i in range(self.order_arg[index], len(self.angle_array)):
            self.animate_line_array[i+1][0], self.animate_line_array[i+1][1] = self.rotate_point(self.animate_line_array[self.order_arg[index]][2], self.animate_line_array[self.order_arg[index]][3], self.animate_line_array[i+1][0], self.animate_line_array[i+1][1], self.angle_check[self.order_arg[index]]*0.1)
            self.animate_line_array[i+1][2], self.animate_line_array[i+1][3] = self.rotate_point(self.animate_line_array[self.order_arg[index]][2], self.animate_line_array[self.order_arg[index]][3], self.animate_line_array[i+1][2], self.animate_line_array[i+1][3], self.angle_check[self.order_arg[index]]*0.1)

        self.animation_id = self.canvas.after(1, partial(self.implement_animate, index))

        
    def draw_animate_lines(self):
        # Iterate over the line information
        # pdb.set_trace()   
        self.edit_mode == False
        for i in range(0,len(self.animate_array)): 
            
            start_x , start_y = self.calculate_transform_coordinate(self.animate_line_array[i][0], self.animate_line_array[i][1])
            end_x, end_y = self.calculate_transform_coordinate(self.animate_line_array[i][2], self.animate_line_array[i][3]) 
  
            # Draw a line on the canvas
            self.draw_line(start_x, start_y, end_x, end_y, "line")
            # self.canvas.create_line(start_x, start_y, end_x, end_y)
            self.draw_line_with_length(start_x, start_y, end_x, end_y)
            if i== 0:
                self.draw_circle_with_number(start_x, start_y, 8, i)
            self.draw_circle_with_number(end_x, end_y, 8, i+1)
            if i > 0:
                x3, y3 = self.calculate_transform_coordinate(self.animate_line_array[i-1][0], self.animate_line_array[i-1][1])
                self.draw_blocked_arc(x3,y3,start_x,start_y,end_x,end_y, 20)
                # half = self.angle_array[:len(self.angle_array)//2]
                # self.angle_array = half
        # pdb.set_trace() 

    def rotate_point(self, center_x, center_y, x1, y1, angle):
        # print(angle)
        angle = math.radians(angle)
        # Translate the coordinates
        translated_x1 = x1 - center_x
        translated_y1 = y1 - center_y        

        # Apply rotation
        rotated_x1 = translated_x1 * math.cos(angle) - translated_y1 * math.sin(angle)
        rotated_y1 = translated_x1 * math.sin(angle) + translated_y1 * math.cos(angle)


        # Translate back to the original coordinate system
        new_x1 = rotated_x1 + center_x
        new_y1 = rotated_y1 + center_y        

        return new_x1, new_y1
    
    def select_mili(self):
        self.unit = "mm"
        self.unit_label.config(text="Unit: mm")
        self.canvas.delete("all")
        self.create_grid(self.canvas, 800, 600, 20)          
        self.update_status_table()
        self.redraw_lines()
        
    def select_inch(self):
        self.unit = "inch"
        self.unit_label.config(text="Unit: inch")
        self.canvas.delete("all")
        self.create_grid(self.canvas, 800, 600, 20)          
        self.update_status_table()
        self.redraw_lines()
        
    def open_line_width_setup(self):
        dialog = LineSettingDialog(self.root, self.line_width)  
        if dialog.result:
            self.line_width = dialog.result
            self.redraw_lines()

    def open_line_color_picker(self):
        color = colorchooser.askcolor(title="Select a color")
        self.line_color = color[1]  # Get the hexadecimal value of the chosen color
        self.redraw_lines()

    def open_background_color_picker(self):
        color = colorchooser.askcolor(title="Select a color")
        self.background_color = color[1]  # Get the hexadecimal value of the chosen color
        self.canvas.configure(bg=self.background_color)

    def open_border_color_picker(self):   
        color = colorchooser.askcolor(title="Select a color")
        self.border_color = color[1]  # Get the hexadecimal value of the chosen color
        self.toolbar.configure(bg=self.border_color) 

    def draw_circle_with_number(self, x, y, radius, number):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="black", outline="black")
        self.canvas.create_text(x, y, text=number, font=("Arial", 8, "bold"), fill="white")

    def create_toolbar(self, parent):
        # Create the toolbar (Backup, Clear, etc.)
        toolbar = tk.Frame(parent, bg = self.border_color)

        self.backup_btn = tk.Button(toolbar, text="Backup", command=self.backup_line, width=10)
        self.backup_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(toolbar, text="Clear", command=self.clear_drawing, width=10)
        self.clear_btn.pack(side=tk.LEFT)

        self.zoom_in_button = tk.Button(toolbar, text="Zoom In", command=self.zoom_in, width=10)
        self.zoom_in_button.pack(side=tk.LEFT)

        self.zoom_out_button = tk.Button(toolbar, text="Zoom Out", command=self.zoom_out, width=10)
        self.zoom_out_button.pack(side=tk.LEFT)

        self.fit_button = tk.Button(toolbar, text="Fit", command=self.fit_canvas, width=10)
        self.fit_button.pack(side=tk.LEFT)

        self.drawing_status_label = tk.Label(toolbar, text="", font=("Arial", 10, "bold"))
        self.drawing_status_label.pack(side=tk.LEFT)

        self.unit_label = tk.Label(toolbar, text="Unit: mm", font=("MingLiU-ExtB", 10))
        self.unit_label.pack(side=tk.RIGHT)

        return toolbar   

    def toggle_to_drawing_state(self):
        self.fit_button.configure(state="active")
        self.zoom_in_button.configure(state="active")
        self.zoom_out_button.configure(state="active")
        self.clear_btn.configure(state="active")
        self.backup_btn.configure(state="active")
        self.clear_drawing()
        self.create_grid(self.canvas, 800, 600, 20)
        self.drawing_enabled = True
        self.edit_state =False
        self.edit_mode = True
        self.drawing_status_label.config(text="Drawing Enabled")
    def update_table_for_edit(self):
        self.status_table.delete(*self.status_table.get_children())
        total_length = 0 
        count = len(self.lines)
        # print(count)
        # print(self.order)
        for i, line in enumerate(self.lines):
            if i + 1 < count:
                angle1 = math.atan2(line[1] - line[3], line[0] - line[2])
                angle2 = math.atan2(self.lines[i+1][3] - line[3], self.lines[i+1][2] - line[2])
                # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle  
                # self.angle_array.append(round(abs(angle),1))
                angle = str(round(abs(angle), 2))
                seq = self.order[i]
            else:                
                # angle = math.degrees(math.atan2(line[3] - line[1], line[2] - line[0]))
                angle = ""    
                seq=""        
            
            
            length = self.calculate_length(line[0], line[1], line[2], line[3])
            total_length +=  length
            
            if self.unit == "inch":
                self.status_table.insert("", "end", text=str(i+1), values=(seq, round(length/25.4, 2), angle, round(total_length/25.4, 2), self.total_length - round(length/25.4, 2)))
            else:
                self.status_table.insert("", "end", text=str(i+1), values=(seq, round(length, 2), angle, round(total_length, 2), self.total_length - round(length, 2)))
    def edit_handle(self):
        # self.edit_mode = True 

        self.edit_state =True
        self.canvas.delete("grid_line")
        # self.create_grid(self.canvas, 800, 600, 20)
        self.drawing_status_label.config(text="Drawing Disabled")
        print(self.total_length)
        print(self.order)
        # self.update_status_table() 
        self.update_table_for_edit()

    def read_handle(self):
        self.edit_mode = False
        self.canvas.delete("grid_line")
        self.drawing_status_label.config(text="")
    def create_grid(self, canvas, width, height, grid_size):        

        # Draw vertical lines
        grid = int(grid_size * self.scale)
        for x in range(0, width, grid):
            canvas.create_line(x, 0, x, height, fill='#d3d3d3', tags='grid_line')

        # Draw horizontal lines
        for y in range(0, height, grid):
            canvas.create_line(0, y, width, y, fill='#d3d3d3', tags='grid_line')
        canvas.lower("grid_line")

    def snap_to_grid(self, x, y, size):
        grid_size = int(self.scale * size)
        # Calculate the nearest grid point
        nearest_x = round(x / grid_size) * grid_size
        nearest_y = round(y / grid_size) * grid_size
        return nearest_x, nearest_y
    
    def draw_blocked_arc(self, x1, y1, x2, y2, x3, y3, radius):
        # Calculate the angle between the lines
        angle1 = math.atan2(y1 - y2, x1 - x2)
        angle2 = math.atan2(y3 - y2, x3 - x2)
        start_angle = math.degrees(angle1)
        end_angle = math.degrees(angle2)
        # print(start_angle)
        # print(end_angle)
        # Draw the blocked arc
        if end_angle - start_angle > 180:
            self.canvas.create_arc(x2 - radius, y2 - radius, x2 + radius, y2 + radius,
                            start=-start_angle, extent=360 - end_angle + start_angle,
                            style=tk.ARC, outline="red", width=2)
            
        elif end_angle - start_angle < -180:
            self.canvas.create_arc(x2 - radius, y2 - radius, x2 + radius, y2 + radius,
                            start=-start_angle, extent= -(360 + end_angle - start_angle),
                            style=tk.ARC, outline="red", width=2)
        else:
            self.canvas.create_arc(x2 - radius, y2 - radius, x2 + radius, y2 + radius,
                            start=-start_angle, extent=-end_angle + start_angle,
                            style=tk.ARC, outline="red", width=2)

        # Calculate the middle angle
        total_angle = start_angle + end_angle
        middle_angle = total_angle / 2
        # middle_angle = (start_angle + end_angle) / 2        

        # Calculate the rotation angle for the text
        if end_angle - start_angle > 180:
            rotation_angle = 270 - middle_angle
            angle = 360 - end_angle + start_angle
            middle_angle =180 - middle_angle
        elif end_angle - start_angle < -180:
            # print("test")
            rotation_angle = -90 - middle_angle
            angle = 360 + end_angle - start_angle
            middle_angle = 180 - middle_angle
        else:
            rotation_angle = 90 - middle_angle
            angle = end_angle - start_angle

        # print(middle_angle)
        intersect_x = x2 + radius * math.cos(math.radians(middle_angle))
        intersect_y = y2 + radius * math.sin(math.radians(middle_angle))
        # Calculate the position of the text
        text_distance = 10
        text_x = intersect_x + text_distance * math.cos(math.radians(middle_angle))
        text_y = intersect_y + text_distance * math.sin(math.radians(middle_angle))
        
        # Draw the text of the angle with rotation
        angle_text = f"{abs(angle):.2f}°"
        self.canvas.create_text(text_x, text_y, text=angle_text, font=("Arial", 10), fill="black", angle=rotation_angle)
        
        
    def draw_line_with_length(self, x1, y1, x2, y2):

        if x2 < x1:
            tmpx = x2
            tmpy = y2
            x2 = x1
            y2 = y1
            x1 = tmpx
            y1 = tmpy
        # self.canvas.create_line(x1, y1, x2, y2)
        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)/self.scale
        mid_x = (x1 + x2) / 2 + 10
        mid_y = (y1 + y2) / 2 + 10
        angle = - math.atan2(y2 - y1, x2 - x1) * 180 / math.pi
        # Calculate the offset coordinates
        offset = 10
        offset_x = offset * math.cos(math.radians(angle))
        offset_y = offset * math.sin(math.radians(angle))
        # print(angle)
        # Adjust the midpoint coordinates with the offset
        text_x = mid_x + offset_x
        text_y = mid_y + offset_y
        # print(angle)
        if self.unit == "mm":
            self.canvas.create_text(text_x, text_y, text=f"{length:.2f}", font=("Arial", 10), fill="black", angle=angle)
        else:
            self.canvas.create_text(text_x, text_y, text=f"{length/25.4:.2f}", font=("Arial", 10), fill="black", angle=angle)
    
    def edit_pdf(self):
        self.save_canvas()
        current_time = datetime.datetime.now()
        filename = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        pdf_path = filename + ".pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
    
        # Create the table data
        table_data = [
            ['Line', 'Length', 'Angle', 'Total_Length']            
        ]
        total_length = 0 
        count = len(self.lines)
        
        for i, line in enumerate(self.lines):
            info = []
            if i + 1 < count:
                angle1 = math.atan2(line[1] - line[3], line[0] - line[2])
                angle2 = math.atan2(self.lines[i+1][3] - line[3], self.lines[i+1][2] - line[2])                
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle                  
                angle = str(round(abs(angle), 2))
                
            else:                
                # angle = math.degrees(math.atan2(line[3] - line[1], line[2] - line[0]))
                angle = ""            

            
            length = self.calculate_length(line[0], line[1], line[2], line[3])
            total_length +=  length
            info.append(i+1)
            info.append(str(round(length, 2)))
            info.append(angle)
            info.append(str(round(total_length, 2)))
            table_data.append(info)
        
        # Create the table and set its style
        table = Table(table_data, colWidths=[100, 100, 100, 100])
        table.setStyle([
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ('BACKGROUND', (0, 0), (-1, 0), 'gray')
        ])
        
        # Get the dimensions of the PDF page
        page_width, page_height = letter
        
        # Calculate the width of the table
        table_width = sum(table._colWidths)
        
        # Calculate the x-coordinate to center the table horizontally
        x = (page_width - table_width) / 2
        
        # Draw the table on the canvas
        table.wrapOn(c, page_width, page_height)
        table.drawOn(c, x, 600)  # Adjust the vertical position as needed
        
        # Open the image and get its dimensions
        img = ImageReader("output.png")
        img_width, img_height = img.getSize()
        
        # Calculate the scaling factor to fit the image within the page width
        scaling_factor = page_width / img_width
        
        # Calculate the new width and height of the image
        new_width = img_width * scaling_factor
        new_height = img_height * scaling_factor
        
        # Calculate the coordinates to center the image horizontally below the table
        x = (page_width - new_width) / 2
        y = 50  # Adjust the vertical position as needed
        
        # Draw the image on the canvas
        c.drawImage(img, x, y, width=new_width, height=new_height)
        
        c.save()
        if os.path.exists("output.png"):
                os.remove("output.png")
   
    def save_file(self):
        file_path = filedialog.asksaveasfilename()
        
        if file_path:
            file_path = os.path.splitext(file_path)[0]
            # Double array (2D array) data
            array_data = np.array(self.lines)
            self.save_canvas()

            # Convert the array to a JSON string
            json_data = json.dumps(array_data.tolist())

            # Open an image           

            targetImage = Image.open("output.png")

            metadata = PngInfo()
            metadata.add_text("data", json_data)            

            targetImage.save(file_path + ".png", pnginfo=metadata)
            # targetImage = Image.open("NewPath.png")

            # print(targetImage.text)

            # Save the image without metadata
            self.read_handle()
            if os.path.exists("output.png"):
                os.remove("output.png")

    def save_canvas(self):
        # Get the canvas coordinates
        x = self.root.winfo_x() + self.canvas.winfo_x() + 360
        y = self.root.winfo_y() + self.canvas.winfo_y() + 50
        # print(x)
        # print(y)
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()

        # Capture the canvas as an image
        image = ImageGrab.grab((x, y, x1, y1))

        # Save the image to a file
        image.save("output.png")
        

    def open_file(self):
        # Open the file dialog for opening a file
        file_path = filedialog.askopenfilename()

        if file_path:
            targetImage = Image.open(file_path)
            # print(targetImage.text)
            data_dict = targetImage.text
            json_data = data_dict['data']
            self.lines = json.loads(json_data)
            self.redraw_lines()
            self.update_status_table()
            
        
    def fit_canvas(self):
        # Calculate the current bounding box of the drawing
        bbox = self.canvas.bbox("line")
        if bbox is not None:
            min_x, min_y, max_x, max_y = bbox
        else:
            return
        # Calculate the dimensions of the bounding box
        width = max_x - min_x
        height = max_y - min_y

        # Calculate the scaling factor to fit the drawing in the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width / width, canvas_height / height)*0.8

        # Move the drawing up by a specified amount
        move_up_amount = 0  # Adjust this value as needed
        dx = (canvas_width - width * scale) / 2 - min_x * scale
        dy = (canvas_height - height * scale) / 2 - min_y * scale - move_up_amount
        self.scale = self.scale*scale
          
        self.canvas.delete("all")
        
        matrix2 = np.array([[scale,  0,       dx],
                            [0,      scale,   dy],
                            [0,      0,       1]])
        
        self.matrix = np.matmul(self.matrix, matrix2)
        # print(self.matrix)
        self.redraw_lines()
        if self.edit_mode == True and self.edit_state == False:
            self.create_grid(self.canvas, 800, 600, 20)    
        


    def zoom_in(self):
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        self.scale = self.scale * 1.2       
        
        self.canvas.delete("all")
        
        matrix2 = np.array([[1.2,   0,    center_x * (1 - 1.2)],
                            [ 0,    1.2,  center_y * (1 - 1.2)],
                            [0,     0,                 1]])
        self.matrix = np.matmul(self.matrix, matrix2)

        self.redraw_lines()

        if self.edit_mode == True and self.edit_state == False:
            self.create_grid(self.canvas, 800, 600, 20)  
        
    def zoom_out(self):
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        self.scale = self.scale * 0.8        
        self.canvas.delete("all")
        self.create_grid(self.canvas, 800, 600, 20)
        matrix2 = np.array([[0.8,   0,    center_x * (1 - 0.8)],
                            [ 0,    0.8,  center_y * (1 - 0.8)],
                            [0,     0,                 1]])
        self.matrix = np.matmul(self.matrix, matrix2)

        self.redraw_lines()
        if self.edit_mode == True and self.edit_state == False:
            self.create_grid(self.canvas, 800, 600, 20) 
        # print(self.matrix)

    def on_mouse_scroll(self, event):
        zoom_factor = 1.2 if event.delta > 0 else 0.8
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.scale = self.scale * zoom_factor
        self.canvas.scale("all", x, y, zoom_factor, zoom_factor)
        
        matrix2 = np.array([[zoom_factor,   0,              x * (1 - zoom_factor)],
                            [0,            zoom_factor,     y * (1 - zoom_factor)],
                            [0,             0,              1]])
        
        self.matrix = np.matmul(self.matrix, matrix2)
        self.canvas.delete("grid_line")
        if self.edit_mode == True and self.edit_state == False:
            self.create_grid(self.canvas, 800, 600, 20)
        
    def toggle_drawing_enabled(self, event):        
        if self.edit_mode == False:
            self.drawing_status_label.config(text="")
        else:
            self.drawing_enabled = not self.drawing_enabled
            if self.drawing_enabled:
                self.drawing_status_label.config(text="Drawing Enabled")
            else:
                self.drawing_status_label.config(text="Drawing Disabled")

    def start_drawing(self, event):
        if self.edit_mode == True and self.edit_state == False:
            if self.drawing_enabled:  # Check if drawing is enabled
                if not self.drawing:
                    if self.lines:                        
                        last_line = self.lines[-1]
                        self.current_line = [last_line[2], last_line[3]]
                    else:
                        x, y=self.snap_to_grid(event.x, event.y, 20)
                        self.draw_circle_with_number(x,y,8,0)
                        self.current_line = [x, y]                        
                    self.drawing = True

    def draw(self, event):
        if self.edit_mode == True and self.edit_state == False:
            if self.drawing_enabled:  # Check if drawing is enabled
                if self.drawing:
                    self.canvas.delete("current_line")    
                    new_x, new_y = self.calculate_transform_coordinate(self.current_line[0], self.current_line[1])
                    self.draw_line(new_x, new_y, event.x, event.y, "current_line")

    def end_drawing(self, event):
        if self.edit_mode == True and self.edit_state == False:
            if self.drawing_enabled:  # Check if drawing is enabled
                if self.drawing:
                    self.canvas.delete("current_line")
                    x, y=self.snap_to_grid(event.x, event.y, 20)
                    # x, y = self.calculate_transform_coordinate(x, y)
                    inverse_matrix = np.linalg.inv(self.matrix)
                    original_coordinates = np.array([[x],
                                                    [y],
                                                    [1]])
                    transformed_coordinates = np.matmul(inverse_matrix, original_coordinates)
                    new_x = transformed_coordinates[0][0]
                    new_y = transformed_coordinates[1][0]
                    self.current_line.extend([new_x, new_y])
                    if abs(self.current_line[0] - self.current_line[2]) > 10 or abs(self.current_line[1] - self.current_line[3]) > 10: 
                        self.lines.append(self.current_line)
                        
                    self.current_line = []
                    self.drawing = False                    
                    self.update_status_table()
                    self.redraw_lines() 
        


    def backup_line(self):
        self.canvas.delete("all")
        if self.lines:
            self.lines.pop()
            self.create_grid(self.canvas, 800, 600, 20)   
            self.update_status_table()
            self.redraw_lines()

    def clear_drawing(self):
        
        self.animate_array = []
        self.animate_line_array = []
        self.current_animate_number = 0
        self.order = []
        self.angle_check = []
        self.angle_array = []
        self.animation_id = None
        self.order_arg = []
        self.lines = []
        self.total_length = 0
        
        self.matrix=np.array([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]])
        
        self.scale=1
        self.canvas.delete("all")
        self.create_grid(self.canvas, 800, 600, 20)          
        self.update_status_table()
        self.redraw_lines()

    def update_status_table(self):
        # self.angle_array = []
        self.status_table.delete(*self.status_table.get_children())
        total_length = 0 
        count = len(self.lines)
        # print(count)
        # print(self.order)
        for i, line in enumerate(self.lines):
            if i + 1 < count:
                angle1 = math.atan2(line[1] - line[3], line[0] - line[2])
                angle2 = math.atan2(self.lines[i+1][3] - line[3], self.lines[i+1][2] - line[2])
                # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle  
                # self.angle_array.append(round(abs(angle),1))
                angle = str(round(abs(angle), 2))
                
            else:                
                # angle = math.degrees(math.atan2(line[3] - line[1], line[2] - line[0]))
                angle = ""            
            # if self.edit_state:
            #     if i > 0:
            #         seq = self.order[i]
            #     else:
            #         seq = ""
            # else:
            #     seq = ""
            seq=""
            length = self.calculate_length(line[0], line[1], line[2], line[3])
            total_length +=  length
            
            if self.unit == "inch":
                self.status_table.insert("", "end", text=str(i+1), values=("", round(length/25.4, 2), angle, round(total_length/25.4, 2), ""))
            else:
                self.status_table.insert("", "end", text=str(i+1), values=("", round(length, 2), angle, round(total_length, 2), ""))
            
        # print(self.angle_array)
        # if index == 1:
        #     self.status_table.selection_set(item_id)
    def calculate_transform_coordinate(self, x, y):
        original_coordinates = np.array([[x],
                                        [y],
                                        [1]])
        transformed_coordinates = np.matmul(self.matrix, original_coordinates)
        new_x = transformed_coordinates[0][0]
        new_y = transformed_coordinates[1][0]
        return new_x, new_y
    
    def redraw_lines(self):
        self.total_length = 0
        self.canvas.delete("all")       
        self.order = [] 
        self.angle_array = []
        self.angle_check = []
        if not self.edit_state:
            self.create_grid(self.canvas, 800, 600, 20)
        for i, line in enumerate(self.lines):   
            length = self.calculate_length(line[0], line[1], line[2], line[3])
            self.total_length +=  length
            x1, y1 = self.calculate_transform_coordinate(line[0], line[1])
            x2, y2 = self.calculate_transform_coordinate(line[2], line[3])           
            
            self.draw_line(x1, y1, x2, y2, "line")
            self.draw_line_with_length(x1, y1, x2, y2)
            if i == 0:
                self.draw_circle_with_number(x1, y1, 8, i)
            self.draw_circle_with_number(x2, y2, 8, i+1)

            if i > 0:
                x3, y3 =self.calculate_transform_coordinate(self.lines[i-1][0], self.lines[i-1][1])
                self.draw_blocked_arc(x3,y3,x1,y1,x2,y2, 25)
                self.angle_check.append(self.is_above_line(x3,y3,x1,y1,x2,y2))
                self.order.append(i)
        self.canvas.tag_raise("oval")
        self.canvas.tag_raise("text")

    def is_above_line(self, x1, y1, x2, y2, x3, y3):
        if (y2-y1)*(x3-x1) - (x2-x1)*(y3-y1) > 0:
            return 1
        else:
            return -1
        # slope_line12 = (y2 - y1) / (x2 - x1)
        # slope_line13 = (y3 - y1) / (x3 - x1)
        
        # if slope_line13 > slope_line12:
        #     return 1
        # else:
        #     return -1
        
    def draw_line(self, x1, y1, x2, y2, tag):
        self.canvas.create_line(x1, y1, x2, y2, fill=self.line_color, width=self.line_width, tags=tag)
           
        
        
    def calculate_length(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return round(math.sqrt(dx ** 2 + dy ** 2), 2)
    
    def handle_double_click(self, event):
        selected_item = self.status_table.focus()
        line_number = int(self.status_table.index(selected_item))
        self.selected_line_index = line_number
        selected_line = self.lines[line_number]

        line = self.lines[line_number]  # Get the line segment at index i from the list
        x1, y1, x2, y2 = line  # Unpack the coordinates of the line

        midpoint_x = (x1 + x2) / 2  # Calculate the x-coordinate of the midpoint
        midpoint_y = (y1 + y2) / 2  # Calculate the y-coordinate of the midpoint

        item = self.canvas.find_closest(midpoint_x, midpoint_y)[0]  # Find the closest item to the click position

        # Check if the selected item is a line
        if "line" in self.canvas.gettags(item):
            # Deselect all lines
            for line in self.canvas.find_withtag("line"):
                self.canvas.itemconfig(line, width=1)

            # Select the clicked line
            self.canvas.itemconfig(item, width=3)        

        if self.edit_mode and self.edit_state == True:
            dialog = LineEditDialog(self.root, selected_line, self.selected_line_index, self.lines, self.unit)
            if dialog.result:
                [dx1,dy1,dx2,dy2]=dialog.result
                # Check if the selected line is not the last line
                if self.selected_line_index < len(self.lines) - 1:
                    # Calculate the difference between the old and new end points
                    # diff_x = dialog.result[2] - self.lines[self.selected_line_index][2]
                    # diff_y = dialog.result[3] - self.lines[self.selected_line_index][3]
                    
                    # Update the subsequent lines
                    for i in range(self.selected_line_index + 1, len(self.lines)):
                        # print(type(self.lines[i]))
                        # self.lines[i] = list(self.lines[i])
                        self.lines[i] = list(self.lines[i])
                        self.lines[i][0] += dx1
                        self.lines[i][1] += dy1
                        self.lines[i][2] += dx1
                        self.lines[i][3] += dy1
                    self.lines[self.selected_line_index] = self.lines[self.selected_line_index][0],self.lines[self.selected_line_index][1],self.lines[self.selected_line_index][2]+dx1,self.lines[self.selected_line_index][3]+dy1
                    if self.selected_line_index < len(self.lines) - 1:
                        for i in range(self.selected_line_index + 2, len(self.lines)):
                            self.lines[i] = list(self.lines[i])
                            self.lines[i][0] += dx2
                            self.lines[i][1] += dy2
                            self.lines[i][2] += dx2
                            self.lines[i][3] += dy2
                        self.lines[self.selected_line_index+1] = self.lines[self.selected_line_index+1][0],self.lines[self.selected_line_index+1][1],self.lines[self.selected_line_index+1][2]+dx2,self.lines[self.selected_line_index+1][3]+dy2
                else:
                    self.lines[self.selected_line_index] = list(self.lines[self.selected_line_index])
                    self.lines[self.selected_line_index][2] += dx1
                    self.lines[self.selected_line_index][3] += dy1
                self.canvas.delete("all")
                self.create_grid(self.canvas, 800, 600, 20)
                self.redraw_lines()
                self.update_table_for_edit()
        

    def select_line(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]  # Find the closest item to the click position

        # Check if the selected item is a line
        if "line" in self.canvas.gettags(item):
            # Deselect all lines
            for line in self.canvas.find_withtag("line"):
                self.canvas.itemconfig(line, width=self.line_width)

            # Select the clicked line
            self.canvas.itemconfig(item, width=self.line_width+2)

        x, y = event.x, event.y
        selected_line = None

        for i, line in enumerate(self.lines):
            x1, y1, x2, y2 = line
            if self.point_near_line(x, y, x1, y1, x2, y2):
                selected_line = line
                self.selected_line_index = i
                break

        if selected_line:
            # Highlight the corresponding row in the status table
            self.status_table.selection_set(self.status_table.get_children()[self.selected_line_index])
            if self.edit_mode == True and self.edit_state == True:
                dialog = LineEditDialog(self.root, selected_line, self.selected_line_index, self.lines, self.unit)
                if dialog.result:
                    [dx1,dy1,dx2,dy2]=dialog.result
                    # Check if the selected line is not the last line
                    if self.selected_line_index < len(self.lines) - 1:
                        # Calculate the difference between the old and new end points
                        # diff_x = dialog.result[2] - self.lines[self.selected_line_index][2]
                        # diff_y = dialog.result[3] - self.lines[self.selected_line_index][3]
                        
                        # Update the subsequent lines
                        for i in range(self.selected_line_index + 1, len(self.lines)):
                            # print(type(self.lines[i]))
                            # self.lines[i] = list(self.lines[i])
                            self.lines[i] = list(self.lines[i])
                            self.lines[i][0] += dx1
                            self.lines[i][1] += dy1
                            self.lines[i][2] += dx1
                            self.lines[i][3] += dy1
                        self.lines[self.selected_line_index] = self.lines[self.selected_line_index][0],self.lines[self.selected_line_index][1],self.lines[self.selected_line_index][2]+dx1,self.lines[self.selected_line_index][3]+dy1
                        if self.selected_line_index < len(self.lines) - 1:
                            for i in range(self.selected_line_index + 2, len(self.lines)):
                                self.lines[i] = list(self.lines[i])
                                self.lines[i][0] += dx2
                                self.lines[i][1] += dy2
                                self.lines[i][2] += dx2
                                self.lines[i][3] += dy2
                            self.lines[self.selected_line_index+1] = self.lines[self.selected_line_index+1][0],self.lines[self.selected_line_index+1][1],self.lines[self.selected_line_index+1][2]+dx2,self.lines[self.selected_line_index+1][3]+dy2
                    else:
                        self.lines[self.selected_line_index] = list(self.lines[self.selected_line_index])
                        self.lines[self.selected_line_index][2] += dx1
                        self.lines[self.selected_line_index][3] += dy1
                    self.canvas.delete("all")
                    self.create_grid(self.canvas, 800, 600, 20)
                    self.redraw_lines()
                    self.update_table_for_edit()
                    

    def point_near_line(self, x, y, x1, y1, x2, y2):
        distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return distance < 5
    
class LineSettingDialog(simpledialog.Dialog):
    def __init__(self, parent, width):
        self.line_width = width        
        super().__init__(parent, title="Edit Line Setting")

    def body(self, master):
        label = tk.Label(master, text="Angle:")
        label.grid(row=0, column=0, sticky=tk.E)
        self.width_entry = tk.Entry(master)
        self.width_entry.grid(row=0, column=1)

    def buttonbox(self):
        box = tk.Frame(self)

        ok_button = tk.Button(box, text="OK", width=10, command=self.ok)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)

        cancel_button = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):        
        try:           

            length = float(self.width_entry.get())
            self.result = length
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid width values.")

    def cancel(self, event=None):
        self.result = None
        self.destroy() 

class LineEditDialog(simpledialog.Dialog):
    def __init__(self, parent, line, index, lines, unit):
        self.line = line
        self.result = None
        self.index = index
        self.lines = lines
        self.unit = unit
        super().__init__(parent, title="Edit Line Information")

    def body(self, master):
        angle_label = tk.Label(master, text="Angle:")
        angle_label.grid(row=0, column=0, sticky=tk.E)

        length_label = tk.Label(master, text="Length:")
        length_label.grid(row=1, column=0, sticky=tk.E)

        self.angle_entry = tk.Entry(master)
        self.angle_entry.grid(row=0, column=1)
        # print(self.index)
        
        self.angle_entry.insert(tk.END, self.calculate_angle())
        count = len(self.lines)
        if not self.index + 1 < count:
            self.angle_entry.configure(state="readonly")

        self.length_entry = tk.Entry(master)
        self.length_entry.grid(row=1, column=1)
        if self.unit == "mm":
            self.length_entry.insert(tk.END, self.calculate_length(self.line[0], self.line[1], self.line[2], self.line[3]))
        else:
            self.length_entry.insert(tk.END, self.calculate_length(self.line[0], self.line[1], self.line[2], self.line[3])/25.4)
      

    def calculate_angle(self):
        count = len(self.lines)
        if self.index + 1 < count:
                angle1 = math.atan2(self.line[1] - self.line[3], self.line[0] - self.line[2])
                angle2 = math.atan2(self.lines[self.index+1][3] - self.line[3], self.lines[self.index+1][2] - self.line[2])
                # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                start_angle = math.degrees(angle1)
                end_angle = math.degrees(angle2)   
                
                if end_angle - start_angle > 180:            
                    angle = 360 - end_angle + start_angle            
                elif end_angle - start_angle < -180:           
                    angle = 360 + end_angle - start_angle
                    
                else:            
                    angle = end_angle - start_angle  

                angle = round(abs(angle), 2)
            
        else:                
            # angle = math.degrees(math.atan2(line[3] - line[1], line[2] - line[0]))
            angle = 0            
            
        return abs(angle)
    
    def buttonbox(self):
        box = tk.Frame(self)

        ok_button = tk.Button(box, text="OK", width=10, command=self.ok)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)

        cancel_button = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):        
        try:
            count = len(self.lines)
            if self.index + 1 < count:
                    angle1 = math.atan2(self.line[1] - self.line[3], self.line[0] - self.line[2])
                    angle2 = math.atan2(self.lines[self.index+1][3] - self.line[3], self.lines[self.index+1][2] - self.line[2])
                    # angle1 = math.atan2(self.lines[i-1][1] - line[1], self.lines[i-1][0] - line[0])
                    # angle2 = math.atan2(line[3] - line[1], line[2] - line[0])
                    start_angle = math.degrees(angle1)
                    end_angle = math.degrees(angle2)
                    
                    if end_angle - start_angle > 180:            
                        angle = 360 - end_angle + start_angle            
                    elif end_angle - start_angle < -180:           
                        angle = 360 + end_angle - start_angle
                        
                    else:            
                        angle = end_angle - start_angle  
                    angle = round(angle, 2)
                
            else:                
                # angle = math.degrees(math.atan2(line[3] - line[1], line[2] - line[0]))
                angle = 0          
        
            # type(self.angle_entry.get())
            if angle > 0:
                input = float(self.angle_entry.get())
            else:
                input = - float(self.angle_entry.get())

            if self.index + 1 < count:
                if end_angle - start_angle > 180:
                    end_angle = 360 + start_angle - input
                elif end_angle - start_angle < -180:
                    end_angle = input + start_angle -360
                else:
                    end_angle = input + start_angle
            else:
                end_angle = input

            if self.unit == "mm":
                length = float(self.length_entry.get())
            else:
                length = float(self.length_entry.get()) * 25.4

            selected_line_angle = self.calculate_horizontal_angle(self.line[0],self.line[1],self.line[2],self.line[3])
            x1, y1, x2, y2 = self.line
            if self.index + 1 < count:            
                next_line_length = self.calculate_length(self.lines[self.index+1][0],self.lines[self.index+1][1],self.lines[self.index+1][2],self.lines[self.index+1][3])
                
                x3, y3, x4, y4 = self.lines[self.index+1]
                dx1 = length * math.cos(math.radians(selected_line_angle)) +x1 -x2
                dy1 = length * math.sin(math.radians(selected_line_angle)) +y1 -y2            
                dx2 = next_line_length * math.cos(math.radians(end_angle)) +x2 -x4
                dy2 = next_line_length * math.sin(math.radians(end_angle)) +y2 -y4
            else:
                dx1 = length * math.cos(math.radians(selected_line_angle)) +x1 -x2
                dy1 = length * math.sin(math.radians(selected_line_angle)) +y1 -y2
                dx2 = None
                dy2 = None
            # dx = length * math.cos(math.radians(end_angle))   
            # dy = length * math.sin(math.radians(end_angle))
            self.result = [dx1,dy1,dx2,dy2]
            # print(self.result)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid angle and length values.")

    def cancel(self, event=None):
        self.result = None
        self.destroy() 

    
    def calculate_horizontal_angle(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return math.degrees(math.atan2(dy, dx))
    
    def calculate_length(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx ** 2 + dy ** 2)

class OrderEditDialog(simpledialog.Dialog):
    def __init__(self, parent, array):
        self.array = array
        self.selected_index = None
        super().__init__(parent, title="Change Array Order")

    def body(self, master):
        frame = tk.Frame(master)
        frame.pack()

        self.listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT)

        for item in self.array:
            self.listbox.insert(tk.END, item)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.LEFT, padx=5)

        button_up = tk.Button(button_frame, text="Move Up", command=self.move_up)
        button_up.pack(side=tk.TOP, padx=5, pady=5)

        button_down = tk.Button(button_frame, text="Move Down", command=self.move_down)
        button_down.pack(side=tk.TOP, padx=5, pady=5)

        return self.listbox

    def buttonbox(self):
        box = tk.Frame(self)

        ok_button = tk.Button(box, text="OK", width=10, command=self.ok)
        ok_button.pack(side=tk.LEFT, padx=5, pady=10)

        cancel_button = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack(side=tk.BOTTOM, padx=5, pady=5)

    def move_up(self):
        if self.selected_index is not None and self.selected_index > 0:
            item = self.array[self.selected_index]
            self.array.pop(self.selected_index)
            self.array.insert(self.selected_index - 1, item)
            self.selected_index -= 1
            self.refresh_listbox()

    def move_down(self):
        if self.selected_index is not None and self.selected_index < len(self.array) - 1:
            item = self.array[self.selected_index]
            self.array.pop(self.selected_index)
            self.array.insert(self.selected_index + 1, item)
            self.selected_index += 1
            self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.array:
            self.listbox.insert(tk.END, item)

        if self.selected_index is not None:
            self.listbox.selection_set(self.selected_index)

    def on_select(self, event):
        selected_items = self.listbox.curselection()
        if selected_items:
            self.selected_index = selected_items[0]
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.selected_index)

    def apply(self):
        self.result = self.array

if __name__ == "__main__":
    app = DrawingApp()