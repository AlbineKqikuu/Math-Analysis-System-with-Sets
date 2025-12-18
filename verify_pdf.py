
import sys
import os

# Mock layout classes to verify logic flow without needing a full GUI/PDF build if libs missing
# But here we want to verify the actual script runs.
# We will import the function from main3 (if possible) or just simulate the calls?
# Since main3.py has a class SetApp, it's hard to unit test without GUI.
# However, we can trust the previous verify_venn.py ran main3 imports.

# Let's create a script that just tries to run the PDF generation part 
# by subclassing or mocking.

import tkinter as tk
from main3 import SetApp

def mock_asksaveasfilename(**kwargs):
    return "test_output.pdf"

def main_verify():
    # Verify logic
    print("Starting verification with dynamic metrics...")
    
    # We will try to instantiate the app and call export_pdf manually with a mock path
    root = tk.Tk()
    app = SetApp(root)
    
    # Populate some dummy data
    app.output.insert("1.0", "TEST RESULT SETS\nA={1,2}\nB={2,3}\n")
    
    # Mock filedialog
    tk.filedialog.asksaveasfilename = mock_asksaveasfilename
    # Mock messagebox
    tk.messagebox.showinfo = lambda title, msg: print(f"MOCK INFO: {title} - {msg}")
    tk.messagebox.showerror = lambda title, msg: print(f"MOCK ERROR: {title} - {msg}")
    
    # Run export
    print("Attempting export_pdf...")
    try:
        app.export_pdf()
        print("export_pdf executed successfully (check for test_output.pdf)")
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)
    
    if os.path.exists("test_output.pdf"):
        print("PDF file created.")
    else:
        print("PDF file NOT created.")

    root.destroy()

if __name__ == "__main__":
    main_verify()
