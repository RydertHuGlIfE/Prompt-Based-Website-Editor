# Prompt-Based-Website-Editor

# 🖥️ AI-Powered Code Editor & Reviewer  

This project is a **Tkinter-based desktop application** that integrates with **Google Gemini API** to help developers:  

- 📝 **Modify HTML/CSS/JS files** with natural language instructions  
- ✅ **Review code quality** instantly  
- 🔄 **Undo unwanted changes** with backups  

It’s like having your **personal AI coding assistant** directly inside a simple desktop app.  

---

## 🚀 Features  

- **AI Editing**:  
  Enter natural language prompts (e.g., *"Add a red button at the top-right corner"*), and Gemini will automatically update your `index.html`.  

- **Code Review**:  
  Quickly check code quality with short AI-generated reviews (4–10 words).  

- **Undo/Reset**:  
  Every time you edit, a `backup.bak` file is created so you can revert with one click.  

- **Clean UI**:  
  Tkinter-powered modern layout with styled buttons.  

---

## 🛠️ Tech Stack  

- **Frontend (UI):** Tkinter (Python)  
- **AI Engine:** Google Gemini 2.5 Flash (`google.generativeai`)  
- **Language Support:** HTML, CSS, JavaScript  

---

## 📂 Project Structure  

├── index.html # Main editable HTML file
├── backup.bak # Backup file (auto-generated before edits)
├── main.py # Tkinter GUI + Gemini integration
└── README.md # Project documentation


🎮 Usage

Type request → Enter your instruction in the input box

Submit → Click ✅ Submit to apply changes

Undo → Click 🔄 Undo to restore backup

Check Code → Click 🔍 Check Code for quick review


User Interface: 
<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/5d6b13c7-b5e2-436c-88a5-e9380c0baca2" />
