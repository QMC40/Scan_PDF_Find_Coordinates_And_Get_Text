# Really Great PDF Data Extractor  v0.01
#
# By: https://github.com/PCarroll9500
#
# Purpose: To create a user-friendly way to mass extract data from PDF files into Excel.

import os
import tkinter as tk

import scan
import map_form

# Create the folders if they don't exist
os.makedirs("To Scan", exist_ok=True)
os.makedirs("Scanned", exist_ok=True)
os.makedirs("Form Templates", exist_ok=True)

print(f"Folders set up: 'To Scan', 'Scanned', 'Form Templates'")


# Call to the function to scan the folder and extract data
def scan_folder_extract_data() -> None:
    """
    Function to call the scanning and data extraction function from scan.py

        Args:
            N/A

        Returns:
            None

        Raises:
            None
    """
    scan.main()


class MainWindow(tk.Tk):
    """
    Class to create the main window for the application.

        Args:
            tk.Tk: The tkinter window class

        Returns:
            None

        Raises:
            None
    """

    def __init__(self):
        """
        Function to initialize the main window for the application as a tkinter window.
        """
        super().__init__()
        # Set the window title, size, background color, and make it non-resizable
        self.title("PDF Data Extractor")
        self.geometry("500x200")
        self.configure(bg="#333333")
        self.resizable(False, False)

        # Create buttons with a light background for contrast
        btn_style = {
            'width': 40,
            'height': 2,
            'bg': '#f0f0f0',
            'fg': 'black',
            'activebackground': '#d3d3d3',
            'font': ('Helvetica', 12, 'bold'),
            'relief': 'flat',
            'bd': 0,
        }

        # Create buttons
        btn_map_form = tk.Button(self, text="Map a new form for scanning", **btn_style,
                                 command=self.map_form)
        btn_map_form.pack(pady=10)

        btn_scan_folder = tk.Button(self, text="Scan Folder and Extract Data", **btn_style,
                                    command=scan.main)
        btn_scan_folder.pack(pady=10)

        btn_import_exit = tk.Button(self, text="Exit", **btn_style, background="red", foreground="white",
                                    command=self.exit_app)
        btn_import_exit.pack(pady=10)

    # Function to import a document
    def map_form(self):
        # Hide the main window
        self.withdraw()

        # Open the PDFViewer window
        viewer = map_form.PDFViewer1(self.deiconify)
        viewer.mainloop()

    def exit_app(self):
        self.quit()


if __name__ == "__main__":
    main_window = MainWindow()
    main_window.mainloop()
