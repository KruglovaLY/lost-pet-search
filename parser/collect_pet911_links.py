import csv
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://pet911.ru"
START_URL = "https://pet911.ru/moskva"
OUTPUT_CSV = "data/pet911_links.csv"

MAX_CATS = 50
MAX_DOGS = 50
MAX_PAGES = 15

HEADERS = {
    "User-Agent": "Mozilla/5.0 LostPetSearchStudentProject/1.0"
}


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def detect_animal_type(text: str) -> str | None:
    text_lower = text.lower()

    cat_words = [
        "кошка",
        "кот",
        "котик",
        "котёнок",
        "котенок",
        "кошечка",
    ]

    dog_words = [
        "собака",
        "пёс",
        "пес",
        "щенок",
        "собачка",
    ]

    if any(word in text_lower for word in cat_words):
        return "Кошка"

    if any(word in text_lower for word in dog_words):
        return "Собака"

    return None


def get_page_url(page_number: int) -> str:
    if page_number == 1:
        return START_URL

    # У Pet911 в выдаче есть пагинация.
    # Если формат страницы отличается, ниже можно заменить на нужный вариант.
    return f"{START_URL}?page={page_number}"


def extract_cards_from_page(page_url: str) -> list[dict]:
    response = requests.get(page_url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    results = []

    links = soup.find_all("a")

    for link in links:
        href = link.get("href")
        text = normalize_text(link.get_text(" ", strip=True))

        if not href:
            continue

        if len(text) < 15:
            continue

        animal_type = detect_animal_type(text)

        if animal_type is None:
            continue

        image_tag = link.find("img")

        image_url = ""

        if image_tag is not None:
            image_src = (
                image_tag.get("src")
                or image_tag.get("data-src")
                or image_tag.get("data-lazy-src")
            )

            if image_src:
                image_url = urljoin(BASE_URL, image_src)

        source_url = urljoin(BASE_URL, href)

        results.append(
            {
                "animal_type": animal_type,
                "title": text[:120],
                "description": text,
                "source_url": source_url,
                "image_url": image_url,
                "location": "Москва",
            }
        )

    return results


def save_to_csv(items: list[dict]):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "animal_type",
                "title",
                "description",
                "location",
                "source_url",
                "image_url",
            ],
        )

        writer.writeheader()

        for item in items:
            writer.writerow(item)


def main():
    collected = []
    seen_urls = set()

    cats_count = 0
    dogs_count = 0

    for page_number in range(1, MAX_PAGES + 1):
        if cats_count >= MAX_CATS and dogs_count >= MAX_DOGS:
            break

        page_url = get_page_url(page_number)
        print(f"Читаю страницу: {page_url}")

        try:
            cards = extract_cards_from_page(page_url)
        except Exception as error:
            print(f"Ошибка на странице {page_url}: {error}")
            continue

        for card in cards:
            if card["source_url"] in seen_urls:
                continue

            if card["animal_type"] == "Кошка" and cats_count >= MAX_CATS:
                continue

            if card["animal_type"] == "Собака" and dogs_count >= MAX_DOGS:
                continue

            seen_urls.add(card["source_url"])
            collected.append(card)

            if card["animal_type"] == "Кошка":
                cats_count += 1

            if card["animal_type"] == "Собака":
                dogs_count += 1

            print(
                f"{card['animal_type']}: {card['title'][:60]} | "
                f"кошек={cats_count}, собак={dogs_count}"
            )

        time.sleep(1)

    save_to_csv(collected)

    print("Готово")
    print(f"Кошек собрано: {cats_count}")
    print(f"Собак собрано: {dogs_count}")
    print(f"Файл сохранен: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()