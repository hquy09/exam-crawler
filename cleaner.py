import os
import glob

def clean_old_files():
    """
    Finds and deletes previous result and log files to ensure a clean run.
    """
    print("Bắt đầu dọn dẹp các file kết quả và file log cũ...")

    # Define file patterns to delete
    patterns_to_delete = [
        "luong_*_ketqua.txt",
        "sbd_khong_co_ket_qua.txt",
        "sbd_bi_loi.txt"
    ]
    
    deleted_count = 0
    
    for pattern in patterns_to_delete:
        # Find all files matching the current pattern
        files = glob.glob(pattern)
        if not files:
            print(f"- Không tìm thấy file nào khớp với mẫu: '{pattern}'")
            continue
            
        for f in files:
            try:
                os.remove(f)
                print(f"- Đã xóa: {f}")
                deleted_count += 1
            except Exception as e:
                print(f"!!! Lỗi khi xóa file {f}: {e}")

    print("-" * 30)
    if deleted_count == 0:
        print("Không có file nào cần dọn dẹp.")
    else:
        print(f"Hoàn tất! Đã xóa tổng cộng {deleted_count} file.")
    print("=============================================")


if __name__ == '__main__':
    clean_old_files()
