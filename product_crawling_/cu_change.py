from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pymysql
import time
from bs4 import BeautifulSoup

# **🔹 MySQL 연결**
db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="products",
    charset="utf8mb4"
)
cursor = db.cursor()

# **🔹 Chrome WebDriver 설정 (headless 모드 사용 가능)**
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 안 띄우기
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver_path = r"C:\dev\chromedriver.exe"
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# **🔹 PB 상품 페이지 URL (Private Brand)**

url = "https://cu.bgfretail.com/product/pb.do?category=product&depth2=1&sf=N"
driver.get(url)
time.sleep(5)  # 페이지 로딩 대기

store_id = 1  # CU 편의점 코드
product_data = set()  # 중복 방지를 위한 데이터 저장
updated_count = 0  # 업데이트된 개수

try:
    # 🔹 탭 클릭 (CU단독운영상품)
    tab_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.cardInfo_02 a"))
    )
    driver.execute_script("arguments[0].click();", tab_element)  # JavaScript 클릭 실행
    time.sleep(3)  # 페이지 변경 대기
    print("✅ 'CU단독운영상품' 탭 클릭 완료.")
except Exception as e:
    print(f"⚠️ 'CU단독운영상품' 탭 클릭 실패: {e}")

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
    except Exception as e:
        print(f"✅ 더 이상 로드할 데이터가 없습니다. (오류: {e})")
        break  # 오류 발생 시 반복 종료

# **🔹 BeautifulSoup을 이용한 HTML 파싱**
soup = BeautifulSoup(driver.page_source, "html.parser")

# **🔹 제품 리스트 가져오기**
li_elements = soup.find_all("li", class_="prod_list")

for li in li_elements:
    try:
        # **제품명 추출**
        name_element = li.select_one("div.prod_text > div.name > p")
        product_name = name_element.text.strip() if name_element else "이름 없음"

        # **이미 존재하는 제품인지 DB에서 확인**
        cursor.execute("SELECT product_id FROM convenient_store_products WHERE product_name = %s", (product_name,))
        result = cursor.fetchone()

        if result:  # 동일한 제품이 존재하는 경우
            product_id = result[0]

            # **category_name을 1로 업데이트**
            cursor.execute("UPDATE convenient_store_products SET convenient_store_name = 1 WHERE product_id = %s", (product_id,))
            db.commit()
            updated_count += 1
            print(f"✅ 업데이트 완료: {product_name} → convenient_store_name = 1")

        else:
            print(f"⚠️ DB에 없는 제품 (저장 안 함): {product_name}")

    except Exception as e:
        print(f"⚠️ 데이터 처리 오류: {e} (제품명: {product_name})")

# **🔹 최종 결과 출력**
print(f"\n🛠️ 업데이트된 제품 개수: {updated_count}")

# **🔹 드라이버 및 MySQL 종료**
driver.quit()
cursor.close()
db.close()
