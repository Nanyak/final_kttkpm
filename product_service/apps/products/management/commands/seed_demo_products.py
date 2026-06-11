from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from slugify import slugify

from apps.products.models import Book, Category, Electronics, Fashion, Product


BASE_IMAGE_URL = 'http://localhost:8000/product-images'
TARGET_PRODUCTS_PER_ROOT = 80


CATEGORY_TREE = {
    'Books': {
        'Software Engineering': {},
        'Data Science': {},
        'Cookbooks': {},
    },
    'Fashion': {
        'Clothing': {},
        'Shoes': {},
        'Bags': {},
    },
    'Electronics': {
        'Technology Devices': {
            'Smartphones': {},
            'Laptops': {},
            'Earbuds': {},
            'Power Banks': {},
            'Speakers': {},
        },
        'Home Appliances': {
            'Cookers': {},
            'Ovens': {},
            'Air Fryers': {},
            'Microwaves': {},
        },
    },
    'Home & Living': {
        'Kitchen & Dining': {},
        'Lighting': {},
        'Storage & Organization': {},
        'Decor': {},
    },
    'Sports & Outdoors': {
        'Fitness': {},
        'Running': {},
        'Cycling': {},
        'Camping': {},
    },
}


PRODUCTS = [
    {
        'category': 'Software Engineering',
        'name': 'Clean Architecture Handbook',
        'description': 'A practical guide for organizing maintainable backend services and frontend boundaries.',
        'base_price': '189000',
        'stock_quantity': 42,
        'image': 'clean-architecture-handbook.svg',
        'book': {
            'author': 'Robert Lane',
            'isbn': '9780000001001',
            'publisher': 'Northstar Press',
            'publication_year': 2024,
            'page_count': 328,
            'language': 'English',
            'genre': 'Software Engineering',
        },
    },
    {
        'category': 'Data Science',
        'name': 'Data Science Field Notes',
        'description': 'Compact lessons on model evaluation, feature engineering, and production analytics.',
        'base_price': '225000',
        'stock_quantity': 35,
        'image': 'data-science-field-notes.svg',
        'book': {
            'author': 'Mina Tran',
            'isbn': '9780000001002',
            'publisher': 'Blue River Books',
            'publication_year': 2025,
            'page_count': 284,
            'language': 'English',
            'genre': 'Data Science',
        },
    },
    {
        'category': 'Cookbooks',
        'name': 'Vietnamese Home Cooking',
        'description': 'Everyday recipes for broths, stir fries, herbs, sauces, and weeknight family meals.',
        'base_price': '159000',
        'stock_quantity': 50,
        'image': 'vietnamese-home-cooking.svg',
        'book': {
            'author': 'Linh Pham',
            'isbn': '9780000001003',
            'publisher': 'Saigon Kitchen',
            'publication_year': 2023,
            'page_count': 216,
            'language': 'Vietnamese',
            'genre': 'Cooking',
        },
    },
    {
        'category': 'Earbuds',
        'name': 'AeroPods Lite Wireless Earbuds',
        'description': 'Lightweight Bluetooth earbuds with clear calls, touch controls, and a compact charging case.',
        'base_price': '690000',
        'stock_quantity': 28,
        'image': 'aeropods-lite.svg',
        'electronics': {
            'brand': 'AeroPods',
            'model_number': 'APL-2026',
            'warranty_period': '12 months',
            'voltage_requirement': '5V USB-C',
            'connectivity': 'Bluetooth 5.3',
            'technical_specs': {'battery_hours': 24, 'water_resistance': 'IPX4'},
        },
    },
    {
        'category': 'Power Banks',
        'name': 'NovaCharge 20000 Power Bank',
        'description': 'High-capacity portable charger with dual USB-C ports and fast charging support.',
        'base_price': '820000',
        'stock_quantity': 31,
        'image': 'novacharge-20000.svg',
        'electronics': {
            'brand': 'NovaCharge',
            'model_number': 'NC20K',
            'warranty_period': '18 months',
            'voltage_requirement': 'USB-C PD 20W',
            'connectivity': 'USB-C, USB-A',
            'technical_specs': {'capacity_mah': 20000, 'ports': 3},
        },
    },
    {
        'category': 'Lighting',
        'name': 'Lumina Desk Lamp Pro',
        'description': 'Adjustable LED desk lamp with dimming, color temperature control, and wireless charging.',
        'base_price': '540000',
        'stock_quantity': 24,
        'image': 'lumina-desk-lamp-pro.svg',
        'electronics': {
            'brand': 'Lumina',
            'model_number': 'LDP-9',
            'warranty_period': '12 months',
            'voltage_requirement': '100-240V',
            'connectivity': 'Qi wireless charging',
            'technical_specs': {'brightness_lumens': 700, 'color_modes': 5},
        },
    },
    {
        'category': 'Speakers',
        'name': 'Orbit Mini Bluetooth Speaker',
        'description': 'Portable speaker with a fabric grille, punchy bass, and all-day battery life.',
        'base_price': '760000',
        'stock_quantity': 18,
        'image': 'orbit-mini-speaker.svg',
        'electronics': {
            'brand': 'Orbit',
            'model_number': 'OMS-5',
            'warranty_period': '12 months',
            'voltage_requirement': '5V USB-C',
            'connectivity': 'Bluetooth 5.2',
            'technical_specs': {'battery_hours': 14, 'driver_watts': 12},
        },
    },
    {
        'category': 'Clothing',
        'name': 'Everyday Cotton Overshirt',
        'description': 'Relaxed cotton overshirt with large pockets and a clean everyday silhouette.',
        'base_price': '430000',
        'stock_quantity': 44,
        'image': 'everyday-cotton-overshirt.svg',
        'fashion': {
            'brand': 'Northline',
            'size': 'M',
            'color': 'Sage Green',
            'material': 'Cotton twill',
            'gender': 'U',
            'season': 'All season',
        },
    },
    {
        'category': 'Shoes',
        'name': 'City Runner Knit Sneakers',
        'description': 'Breathable knit sneakers with cushioned soles for commuting and casual weekends.',
        'base_price': '990000',
        'stock_quantity': 22,
        'image': 'city-runner-knit-sneakers.svg',
        'fashion': {
            'brand': 'Stride',
            'size': '42',
            'color': 'Graphite',
            'material': 'Knit textile and rubber',
            'gender': 'U',
            'season': 'All season',
        },
    },
    {
        'category': 'Bags',
        'name': 'Linen Weekend Tote',
        'description': 'Structured linen tote with reinforced handles and a padded inner pocket.',
        'base_price': '380000',
        'stock_quantity': 39,
        'image': 'linen-weekend-tote.svg',
        'fashion': {
            'brand': 'Atelier Home',
            'size': 'One size',
            'color': 'Natural',
            'material': 'Linen canvas',
            'gender': 'U',
            'season': 'Summer',
        },
    },
    {
        'category': 'Kitchen & Dining',
        'name': 'Ceramic Pour Over Set',
        'description': 'Minimal ceramic coffee dripper with a matching server for slow morning brewing.',
        'base_price': '470000',
        'stock_quantity': 26,
        'image': 'ceramic-pour-over-set.svg',
    },
    {
        'category': 'Storage & Organization',
        'name': 'Bamboo Storage Organizer',
        'description': 'Modular bamboo organizer for desks, cosmetics, stationery, and small home essentials.',
        'base_price': '310000',
        'stock_quantity': 56,
        'image': 'bamboo-storage-organizer.svg',
    },
]


