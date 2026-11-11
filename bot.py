import os
import time
import requests
from bs4 import BeautifulSoup

# Lấy thông tin cấu hình từ Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")
KEYWORD = os.getenv("KEYWORD", "SHB")  # Từ khóa bạn muốn săn tin

# Danh sách các mục/chuyên mục bạn muốn quét (thêm bao nhiêu link tùy thích vào đây)
URL_LIST = [
    "https://vietstock.vn/chu-de/1-2/moi-cap-nhat.htm",
    "https://vietstock.vn/chung-khoan.htm",
    "https://vietstock.vn/doanh-nghiep.htm",
    "https://vietstock.vn/bat-dong-san.htm",
    "https://vietstock.vn/tai-chinh.htm",
]

# Set này dùng để ghi nhớ các link đã gửi, đảm bảo KHÔNG BAO GIỜ lặp lại
sent_links = set()


def send_telegram(message):
  if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
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


def check_content():
  print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Đang quét các chuyên mục...")
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  for main_url in URL_LIST:
    try:
      response = requests.get(main_url, headers=headers, timeout=10)
      if response.status_code != 200:
        continue

      soup = BeautifulSoup(response.text, "html.parser")
      # Lấy tất cả các thẻ link bài viết trên trang danh mục
      links = soup.find_all("a", href=True)

      for tag in links:
        link = tag.get("href", "")
        title = tag.get_text(strip=True)

        # Lọc các link bài viết hợp lệ của trang
        if not link or not title or len(title) < 10:
          continue

        if link.startswith("/"):
          full_link = f"https://vietstock.vn{link}"
        elif link.startswith("http"):
          full_link = link
        else:
          continue

        # Chỉ xử lý nếu bài này chưa từng được gửi thông báo trước đó
        if full_link not in sent_links:
          # Kiểm tra ngay trong tiêu đề trước xem có từ khóa không
          matched = KEYWORD.lower() in title.lower()

          # Nếu tiêu đề không có, tiến hành vào sâu bên trong nội dung bài viết để quét tiếp
          if not matched:
            try:
              art_res = requests.get(full_link, headers=headers, timeout=5)
              if art_res.status_code == 200:
                art_soup = BeautifulSoup(art_res.text, "html.parser")
                # Lấy toàn bộ nội dung text của bài viết
                art_text = art_soup.get_text()
                if KEYWORD.lower() in art_text.lower():
                  matched = True
            except:
              pass

          # Nếu tìm thấy từ khóa ở tiêu đề HOẶC trong nội dung bài viết
          if matched:
            sent_links.add(
                full_link
            )  # Đánh dấu đã gửi để không bao giờ lặp lại
            msg = (
                f"🔥 *Phát hiện bài viết chứa từ khóa '{KEYWORD}':*\n\n[{title}]({full_link})"
            )
            send_telegram(msg)
            print(f"Đã báo về Telegram bài: {title}")

            # Nghỉ ngắn giữa các bài để không bị trang web chặn IP
            time.sleep(1)

    except Exception as e:
      print(f"Lỗi quét mục {main_url}: {e}")


if __name__ == "__main__":
  send_telegram(
      f"🤖 Bot quét sâu từ khóa *{KEYWORD}* (Tiêu đề + Nội dung) đã khởi động!"
  )

  while True:
    check_content()
    # Cứ sau mỗi 3 phút (180 giây), tool sẽ tự động quét lại toàn bộ một lượt
    time.sleep(180)
