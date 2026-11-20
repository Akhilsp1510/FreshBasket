"""
Management command: seed_data
Loads sample grocery categories, products, images, and inventory data.

Safe to re-run: will not overwrite existing user or order records.

Usage:
  python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from products.models import Category, Product, SubstituteGroup, SubstituteGroupItem
from inventory.models import Inventory


CATEGORIES = [
    {'name': 'Fruits & Vegetables', 'icon': 'bi-apple', 'sort_order': 1,
     'image': 'categories/cat_fruits_veggies.jpg',
     'description': 'Fresh farm-picked fruits and seasonal vegetables'},
    {'name': 'Dairy & Eggs', 'icon': 'bi-egg-fried', 'sort_order': 2,
     'image': 'categories/cat_dairy.jpg',
     'description': 'Milk, curd, cheese, paneer, butter and fresh eggs'},
    {'name': 'Grains & Pulses', 'icon': 'bi-moisture', 'sort_order': 3,
     'image': 'categories/cat_grains.jpg',
     'description': 'Rice, wheat, lentils, chickpeas and more'},
    {'name': 'Beverages', 'icon': 'bi-cup-hot', 'sort_order': 4,
     'image': 'categories/cat_beverages.jpg',
     'description': 'Tea, coffee, juices and cold drinks'},
    {'name': 'Snacks & Sweets', 'icon': 'bi-stars', 'sort_order': 5,
     'image': 'categories/cat_snacks.jpg',
     'description': 'Biscuits, namkeen, chocolates and Indian sweets'},
    {'name': 'Spices & Condiments', 'icon': 'bi-fire', 'sort_order': 6,
     'image': 'categories/cat_spices.jpg',
     'description': 'Masalas, pickles, oils and sauces'},
    {'name': 'Bakery', 'icon': 'bi-bucket', 'sort_order': 7,
     'image': 'categories/cat_bakery.jpg',
     'description': 'Fresh bread, pav, cookies and cakes'},
    {'name': 'Personal Care', 'icon': 'bi-heart', 'sort_order': 8,
     'image': 'categories/cat_personal_care.jpg',
     'description': 'Soap, shampoo, toothpaste and hygiene products'},
]

PRODUCTS = [
    # Fruits & Vegetables
    {'cat': 'Fruits & Vegetables', 'name': 'Tomatoes', 'price': '30.00', 'unit': 'kg', 'qty': 1, 'stock': 50, 'threshold': 10, 'featured': True, 'desc': 'Fresh red tomatoes, handpicked daily from farms.', 'brand': 'Farm Fresh', 'image': 'products/tomatoes.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Onions', 'price': '25.00', 'unit': 'kg', 'qty': 1, 'stock': 80, 'threshold': 15, 'featured': False, 'desc': 'Premium quality red onions, dried and cleaned.', 'brand': 'Farm Fresh', 'image': 'products/onions.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Potatoes', 'price': '20.00', 'unit': 'kg', 'qty': 1, 'stock': 100, 'threshold': 20, 'featured': False, 'desc': 'Freshly harvested potatoes, ideal for everyday curries.', 'brand': 'Farm Fresh', 'image': 'products/potatoes.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Bananas', 'price': '40.00', 'unit': 'dozen', 'qty': 12, 'stock': 30, 'threshold': 8, 'featured': True, 'desc': 'Ripe sweet bananas, rich in potassium and energy.', 'brand': 'Fresh Valley', 'image': 'products/bananas.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Apples (Shimla)', 'price': '180.00', 'unit': 'kg', 'qty': 1, 'stock': 25, 'threshold': 5, 'featured': True, 'desc': 'Crisp and sweet Shimla apples from Himachal Pradesh orchards.', 'brand': 'Hills Organic', 'image': 'products/apples.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Spinach (Palak)', 'price': '15.00', 'unit': 'pcs', 'qty': 1, 'stock': 40, 'threshold': 10, 'featured': False, 'desc': 'Fresh tender green spinach bundle, cleaned and sorted.', 'brand': 'Farm Fresh', 'image': 'products/spinach.jpg'},
    {'cat': 'Fruits & Vegetables', 'name': 'Carrots', 'price': '35.00', 'unit': 'kg', 'qty': 1, 'stock': 45, 'threshold': 10, 'featured': False, 'desc': 'Fresh juicy orange carrots, great for salads and cooking.', 'brand': 'Fresh Valley', 'image': 'products/carrots.jpg'},
    # Dairy & Eggs
    {'cat': 'Dairy & Eggs', 'name': 'Amul Full Cream Milk', 'price': '68.00', 'unit': 'L', 'qty': 1, 'stock': 60, 'threshold': 15, 'featured': True, 'desc': 'Pasteurized fresh full cream milk with 6% fat, 1 litre.', 'brand': 'Amul', 'image': 'products/amul_milk.jpg'},
    {'cat': 'Dairy & Eggs', 'name': 'Mother Dairy Toned Milk', 'price': '54.00', 'unit': 'L', 'qty': 1, 'stock': 50, 'threshold': 10, 'featured': False, 'desc': 'Toned milk with 3% fat, fortified with vitamins A & D, 1 litre.', 'brand': 'Mother Dairy', 'image': 'products/mother_dairy_milk.jpg'},
    {'cat': 'Dairy & Eggs', 'name': 'Amul Butter', 'price': '56.00', 'unit': 'g', 'qty': 100, 'stock': 35, 'threshold': 8, 'featured': True, 'desc': 'The classic taste of India! Pasteurised salted table butter, 100g.', 'brand': 'Amul', 'image': 'products/butter.jpg'},
    {'cat': 'Dairy & Eggs', 'name': 'Amul Paneer', 'price': '90.00', 'unit': 'g', 'qty': 200, 'stock': 25, 'threshold': 5, 'featured': True, 'desc': 'Fresh, soft cottage cheese block, high in protein, 200g.', 'brand': 'Amul', 'image': 'products/paneer.jpg'},
    {'cat': 'Dairy & Eggs', 'name': 'Eggs (White)', 'price': '72.00', 'unit': 'dozen', 'qty': 12, 'stock': 40, 'threshold': 10, 'featured': False, 'desc': 'Farm fresh white eggs, pack of 12.', 'brand': 'Farm Fresh', 'image': 'products/eggs.jpg'},
    {'cat': 'Dairy & Eggs', 'name': 'Curd (Dahi)', 'price': '45.00', 'unit': 'g', 'qty': 400, 'stock': 30, 'threshold': 8, 'featured': False, 'desc': 'Thick and creamy set curd, made from pure milk, 400g.', 'brand': 'Amul', 'image': 'products/curd.jpg'},
    # Grains & Pulses
    {'cat': 'Grains & Pulses', 'name': 'Basmati Rice (Premium)', 'price': '120.00', 'unit': 'kg', 'qty': 1, 'stock': 70, 'threshold': 15, 'featured': True, 'desc': 'Aromatic aged long grain basmati rice for daily meals.', 'brand': 'India Gate', 'image': 'products/basmati_rice.jpg'},
    {'cat': 'Grains & Pulses', 'name': 'Toor Dal (Split Pigeon Peas)', 'price': '140.00', 'unit': 'kg', 'qty': 1, 'stock': 55, 'threshold': 10, 'featured': False, 'desc': 'Unpolished high-protein toor dal, 1kg pack.', 'brand': 'Tata Sampann', 'image': 'products/toor_dal.jpg'},
    {'cat': 'Grains & Pulses', 'name': 'Wheat Flour (Atta)', 'price': '55.00', 'unit': 'kg', 'qty': 5, 'stock': 40, 'threshold': 10, 'featured': False, 'desc': '100% whole wheat chakki atta for soft rotis, 5kg.', 'brand': 'Aashirvaad', 'image': 'products/atta.jpg'},
    {'cat': 'Grains & Pulses', 'name': 'Chana Dal (Split Chickpeas)', 'price': '110.00', 'unit': 'kg', 'qty': 1, 'stock': 35, 'threshold': 8, 'featured': False, 'desc': 'Clean split chickpeas dal, rich in dietary fiber.', 'brand': 'Tata Sampann', 'image': 'products/chana_dal.jpg'},
    {'cat': 'Grains & Pulses', 'name': 'Poha (Flattened Rice)', 'price': '45.00', 'unit': 'kg', 'qty': 1, 'stock': 30, 'threshold': 8, 'featured': False, 'desc': 'Medium thick flattened rice flakes, quick breakfast staple.', 'brand': 'Nature Fresh', 'image': 'products/poha.jpg'},
    # Beverages
    {'cat': 'Beverages', 'name': 'Tata Tea Gold', 'price': '185.00', 'unit': 'g', 'qty': 250, 'stock': 45, 'threshold': 10, 'featured': True, 'desc': 'Exquisite blend of Assam CTC tea with gently rolled Darjeeling leaves.', 'brand': 'Tata Tea', 'image': 'products/tea.jpg'},
    {'cat': 'Beverages', 'name': 'Nescafe Classic Coffee', 'price': '230.00', 'unit': 'g', 'qty': 100, 'stock': 30, 'threshold': 8, 'featured': True, 'desc': '100% pure instant coffee granules with rich aroma, 100g jar.', 'brand': 'Nescafe', 'image': 'products/coffee.jpg'},
    {'cat': 'Beverages', 'name': 'Real Fruit Juice (Mango)', 'price': '90.00', 'unit': 'ml', 'qty': 1000, 'stock': 40, 'threshold': 10, 'featured': False, 'desc': 'Delicious mango fruit beverage, no added preservatives, 1 litre.', 'brand': 'Dabur Real', 'image': 'products/mango_juice.jpg'},
    {'cat': 'Beverages', 'name': 'Bournvita', 'price': '210.00', 'unit': 'g', 'qty': 400, 'stock': 25, 'threshold': 5, 'featured': False, 'desc': 'Nutritional chocolate health malt drink powder, 400g.', 'brand': 'Cadbury', 'image': 'products/bournvita.jpg'},
    # Snacks & Sweets
    {'cat': 'Snacks & Sweets', 'name': 'Haldirams Aloo Bhujia', 'price': '50.00', 'unit': 'g', 'qty': 200, 'stock': 50, 'threshold': 10, 'featured': True, 'desc': 'Crispy, spicy potato bhujia namkeen snack, 200g.', 'brand': 'Haldirams', 'image': 'products/aloo_bhujia.jpg'},
    {'cat': 'Snacks & Sweets', 'name': 'Parle-G Biscuits', 'price': '10.00', 'unit': 'g', 'qty': 100, 'stock': 80, 'threshold': 20, 'featured': False, 'desc': 'The iconic Indian glucose biscuit, 100g pack.', 'brand': 'Parle', 'image': 'products/biscuits.jpg'},
    {'cat': 'Snacks & Sweets', 'name': 'Lays Classic Salted', 'price': '20.00', 'unit': 'g', 'qty': 55, 'stock': 60, 'threshold': 15, 'featured': False, 'desc': 'Crispy potato chips seasoned with fine salt, 55g.', 'brand': "Lay's", 'image': 'products/lays_chips.jpg'},
    {'cat': 'Snacks & Sweets', 'name': 'Dairy Milk Chocolate', 'price': '50.00', 'unit': 'g', 'qty': 55, 'stock': 45, 'threshold': 10, 'featured': True, 'desc': 'Creamy smooth milk chocolate bar, 55g.', 'brand': 'Cadbury', 'image': 'products/chocolate.jpg'},
    # Spices & Condiments
    {'cat': 'Spices & Condiments', 'name': 'MDH Garam Masala', 'price': '65.00', 'unit': 'g', 'qty': 100, 'stock': 35, 'threshold': 8, 'featured': False, 'desc': 'Aromatic Indian blend of roasted ground spices, 100g.', 'brand': 'MDH', 'image': 'products/garam_masala.jpg'},
    {'cat': 'Spices & Condiments', 'name': 'Fortune Sunflower Oil', 'price': '170.00', 'unit': 'L', 'qty': 1, 'stock': 40, 'threshold': 10, 'featured': True, 'desc': 'Light and healthy refined sunflower cooking oil, 1 litre pouch.', 'brand': 'Fortune', 'image': 'products/sunflower_oil.jpg'},
    {'cat': 'Spices & Condiments', 'name': 'Maggi Tomato Ketchup', 'price': '78.00', 'unit': 'g', 'qty': 500, 'stock': 30, 'threshold': 8, 'featured': False, 'desc': 'Rich, tangy tomato ketchup, easy squeeze bottle 500g.', 'brand': 'Maggi', 'image': 'products/ketchup.jpg'},
    {'cat': 'Spices & Condiments', 'name': 'Everest Turmeric Powder', 'price': '55.00', 'unit': 'g', 'qty': 100, 'stock': 50, 'threshold': 10, 'featured': False, 'desc': 'Pure natural golden haldi powder for rich color, 100g.', 'brand': 'Everest', 'image': 'products/turmeric.jpg'},
    # Bakery
    {'cat': 'Bakery', 'name': 'Britannia Bread (White)', 'price': '40.00', 'unit': 'g', 'qty': 400, 'stock': 25, 'threshold': 5, 'featured': False, 'desc': 'Soft, freshly baked white sandwich bread, 400g.', 'brand': 'Britannia', 'image': 'products/bread.jpg'},
    {'cat': 'Bakery', 'name': 'Pav Buns (8 pieces)', 'price': '30.00', 'unit': 'pcs', 'qty': 8, 'stock': 20, 'threshold': 5, 'featured': False, 'desc': 'Fluffy soft bakery pav buns, pack of 8.', 'brand': 'Local Bakery', 'image': 'products/pav_buns.jpg'},
]


class Command(BaseCommand):
    help = 'Load sample grocery data with realistic images and stock levels.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('Seeding FreshBasket categories and products...'))

        cat_map = {}
        for c in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=c['name'],
                defaults={
                    'icon': c['icon'],
                    'sort_order': c['sort_order'],
                    'description': c['description'],
                    'image': c.get('image', ''),
                    'is_active': True,
                }
            )
            # Ensure image is updated if it was previously empty
            if not cat.image and c.get('image'):
                cat.image = c['image']
                cat.save()
            cat_map[c['name']] = cat
            self.stdout.write(f'  Category: {cat.name}')

        for p in PRODUCTS:
            cat = cat_map.get(p['cat'])
            if not cat:
                continue

            prod, created = Product.objects.get_or_create(
                name=p['name'],
                defaults={
                    'category': cat,
                    'price': p['price'],
                    'unit': p['unit'],
                    'unit_quantity': p['qty'],
                    'low_stock_threshold': p['threshold'],
                    'is_active': True,
                    'is_featured': p.get('featured', False),
                    'description': p.get('desc', ''),
                    'brand': p.get('brand', ''),
                    'image': p.get('image', ''),
                }
            )

            # Ensure image is updated if it was previously empty
            if not prod.image and p.get('image'):
                prod.image = p['image']
                prod.save()

            Inventory.objects.get_or_create(
                product=prod,
                defaults={
                    'physical_stock': p['stock'],
                    'reserved_stock': 0,
                }
            )
            self.stdout.write(f'  Product: {prod.name} -> {prod.image}')

        self.stdout.write(self.style.SUCCESS('✅ Seed data successfully synchronized with real product images!'))