IMAGE_BY_ROOT = {
    'Books': [
        'clean-architecture-handbook.svg',
        'data-science-field-notes.svg',
        'vietnamese-home-cooking.svg',
    ],
    'Fashion': [
        'everyday-cotton-overshirt.svg',
        'city-runner-knit-sneakers.svg',
        'linen-weekend-tote.svg',
    ],
    'Electronics': [
        'aeropods-lite.svg',
        'novacharge-20000.svg',
        'orbit-mini-speaker.svg',
        'lumina-desk-lamp-pro.svg',
    ],
    'Home & Living': [
        'ceramic-pour-over-set.svg',
        'bamboo-storage-organizer.svg',
        'lumina-desk-lamp-pro.svg',
    ],
    'Sports & Outdoors': [
        'city-runner-knit-sneakers.svg',
        'bamboo-storage-organizer.svg',
        'novacharge-20000.svg',
    ],
}


DUMMYJSON_CATEGORY_MAP = {
    'smartphones': 'Smartphones',
    'laptops': 'Laptops',
    'tablets': 'Laptops',
    'mobile-accessories': None,
    'sports-accessories': None,
    'mens-shirts': 'Clothing',
    'tops': 'Clothing',
    'womens-dresses': 'Clothing',
    'mens-shoes': 'Shoes',
    'womens-shoes': 'Shoes',
    'womens-bags': 'Bags',
    'mens-watches': 'Clothing',
    'womens-watches': 'Clothing',
    'sunglasses': 'Clothing',
    'womens-jewellery': 'Bags',
    'furniture': 'Decor',
    'home-decoration': 'Decor',
    'kitchen-accessories': 'Kitchen & Dining',
    'groceries': 'Kitchen & Dining',
}


