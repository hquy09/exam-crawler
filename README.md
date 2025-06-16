# Exam Scores Crawler
![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![GitHub stars](https://img.shields.io/github/stars/hquy09/exam-crawler?style=social)

This is a Python and Selenium-based tool to crawl 10th-grade entrance exam scores from the official education portal in Quang Ninh province, Vietnam. The script is multithreaded, handles the website's complex logic, and writes the results to structured text files.


## Key Features

  - **Full Automation**: Automatically selects form fields (education board, academic year, exam name) based on your configuration.
  - **Intelligent Data Crawling**: Fetches scores for each candidate based on their provided ID range.
  - **High Performance with Multithreading**: Utilizes multiple CPU cores to run browsers in parallel, drastically speeding up the lookup process.
  - **Clean and Clear Output**: Records detailed scores for each subject (Math, Literature, English) and any bonus points into well-formatted text files.

## Table of Contents

  - [Key Features](https://www.google.com/search?q=%23key-features)
  - [Installation and Setup](https://www.google.com/search?q=%23installation-and-setup)
      - [Method 1: Direct Python Environment (Recommended)](https://www.google.com/search?q=%23method-1-direct-python-environment-recommended)
      - [Method 2: Docker (Advanced)](https://www.google.com/search?q=%23method-2-docker-advanced)
  - [Configuration and Usage](https://www.google.com/search?q=%23configuration-and-usage)
      - [Step 1: Configure `main.py`](https://www.google.com/search?q=%23step-1-configure-mainpy)
      - [Step 2: Run the Script](https://www.google.com/search?q=%23step-2-run-the-script)
      - [Step 3: Review the Output](https://www.google.com/search?q=%23step-3-review-the-output)
  - [Technical](https://www.google.com/search?q=%23technical-deep-dive)
      - [Program Architecture](https://www.google.com/search?q=%23program-architecture)
      - [Canvas Scraping Logic](https://www.google.com/search?q=%23canvas-scraping-logic)
  - [Cleaner.py](https://www.google.com/search?q=cleaner+file+python&oq=cleaner+file+python&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIKCAEQABgIGA0YHjINCAIQABiGAxiABBiKBTIHCAMQABjvBTIHCAQQABjvBdIBCDMzNzRqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8)
  - [Contributing](https://www.google.com/search?q=%23contributing)
  - [Legal Disclaimer and Terms of Use](https://www.google.com/search?q=%23legal-disclaimer-and-terms-of-use)
  - [License](https://www.google.com/search?q=%23license)
  - [Author](https://www.google.com/search?q=%23author)

<br>

## Installation and Setup

### Method 1: Direct Python Environment (Recommended)

#### 1\. Install Prerequisites:

  - **Python (\>= 3.8)**: Download and install from [python.org](https://www.python.org/).
    *During installation on Windows, be sure to check the box **"Add Python to PATH"**.*
  - **Google Chrome**: Install the latest version of the Chrome browser.

#### 2\. Download and Set Up ChromeDriver:

This is the most critical step. ChromeDriver acts as the bridge between your Python script and the Chrome browser.

  - **Check your Chrome version**: Navigate to `chrome://settings/help`.
  - **Download ChromeDriver**: Go to the [Chrome for Testing dashboard](https://googlechromelabs.github.io/chrome-for-testing/) and download the ChromeDriver version that **exactly matches** your Chrome browser version.
  - **Place ChromeDriver correctly**: Unzip the downloaded file and place the `chromedriver.exe` (on Windows) or `chromedriver` (on macOS/Linux) executable in the **same directory** as your `main.py` script.

#### 3\. Download Code and Install Dependencies:

  - Download or clone this repository.
  - Open a terminal (or Command Prompt) in the project's directory and run the following command to install Selenium:

<!-- end list -->

```bash
pip install -r requirements.txt
```

*(The `requirements.txt` file contains a single line: `selenium`)*

or:

 ```bash
pip install selenium
```

### Method 2: Docker (Advanced)

If you are familiar with Docker, this method simplifies setup by avoiding manual installations.

1.  **Install Docker**: Download it from the official [Docker website](https://www.docker.com/).
2.  **Build the Docker image**:
    ```bash
    docker build -t diemthi-crawler .
    ```
3.  **Run the container**: This command runs the script and saves the output files to your machine's current directory.
    ```bash
    docker run --rm -v "$(pwd)/output:/app/output" diemthi-crawler
    ```
    *(Note: You will need to create an `output` directory in your project folder before running this command).*

## Configuration and Usage

### Step 1: Configure `main.py`

Open the `main.py` file and edit the values within the `if __name__ == '__main__':` block.

#### 1\. Set the Candidate ID Range:

Specify the range of student IDs (Số Báo Danh) you wish to look up.

```python
start_sbd = 260001
end_sbd = 260720
```

#### 2\. Define the Exam Information (Dropdowns):

This section is crucial for ensuring the script selects the correct exam.

```python
du_lieu_chung = {
    "don_vi": "Sở Giáo dục và Đào tạo Tỉnh XXXXX XXX",
    "cap_hoc": "THPT",
    "nam_hoc": "2025-2026",
    "dot_tuyen_sinh": "THPT công lập năm 2025 - 2026 (Chính thức)",
    "ky_thi": "Tuyển sinh 10 THPT"
}
```

> **Tip**: To find the correct values for a different exam, go to the website, manually select your desired options, and then open your browser's Developer Tools (F12). Inspect the elements or network requests to find the exact text of the selected options and use them here.

### Step 2: Run the Script

Open a terminal in the project directory and execute:

```bash
python main.py
```

The program will prompt you for the number of concurrent threads you want to run. Choose a number that is reasonable for *your system's CPU capacity.*

```
Enter the number of browser threads to initialize: 8
[Thread-1] Successfully opened the website.
[Thread-2] Successfully opened the website.
...
```

### Step 3: Review the Output

The results will be saved into text files in the root directory:

  * `luong_1_ketqua.txt`, `luong_2_ketqua.txt`, etc.: These files contain the successfully fetched scores for the candidate IDs handled by each thread.
    ```
    SDB: 260001, Điểm ƯT/KK: 0, Điểm Toán: 8.5, Điểm Văn: 7.0, Điểm Anh: 9.2
    ```
  * `sbd_khong_co_ket_qua.txt`: This file lists all candidate IDs for which no results were found.

<br>

## Technical 

### Program Architecture

1.  **`main.py`**: The entry point of the script. It takes user input and reads the configuration.
2.  **`threading`**: Creates multiple `worker` threads for parallel execution. The list of candidate IDs is split evenly among these threads.
3.  **`worker()`**: Each thread runs this function, managing its own Selenium `webdriver` instance. It is responsible for navigation, dropdown selection, and iterating through its assigned list of IDs.
4.  **`crawl_sbd()`**: The core function that performs the lookup. It enters the candidate ID, clicks the search button, and intelligently parses the result (success, error popup, or empty table).
5.  **`get_scores_from_canvas()`**: This function executes a JavaScript snippet to "see through" the `<canvas>` element and retrieve the underlying score data.

This is an effective and advanced technique for handling modern, JavaScript-heavy websites.

## Cleaner.py

If you are tired of the files generated, use this file to delete log files like **`luong_XX_ketqua.txt`**, **`sbd_khong_co_ket_qua.txt`**, etc......

How to run: 
On your computer, run this script in **root** directory.

```bash
python cleaner.py
```

or

```bash
python3 cleaner.py
```

## Contributing

A special thanks to [@giauydev](https://github.com/giauydev) for contributing ideas and code.



## Legal Disclaimer and Terms of Use

>   - This tool is **non-commercial** and created for **educational, research, or personal use only**.
>   - **Do not** use this tool for illegal activities, or to maliciously attack or exploit the education portal's system.
>   - The author is **not responsible** for any consequences arising from the misuse of this tool or any impact it may have on the source system.
>   - The author **does not store** or use any personal data of candidates retrieved from the system.
>   - Please use this tool **ethically, responsibly, and with respect for the privacy** of others.


## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT). You are free to use, copy, modify, and distribute it, provided you include the original copyright and license notice in any redistribution.


## Author

  - Developed by Huu Quy(cookie)
  - GitHub: [@hquy09](https://github.com/hquy09)

If you find it helpful, don’t forget to ⭐ the repo and share it!
