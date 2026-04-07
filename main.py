import os
import shutil

def start_organizing():
    # 1. المسار المستهدف للترتيب
    target_folder = input(r"أدخل المسار المجلد اللي تبي تنظفه:").strip('\"\'')
    
    # 2. خريطة الترتيب (القواعد)
    extensions_map = {
        ".pdf": "Documents",
        ".docx": "Documents",
        ".png": "Images",
        ".jpg": "Images",
        ".exe": "Programs"
    }
    
    print(f"🚀 بدأنا فحص المجلد: {target_folder}")
    
    # 3. جلب وقراءة جميع الملفات
    files = os.listdir(target_folder)
    
    # 4. لفة على كل ملف
    for filename in files:
        name, extension = os.path.splitext(filename)
        
        # 5. إذا الصيغة موجودة في القاموس
        if extension in extensions_map:
            folder_name = extensions_map[extension]
            new_folder_path = os.path.join(target_folder, folder_name)
            
            # نصنع المجلد إذا مو موجود
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            
            # مسار الملف القديم والجديد
            old_file_path = os.path.join(target_folder, filename)
            new_file_path = os.path.join(new_folder_path, filename)
            
            # أمر النقل الفعلي
            shutil.move(old_file_path, new_file_path)
            print(f"✅ تم نقل: {filename} -> إلى مجلد {folder_name}")
            
    print("🎉 انتهت عملية الترتيب بنجاح!")


# (Main Entry Point) نقطة الانطلاق
if __name__ == "__main__":
    start_organizing()