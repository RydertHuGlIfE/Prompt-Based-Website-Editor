import threading
import re
import os
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk
import google.generativeai as genai

API_KEY = os.getenv("ENTER API KEY HERE")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    "models/gemini-2.5-flash",
    generation_config={
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 50000,
    },
)

# --- system prompt used when editing HTML ---
SYSTEM_PROMPT = '''You are an AI Code Assistant. Your job is to generate and edit HTML, CSS, and JS code for a website according to the user's instructions.

IMPORTANT: Each request is INDEPENDENT. Generate complete, self-contained code for the current request only. Do not assume previous requests or try to build upon them.

Follow these rules strictly:
You will be provided a full html file as context below which will include all 3 ie HTML CSS and JS. You will also be provided a user request below modify the code accordingly and give the full code output
dont make it unnecessarily complex. Keep it simple and functional. and anything previously there should not be removed unless specifically asked so....

5. Code constraints:
   - Return exactly what is needed, nothing extra.
   - Ensure the dynamic JS runs correctly for requested interactions (like “fall everything down” or “rotate box”).
   - Single well-formed tags only. No duplicates or partial tags.

End of instructions.'''

REVIEW_PROMPT = '''You are an expert code reviewer. Your job is to review HTML, CSS, and JS code for a website and responde accordingly in 4-10 words..'''

# --- UI setup ---
# Revert to default/light appearance mode
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("DevAlchemy — AI HTML Editor")
app.geometry("1000x640")
app.minsize(900, 560)

# Keep apply_theme_styles as a no-op so CTk default styling is used
def apply_theme_styles():
    pass

# Sidebar
sidebar = ctk.CTkFrame(app, width=220, corner_radius=8)
sidebar.pack(side="left", fill="y", padx=12, pady=12)

logo = ctk.CTkLabel(sidebar, text="DevAlchemy", font=ctk.CTkFont(size=20, weight="bold"))
logo.pack(pady=(8, 18))

btn_open = ctk.CTkButton(sidebar, text="Open index.html", width=180)
btn_open.pack(pady=(6, 6))

btn_backup = ctk.CTkButton(sidebar, text="Create Backup", width=180)
btn_backup.pack(pady=(6, 6))

btn_submit = ctk.CTkButton(sidebar, text="Submit (AI Edit)", fg_color="#1e810a", width=180)
btn_submit.pack(pady=(6, 6))

btn_undo = ctk.CTkButton(sidebar, text="Undo (Restore)", fg_color="#e74c3c", width=180)
btn_undo.pack(pady=(6, 6))

btn_check = ctk.CTkButton(sidebar, text="Quick Code Review", width=180)
btn_check.pack(pady=(6, 6))

theme_toggle = ctk.CTkSwitch(sidebar, text="Light Mode")
theme_toggle.pack(pady=(18, 6))

# Main area
main = ctk.CTkFrame(app, corner_radius=8)
main.pack(side="right", expand=True, fill="both", padx=12, pady=12)

# Instruction entry (what user wants the AI to do)
instr_label = ctk.CTkLabel(main, text="Instruction (what should the AI do?)", anchor="w")
instr_label.pack(fill="x", padx=12, pady=(8, 2))

instr_entry = ctk.CTkEntry(main, placeholder_text="e.g. Add a sticky navbar and a dark theme toggle.", height=36)
instr_entry.pack(fill="x", padx=12, pady=(0, 12))

# Split view: left = file preview, right = AI output
split_frame = ctk.CTkFrame(main)
split_frame.pack(expand=True, fill="both", padx=12, pady=(0, 12))

left_frame = ctk.CTkFrame(split_frame, corner_radius=6)
left_frame.pack(side="left", expand=True, fill="both", padx=(0, 6), pady=6)

right_frame = ctk.CTkFrame(split_frame, corner_radius=6)
right_frame.pack(side="right", expand=True, fill="both", padx=(6, 0), pady=6)

lbl_preview = ctk.CTkLabel(left_frame, text="index.html Preview", anchor="w")
lbl_preview.pack(fill="x", padx=8, pady=(6, 2))
preview_text = scrolledtext.ScrolledText(left_frame, wrap="none", font=("Consolas", 11))
preview_text.pack(expand=True, fill="both", padx=8, pady=(0, 8))

lbl_output = ctk.CTkLabel(right_frame, text="AI Output / Result", anchor="w")
lbl_output.pack(fill="x", padx=8, pady=(6, 2))
output_text = scrolledtext.ScrolledText(right_frame, wrap="none", font=("Consolas", 11))
output_text.pack(expand=True, fill="both", padx=8, pady=(0, 8))

# Status bar
status_frame = ctk.CTkFrame(main, height=36, corner_radius=6)
status_frame.pack(fill="x", padx=12, pady=(0, 6))
status_label = ctk.CTkLabel(status_frame, text="Ready", anchor="w")
status_label.pack(side="left", padx=12)
progress = ctk.CTkProgressBar(status_frame)
progress.set(0)
progress.pack(side="right", padx=12, pady=6, fill="x", expand=True)

# Helper functions
current_file_path = "index.html"
backup_path = "backup.bak"

