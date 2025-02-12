import pandas as pd
import pymysql

# **🔹 MySQL 연결**
db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="products",
    charset="utf8mb4"
)
cursor = db.cursor()

# **🔹 CSV 파일 로드**
csv_file_path = "./gs25_pb_food_by_category_modified.csv"
df = pd.read_csv(csv_file_path)

# **🔹 컬럼명을 DB 컬럼에 맞게 변경**
df = df.rename(columns={
    'category': 'product_category_name',
    'title': 'product_name',
    'price': 'product_price',
    'img_url': 'product_image_url'
})

# **🔹 필요한 컬럼만 선택**
df = df[['product_category_name', 'product_name', 'product_price', 'product_image_url']]

# **🔹 고정값 추가**
# df['product_category_name'] = '음료'
df['convenient_store_name'] = 2  # GS25 편의점 코드

# **🔹 SQL INSERT 문 (중복 방지: ON DUPLICATE KEY UPDATE)**
sql = """
    INSERT INTO convenient_store_products (product_name, product_category_name, convenient_store_name, product_price, product_image_url, updated_at)
    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON DUPLICATE KEY UPDATE 
        product_price = VALUES(product_price),
        product_image_url = VALUES(product_image_url),
        updated_at = CURRENT_TIMESTAMP;
"""

# **🔹 데이터 삽입**
inserted_count = 0
for _, row in df.iterrows():
    try:
        cursor.execute(sql, (row['product_name'], row['product_category_name'], row['convenient_store_name'], row['product_price'], row['product_image_url']))
        db.commit()
        inserted_count += 1
    except Exception as e:
        print(f"⚠️ SQL 저장 오류: {e} (데이터: {row['product_name']})")

# **🔹 최종 결과 출력**
print(f"\n🛠️ 총 {inserted_count}개의 제품이 DB에 저장됨.")

# **🔹 MySQL 연결 종료**
cursor.close()
db.close()
