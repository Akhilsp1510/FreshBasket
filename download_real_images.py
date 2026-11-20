"""
Script to download real, high-resolution product and category images
for the Blinkit-style UI/UX overhaul of FreshBasket.
"""
import os
import sys
import urllib.request
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freshbasket.settings')
django.setup()

from products.models import Product, Category

PRODUCT_IMAGES = {
    'Tomatoes': {
        'file': 'tomatoes.jpg',
        'url': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80',
    },
    'Onions': {
        'file': 'onions.jpg',
        'url': 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=600&auto=format&fit=crop&q=80',
    },
    'Potatoes': {
        'file': 'potatoes.jpg',
        'url': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600&auto=format&fit=crop&q=80',
    },
    'Bananas': {
        'file': 'bananas.jpg',
        'url': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600&auto=format&fit=crop&q=80',
    },
    'Apples (Shimla)': {
        'file': 'apples.jpg',
        'url': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80',
    },
    'Spinach (Palak)': {
        'file': 'spinach.jpg',
        'url': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&auto=format&fit=crop&q=80',
    },
    'Carrots': {
        'file': 'carrots.jpg',
        'url': 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=600&auto=format&fit=crop&q=80',
    },
    'Amul Full Cream Milk': {
        'file': 'amul_milk.jpg',
        'url': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=600&auto=format&fit=crop&q=80',
    },
    'Mother Dairy Toned Milk': {
        'file': 'mother_dairy_milk.jpg',
        'url': 'https://images.unsplash.com/photo-1528750997573-59b89d56f4f7?w=600&auto=format&fit=crop&q=80',
    },
    'Amul Butter': {
        'file': 'butter.jpg',
        'url': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=600&auto=format&fit=crop&q=80',
    },
    'Amul Paneer': {
        'file': 'paneer.jpg',
        'url': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80',
    },
    'Eggs (White)': {
        'file': 'eggs.jpg',
        'url': 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=600&auto=format&fit=crop&q=80',
    },
    'Curd (Dahi)': {
        'file': 'curd.jpg',
        'url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=600&auto=format&fit=crop&q=80',
    },
    'Basmati Rice (Premium)': {
        'file': 'basmati_rice.jpg',
        'url': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80',
    },
    'Toor Dal (Split Pigeon Peas)': {
        'file': 'toor_dal.jpg',
        'url': 'https://images.unsplash.com/photo-1585996746979-6e3e57390977?w=600&auto=format&fit=crop&q=80',
    },
    'Wheat Flour (Atta)': {
        'file': 'atta.jpg',
        'url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80',
    },
    'Chana Dal (Split Chickpeas)': {
        'file': 'chana_dal.jpg',
        'url': 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=600&auto=format&fit=crop&q=80',
    },
    'Poha (Flattened Rice)': {
        'file': 'poha.jpg',
        'url': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80',
    },
    'Tata Tea Gold': {
        'file': 'tea.jpg',
        'url': 'https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=600&auto=format&fit=crop&q=80',
    },
    'Nescafe Classic Coffee': {
        'file': 'coffee.jpg',
        'url': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80',
    },
    'Real Fruit Juice (Mango)': {
        'file': 'mango_juice.jpg',
        'url': 'https://images.unsplash.com/photo-1546833998-877b37c2e5c6?w=600&auto=format&fit=crop&q=80',
    },
    'Bournvita': {
        'file': 'bournvita.jpg',
        'url': 'https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=600&auto=format&fit=crop&q=80',
    },
    'Haldirams Aloo Bhujia': {
        'file': 'aloo_bhujia.jpg',
        'url': 'https://images.unsplash.com/photo-1621996346565-e3d5d628169e?w=600&auto=format&fit=crop&q=80',
    },
    'Parle-G Biscuits': {
        'file': 'biscuits.jpg',
        'url': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&auto=format&fit=crop&q=80',
    },
    'Lays Classic Salted': {
        'file': 'lays_chips.jpg',
        'url': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600&auto=format&fit=crop&q=80',
    },
    'Dairy Milk Chocolate': {
        'file': 'chocolate.jpg',
        'url': 'https://images.unsplash.com/photo-1548907040-4baa42d10919?w=600&auto=format&fit=crop&q=80',
    },
    'MDH Garam Masala': {
        'file': 'garam_masala.jpg',
        'url': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=600&auto=format&fit=crop&q=80',
    },
    'Fortune Sunflower Oil': {
        'file': 'sunflower_oil.jpg',
        'url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=600&auto=format&fit=crop&q=80',
    },
    'Maggi Tomato Ketchup': {
        'file': 'ketchup.jpg',
        'url': 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80',
    },
    'Everest Turmeric Powder': {
        'file': 'turmeric.jpg',
        'url': 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=600&auto=format&fit=crop&q=80',
    },
    'Britannia Bread (White)': {
        'file': 'bread.jpg',
        'url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80',
    },
    'Pav Buns (8 pieces)': {
        'file': 'pav_buns.jpg',
        'url': 'https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=600&auto=format&fit=crop&q=80',
    },
}

