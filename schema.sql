DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    image TEXT,
    specs TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    comment TEXT,
    items TEXT NOT NULL,
    total_price REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categories (name, parent_id) VALUES
('Страйкбольна зброя', NULL),
('Приводи та внутрішні деталі', NULL),
('Зовнішні аксесуари', NULL),
('Спорядження', NULL),
('Захист', NULL),
('Одяг', NULL),
('Витратні матеріали', NULL),
('Гранати та піротехніка', NULL),
('Тюнінг та сервіс', NULL),
('Бренди', NULL),
('Товари для новачків', NULL),
('Акційні товари', NULL),
('Популярні товари', NULL),
('Новинки', NULL),
('Уцінені товари', NULL);

INSERT INTO categories (name, parent_id) VALUES
('Автомати (AEG / AEP)', 1),
('Пістолети', 1),
('Снайперські гвинтівки', 1),
('Пістолети-кулемети', 1),
('Дробовики', 1),
('Кулемети', 1),
('Гранатомети', 1),
('Комплекти зброї', 1);

INSERT INTO categories (name, parent_id) VALUES
('Електроприводи', 1),
('Газові (Green Gas / CO₂)', 1),
('Пружинні', 1),
('Для новачків', 1),
('Для досвідчених гравців', 1);

INSERT INTO categories (name, parent_id) VALUES
('Гірбокси', 2),
('Двигуни', 2),
('Шестерні', 2),
('Поршні', 2),
('Циліндри', 2),
('Пружини', 2),
('Хоп-ап камери', 2),
('Хоп-ап гумки', 2),
('Внутрішні стволики', 2),
('MOSFET та електроніка', 2),
('Газові клапани', 2),
('Форсунки', 2);

INSERT INTO categories (name, parent_id) VALUES
('Приціли', 3),
('Лазерні цілевказівники', 3),
('Тактичні ліхтарі', 3),
('Глушники та полум’ягасники', 3),
('Цівки', 3),
('Приклади та рукоятки', 3),
('Магазини та бункери', 3),
('Планки та кріплення', 3);

INSERT INTO categories (name, parent_id) VALUES
('Плитоноски та chest rig', 4),
('Підсумки', 4),
('Тактичні пояси', 4),
('Рюкзаки', 4),
('Гідратори', 4),
('Маски та сітки', 4);

INSERT INTO categories (name, parent_id) VALUES
('Окуляри', 5),
('Захисні маски', 5),
('Шоломи', 5),
('Наколінники та налокітники', 5),
('Тактичні рукавиці', 5);

INSERT INTO categories (name, parent_id) VALUES
('Камуфляжна форма', 6),
('Куртки та штормівки', 6),
('Брюки', 6),
('Берці', 6),
('Головні убори', 6),
('Рукавиці', 6);

INSERT INTO categories (name, parent_id) VALUES
('Кульки BB / BIO / Tracer', 7),
('Газ Green Gas / CO₂', 7),
('Акумулятори NiMH / Li-Po', 7),
('Зарядні пристрої', 7),
('Мастила та обслуговування', 7);

INSERT INTO categories (name, parent_id) VALUES
('Піротехнічні гранати', 8),
('Механічні гранати', 8),
('Димові шашки', 8),
('Флешбенги', 8);

INSERT INTO categories (name, parent_id) VALUES
('Тюнінг-комплекти', 9),
('Апгрейд-комплекти', 9),
('Ремкомплекти', 9),
('Сервісне обслуговування', 9);

INSERT INTO categories (name, parent_id) VALUES
('Tokyo Marui', 10),
('G&G', 10),
('CYMA', 10),
('LCT', 10),
('WE', 10),
('KJW', 10),
('Nuprol', 10),
('E&L', 10),
('ICS', 10);