# Processing animation state
processing_active = False
spinner_index = 0
processing_base_text = "Processing..."
spinner_chars = ["◐", "◓", "◑", "◒"]


def start_processing():
    global processing_active, spinner_index, processing_base_text
    processing_active = True
    spinner_index = 0
    # ensure base text shows immediately
    processing_base_text = "Processing..."
    app.after(120, update_processing)
    # disable submit to prevent double submits
    btn_submit.configure(state="disabled")


def stop_processing():
    global processing_active
    processing_active = False
    # reset progress bar and enable button
    progress.set(0.0)
    btn_submit.configure(state="normal")


def update_processing():
    global spinner_index
    if not processing_active:
        return
    spinner = spinner_chars[spinner_index % len(spinner_chars)]
    spinner_index += 1
    # show rotating spinner appended to base text
    status_label.configure(text=f"{processing_base_text} {spinner}")
    # simple cyclic progress animation
    progress.set((spinner_index % 20) / 20.0)
    app.after(120, update_processing)


def set_status(text, value=0.0):
    global processing_base_text
    # If processing animation is active, update the base text so the spinner appends to it
    if processing_active:
        processing_base_text = text
    else:
        status_label.configure(text=text)
        progress.set(value)


def load_file(path=None):
    global current_file_path
    if path is None:
        path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html"), ("All files", "*.*")]) or current_file_path
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", content)
        current_file_path = path
        set_status(f"Loaded: {os.path.basename(path)}", 0.0)
    except Exception as e:
        messagebox.showerror("Open Error", str(e))


def create_backup():
    try:
        with open(current_file_path, "r", encoding="utf-8") as f:
            data = f.read()
        with open(backup_path, "w", encoding="utf-8") as b:
            b.write(data)
        set_status("Backup created", 0.0)
    except Exception as e:
        messagebox.showerror("Backup Error", str(e))


def restore_backup():
    try:
        with open(backup_path, "r", encoding="utf-8") as b:
            data = b.read()
        with open(current_file_path, "w", encoding="utf-8") as w:
            w.write(data)
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", data)
        set_status("Restored from backup", 0.0)
        messagebox.showinfo("Restore", "File restored from backup.")
    except Exception as e:
        messagebox.showerror("Restore Error", str(e))


def quick_code_review():
    try:
        content = preview_text.get("1.0", "end")
        set_status("Reviewing...", 0.2)
        result = model.generate_content(REVIEW_PROMPT + "\n\n" + content)
        ai_response = "".join([p.text for p in result.candidates[0].content.parts])
        output_text.delete("1.0", "end")
        output_text.insert("1.0", ai_response.strip())
        set_status("Review complete", 0.0)
    except Exception as e:
        messagebox.showerror("Review Error", str(e))


def clean_response(text):
    # strip wrapping ``` fences that Gemini sometimes returns
    t = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    t = re.sub(r"\n?```$", "", t)
    return t.strip()


def ai_edit_task(user_instruction):
    try:
        # start GUI-side processing indicator
        app.after(0, start_processing)

        set_status("Creating backup...", 0.05)
        create_backup()

        set_status("Sending request to AI...", 0.25)
        content = preview_text.get("1.0", "end")
        result = model.generate_content(user_instruction + "\n\n" + SYSTEM_PROMPT + "\n\n" + content)
        set_status("Receiving response...", 0.7)
        ai_response = "".join([p.text for p in result.candidates[0].content.parts])
        ai_response = clean_response(ai_response)

        # write result back to file and update preview
        with open(current_file_path, "w", encoding="utf-8") as w:
            w.write(ai_response)

        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", ai_response)
        output_text.delete("1.0", "end")
        output_text.insert("1.0", ai_response)
        set_status("Done — file updated", 1.0)
        messagebox.showinfo("Success", "Modifications completed successfully!")
    except Exception as e:
        set_status("Error", 0.0)
        messagebox.showerror("AI Edit Error", str(e))
    finally:
        # stop processing animation on the GUI thread
        app.after(0, stop_processing)


def threaded_task(func, *args):
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()


# Wire buttons
btn_open.configure(command=lambda: threaded_task(load_file))
btn_backup.configure(command=lambda: threaded_task(create_backup))
btn_submit.configure(command=lambda: threaded_task(ai_edit_task, instr_entry.get().strip() or "Improve structure and styling."))
btn_undo.configure(command=lambda: threaded_task(restore_backup))
btn_check.configure(command=lambda: threaded_task(quick_code_review))

# Theme toggle
def toggle_theme():
    mode = "light" if theme_toggle.get() else "dark"
    ctk.set_appearance_mode(mode)
    apply_theme_styles()


theme_toggle.configure(command=toggle_theme)
# make the switch reflect the current (light) mode
try:
    theme_toggle.select()
except Exception:
    pass

# Apply initial theme styles (no-op uses CTk defaults)
apply_theme_styles()

# Load default file if exists
if os.path.exists(current_file_path):
    load_file(current_file_path)
else:
    preview_text.insert("1.0", "<!-- index.html not found. Use 'Open index.html' -->")
    set_status("Ready (no file loaded)", 0.0)

app.mainloop()
