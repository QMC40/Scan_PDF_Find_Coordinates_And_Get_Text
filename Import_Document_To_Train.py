import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import json
import matplotlib.pyplot as plt

class PDFViewer(tk.Toplevel):  # Use Toplevel instead of Tk
    def __init__(self, pdf_path, on_close_callback):
        super().__init__()
        self.title("PDF Viewer")
        self.geometry("800x600")

        self.pdf_path = pdf_path
        self.current_page_number = 0
        self.rectangles = {}  # Dictionary to store rectangles with page numbers
        self.current_rect = None
        self.start_x = self.start_y = 0
        self.zoom_scale = 1.0  # Initial zoom scale

        self.doc = fitz.open(pdf_path)
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.create_navigation_buttons()
        self.load_page()

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Set the close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.on_close_callback = on_close_callback

    def on_close(self):
        # Cleanup and call the provided callback function
        self.destroy()
        if self.on_close_callback:
            self.on_close_callback()

    def create_navigation_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        prev_button = tk.Button(button_frame, text="Previous Page", command=self.prev_page)
        prev_button.pack(side=tk.LEFT)

        next_button = tk.Button(button_frame, text="Next Page", command=self.next_page)
        next_button.pack(side=tk.LEFT)

        zoom_in_button = tk.Button(button_frame, text="Zoom In", command=self.zoom_in)
        zoom_in_button.pack(side=tk.LEFT)

        zoom_out_button = tk.Button(button_frame, text="Zoom Out", command=self.zoom_out)
        zoom_out_button.pack(side=tk.LEFT)

        extract_button = tk.Button(button_frame, text="Extract Text", command=self.extract_text_from_boxes)
        extract_button.pack(side=tk.LEFT)

        save_button = tk.Button(button_frame, text="Save Boxes", command=self.save_boxes)
        save_button.pack(side=tk.LEFT)

        delete_top_button = tk.Button(button_frame, text="Delete Top Box", command=self.delete_top_rectangle)
        delete_top_button.pack(side=tk.LEFT)

        clear_button = tk.Button(button_frame, text="Clear Boxes", command=self.clear_boxes)
        clear_button.pack(side=tk.LEFT)

    def on_click(self, event):
        self.start_x = self.canvas.canvasx(event.x) / self.zoom_scale
        self.start_y = self.canvas.canvasy(event.y) / self.zoom_scale

        if self.current_rect:
            self.canvas.delete(self.current_rect)

        self.current_rect = self.canvas.create_rectangle(
            self.start_x * self.zoom_scale, self.start_y * self.zoom_scale, 
            self.start_x * self.zoom_scale, self.start_y * self.zoom_scale, 
            outline="red", width=2
        )

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x) / self.zoom_scale
        cur_y = self.canvas.canvasy(event.y) / self.zoom_scale
        self.canvas.coords(
            self.current_rect,
            self.start_x * self.zoom_scale, self.start_y * self.zoom_scale,
            cur_x * self.zoom_scale, cur_y * self.zoom_scale
        )

    def on_release(self, event):
        if self.current_rect:
            x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
            x1 /= self.zoom_scale
            y1 /= self.zoom_scale
            x2 /= self.zoom_scale
            y2 /= self.zoom_scale
            if x1 != x2 and y1 != y2:  # Ensure the rectangle is not degenerate
                box_name = simpledialog.askstring("Box Name", "Enter a name for the data in the box:")
                if box_name:
                    page_key = f"page number: {self.current_page_number + 1}"
                    self.rectangles.setdefault(page_key, []).append({
                        'name': box_name,
                        'coords': (x1, y1, x2, y2)
                    })
            self.current_rect = None
            self.load_page()

    def prev_page(self):
        if self.current_page_number > 0:
            self.current_page_number -= 1
            self.load_page()

    def next_page(self):
        if self.current_page_number < len(self.doc) - 1:
            self.current_page_number += 1
            self.load_page()
        else:
            messagebox.showinfo("Info", "No more pages to go forward.")

    def load_page(self):
        try:
            self.page = self.doc.load_page(self.current_page_number)
            self.pagemap = self.page.get_pixmap(matrix=fitz.Matrix(self.zoom_scale, self.zoom_scale))
            self.image = Image.frombytes("RGB", [self.pagemap.width, self.pagemap.height], self.pagemap.samples)
            self.img_tk = ImageTk.PhotoImage(image=self.image)

            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

            self.draw_rectangles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load page: {e}")

    def draw_rectangles(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles:
            for box in self.rectangles[page_key]:
                x1, y1, x2, y2 = box['coords']
                x1 *= self.zoom_scale
                y1 *= self.zoom_scale
                x2 *= self.zoom_scale
                y2 *= self.zoom_scale
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

    def extract_text_from_boxes(self):
        extracted_text = []
        page_key = f"page number: {self.current_page_number + 1}"
        for box in self.rectangles.get(page_key, []):
            x1, y1, x2, y2 = box['coords']
            # Convert canvas coordinates to PDF coordinates
            page_width, page_height = self.page.rect.width, self.page.rect.height
            img_width, img_height = self.img_tk.width(), self.img_tk.height()
            scale_x, scale_y = page_width / img_width, page_height / img_height
            pdf_rect = fitz.Rect(x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)
            text = self.page.get_text("text", clip=pdf_rect)
            extracted_text.append(f"{box['name']}: {text}")

    def display_extracted_text(self, text):
        plt.figure(figsize=(10, 7))
        plt.text(0.5, 0.5, text, fontsize=12, ha='center', wrap=True)
        plt.axis('off')
        plt.show()

    def save_boxes(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if save_path:
            # Remove empty page entries before saving
            self.rectangles = {k: v for k, v in self.rectangles.items() if v}
            with open(save_path, 'w') as file:
                json.dump(self.rectangles, file, indent=4)
            messagebox.showinfo("Info", "Boxes saved successfully!")

    def delete_top_rectangle(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles and self.rectangles[page_key]:
            self.rectangles[page_key].pop()
        self.load_page()

    def clear_boxes(self):
        page_key = f"page number: {self.current_page_number + 1}"
        if page_key in self.rectangles:
            self.rectangles[page_key] = []
        self.canvas.delete("all")
        self.load_page()

    def zoom_in(self):
        self.zoom_scale *= 1.2
        self.load_page()

    def zoom_out(self):
        self.zoom_scale /= 1.2
        self.load_page()
