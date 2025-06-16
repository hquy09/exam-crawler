# Made by Huu Quy
# Copyright 2025 Huu Quy
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import json
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


file_lock = threading.Lock()
NOT_FOUND_FILENAME = "sbd_khong_co_ket_qua.txt"

def wait_for_loader_to_disappear(driver):
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.el-loading-mask"))
        )
    except TimeoutException:
        print(f"[{threading.current_thread().name}] Quá thời gian chờ loader biến mất. Thử tải lại trang.")
        driver.refresh()
        wait_for_loader_to_disappear(driver)


def chon_muc_dropdown(driver, label_text, option_text):
  
    for attempt in range(3): #try 3 times
        try:
            print(f"[{threading.current_thread().name}] Đang xử lý dropdown '{label_text}'...")
            dropdown_xpath = f"//label[contains(normalize-space(), '{label_text}')]/ancestor::div[contains(@class, 'col-md-4')]//input"
            
            # click dropdown
            dropdown_trigger = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, dropdown_xpath))
            )
            driver.execute_script("arguments[0].click();", dropdown_trigger)
            option_xpath = f"//li[.//span[text()='{option_text}']]"
            option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, option_xpath))
            )
            driver.execute_script("arguments[0].click();", option)
            print(f"[{threading.current_thread().name}] - Đã chọn: '{option_text}'.")
            time.sleep(0.75) #add delay to ensure the selection is processed
            return True
        except StaleElementReferenceException:
            print(f"[{threading.current_thread().name}] Gặp StaleElementReferenceException khi chọn '{label_text}'. Đang thử lại lần {attempt + 1}...")
            time.sleep(1) 
        except Exception as e:
            print(f"!!! [{threading.current_thread().name}] Lỗi khi chọn '{option_text}' cho '{label_text}': {e}")
            return False
    return False


def chon_tat_ca_dropdowns(driver, du_lieu):
    wait_for_loader_to_disappear(driver)
    chon_muc_dropdown(driver, "Đơn vị", du_lieu["don_vi"])
    chon_muc_dropdown(driver, "Cấp học", du_lieu["cap_hoc"])
    chon_muc_dropdown(driver, "Năm học", du_lieu["nam_hoc"])
    chon_muc_dropdown(driver, "Đợt tuyển sinh", du_lieu["dot_tuyen_sinh"])
    chon_muc_dropdown(driver, "Kỳ thi", du_lieu["ky_thi"])


def get_scores_from_canvas(driver):
    get_all_scores_js = """
        const getScoreFromCanvas = (canvasElement) => {
            if (!canvasElement) return 'N/A';
            try {
                const vueInstance = canvasElement.__vue__ || canvasElement.__vueParentComponent;
                if (vueInstance) {
                    const text = vueInstance.text || (vueInstance.proxy && vueInstance.proxy.text);
                    return text !== undefined ? text : 'N/A';
                }
            } catch (e) { }
            return 'N/A';
        };

        const subjectRows = document.querySelectorAll('.el-table__body tr.el-table__row');
        const subjectScores = [];
        subjectRows.forEach(row => {
            const subjectElement = row.querySelector('td:nth-child(2) .cell');
            const canvas = row.querySelector('td:nth-child(3) canvas');
            if (subjectElement && canvas) {
                subjectScores.push({
                    subject: subjectElement.innerText.trim(),
                    score: getScoreFromCanvas(canvas)
                });
            }
        });

        let priorityScore = 'N/A';
        const infoParagraphs = document.querySelectorAll('div.card-body p');
        infoParagraphs.forEach(p => {
            const span = p.querySelector('span.font-weight-bold');
            if (span && span.innerText.includes('Điểm Ưu tiên')) {
                const canvas = p.querySelector('canvas');
                priorityScore = getScoreFromCanvas(canvas);
            }
        });
        
        return JSON.stringify({
            priorityScore: priorityScore,
            subjectScores: subjectScores
        });
    """
    json_results = driver.execute_script(get_all_scores_js)
    return json.loads(json_results)


