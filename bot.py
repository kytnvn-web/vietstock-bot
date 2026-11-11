import os
import time
import requests
from bs4 import BeautifulSoup

# Lấy thông tin từ cấu hình server hoặc điền trực tiếp
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")
KEYWORD = os.getenv("KEYWORD", "SHB")  # Từ khóa bạn muốn săn tin

# DANH SÁCH CÁC MỤC/TRANG WEB BẠN MUỐN QUÉT ĐỒNG THỜI
# Bạn có thể thêm bao nhiêu mục tùy thích vào danh sách này:
URL_LIST = [
    "https://vietstock.vn/chu-de/1-2/moi-cap-nhat.htm",  # Mục Mới cập nhật
    "https://vietstock.vn/chung-khoan.htm",  # Mục Chứng khoán
    "https://vietstock.vn/doanh-nghiep.htm",  # Mục Doanh nghiệp
    "https://vietstock.vn/bat-dong-san.htm",  # Mục Bất động sản
]

sent_links = set()  # Lưu link đã gửi để tránh bị lặp


def send_telegram(message):
  if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
    print("Chưa cấu hình Telegram Token!")
    return
  api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": False,
  }
  try:
    requests.post(api_url, json=payload, timeout=10)
  except Exception as e:
    print(f"Lỗi gửi Telegram: {e}")


def check_all_sites():
  print(
      f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Đang quét các chuyên mục đã"
      " chọn..."
  )
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  for url in URL_LIST:
    try:
      response = requests.get(url, headers=headers, timeout=10)
      if response.status_code != 200:
        continue

      soup = BeautifulSoup(response.text, "html.parser")
      # Lấy tất cả các thẻ a (đường dẫn bài viết trên trang)
      articles = soup.find_all("a")

      for article in articles:
        title = article.get_text(strip=True)
        link = article.get("href", "")

        # Kiểm tra nếu tiêu đề có chứa từ khóa bạn quan tâm
        if link and title and KEYWORD.lower() in title.lower():
          # Chuẩn hóa link đầy đủ
          if link.startswith("/"):
            full_link = f"https://vietstock.vn{link}"
          elif link.startswith("http"):
            full_link = link
          else:
            continue

          # Nếu bài này chưa từng gửi thông báo thì tiến hành gửi
          if full_link not in sent_links:
            sent_links.add(full_link)
            msg = f"🔥 *Phát hiện bài viết chứa từ khóa '{KEYWORD}':*\n\n[{title}]({full_link})"
            send_telegram(msg)
            print(f"Đã gửi: {title}")

    except Exception as e:
      print(f"Lỗi khi quét {url}: {e}")


if __name__ == "__main__":
  print("Bot bắt đầu chạy vòng lặp quét đa chuyên mục...")
  send_telegram(
      f"🤖 Bot theo dõi từ khóa *{KEYWORD}* đa chuyên mục đã khởi động thành"
      " công!"
  )

  while True:
    check_all_sites()
    # Nghỉ 5 phút (300 giây) rồi quét lại toàn bộ danh sách các mục trên
    time.sleep(300)
