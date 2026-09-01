from PIL import Image, ImageDraw
import cv2
import numpy as np
import os
import json
import shutil

# ====== 自行設定變數 ======
INPUT_FOLDER = r".\rotated_115598014_2"
OUTPUT_FOLDER = r"crop\crop_2"
JSON_PATH = r".\CP950\CP950-其他.json"
UNICODE_NUM = 605
CROP_LENGTH = 200
MIN_BOX_SIZE = 180
MIN_AREA_THRESHOLD = 10
PADDING = 20
PER_PAGE = 100
# ============================

def read_json(file, unicode_num):
    with open(file, encoding="utf-8") as f:
        p = json.load(f)
        unicode_list = [''] * unicode_num
        for i in range(unicode_num):
            unicode_list[i] = 'U+' + p['CP950'][i]['UNICODE'][2:6]  # ex: 0x1234 --> U+1234
        return unicode_list

def scale_adjustment(word_img, img_name):
    """調整文字大小、重心
    
    Keyword arguments:
        word_img -- 文字圖片
    """
    word_img = np.array(word_img)
    word_img_copy = cv2.copyMakeBorder(word_img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    # 二值化處理
    binary_word_img = cv2.cvtColor(word_img_copy, cv2.COLOR_BGR2GRAY) if len(word_img_copy.shape) == 3 else word_img_copy
    binary_word_img = cv2.threshold(binary_word_img, 127, 255, cv2.THRESH_BINARY_INV)[1]

    # 取得文字 Bounding Box
    topLeftX, topLeftY, word_w, word_h = cv2.boundingRect(binary_word_img)
    
    # 計算質心
    cX, cY = topLeftX + word_w // 2, topLeftY + word_h // 2  # 幾何中心

    # 標註 bounding box 和質心
    annotated_img = cv2.cvtColor(word_img_copy, cv2.COLOR_GRAY2BGR) if len(word_img_copy.shape) == 2 else word_img_copy
    cv2.rectangle(annotated_img, (topLeftX, topLeftY), (topLeftX + word_w, topLeftY + word_h), (255, 168, 0), 4)
    cv2.circle(annotated_img, (cX, cY), 10, (0, 0, 255), -1)

    # 保存標註的圖片
    annotated_img_path = os.path.join('annotated_images', f'{img_name}_annotated.png')
    os.makedirs('annotated_images', exist_ok=True)
    cv2.imwrite(annotated_img_path, annotated_img)
    
    h, w = word_img_copy.shape
    left_x = max(0, cX - int(CROP_LENGTH / 2))
    right_x = min(w, cX + int(CROP_LENGTH / 2))
    top_y = max(0, cY - int(CROP_LENGTH / 2))
    bot_y = min(h, cY + int(CROP_LENGTH / 2))

    final_word_img = word_img_copy[top_y:bot_y, left_x:right_x]
    return cv2.resize(final_word_img, (300, 300), interpolation=cv2.INTER_AREA)

def get_unique_filename(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 2
    unique_filename = filename
    
    # 當檔案已存在時，循環嘗試新的檔名
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{counter}{extension}"
        counter += 1
        
    return unique_filename

def crop_boxes(start_page, end_page):
    if os.path.exists(OUTPUT_FOLDER):
        # 刪除整個資料夾及其內容
        shutil.rmtree(OUTPUT_FOLDER)
        
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    unicode_list = read_json(JSON_PATH, UNICODE_NUM)
    for page in range(start_page, end_page + 1):
        #限制字數
        k = (page - 1) * PER_PAGE
        print(f"Processing starting character index: {k}")
        page_char_count = 0 

        # 構建檔案名稱
        image_file = f"page-{page}.png"
        # 圖片路徑
        image_path = os.path.join(INPUT_FOLDER, image_file)

        if not os.path.exists(image_path):
            print(f"Warning: {image_path} not found. Skipping page {page}.")
            continue

        # 讀取圖片
        image = Image.open(image_path)
        img_np = cv2.imread(image_path, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # 使用二值化處理，使方框更容易被檢測
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # 排除右下角的QR碼區域
        h_img, w_img = binary.shape
        qr_size = int(min(h_img, w_img) * 0.12)  # 假設QR碼大約佔圖片的12%
        binary[-qr_size:, -qr_size:] = 0  # 將右下角區域設為黑色
        
        # 使用輪廓檢測方框
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 對輪廓進行處理，將 y 值相差小於 10 的視為同一行
        contours = sorted(contours, key=lambda x: (cv2.boundingRect(x)[1] // 120, cv2.boundingRect(x)[0]))

        for i, contour in enumerate(contours):
            if page_char_count >= PER_PAGE:      # 這一頁裁滿就強制換頁，不再往下溢出
                break
            x, y, w, h = cv2.boundingRect(contour)
            
            # 排除右下角的QR碼區域
            if x + w > img_np.shape[1] - qr_size and y + h > img_np.shape[0] - qr_size:
                continue

            # 內縮方框
            x += PADDING
            y += PADDING
            w -= 2 * PADDING
            h -= 2 * PADDING

            # 略過小於閾值的方框
            if w >= MIN_BOX_SIZE and h >= MIN_BOX_SIZE:
                cropped_image = Image.fromarray(cv2.cvtColor(img_np[y:y + h, x:x + w], cv2.COLOR_BGR2RGB))
                cropped_image = np.array(cropped_image)
                cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
                median_filtered = cv2.medianBlur(cropped_image, 3)
                kernel = np.ones((2, 2), np.uint8)
                processed_image = cv2.morphologyEx(median_filtered, cv2.MORPH_OPEN, kernel)
                connectivity, labels, stats, centroids = cv2.connectedComponentsWithStats(processed_image, connectivity=8)
                
                for j in range(1, connectivity):
                    area = stats[j, cv2.CC_STAT_AREA]
                    if area < MIN_AREA_THRESHOLD:
                        processed_image[labels == j] = 0
                
                current_index = k + page_char_count
                if current_index >= UNICODE_NUM:
                    break

                cropped_image = scale_adjustment(processed_image, unicode_list[current_index])

                # 檢查是否為重複字，並用 -n 輔助命名
                original_filename = f'{unicode_list[current_index]}.png'
                final_filename = get_unique_filename(OUTPUT_FOLDER, original_filename)
                cv2.imwrite(os.path.join(OUTPUT_FOLDER, final_filename), cropped_image)
                
                page_char_count += 1
                cv2.rectangle(img_np, (x, y), (x + w, y + h), (255, 0, 0), 2)

        bound_output_directory = 'rec_bound'
        os.makedirs(bound_output_directory, exist_ok=True)
        cv2.imwrite(os.path.join(bound_output_directory, f"page-{page}.png"), img_np)

if __name__ == "__main__":
    auto_start_page = 1
    auto_end_page = (UNICODE_NUM + PER_PAGE - 1) // PER_PAGE 
    
    crop_boxes(auto_start_page, auto_end_page)