from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time


# # MySQL 연결
# db = pymysql.connect(
#     host="localhost",
#     user="root",
#     password="mysql",
#     database="cu_store",
#     charset="utf8mb4"
# )
# cursor = db.cursor()

# Chrome WebDriver 설정 (headless 모드 사용 가능)
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 안 띄우기
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver_path = r"C:\dev\chromedriver.exe"
service = Service(driver_path)  # ChromeDriver 경로
driver = webdriver.Chrome(service=service, options=chrome_options)

# CU 상품 페이지 URL
url = "https://www.7-eleven.co.kr/product/bestdosirakList.asp"
driver.get(url)

# 페이지 로딩 대기
time.sleep(5)

# **🔹 "더보기" 버튼 클릭하여 모든 제품 로드 🔹**
while True:
    try:
        # "더보기" 버튼 찾기
        more_button = driver.find_element(By.CSS_SELECTOR, "li.btn_more a")
        if more_button:
            driver.execute_script("fncMore('');")  # JavaScript 실행
            time.sleep(2)  # 데이터 로드 대기
            print("🔄 MORE 버튼 클릭 - 추가 로드 중...")
        else:
            print("✅ 모든 제품이 로드되었습니다.")
            break
    except:
        print("✅ 더 이상 로드할 데이터가 없습니다.")
        break


# **🔹 모든 제품 가져오기 🔹**
products = driver.find_elements(By.CSS_SELECTOR, "div.pic_product")
print(f"총 {len(products)}개의 제품을 찾았습니다.")

# 중복 제거를 위한 Set 자료구조 사용
seen_products = set()
product_data = []

for product in products:
    try:
        # 이미지 URL 가져오기
        img_tag = product.find_element(By.CSS_SELECTOR, "img")
        image_url = img_tag.get_attribute("src")

        # 제품명 가져오기
        name_tag = product.find_element(By.CSS_SELECTOR, "div.infowrap div.name")
        name = name_tag.text.strip()

        # 가격 가져오기
        try:
            price_tag = product.find_element(By.CSS_SELECTOR, "div.infowrap div.price span")
            price_text = price_tag.text.strip().replace(",", "")
            price = int(price_text) if price_text else 0
        except:
            price = 0  # 가격이 없거나 오류 발생 시 기본값 0

        # **중복 제거: 같은 상품이 이미 리스트에 있는 경우 추가하지 않음**
        product_key = (name, price, image_url)
        if product_key not in seen_products:
            seen_products.add(product_key)
            product_data.append([name, price, image_url])

            print(f"✅ 추가된 상품: {name}, 가격: {price}원, 이미지: {image_url}")

    except Exception as e:
        print(f"오류 발생: {e}")

# 드라이버 종료
driver.quit()

# **🔹 DataFrame으로 변환 및 CSV 저장 🔹**
df = pd.DataFrame(product_data, columns=["상품명", "가격", "이미지_URL"])
df.to_csv("seven_eleven_freshfood.csv", index=False, encoding="utf-8-sig")

print("✅ CSV 파일 저장 완료: seven_eleven_freshfood.csv")