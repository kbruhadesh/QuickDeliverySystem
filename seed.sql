INSERT INTO stores (name, pincode, address) VALUES
('Banjara Hills Node', '500034', 'Banjara Hills, Hyderabad'),
('Gachibowli Hub', '500032', 'Gachibowli, Hyderabad'),
('Hi-Tech City Express', '500081', 'Hi-Tech City, Hyderabad')
ON CONFLICT DO NOTHING;

INSERT INTO products (id, name, price, category, store_id) VALUES
(1, 'Farm Fresh Milk', 30, 'Dairy', 1),
(2, 'Whole Wheat Bread', 45, 'Bakery', 1),
(3, 'Bananas (Robusta)', 50, 'Fruits', 1),
(4, 'Red Tomatoes', 40, 'Vegetables', 1),
(5, 'Potato Chips - Salted', 35, 'Snacks', 1),
(6, 'Cold Brew Coffee', 120, 'Drinks', 1),
(7, 'Organic Eggs', 65, 'Dairy', 1),
(8, 'Dark Chocolate', 100, 'Snacks', 1)
ON CONFLICT DO NOTHING;
