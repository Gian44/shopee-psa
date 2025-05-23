import threading
import webbrowser
import os
import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from database import DatabaseManager
from scraper import ShopeeScraper

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Shopee Price Scraper")
        self.db = DatabaseManager(DB_NAME)
        self.keyword = ""
        self.setup_gui()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

         # Add table selection frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill="x", pady=5)

        ttk.Label(table_frame, text="Saved Searches:").pack(side="left")
        
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(table_frame, 
                                        textvariable=self.table_var,
                                        state="readonly")
        self.table_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.load_selected_table)

        refresh_tables_btn = ttk.Button(table_frame, text="↻", 
                                    command=self.refresh_table_list,
                                    width=3)
        refresh_tables_btn.pack(side="left")

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=10)

        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        search_button = ttk.Button(search_frame, text="Search", command=self.start_scraping)
        search_button.pack(side="left", padx=5)

        delete_cookies_btn = ttk.Button(search_frame, text="Delete Cookies", 
                                      command=self.delete_cookies)
        delete_cookies_btn.pack(side="left", padx=5)

        # Add Login Credentials Frame
        cred_frame = ttk.Frame(main_frame)
        cred_frame.pack(fill="x", pady=5)

        ttk.Label(cred_frame, text="Username:").pack(side="left")
        self.username_entry = ttk.Entry(cred_frame, width=20)
        self.username_entry.pack(side="left", padx=5)

        ttk.Label(cred_frame, text="Password:").pack(side="left")
        self.password_entry = ttk.Entry(cred_frame, width=20, show="*")
        self.password_entry.pack(side="left", padx=5)

        self.sort_label = ttk.Label(main_frame, text="Sort by:")
        self.sort_label.pack(anchor="w", pady=5)

        self.sort_variable = tk.StringVar()
        self.sort_variable.set("default")  # default value

        sort_options = [
            "default (original order)",
            "price (low to high)",
            "price (high to low)",
            "sold (high to low)",
            "sold (low to high)"
        ]
        
        sort_menu = ttk.OptionMenu(main_frame, self.sort_variable, *sort_options)
        sort_menu.pack(anchor="w")

        # Add trace to automatically refresh when sorting option changes
        self.sort_variable.trace('w', lambda *args: self.refresh_data())

        self.tree = ttk.Treeview(main_frame)
        self.tree['columns'] = ('Name', 'Price', 'Sold', 'Link')
    
        self.tree.column("#0", width=0, stretch='no')
        self.tree.column("Name", anchor='w', width=250)
        self.tree.column("Price", anchor='w', width=100)
        self.tree.column("Sold", anchor='w', width=100)
        self.tree.column("Link", anchor='w', width=200)
        
        self.tree.heading("#0", text='', anchor='w')
        self.tree.heading('Name', text='Name', anchor='w')
        self.tree.heading('Price', text='Price', anchor='w')
        self.tree.heading('Sold', text='Sold', anchor='w')
        self.tree.heading('Link', text='Link', anchor='w')
        
        # Add click event handler
        self.tree.bind('<Button-1>', self.on_tree_click)

        self.tree.pack(fill="both", expand=True, pady=10)

        refresh_button = ttk.Button(main_frame, text="Refresh", command=self.refresh_data)
        refresh_button.pack(fill="x", pady=5)

        # Add page selection frame
        page_frame = ttk.Frame(main_frame)
        page_frame.pack(fill="x", pady=5)

        ttk.Label(page_frame, text="Pages to scrape:").pack(side="left")
        self.page_var = tk.StringVar()
        self.page_var.set("3")  # Default value
        self.page_entry = ttk.Entry(page_frame, textvariable=self.page_var, width=5)
        self.page_entry.pack(side="left", padx=5)

        self.refresh_table_list()

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.focus()
            if column == "#4":  # Link column
                link = self.tree.item(item)['values'][3]
                webbrowser.open(link)

    def refresh_table_list(self):
        db = DatabaseManager(DB_NAME)
        db.connect()
        tables = db.get_all_product_tables()
        db.close()
        
        self.table_dropdown['values'] = tables
        if tables:
            # Only update if we don't already have a selected value
            if not self.table_var.get():
                self.table_var.set(tables[0])
                self.load_selected_table()

    def load_selected_table(self, event=None):
        selected_keyword = self.table_var.get()
        if selected_keyword:
            self.keyword = selected_keyword
            self.refresh_data()
    
    def delete_cookies(self):
        scraper = ShopeeScraper(self.root)
        if scraper.delete_cookies():
            messagebox.showinfo("Success", "Cookies deleted successfully")
        else:
            messagebox.showwarning("Info", "No cookies found or error occurred")

    def start_scraping(self):
        keyword = self.search_entry.get()
        if not keyword:
            messagebox.showerror("Error", "Please enter a search term")
            return

        self.scraping_in_progress = True
        self.search_entry.config(state="disabled")
        self.keyword = keyword

        # Get credentials from input fields
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Create a new thread to run the scraping process
        scraping_thread = threading.Thread(
            target=self.scrape_products, 
            args=(keyword, username, password)
        )
        scraping_thread.start()

    def scrape_products(self, keyword, username=None, password=None):
        try:
            # Get page count from GUI
            try:
                max_pages = int(self.page_var.get())
            except ValueError:
                max_pages = 3

            # Initialize the scraper
            scraper = ShopeeScraper(self.root)
        
            if not os.path.exists(COOKIE_FILE) and username and password:
                results = scraper.scrape(keyword, username, password, max_pages)
            else:
                results = scraper.scrape(keyword, max_pages=max_pages)
            
            # Update the GUI with the results
            self.update_gui(results)
            
            # Store the current keyword for sorting/refresh
            self.keyword = keyword

            # After successful scrape, refresh table list
            self.refresh_table_list()
            
            # Auto-select the newly created table
            self.table_var.set(keyword)
            self.load_selected_table()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during scraping: {str(e)}")
        finally:
            self.scraping_in_progress = False
            self.search_entry.config(state="normal")

    def update_gui(self, products):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for product in products:
            self.tree.insert('', 'end', values=(product['name'], product['price'], product['sold']))

    def refresh_data(self):
        if not hasattr(self, 'keyword') or not self.keyword:
            return
            
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Create new database connection for this operation
        db = DatabaseManager(DB_NAME)
        db.connect()
        
        sort_mapping = {
            "default (original order)": "default",
            "price (low to high)": "price_low_to_high",
            "price (high to low)": "price_high_to_low",
            "sold (high to low)": "sold_high_to_low",
            "sold (low to high)": "sold_low_to_high"
        }
        
        sort_option = sort_mapping.get(self.sort_variable.get(), "default")
        
        products = db.get_products(
            f"products_{self.keyword.replace(' ', '_')}",
            sort_option
        )

        for product in products:
            self.tree.insert('', 'end', values=product)
            
        db.close()

if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()