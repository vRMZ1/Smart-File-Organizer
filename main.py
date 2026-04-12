import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox

# إعدادات المظهر الأساسية
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- إعدادات النافذة ---
        self.title("vRMZ Smart Organizer - PRO")
        self.geometry("700x600")
        self.resizable(True, True) # تفعيل تكبير وتصغير الشاشة

        # جعل العناصر تتوسط الشاشة عند التكبير
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- الحاوية الرئيسية (Main Frame) لتعطي شكل الخلفية الفخمة ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color=("#E0E0E0", "#1A1A1A"))
        self.main_frame.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- شعار vRMZ ---
        self.logo_label = ctk.CTkLabel(self.main_frame, text="App", 
                                      font=("Arial Black", 50, "bold"), 
                                      text_color="#2E7D32")
        self.logo_label.pack(pady=(40, 10))

        self.sub_title = ctk.CTkLabel(self.main_frame, text="ULTIMATE FILE ORGANIZER", 
                                     font=("Helvetica", 18, "bold"), 
                                     text_color="gray")
        self.sub_title.pack(pady=(0, 30))

        # --- قسم اختيار المجلد ---
        self.select_button = ctk.CTkButton(self.main_frame, text="📂 BROWSE FOLDER", 
                                          command=self.select_folder,
                                          width=300, height=60,
                                          font=("Helvetica", 16, "bold"),
                                          corner_radius=10)
        self.select_button.pack(pady=20)

        self.path_label = ctk.CTkLabel(self.main_frame, text="No directory selected yet", 
                                      font=("Helvetica", 14), 
                                      text_color="gray")
        self.path_label.pack(pady=10)

        # --- شريط التحميل ---
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=500, height=15)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=40)

        # --- زر التنفيذ ---
        self.organize_button = ctk.CTkButton(self.main_frame, text="🚀 START ORGANIZING", 
                                            command=self.start_process,
                                            state="disabled",
                                            width=300, height=60,
                                            font=("Helvetica", 18, "bold"),
                                            fg_color="gray")
        self.organize_button.pack(pady=20)

        # --- زر تغيير الخلفية (الثيم) ---
        self.theme_switch = ctk.CTkSwitch(self.main_frame, text="Light / Dark Mode", 
                                         command=self.change_theme,
                                         font=("Helvetica", 12))
        self.theme_switch.pack(side="bottom", pady=20)

        self.current_path = ""

    def change_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_path = folder
            self.path_label.configure(text=f"Target: {folder}", text_color="#4CAF50")
            self.organize_button.configure(state="normal", fg_color="#2E7D32")

    def start_process(self):
        files = [f for f in os.listdir(self.current_path) if os.path.isfile(os.path.join(self.current_path, f))]
        total = len(files)
        
        if total == 0:
            messagebox.showwarning("Empty", "Selected folder has no files!")
            return

        for i, filename in enumerate(files):
            # تحريك شريط التحميل
            self.progress_bar.set((i + 1) / total)
            self.update_idletasks()

            old_path = os.path.join(self.current_path, filename)
            ext = os.path.splitext(filename)[1].replace(".", "").upper()
            
            if ext:
                new_dir = os.path.join(self.current_path, ext)
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)
                shutil.move(old_path, os.path.join(new_dir, filename))

        messagebox.showinfo("Done", "Your files are now perfectly organized!")
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()