CATEGORY_IMAGES = {
    'Fruits & Vegetables': {
        'file': 'cat_fruits_veggies.jpg',
        'url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&auto=format&fit=crop&q=80',
    },
    'Dairy & Eggs': {
        'file': 'cat_dairy.jpg',
        'url': 'https://images.unsplash.com/photo-1528750997573-59b89d56f4f7?w=400&auto=format&fit=crop&q=80',
    },
    'Grains & Pulses': {
        'file': 'cat_grains.jpg',
        'url': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&auto=format&fit=crop&q=80',
    },
    'Beverages': {
        'file': 'cat_beverages.jpg',
        'url': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=400&auto=format&fit=crop&q=80',
    },
    'Snacks & Sweets': {
        'file': 'cat_snacks.jpg',
        'url': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&auto=format&fit=crop&q=80',
    },
    'Spices & Condiments': {
        'file': 'cat_spices.jpg',
        'url': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&auto=format&fit=crop&q=80',
    },
    'Bakery': {
        'file': 'cat_bakery.jpg',
        'url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&auto=format&fit=crop&q=80',
    },
    'Personal Care': {
        'file': 'cat_personal_care.jpg',
        'url': 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&auto=format&fit=crop&q=80',
    },
}

def download_file(url, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=12) as response, open(target_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    print("--- 1. Downloading Product Images & Linking to Database ---")
    prod_dir = os.path.join('media', 'products')
    for prod_name, info in PRODUCT_IMAGES.items():
        file_path = os.path.join(prod_dir, info['file'])
        db_rel_path = f"products/{info['file']}"
        success = download_file(info['url'], file_path)
        if success:
            count = Product.objects.filter(name=prod_name).update(image=db_rel_path)
            print(f"  [OK] {prod_name} -> {db_rel_path} (updated {count} DB rows)")
        else:
            print(f"  [FAILED] {prod_name}")

    print("\n--- 2. Downloading Category Images & Linking to Database ---")
    cat_dir = os.path.join('media', 'categories')
    for cat_name, info in CATEGORY_IMAGES.items():
        file_path = os.path.join(cat_dir, info['file'])
        db_rel_path = f"categories/{info['file']}"
        success = download_file(info['url'], file_path)
        if success:
            count = Category.objects.filter(name=cat_name).update(image=db_rel_path)
            print(f"  [OK] {cat_name} -> {db_rel_path} (updated {count} DB rows)")
        else:
            print(f"  [FAILED] {cat_name}")

    print("\n--- Summary ---")
    prods_with_img = Product.objects.exclude(image='').count()
    cats_with_img = Category.objects.exclude(image='').count()
    print(f"Total Products with real images: {prods_with_img}/{Product.objects.count()}")
    print(f"Total Categories with real images: {cats_with_img}/{Category.objects.count()}")

if __name__ == '__main__':
    main()
