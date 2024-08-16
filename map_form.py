import os
import tkinter as tk
import pymupdf as pmu
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import json
import scan


# TODO: add a listing of the rectangles on the side of the canvas just names, when clicked on the name it will
#  highlight the rectangle and you can edit the name or delete the rectangle
# TODO: click inside a rectangle to edit the name
# TODO: make rectangles resizable
# TODO: make rectangles draggable
# TODO: make rectangles persistent on the page
# TODO: make the field list populate with the text from the fields on the page as they are created
class PDFViewer1(tk.Toplevel):

    def __init__(self, on_close_callback):
        super().__init__()
        self.title("PDF Viewer")
        self.geometry("800x600")

        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.grid(row=0, column=0, sticky='nsew')

        # Scrollbars
        self.v_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.canvas.config(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Configure layout to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Set up zoom
        self.zoom_level = 1.0
        self.min_zoom_level = 1.0

        # Initialize variables for storing rectangles, photo image, PDF document, and current page
        self.rectangles = {}
        self.photo_img = None
        self.pdf_document = None
        self.current_page = 0

        # Bind mouse wheel event for zooming
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)  # For Windows and macOS

        # Set the close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.on_close_callback = on_close_callback

        # Initialize variables for creating text boxes: current page number, dictionary to store rectangles,
        # current text field being drawn and its starting coordinates
        self.current_page_number = 0
        self.text_field = {}
        self.current_rect = None
        self.start_x = self.start_y = 0

        # Bind events for drawing text boxes
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Create navigation buttons
        self.create_navigation_buttons()
        # Load a PDF file
        self.load_pdf()

    def load_pdf(self):
        pdf_file = None
        try:
            # # Loop till a valid PDF file is selected or user cancels the dialog
            # while not pdf_file:
            pdf_file = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF files", "*.pdf")])
            if pdf_file:
                self.pdf_document = pmu.open(pdf_file)
                self.show_page(self.current_page)  # Start with the first page
            else:
                messagebox.showinfo("Info", "No PDF file selected.")
                self.on_close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")

    def on_close(self):
        # Cleanup and call the provided callback function
        self.destroy()
        if self.on_close_callback:
            self.on_close_callback()
        self.quit()

    def show_page(self, page_number):
        if self.pdf_document:
            self.current_page = self.pdf_document.load_page(page_number)
            self.render_page()

    def render_page(self):
        zoom_matrix = pmu.Matrix(self.zoom_level, self.zoom_level)
        pix = self.current_page.get_pixmap(matrix=zoom_matrix)
        dimensions = tuple((pix.width, pix.height))
        img = Image.frombytes("RGB", dimensions, pix.samples)
        self.photo_img = ImageTk.PhotoImage(image=img)

        self.canvas.create_image(0, 0, anchor='nw', image=self.photo_img)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_in(self):
        self.zoom_level *= 1.1
        self.render_page()

    def zoom_out(self):
        if self.zoom_level > self.min_zoom_level:  # Only zoom out if above the minimum zoom level
            self.zoom_level /= 1.1
            self.render_page()

    def mouse_wheel(self, event):
        if event.delta > 0:  # Scroll up
            self.zoom_in()
        else:  # Scroll down
            self.zoom_out()

    def create_navigation_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')

        prev_button = tk.Button(button_frame, text="Previous Page", command=self.prev_page)
        prev_button.grid(row=0, column=0, sticky='nsew')

        next_button = tk.Button(button_frame, text="Next Page", command=self.next_page)
        next_button.grid(row=0, column=1, sticky='nsew')

        zoom_in_button = tk.Button(button_frame, text="Zoom In", command=self.zoom_in)
        zoom_in_button.grid(row=0, column=2, sticky='nsew')

        zoom_out_button = tk.Button(button_frame, text="Zoom Out", command=self.zoom_out)
        zoom_out_button.grid(row=0, column=3, sticky='nsew')

        extract_button = tk.Button(button_frame, text="Extract Text", command=self.extract_text_from_boxes)
        extract_button.grid(row=0, column=4, sticky='nsew')

        save_button = tk.Button(button_frame, text="Save Boxes", command=self.save_boxes)
        save_button.grid(row=0, column=5, sticky='nsew')

        delete_top_button = tk.Button(button_frame, text="Delete Top Box", command=self.delete_top_rectangle)
        delete_top_button.grid(row=0, column=6, sticky='nsew')

        clear_button = tk.Button(button_frame, text="Clear Boxes", command=self.clear_boxes)
        clear_button.grid(row=0, column=7, sticky='nsew')

        exit_button = tk.Button(button_frame, text="Exit", background="red", foreground="white",
                                font=('Helvetica', 12, 'bold'), width=20, command=self.on_close)
        exit_button.grid(row=0, column=8, sticky='nsew')

    def on_click(self, event):
        self.start_x = self.canvas.canvasx(event.x) / self.zoom_level
        self.start_y = self.canvas.canvasy(event.y) / self.zoom_level

        if self.current_rect:
            self.canvas.delete(self.current_rect)

        self.current_rect = self.canvas.create_rectangle(
            self.start_x * self.zoom_level, self.start_y * self.zoom_level,
            self.start_x * self.zoom_level, self.start_y * self.zoom_level,
            outline="red", width=2
        )

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x) / self.zoom_level
        cur_y = self.canvas.canvasy(event.y) / self.zoom_level
        self.canvas.coords(
            self.current_rect,
            self.start_x * self.zoom_level, self.start_y * self.zoom_level,
            cur_x * self.zoom_level, cur_y * self.zoom_level
        )

    def on_release(self, event):
        if self.current_rect:
            x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
            x1 /= self.zoom_level
            y1 /= self.zoom_level
            x2 /= self.zoom_level
            y2 /= self.zoom_level
            if x1 != x2 and y1 != y2:  # Ensure the rectangle is not degenerate
                # Get the name for the box from the user, center the window on the canvas
                box_name = simpledialog.askstring("Box Name", "Enter a name for the data in the box:")
                if box_name:
                    page_key = f"page number: {self.current_page_number + 1}"
                    self.rectangles.setdefault(page_key, []).append({
                        'name': box_name,
                        'coords': (x1, y1, x2, y2)
                    })
            self.current_rect = None
            self.pdf_document.load_page(self.current_page_number)

    def prev_page(self):
        if self.current_page_number > 0:
            self.current_page_number -= 1
            # self.pdf_document.load_page(page_number=self.current_page_number)
            self.show_page(self.current_page_number)
        else:
            messagebox.showinfo("Info", "No more pages to go back.")

    def next_page(self):
        if self.current_page_number < len(self.pdf_document) - 1:
            self.current_page_number += 1
            # self.pdf_document.load_page(self.current_page_number)
            self.show_page(self.current_page_number)
        else:
            messagebox.showinfo("Info", "No more pages to go forward.")

    def draw_rectangles(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles:
            for box in self.rectangles[page_key]:
                x1, y1, x2, y2 = box['coords']
                x1 *= self.zoom_level
                y1 *= self.zoom_level
                x2 *= self.zoom_level
                y2 *= self.zoom_level
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2, tags=box['name'])

    def save_current_page_boxes(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles:
            updated_boxes = []
            for box in self.rectangles[page_key]:
                tag = box['name']
                item_ids = self.canvas.find_withtag(tag)
                if item_ids:  # Check if the item exists
                    coords = self.canvas.coords(item_ids[0])
                    if len(coords) == 4:  # Ensure the coords tuple has 4 elements
                        updated_boxes.append({
                            'name': tag,
                            'coords': (coords[0], coords[1], coords[2], coords[3])
                        })
                else:
                    print(f"Warning: Rectangle '{tag}' not found on canvas.")

            if updated_boxes:  # Only update if there are valid boxes
                self.rectangles[page_key] = updated_boxes
            else:
                del self.rectangles[page_key]  # Remove page entry if no valid rectangles

    # TODO: this only extracts text from the current page, need to extract text from all pages?
    def extract_text_from_boxes(self):
        # pull the current page from the pdf document
        page = self.pdf_document.load_page(self.current_page_number)
        # create a temp JSON file to store the rectangles
        with open('temp.json', 'w') as file:
            json.dump(self.rectangles, file, indent=4)
        # extract the text from the page using the existing rectangles
        extracted_text = scan.extract_text_from_page(page, 'temp.json')
        self.display_extracted_text(extracted_text)
        # Remove the temp JSON file
        os.remove('temp.json')

    # TODO: make text window scrollable
    def display_extracted_text(self, text):
        text_window = tk.Toplevel()
        text_window.title("Extracted Text")
        text_window.geometry("500x500")

        holder = "field name: field value\n"

        # Format the extracted text for display show each field name and value on a new line with a colon
        for i in range(0, len(text)):
            holder += text[i]['name'] + ": " + text[i]['text'] + "\n"

        text = f'Extracted Text:\n\n{holder}'

        # Create a text area to display the extracted text
        text_area = tk.Text(text_window, wrap=tk.WORD)
        text_area.insert(tk.END, text)
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.config(state=tk.DISABLED)

    def save_boxes(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if save_path:
            # Remove empty page entries before saving
            self.rectangles = {k: v for k, v in self.rectangles.items() if v}
            with open(save_path, 'w') as file:
                json.dump(self.rectangles, file, indent=4)
            messagebox.showinfo("Info", "Boxes saved successfully!")

    # TODO: make this delete the selected rectangle
    # TODO: DOESN'T WORK YET*******************************************************************************************
    def delete_top_rectangle(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles and self.rectangles[page_key]:
            self.rectangles[page_key].pop()
        self.pdf_document.load_page()

    # TODO: DOESN'T WORK YET*******************************************************************************************
    def clear_boxes(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles:
            self.rectangles[page_key] = []
        self.canvas.delete("all")
        self.pdf_document.load_page()