OPEN_LIBRARY_SUBJECTS = {
    'Software Engineering': ['software', 'computer_science'],
    'Data Science': ['data_science', 'statistics'],
    'Cookbooks': ['cooking', 'cookery'],
}


CURATED_NAMES = {
    'Software Engineering': ['Clean Code', 'Design Patterns', 'Refactoring', 'Domain-Driven Design', 'The Pragmatic Programmer', 'Building Microservices', 'Release It!', 'Accelerate'],
    'Data Science': ['Hands-On Machine Learning', 'Python for Data Analysis', 'Designing Data-Intensive Applications', 'Practical Statistics for Data Scientists', 'Deep Learning with Python', 'Storytelling with Data', 'Data Science from Scratch'],
    'Cookbooks': ['Salt Fat Acid Heat', 'The Food Lab', 'The Wok', 'Vietnamese Food Any Day', 'Ottolenghi Simple', 'Mastering the Art of French Cooking', 'The Flavor Bible'],
    'Smartphones': ['iPhone 15 Pro', 'Samsung Galaxy S24 Ultra', 'Google Pixel 8 Pro', 'Xiaomi 14', 'OnePlus 12', 'OPPO Find X7', 'Vivo V30 Pro', 'Nothing Phone 2', 'Sony Xperia 1 V', 'Motorola Edge 50 Pro'],
    'Laptops': ['MacBook Air 13 M3', 'Dell XPS 15', 'Lenovo ThinkPad X1 Carbon', 'ASUS Zenbook 14 OLED', 'HP Spectre x360 14', 'Acer Swift Go 14', 'Microsoft Surface Laptop 6', 'LG Gram 16', 'MSI Prestige 14', 'Razer Blade 14'],
    'Earbuds': ['AirPods Pro 2', 'Sony WF-1000XM5', 'Samsung Galaxy Buds2 Pro', 'Bose QuietComfort Ultra Earbuds', 'Jabra Elite 10', 'Beats Studio Buds Plus', 'Nothing Ear 2', 'Anker Soundcore Liberty 4 NC'],
    'Power Banks': ['Anker 737 Power Bank', 'UGREEN Nexode 20000mAh', 'Belkin BoostCharge 20K', 'Baseus Blade 100W', 'Xiaomi Power Bank 20000', 'Zendure SuperMini X3'],
    'Speakers': ['JBL Flip 6', 'Bose SoundLink Flex', 'Sony SRS-XB100', 'Marshall Emberton II', 'Ultimate Ears Boom 3', 'Sonos Roam SL'],
    'Cookers': ['Instant Pot Duo 7-in-1', 'Zojirushi Neuro Fuzzy Rice Cooker', 'Cuckoo CRP-P1009S Pressure Rice Cooker', 'Tefal RK732 Rice Cooker', 'Panasonic SR-CN188 Rice Cooker'],
    'Ovens': ['Breville Smart Oven Air Fryer Pro', 'Panasonic FlashXpress Toaster Oven', 'KitchenAid Digital Countertop Oven', 'Sharp Superheated Steam Oven', 'Toshiba Convection Toaster Oven'],
    'Air Fryers': ['Philips Premium Airfryer XXL', 'Ninja Foodi DualZone Air Fryer', 'Cosori TurboBlaze Air Fryer', 'Instant Vortex Plus Air Fryer', 'Tefal Easy Fry Grill & Steam'],
    'Microwaves': ['Panasonic Inverter Microwave NN-SN966S', 'Toshiba Smart Sensor Microwave', 'Samsung Bespoke Microwave', 'LG NeoChef Microwave', 'Sharp Carousel Microwave'],
    'Clothing': ['Uniqlo Oxford Shirt', 'Levi’s 501 Original Jeans', 'Patagonia Better Sweater Fleece', 'Nike Sportswear Club Hoodie', 'Adidas Adicolor Classics Tee', 'Muji French Linen Shirt'],
    'Shoes': ['Nike Air Max 270', 'Adidas Ultraboost Light', 'New Balance 574 Core', 'Converse Chuck 70 High Top', 'Vans Old Skool', 'On Cloud 5', 'ASICS Gel-Kayano 30'],
    'Bags': ['Herschel Little America Backpack', 'Fjallraven Kanken Backpack', 'Bellroy Tokyo Tote', 'Longchamp Le Pliage Tote', 'Peak Design Everyday Sling', 'Eastpak Padded Pak’r'],
    'Kitchen & Dining': ['Hario V60 Dripper Set', 'Bodum Chambord French Press', 'Lodge Cast Iron Skillet', 'Zwilling Pro Chef Knife', 'Joseph Joseph Nest Bowls', 'OXO Good Grips Salad Spinner'],
    'Lighting': ['Philips Hue White Ambiance Starter Kit', 'BenQ ScreenBar Monitor Light', 'IKEA Tertial Work Lamp', 'Dyson Solarcycle Morph Desk Light', 'Nanoleaf Shapes Starter Kit'],
    'Storage & Organization': ['IKEA Kallax Shelf Unit', 'Yamazaki Tower Storage Rack', 'Muji Polypropylene Storage Drawer', 'OXO Pop Container Set', 'Umbra Cubiko Wall Organizer'],
    'Decor': ['IKEA Stockholm Rug', 'HAY Colour Crate', 'Umbra Prisma Wall Decor', 'Yamazaki Rin Side Table', 'West Elm Ceramic Vase', 'Muji Aroma Diffuser'],
    'Fitness': ['Manduka PRO Yoga Mat', 'Bowflex SelectTech 552 Dumbbells', 'TRX All-in-One Suspension Trainer', 'Theragun Mini', 'Fitbit Charge 6', 'Garmin Venu 3'],
    'Running': ['Garmin Forerunner 265', 'Nike Pegasus 40', 'ASICS Novablast 4', 'Salomon Active Skin 8 Vest', 'Nathan QuickSqueeze Bottle', 'Goodr OG Sunglasses'],
    'Cycling': ['Garmin Edge 840', 'Wahoo ELEMNT Bolt V2', 'Giro Syntax MIPS Helmet', 'Lezyne Micro Drive 800XL', 'Topeak JoeBlow Sport III Pump', 'Kryptonite Evolution Mini-7 Lock'],
    'Camping': ['Coleman Skydome Tent', 'MSR PocketRocket 2 Stove', 'Therm-a-Rest NeoAir XLite', 'Black Diamond Spot 400 Headlamp', 'YETI Rambler 26 oz Bottle', 'Sea to Summit Dry Bag'],
}