def crawl_sbd(driver, sbd):
    try:
        # sbd
        sbd_xpath = "//label[contains(normalize-space(), 'Số báo danh')]/ancestor::div[contains(@class, 'col-md-4')]//input"
        sbd_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, sbd_xpath)))
        sbd_input.clear()
        sbd_input.send_keys(sbd)
        tra_cuu_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(normalize-space(), 'Tra cứu')]]"))
        )
        tra_cuu_button.click()
        wait = WebDriverWait(driver, 15)
        wait.until(EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body")),
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'el-message-box__wrapper')]")),
        ))
        # checking for errors or results
        try:
            reload_popup_msg_xpath = "//div[contains(@class, 'el-message-box__wrapper')]//p[contains(text(), 'Có dữ liệu chưa tải thành công')]"
            reload_popup = driver.find_element(By.XPATH, reload_popup_msg_xpath)
            if reload_popup.is_displayed():
                print(f"[{threading.current_thread().name}] Lỗi tải dữ liệu cho SBD {sbd}. Sẽ tải lại trang và thử lại.")
                close_button = driver.find_element(By.XPATH, "//div[@class='el-message-box__btns']//button")
                close_button.click()
                WebDriverWait(driver, 5).until_not(EC.presence_of_element_located((By.CLASS_NAME, "v-modal")))
                return "RELOAD_PAGE"
        except NoSuchElementException:
            pass 

        try:
            not_found_popup_msg_xpath = "//div[contains(@class, 'el-message-box__wrapper')]//p[contains(text(), 'Không tìm thấy kết quả')]"
            not_found_popup = driver.find_element(By.XPATH, not_found_popup_msg_xpath)
            if not_found_popup.is_displayed():
                print(f"[{threading.current_thread().name}] Không tìm thấy kết quả cho SBD {sbd} (Popup).")
                close_button = driver.find_element(By.XPATH, "//div[@class='el-message-box__btns']//button")
                close_button.click()
                WebDriverWait(driver, 5).until_not(EC.presence_of_element_located((By.CLASS_NAME, "v-modal")))
                return "NOT_FOUND"
        except NoSuchElementException:
            pass 

        try:
            
            empty_table_text = driver.find_element(By.XPATH, "//span[@class='el-table__empty-text' and text()='Không có dữ liệu']")
            if empty_table_text.is_displayed():
                print(f"[{threading.current_thread().name}] Không tìm thấy kết quả cho SBD {sbd} (Bảng trống).")
                return "NOT_FOUND"
        except NoSuchElementException:
            # res
            scores = get_scores_from_canvas(driver)
            priority_score = scores.get('priorityScore', 'N/A')
            if priority_score == 'N/A' or priority_score is None:
                priority_score = '0'

            return {
                "sbd": sbd,
                "priority_score": priority_score,
                "subjects": scores.get('subjectScores', [])
            }

    except TimeoutException:
        print(f"[{threading.current_thread().name}] Timeout khi chờ kết quả cho SBD {sbd}. Sẽ tải lại trang và thử lại.")
        return "RELOAD_PAGE"
    except Exception as e:
        print(f"!!! [{threading.current_thread().name}] Lỗi không xác định với SBD {sbd}: {str(e)}. Sẽ tải lại trang và thử lại.")
        return "RELOAD_PAGE"
    return None


