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

# --- Global Configurations ---
file_lock = threading.Lock()
# File for SBDs that are found to have no results
NOT_FOUND_FILENAME = "sbd_khong_co_ket_qua.txt"
# File for SBDs that cause persistent errors after multiple retries
SBD_ERROR_FILENAME = "sbd_bi_loi.txt"


def wait_for_loader_to_disappear(driver):
    """Waits for the loading spinner to disappear, reloading on timeout."""
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.el-loading-mask"))
        )
    except TimeoutException:
        print(f"[{threading.current_thread().name}] Timed out waiting for loader to disappear. Reloading page.")
        driver.refresh()
        wait_for_loader_to_disappear(driver)


def chon_muc_dropdown(driver, label_text, option_text):
    """Selects an option from a dropdown menu with retries."""
    for attempt in range(3):
        try:
            # Locate and click the dropdown trigger
            dropdown_xpath = f"//label[contains(normalize-space(), '{label_text}')]/ancestor::div[contains(@class, 'col-md-4')]//input"
            dropdown_trigger = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, dropdown_xpath))
            )
            driver.execute_script("arguments[0].click();", dropdown_trigger)
            
            # Locate and click the desired option
            option_xpath = f"//li[.//span[text()='{option_text}']]"
            option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, option_xpath))
            )
            driver.execute_script("arguments[0].click();", option)
            
            print(f"[{threading.current_thread().name}] - Dropdown '{label_text}' set to: '{option_text}'.")
            time.sleep(0.75)  # Delay to ensure the selection is processed
            return True
        except StaleElementReferenceException:
            print(f"[{threading.current_thread().name}] StaleElementReferenceException on '{label_text}'. Retrying attempt {attempt + 1}...")
            time.sleep(1)
        except Exception as e:
            print(f"!!! [{threading.current_thread().name}] Error selecting '{option_text}' for '{label_text}': {e}")
            return False
    print(f"!!! [{threading.current_thread().name}] Failed to select '{label_text}' after multiple attempts.")
    return False


def chon_tat_ca_dropdowns(driver, du_lieu):
    """Selects all necessary dropdowns to set the search context."""
    print(f"[{threading.current_thread().name}] Setting all dropdown filters...")
    wait_for_loader_to_disappear(driver)
    chon_muc_dropdown(driver, "Đơn vị", du_lieu["don_vi"])
    chon_muc_dropdown(driver, "Cấp học", du_lieu["cap_hoc"])
    chon_muc_dropdown(driver, "Năm học", du_lieu["nam_hoc"])
    chon_muc_dropdown(driver, "Đợt tuyển sinh", du_lieu["dot_tuyen_sinh"])
    chon_muc_dropdown(driver, "Kỳ thi", du_lieu["ky_thi"])
    print(f"[{threading.current_thread().name}] All dropdowns have been set.")


