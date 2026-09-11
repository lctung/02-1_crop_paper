import os
import shutil

# ===== 請確認這裡是你的裁切資料夾路徑 =====
INPUT_FOLDER = r"crop\crop_114C51512_1"
CHECK_FOLDER = r"check_crop_name\name_114C51512_1"
# ==========================================

def copy_and_rename_files():
    if not os.path.exists(INPUT_FOLDER):
        print(f"找不到原始資料夾: {INPUT_FOLDER}")
        return

    # 建立全新的資料夾，exist_ok=True 避免資料夾已存在時報錯
    os.makedirs(CHECK_FOLDER, exist_ok=True)
    
    count = 0
    for filename in os.listdir(INPUT_FOLDER):
        # 只處理 U+ 開頭的 png 檔
        if filename.startswith("U+") and filename.endswith(".png"):
            
            # 提取 U+ 後面的 4 個代碼 (相容 U+65FB_2.png 這種有重複後綴的檔案)
            hex_code = filename[2:6]
            
            try:
                chinese_char = chr(int(hex_code, 16))
                
                # 如果檔名已經有 '-'，代表已經改過，直接使用原檔名
                if "-" in filename:
                    new_filename = filename
                else:
                    # 組合新檔名
                    name_part, ext = os.path.splitext(filename)
                    new_filename = f"{name_part}-{chinese_char}{ext}"
                
                # 設定來源與目標路徑
                old_path = os.path.join(INPUT_FOLDER, filename)
                new_path = os.path.join(CHECK_FOLDER, new_filename)
                
                # 重點：使用 copy2 複製檔案，這不會動到你的原檔
                shutil.copy2(old_path, new_path)
                count += 1
                
            except Exception as e:
                print(f"無法處理 {filename}: {e}")

    print(f"複製完成！已將 {count} 個檔案加上中文字，存放到 '{CHECK_FOLDER}' 資料夾中。")

if __name__ == "__main__":
    copy_and_rename_files()