def worker(driver, sbd_list, output_filename, du_lieu):
    url = 'https://quangninh.tsdc.edu.vn/tra-cuu-diem-thi'
    try:
        driver.get(url)
        print(f"[{threading.current_thread().name}] Đã mở trang web thành công.")
        chon_tat_ca_dropdowns(driver, du_lieu)
        i = 0
        while i < len(sbd_list):
            sbd = sbd_list[i]
            print(f"[{threading.current_thread().name}] Đang tiến hành tra cứu SBD: {sbd} ({i+1}/{len(sbd_list)})")
            result = crawl_sbd(driver, sbd)
            if isinstance(result, dict): #success case
                try:
                    scores_dict = {"Toán": "N/A", "Văn": "N/A", "Anh": "N/A"}
                    for subject in result.get('subjects', []):
                        subject_name = subject.get('subject', '').lower()
                        score = subject.get('score', 'N/A')
                        if 'toán' in subject_name:
                            scores_dict['Toán'] = score
                        elif 'văn' in subject_name:
                            scores_dict['Văn'] = score
                        elif 'anh' in subject_name or 'ngoại ngữ' in subject_name:
                            scores_dict['Anh'] = score
                    
                    output_line = (f"SDB: {result['sbd']}, Điểm ƯT/KK: {result['priority_score']}, "
                                   f"Điểm Toán: {scores_dict['Toán']}, Điểm Văn: {scores_dict['Văn']}, "
                                   f"Điểm Anh: {scores_dict['Anh']}\n")

                    with open(output_filename, 'a', encoding='utf-8') as f:
                        f.write(output_line)
                    print(f"[{threading.current_thread().name}] Đã ghi kết quả SBD {sbd} vào file {output_filename}")
                    i += 1 

                except Exception as e:
                    print(f"!!! [{threading.current_thread().name}] Lỗi khi ghi file cho SBD {sbd}: {e}")
                    i += 1 

            elif result == "NOT_FOUND": # unsuccessful case
                with file_lock: 
                    with open(NOT_FOUND_FILENAME, 'a', encoding='utf-8') as f:
                        f.write(f"{sbd}\n")
                print(f"[{threading.current_thread().name}] Đã ghi SBD {sbd} không tìm thấy vào file {NOT_FOUND_FILENAME}")
                i += 1 

            elif result == "RELOAD_PAGE": #reload page
                print(f"[{threading.current_thread().name}] Đang thực hiện tải lại trang...")
                driver.get(url)
                chon_tat_ca_dropdowns(driver, du_lieu)
            
            else: 
                print(f"[{threading.current_thread().name}] Gặp lỗi không xác định với SBD {sbd}, bỏ qua.")
                i += 1
            time.sleep(0.75)

    except Exception as e:
        print(f"!!! [{threading.current_thread().name}] Lỗi nghiêm trọng trong worker: {e}")
    finally:
        print(f"[{threading.current_thread().name}] Đã hoàn thành nhiệm vụ. Đóng trình duyệt.")
        driver.quit()


if __name__ == '__main__':
    try:
        num_thr = int(input("Nhập số lượng trình duyệt (luồng) cần khởi tạo: "))
    except ValueError:
        print("Vui lòng nhập một số nguyên.")
        exit()
        
    start_sbd = 260001
    end_sbd = 260720
    du_lieu_chung = {
        "don_vi": "Sở Giáo dục và Đào tạo Tỉnh Quảng Ninh",
        "cap_hoc": "THPT",
        "nam_hoc": "2025-2026",
        "dot_tuyen_sinh": "THPT công lập năm 2025 - 2026 (Chính thức)",
        "ky_thi": "Tuyển sinh 10 THPT"
    }

    with open(NOT_FOUND_FILENAME, 'w') as f:
        f.write('') 
    
    all_sbds = [str(i) for i in range(start_sbd, end_sbd + 1)]
    
    # divide 
    chunk_size = (len(all_sbds) + num_thr - 1) // num_thr # Chia đều hơn
    chunks = [all_sbds[i:i + chunk_size] for i in range(0, len(all_sbds), chunk_size)]
    #config
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless") # hide the browser window
    
    drivers = []
    for i in range(num_thr):
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(300, 300)
            x = (i % 5) * 300
            y = (i // 5) * 300
            driver.set_window_position(x, y)
            driver.execute_script("document.body.style.zoom = '0.5'")
            drivers.append(driver)
        except Exception as e:
            print(f"Lỗi khi khởi tạo driver {i+1}: {e}")
            for d in drivers:
                d.quit()
            exit()

    if len(drivers) != num_thr:
        print("Không thể khởi tạo đủ số lượng trình duyệt yêu cầu. Thoát chương trình.")
        exit()

    threads = []
    for i in range(num_thr):
        output_filename = f"luong_{i+1}_ketqua.txt"
        with open(output_filename, 'w') as f:
            f.write('')
            
        thread = threading.Thread(
            target=worker, 
            args=(drivers[i], chunks[i], output_filename, du_lieu_chung),
            name=f"Luồng-{i+1}"
        )
        threads.append(thread)
        thread.start()
        time.sleep(1) 
    
    for thread in threads:
        thread.join()
    
    print("\n\n=============================================")
    print("=== TẤT CẢ CÁC LUỒNG ĐÃ HOÀN TẤT ===")
    print(f"Kết quả đã được lưu vào các file luong_..._ketqua.txt")
    print(f"Các SBD không có dữ liệu đã được lưu vào file {NOT_FOUND_FILENAME}")
    print("=============================================")
