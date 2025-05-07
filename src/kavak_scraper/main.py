import re
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from kavak_scraper.models import Car


# -------------------- Utilidades --------------------

def parse_price(text: str) -> int | None:
    digits = re.findall(r"\d[\d.]*", text)
    if digits:
        return int(digits[0].replace(".", ""))
    return None


def save_to_json(cars: list[Car], filename: str = "autos.json") -> None:
    data = [car.model_dump() for car in cars]
    Path(filename).write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nSe guardaron {len(cars)} autos en {filename}")


# -------------------- Scraping --------------------

def get_total_pages(page) -> int:
    # Espera a que aparezca la nueva sección de paginación por clase
    page.wait_for_selector(".results_results__pagination__yZaD_", timeout=120000)

    # Selecciona el contenedor de paginación
    pagination = page.query_selector(".results_results__pagination__yZaD_")

    if pagination:
        # Busca todos los elementos que parezcan ser números de página
        page_links = pagination.query_selector_all("a")
        numbers = []

        for link in page_links:
            text = link.inner_text().strip()
            if text.isdigit():
                numbers.append(int(text))

        if numbers:
            return max(numbers)

    return 1  # Valor por defecto si no se encuentra paginación




def extract_cars_from_text(text: str) -> list[Car]:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    blocks = []

    current_block = []
    for line in lines:
        if line.count("•") == 1:
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)

    valid_blocks = [b for b in blocks if len(b) >= 5]
    parsed_cars = []

    for block in valid_blocks:
        try:
            brand, model = [x.strip() for x in block[0].split("•")]

            year_line = block[1]
            year_str, km_str, version, transmission = [x.strip() for x in year_line.split("•")]

            year = int(year_str)
            km = int(km_str.lower().replace("km", "").replace(".", "").strip())

            price_lines = []
            for i, line in enumerate(block):
                if "$" in line and re.search(r"\d", line):
                    price_lines.append(line)
                elif line.strip() == "$" and i + 1 < len(block):
                    next_line = block[i + 1]
                    if re.search(r"\d", next_line):
                        price_lines.append(next_line)

            price_actual = parse_price(price_lines[0]) if price_lines else 0
            price_original = parse_price(price_lines[1]) if len(price_lines) > 1 else None
            print(block)

            # Obtiene ultimo elemnto de block que no contenga los siguientes textos
            location = next(
                (
                    line for line in reversed(block)
                    if not any(x in line for x in [
                        "$", "Bono Financiando", "Nuevo ingreso",
                        "Precio", "¡Promoción!", "Reservado", "Precio Imbatible"
                    ])
                ),
                "Desconocido"
            )

            car = Car(
                brand=brand,
                model=model,
                year=year,
                km=km,
                version=version,
                transmission=transmission,
                price_actual=price_actual,
                price_original=price_original,
                location=location,
            )
            parsed_cars.append(car)

        except Exception as e:
            print("Error al parsear un auto:", e)
            print(block)

    return parsed_cars


# -------------------- Ejecución principal --------------------

def main():
    all_cars = []

    proxy_config = {
        "server": "http://brd.superproxy.io:33335",
        "username": "brd-customer-hl_1bde1bb4-zone-residential_proxy1-country-cl",
        "password": "www0ye7kbgs9"
    }



    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=["--ignore-certificate-errors"]
            )
        page = browser.new_page()

        # Página inicial para conocer el total
        page.goto("https://www.kavak.com/cl/usados", timeout=120000)
        total_pages = get_total_pages(page)
        print(f"Total de páginas detectadas: {total_pages}")

        for page_num in range(1):
            print(f"Scrapeando página {page_num}...")
            url = f"https://www.kavak.com/cl/usados?page={page_num}"
            page.goto(url, timeout=120000)
            content_xpath = "/html/body/div[1]/main/div/div[1]/section/article/div[3]"
            page.wait_for_selector(f"xpath={content_xpath}", timeout=120000)

            element = page.query_selector(f"xpath={content_xpath}")
            if element:
                raw_text = element.inner_text()
                cars = extract_cars_from_text(raw_text)
                all_cars.extend(cars)
            else:
                print(f"No se encontró el contenedor de autos en la página {page_num}.")

        browser.close()

    for car in all_cars:
        print(f"{car.brand} {car.model} - {car.price_actual:,} CLP")

    save_to_json(all_cars)


if __name__ == "__main__":
    main()
