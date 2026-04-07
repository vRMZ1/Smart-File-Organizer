import os
import shutil

def start_organizing():
    # 1. طلب المسار من المستخدم
    target_folder = input(r"أدخل مسار المجلد اللي تبي تنظفه: ").strip('\"\'')
    print(f"🚀 بدأنا فحص المجلد: {target_folder}")
    
    # 2. جلب جميع الملفات في المجلد
    files = os.listdir(target_folder)
    
    for filename in files:
        # مسار الملف الحالي
        old_file_path = os.path.join(target_folder, filename)
        
        # تخطي المجلدات (عشان البرنامج ما ينقل المجلدات داخل بعضها ويحوس الدنيا)
        if os.path.isdir(old_file_path):
            continue
            
        # 3. فصل الاسم عن الصيغة
        name, extension = os.path.splitext(filename)
        
        # 4. إذا الملف له صيغة (عشان نتجاهل الملفات اللي بدون صيغ)
        if extension:
            # نمسح النقطة من الصيغة ونحول الحروف لكبيرة (مثال: .pdf تصير PDF)
            folder_name = extension.replace(".", "").upper()
            
            # مسار المجلد الجديد
            new_folder_path = os.path.join(target_folder, folder_name)
            
            # 5. نصنع المجلد إذا مو موجود
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                
            # مسار الملف بعد النقل
            new_file_path = os.path.join(new_folder_path, filename)
            
            # 6. النقل الفعلي
            shutil.move(old_file_path, new_file_path)
            print(f"✅ تم نقل: {filename} -> إلى مجلد {folder_name}")
            
    print("🎉 انتهت عملية الترتيب بنجاح! كل صيغة صار لها مجلدها المستقل.")


if __name__ == "__main__":
    start_organizing()