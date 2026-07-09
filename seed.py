import json
import os
from database import SessionLocal, engine
import models

def seed_cars():
    # Сбрасываем и пересоздаем таблицы для обновления схемы
    print("[*] Сброс старой схемы и пересоздание таблиц...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, заполнена ли таблица
        if db.query(models.Car).count() > 0:
            print("[*] База данных уже содержит автомобили. Пропуск.")
            return

        json_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
        if not os.path.exists(json_path):
            print(f"[!] Файл данных {json_path} не найден.")
            return
            
        with open(json_path, "r", encoding="utf-8") as f:
            cars_data = json.load(f)
            
        for car_data in cars_data:
            car = models.Car(
                car_id=car_data["car_id"],
                brand=car_data["brand"],
                title=car_data["title"],
                price=car_data["price"],
                preorder_url=car_data["preorder_url"],
                images=car_data["images"],
                specs=car_data["specs"]
            )
            db.add(car)
            
        db.commit()
        print(f"[+] База данных успешно заполнена. Добавлено {len(cars_data)} автомобилей.")
    except Exception as e:
        db.rollback()
        print(f"[!] Ошибка при автозаполнении БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_cars()