def get_scores_from_canvas(driver):
    """Executes JavaScript to extract scores from canvas elements, which are used to render text."""
    get_all_scores_js = """
        const getScoreFromCanvas = (canvasElement) => {
            if (!canvasElement) return 'N/A';
            try {
                // Access the Vue instance associated with the canvas to get the rendered text
                const vueInstance = canvasElement.__vue__ || canvasElement.__vueParentComponent;
                if (vueInstance) {
                    const text = vueInstance.text || (vueInstance.proxy && vueInstance.proxy.text);
                    return text !== undefined ? text : 'N/A';
                }
            } catch (e) { /* Ignore errors */ }
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
    """
    Searches for a single SBD and returns the result.
    Returns:
    - A dictionary with scores on success.
    - "NOT_FOUND" if the server returns a 'not found' message.
    - "RELOAD_PAGE" if a recoverable page error occurs.
    """
    try:
        sbd_xpath = "//label[contains(normalize-space(), 'Số báo danh')]/ancestor::div[contains(@class, 'col-md-4')]//input"
        sbd_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, sbd_xpath)))
        sbd_input.clear()
        sbd_input.send_keys(sbd)
        
        tra_cuu_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(normalize-space(), 'Tra cứu')]]")))
        tra_cuu_button.click()
        
        # Wait for either the results table or a message box to appear
        WebDriverWait(driver, 15).until(EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body")),
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'el-message-box__wrapper')]")),
        ))
        
        # Check for specific pop-up messages
        try:
            # This pop-up indicates a data loading failure, requiring a page reload
            reload_popup_msg_xpath = "//div[contains(@class, 'el-message-box__wrapper')]//p[contains(text(), 'Có dữ liệu chưa tải thành công')]"
            driver.find_element(By.XPATH, reload_popup_msg_xpath)
            print(f"[{threading.current_thread().name}] Data load error for SBD {sbd}. Will reload page.")
            close_button = driver.find_element(By.XPATH, "//div[@class='el-message-box__btns']//button")
            close_button.click()
            WebDriverWait(driver, 5).until_not(EC.presence_of_element_located((By.CLASS_NAME, "v-modal")))
            return "RELOAD_PAGE"
        except NoSuchElementException:
            pass 

        try:
            # This pop-up definitively means the SBD does not exist
            not_found_popup_msg_xpath = "//div[contains(@class, 'el-message-box__wrapper')]//p[contains(text(), 'Không tìm thấy kết quả')]"
            driver.find_element(By.XPATH, not_found_popup_msg_xpath)
            print(f"[{threading.current_thread().name}] SBD {sbd} not found (Popup message).")
            close_button = driver.find_element(By.XPATH, "//div[@class='el-message-box__btns']//button")
            close_button.click()
            WebDriverWait(driver, 5).until_not(EC.presence_of_element_located((By.CLASS_NAME, "v-modal")))
            return "NOT_FOUND"
        except NoSuchElementException:
            pass 

        # Check for an empty results table
        try:
            driver.find_element(By.XPATH, "//span[@class='el-table__empty-text' and text()='Không có dữ liệu']")
            print(f"[{threading.current_thread().name}] SBD {sbd} not found (Empty table).")
            return "NOT_FOUND"
        except NoSuchElementException:
            # If no errors were found, assume success and extract scores
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
        print(f"[{threading.current_thread().name}] Timeout waiting for results for SBD {sbd}. Will reload page.")
        return "RELOAD_PAGE"
    except Exception as e:
        print(f"!!! [{threading.current_thread().name}] An unknown error occurred with SBD {sbd}: {str(e)}. Will reload page.")
        return "RELOAD_PAGE"


def worker(driver, sbd_list, output_filename, du_lieu):
    """The main worker function for each thread. It iterates through its assigned list of SBDs."""
    url = 'https://quangninh.tsdc.edu.vn/tra-cuu-diem-thi'
    try:
        driver.get(url)
        chon_tat_ca_dropdowns(driver, du_lieu)
        
        i = 0
        while i < len(sbd_list):
            sbd = sbd_list[i]
            succeeded = False
            
            # --- MODIFIED: Retry loop for each SBD ---
            for attempt in range(3):
                print(f"[{threading.current_thread().name}] Looking up SBD: {sbd} ({i+1}/{len(sbd_list)}) - Attempt {attempt + 1}")
                result = crawl_sbd(driver, sbd)

                if isinstance(result, dict):  # Success case
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
                        print(f"[{threading.current_thread().name}] Wrote result for SBD {sbd} to {output_filename}")
                        succeeded = True
                        break  # Exit retry loop on success

                    except Exception as e:
                        print(f"!!! [{threading.current_thread().name}] Error writing file for SBD {sbd}: {e}")
                        succeeded = True  # Treat as success to avoid logging as a failed SBD
                        break

                elif result == "NOT_FOUND":  # Definitive 'not found' case
                    with file_lock: 
                        with open(NOT_FOUND_FILENAME, 'a', encoding='utf-8') as f:
                            f.write(f"{sbd}\n")
                    print(f"[{threading.current_thread().name}] Wrote SBD {sbd} (not found) to {NOT_FOUND_FILENAME}")
                    succeeded = True
                    break # Exit retry loop, no need to retry

                elif result == "RELOAD_PAGE":  # Recoverable page error
                    print(f"[{threading.current_thread().name}] Reloading page due to an external error...")
                    driver.get(url)
                    chon_tat_ca_dropdowns(driver, du_lieu)
                    time.sleep(1) # Wait a bit after reload before retrying the same SBD

                else:  # Unknown error
                    print(f"[{threading.current_thread().name}] Unknown error with SBD {sbd}, continuing to next attempt.")
            
            # --- MODIFICATION: Handle persistent failure after all retries ---
            if not succeeded:
                print(f"!!! [{threading.current_thread().name}] All attempts failed for SBD {sbd}. Saving it to the error file.")
                with file_lock:
                    with open(SBD_ERROR_FILENAME, 'a', encoding='utf-8') as f:
                        f.write(f"{sbd}\n")

            i += 1  # Move to the next SBD regardless of outcome
            time.sleep(2.5) # Polling delay to be respectful to the server

    except Exception as e:
        print(f"!!! [{threading.current_thread().name}] A critical error occurred in the worker: {e}")
    finally:
        print(f"[{threading.current_thread().name}] Task completed. Closing browser.")
        driver.quit()


if __name__ == '__main__':
    try:
        num_thr = int(input("Nhập số lượng trình duyệt (luồng) cần khởi tạo: "))
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")
        exit()
        
    # --- Configuration ---
    start_sbd = 260001
    end_sbd = 260720
    du_lieu_chung = {
        "don_vi": "Sở Giáo dục và Đào tạo Tỉnh Quảng Ninh",
        "cap_hoc": "THPT",
        "nam_hoc": "2025-2026",
        "dot_tuyen_sinh": "THPT công lập năm 2025 - 2026 (Chính thức)",
        "ky_thi": "Tuyển sinh 10 THPT"
    }

    # --- File Initialization ---
    # Clear the 'not found' and 'error' files at the start of the run
    with open(NOT_FOUND_FILENAME, 'w') as f:
        f.write('')
    with open(SBD_ERROR_FILENAME, 'w') as f:
        f.write('')
    
    all_sbds = [str(i) for i in range(start_sbd, end_sbd + 1)]
    
    # --- Thread and Driver Setup ---
    chunk_size = (len(all_sbds) + num_thr - 1) // num_thr
    chunks = [all_sbds[i:i + chunk_size] for i in range(0, len(all_sbds), chunk_size)]
    
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Disable images for speed
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless") # Uncomment to hide browser windows
    
    drivers = []
    for i in range(num_thr):
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(300, 300)
            x = (i % 5) * 300
            y = (i // 5) * 300
            driver.set_window_position(x, y)
            driver.execute_script("document.body.style.zoom = '0.5'") # Zoom out to fit more content
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
        time.sleep(0.25) 
    
    for thread in threads:
        thread.join()
    
    print("\n\n=============================================")
    print("=== TẤT CẢ CÁC LUỒNG ĐÃ HOÀN TẤT ===")
    print(f"Kết quả đã được lưu vào các file luong_..._ketqua.txt.")
    print(f"Các SBD không tìm thấy kết quả đã được lưu vào file: {NOT_FOUND_FILENAME}")
    print(f"Các SBD gây lỗi liên tục đã được lưu vào file: {SBD_ERROR_FILENAME}")
    print("=============================================")
