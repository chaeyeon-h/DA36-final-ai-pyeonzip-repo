from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pymysql
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# MySQL 연결
db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="products",
    charset="utf8mb4"
)
cursor = db.cursor()

# Chrome WebDriver 설정 (headless 모드 사용 가능)
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 안 띄우기
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver_path = r"C:\dev\chromedriver.exe"
service = Service(driver_path)  # ChromeDriver 경로
driver = webdriver.Chrome(service=service, options=chrome_options)

# **CU 상품 페이지 URL**
url = "https://cu.bgfretail.com/product/pb.do?category=product&depth2=1&sf=N"
driver.get(url)
time.sleep(5)  # 페이지 로딩 대기

category = "음료"
store_id = 1  # 0: 전체, 1: CU, 2: GS25, 3: 7-eleven
product_data = set()  # 중복 방지를 위한 데이터 저장

# **🔹 '더보기' 버튼 클릭하여 모든 제품 로드**
while True:
    try:
        more_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.prodListBtn-w a"))
        )
        if more_button.is_displayed():
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)  # 데이터 로드 대기
            print("🔄 더보기 버튼 클릭 - 추가 로드 중...")
        else:
            print("✅ 모든 제품이 로드되었습니다.")
            break
    except:
        print("✅ 더 이상 로드할 데이터가 없습니다.")
        break  # 오류 발생 시 반복 종료

# **🔹 BeautifulSoup을 이용한 HTML 파싱**
soup = BeautifulSoup(driver.page_source, "html.parser")

# **🔹 제품 리스트 가져오기**
li_elements = soup.find_all("li", class_="prod_list")

for li in li_elements:
    # **제품명 추출**
    name_element = li.select_one("div.prod_text > div.name > p")
    product_name = name_element.text.strip() if name_element else "이름 없음"

    # **가격 추출**
    price_element = li.select_one("div.prod_text > div.price > strong")
    product_price = price_element.text.strip().replace(",", "") if price_element else "0"
    product_price = int(product_price) if product_price.isdigit() else 0

    # **이미지 URL 추출**
    img_element = li.select_one("div.prod_img > img")
    product_img_url = "https:" + img_element["src"] if img_element else "이미지 없음"

    # **중복 방지를 위해 리스트 사용**
    product_data.add((product_name, category, store_id, product_price, product_img_url))

# SQL INSERT 문 (중복 방지: IGNORE 사용)
sql = """
        INSERT INTO convenient_store_products (product_name, product_category_name, convenient_store_name, product_price, product_image_url, updated_at)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE 
            product_price = VALUES(product_price),
            product_image_url = VALUES(product_image_url),
            updated_at = CURRENT_TIMESTAMP;
        """

# **🔹 중복 제거 후 MySQL 저장**
inserted_count = 0  # 성공적으로 삽입된 데이터 개수
for product in product_data:
    try:
        cursor.execute(sql, product)
        db.commit()
        inserted_count += 1
        print(f"✅ 저장 완료: {product[0]} | {product[3]}원")
    except Exception as e:
        print(f"⚠️ SQL 저장 오류: {e} (데이터: {product})")

# 크롤링한 데이터 개수 확인
print(f"📊 크롤링된 제품 개수: {len(product_data)}")
print(f"🗄️ 실제 DB에 삽입된 개수: {inserted_count}")

# MySQL 데이터 개수 확인
cursor.execute("SELECT COUNT(*) FROM convenient_store_products WHERE product_category_name = %s", (category,))
db_count = cursor.fetchone()[0]


print(f"🗄️ DB 저장된 제품 개수: {db_count}")

# **🔹 크롤링된 데이터와 DB 저장된 데이터 개수 비교**
if inserted_count != db_count:
    print(f"⚠️ 데이터 누락 가능성이 있음! 실제 삽입된 개수 ({inserted_count})와 DB 저장 개수 ({db_count})를 확인하세요.")
else:
    print(f"✅ '{category}' 카테고리 데이터가 정상적으로 저장됨.")


# **🔹 드라이버 및 MySQL 종료**
driver.quit()
cursor.close()
db.close()