def _walk_tree(tree, root=None):
    for name, children in tree.items():
        current_root = root or name
        yield name, current_root, children
        yield from _walk_tree(children, current_root)


def _leaf_categories_by_root():
    leaves = {root: [] for root in CATEGORY_TREE}
    for name, root, children in _walk_tree(CATEGORY_TREE):
        if not children:
            leaves[root].append(name)
    return leaves


def _root_by_category():
    return {name: root for name, root, _ in _walk_tree(CATEGORY_TREE)}


class Command(BaseCommand):
    help = 'Seed demo product categories, products, subtype details, and image URLs.'

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        self._seed_categories(CATEGORY_TREE, categories=categories)
        self._deactivate_legacy_categories()

        products = self._expanded_products()
        created = 0
        updated = 0
        for item in products:
            subtype_keys = {'book', 'electronics', 'fashion'}
            product_data = {key: value for key, value in item.items() if key not in subtype_keys | {'category', 'image'}}
            product_slug = self._product_slug(item['name'])
            product, was_created = Product.objects.update_or_create(
                slug=product_slug,
                defaults={
                    **product_data,
                    'name': item['name'],
                    'base_price': Decimal(item['base_price']),
                    'category': categories[item['category']],
                    'image_url': f'{BASE_IMAGE_URL}/{item["image"]}',
                    'is_active': True,
                },
            )
            created += int(was_created)
            updated += int(not was_created)

            if 'book' in item:
                Book.objects.update_or_create(
                    isbn=item['book']['isbn'],
                    defaults={**item['book'], 'product': product},
                )
            if 'electronics' in item:
                Electronics.objects.update_or_create(product=product, defaults=item['electronics'])
            if 'fashion' in item:
                Fashion.objects.update_or_create(product=product, defaults=item['fashion'])

        self._deactivate_legacy_catalog(products)
        self.stdout.write(self.style.SUCCESS(
            f'Seeded demo products: {created} created, {updated} updated, {len(products)} total.'
        ))

    def _seed_categories(self, tree, categories, parent=None):
        for name, children in tree.items():
            category, _ = Category.objects.update_or_create(
                name=name,
                defaults={
                    'parent': parent,
                    'description': f'Demo {name.lower()} category',
                    'is_active': True,
                },
            )
            categories[name] = category
            self._seed_categories(children, categories=categories, parent=category)

    def _deactivate_legacy_categories(self):
        current_names = {name for name, _, _ in _walk_tree(CATEGORY_TREE)}
        Category.objects.exclude(name__in=current_names).update(is_active=False)

    def _deactivate_legacy_catalog(self, products):
        current_slugs = {self._product_slug(item['name']) for item in products}
        Product.objects.exclude(slug__in=current_slugs).update(is_active=False)

    def _expanded_products(self):
        root_for_category = _root_by_category()
        leaves_by_root = _leaf_categories_by_root()
        products = self._dedupe_products(list(PRODUCTS) + self._load_external_products())

        counts = {root: 0 for root in CATEGORY_TREE}
        for item in products:
            root = root_for_category.get(item['category'])
            if root:
                counts[root] += 1

        seen = {item['name'].strip().lower() for item in products}
        for root, leaves in leaves_by_root.items():
            sequence = 1
            while counts[root] < TARGET_PRODUCTS_PER_ROOT:
                category = leaves[counts[root] % len(leaves)]
                product = self._generated_product(root, category, sequence)
                sequence += 1
                key = product['name'].strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                products.append(product)
                counts[root] += 1

        return products

    def _dedupe_products(self, products):
        seen = set()
        result = []
        root_for_category = _root_by_category()
        counts = {root: 0 for root in CATEGORY_TREE}
        for item in products:
            if item['category'] not in root_for_category:
                continue
            root = root_for_category[item['category']]
            if counts[root] >= TARGET_PRODUCTS_PER_ROOT:
                continue
            key = item['name'].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            counts[root] += 1
            result.append(item)
        return result

    def _load_external_products(self):
        products = []
        try:
            products.extend(self._load_open_library_books())
        except Exception as exc:
            self.stderr.write(f'Open Library product fetch skipped: {exc}')
        try:
            products.extend(self._load_dummyjson_products())
        except Exception as exc:
            self.stderr.write(f'DummyJSON product fetch skipped: {exc}')
        if products:
            self.stdout.write(f'Loaded {len(products)} external catalog products.')
        return products

    def _load_dummyjson_products(self):
        import requests

        response = requests.get('https://dummyjson.com/products', params={'limit': 0}, timeout=15)
        response.raise_for_status()
        data = response.json()
        products = []
        for row in data.get('products', []):
            category = self._map_dummyjson_category(row)
            if not category:
                continue
            root = _root_by_category()[category]
            item = {
                'category': category,
                'name': row.get('title', '').strip(),
                'description': row.get('description') or f'{row.get("title")} from DummyJSON catalog data.',
                'base_price': str(max(49000, int(float(row.get('price') or 0) * 25000))),
                'stock_quantity': int(row.get('stock') or 25),
                'image': IMAGE_BY_ROOT[root][int(row.get('id', 1)) % len(IMAGE_BY_ROOT[root])],
            }
            if root == 'Electronics':
                brand = row.get('brand') or item['name'].split()[0]
                item['electronics'] = {
                    'brand': brand[:100],
                    'model_number': (row.get('sku') or f'DJ-{row.get("id", 0)}')[:100],
                    'warranty_period': row.get('warrantyInformation') or '12 months',
                    'voltage_requirement': '5V USB-C' if category in {'Earbuds', 'Power Banks', 'Speakers'} else '100-240V',
                    'connectivity': self._connectivity(category),
                    'technical_specs': {
                        'rating': row.get('rating'),
                        'source_category': row.get('category'),
                        'source': 'dummyjson',
                    },
                }
            elif root == 'Fashion':
                item['fashion'] = {
                    'brand': (row.get('brand') or item['name'].split()[0])[:100],
                    'size': 'One size',
                    'color': 'Assorted',
                    'material': 'Mixed materials',
                    'gender': 'U',
                    'season': 'All season',
                }
            products.append(item)
        return products

    def _map_dummyjson_category(self, row):
        source = row.get('category')
        mapped = DUMMYJSON_CATEGORY_MAP.get(source)
        if mapped:
            return mapped
        title = row.get('title', '').lower()
        if source == 'mobile-accessories':
            if any(word in title for word in ['charger', 'power', 'bank']):
                return 'Power Banks'
            if any(word in title for word in ['speaker', 'sound']):
                return 'Speakers'
            return 'Earbuds'
        if source == 'sports-accessories':
            if any(word in title for word in ['bike', 'cycle', 'helmet']):
                return 'Cycling'
            if any(word in title for word in ['shoe', 'run']):
                return 'Running'
            if any(word in title for word in ['ball', 'mat', 'yoga', 'fitness']):
                return 'Fitness'
            return 'Camping'
        return None

    def _load_open_library_books(self):
        import requests

        products = []
        for category, subjects in OPEN_LIBRARY_SUBJECTS.items():
            for subject in subjects:
                response = requests.get(
                    f'https://openlibrary.org/subjects/{subject}.json',
                    params={'limit': 35},
                    timeout=15,
                    headers={'User-Agent': 'final-kttkpm-demo-seeder/1.0'},
                )
                response.raise_for_status()
                for work in response.json().get('works', []):
                    title = work.get('title')
                    if not title:
                        continue
                    authors = work.get('authors') or []
                    author = authors[0].get('name') if authors else 'Open Library'
                    year = int(work.get('first_publish_year') or 2020)
                    stable = self._stable_number(f'{title}-{author}', 10**9)
                    products.append({
                        'category': category,
                        'name': title[:255],
                        'description': f'{title} by {author}, listed in Open Library subject data for {subject.replace("_", " ")}.',
                        'base_price': str(99000 + stable % 260000),
                        'stock_quantity': 10 + stable % 80,
                        'image': IMAGE_BY_ROOT['Books'][stable % len(IMAGE_BY_ROOT['Books'])],
                        'book': {
                            'author': author[:255],
                            'isbn': f'9788{stable:09d}'[:13],
                            'publisher': 'Open Library',
                            'publication_year': max(1900, min(year, 2026)),
                            'page_count': 120 + stable % 620,
                            'language': 'English',
                            'genre': category,
                        },
                    })
        return products

    def _generated_product(self, root, category, sequence):
        image_pool = IMAGE_BY_ROOT[root]
        image = image_pool[(sequence - 1) % len(image_pool)]
        base = {
            'category': category,
                'name': self._product_name(category, sequence),
            'description': self._description(root, category, sequence),
            'base_price': str(self._price(root, sequence)),
            'stock_quantity': 12 + (sequence * 7) % 89,
            'image': image,
        }

        if root == 'Books':
            base['book'] = {
                'author': ['Martin Fowler', 'Robert C. Martin', 'Aurélien Géron', 'Julia Child', 'Samin Nosrat'][sequence % 5],
                'isbn': f'9787{self._stable_number(base["name"], 10**9):09d}'[:13],
                'publisher': ['Northstar Press', 'Blue River Books', 'Saigon Kitchen'][sequence % 3],
                'publication_year': 2020 + sequence % 7,
                'page_count': 160 + sequence % 420,
                'language': 'English' if sequence % 3 else 'Vietnamese',
                'genre': category,
            }
        elif root == 'Fashion':
            base['fashion'] = {
                'brand': ['Northline', 'Stride', 'Atelier Home', 'Urban Loom'][sequence % 4],
                'size': ['S', 'M', 'L', 'XL', '42', 'One size'][sequence % 6],
                'color': ['Black', 'White', 'Graphite', 'Sage Green', 'Natural'][sequence % 5],
                'material': ['Cotton', 'Linen', 'Knit textile', 'Canvas', 'Recycled polyester'][sequence % 5],
                'gender': ['U', 'M', 'F'][sequence % 3],
                'season': ['All season', 'Summer', 'Winter'][sequence % 3],
            }
        elif root == 'Electronics':
            brand = ['AeroPods', 'NovaCharge', 'Orbit', 'Lumina', 'TechNova'][sequence % 5]
            base['electronics'] = {
                'brand': brand,
                'model_number': f'{brand[:3].upper()}-{category[:3].upper()}-{sequence:03d}',
                'warranty_period': f'{12 + sequence % 3 * 6} months',
                'voltage_requirement': '5V USB-C' if category in {'Earbuds', 'Power Banks', 'Speakers'} else '100-240V',
                'connectivity': self._connectivity(category),
                'technical_specs': self._technical_specs(category, sequence),
            }

        return base

    def _product_name(self, category, sequence):
        names = CURATED_NAMES[category]
        name = names[(sequence - 1) % len(names)]
        variant = ['Black', 'White', 'Blue', 'Silver', 'Green', 'Graphite', 'Navy', 'Natural'][(sequence - 1) // len(names) % 8]
        return name if sequence <= len(names) else f'{name} - {variant}'

    def _description(self, root, category, sequence):
        return (
            f'{category} item from the {root} catalog, prepared for demo browsing, '
            f'search, recommendation, and RAG retrieval scenarios.'
        )

    def _stable_number(self, value, modulo):
        total = 0
        for char in value:
            total = (total * 131 + ord(char)) % modulo
        return total

    def _product_slug(self, name):
        return f'{slugify(name)[:220]}-{self._stable_number(name.lower(), 10**8):08d}'

    def _price(self, root, sequence):
        ranges = {
            'Books': (99000, 420000),
            'Fashion': (180000, 1800000),
            'Electronics': (450000, 32000000),
            'Home & Living': (120000, 5200000),
            'Sports & Outdoors': (150000, 8500000),
        }
        low, high = ranges[root]
        step = ((sequence * 7919) % (high - low)) // 1000 * 1000
        return low + step

    def _connectivity(self, category):
        if category in {'Smartphones', 'Laptops'}:
            return 'WiFi, Bluetooth, USB-C'
        if category in {'Earbuds', 'Speakers'}:
            return 'Bluetooth 5.3'
        if category == 'Power Banks':
            return 'USB-C, USB-A'
        return 'Standard power'

    def _technical_specs(self, category, sequence):
        if category == 'Smartphones':
            return {'storage_gb': 128 + (sequence % 4) * 128, 'battery_mah': 4200 + sequence % 8 * 150}
        if category == 'Laptops':
            return {'ram_gb': 8 + (sequence % 4) * 8, 'storage_gb': 256 + (sequence % 4) * 256}
        if category == 'Earbuds':
            return {'battery_hours': 18 + sequence % 18, 'water_resistance': 'IPX4'}
        if category == 'Power Banks':
            return {'capacity_mah': 10000 + (sequence % 4) * 5000, 'ports': 2 + sequence % 3}
        if category == 'Speakers':
            return {'battery_hours': 10 + sequence % 14, 'driver_watts': 8 + sequence % 20}
        if category in {'Cookers', 'Ovens', 'Air Fryers', 'Microwaves'}:
            return {'capacity_liters': 3 + sequence % 32, 'power_watts': 700 + sequence % 14 * 100}
        return {'variant': sequence}
