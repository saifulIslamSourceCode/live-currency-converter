import tkinter as tk
from tkinter import ttk, messagebox
import requests

# API key and base URL for exchange rate API
EXCHANGE_API_KEY = "daa6e960620c0165ca4b4a7a"
EXCHANGE_API_BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}"

conversion_records = []

class AutocompleteCombobox(ttk.Combobox):
    def set_list_of_items(self, items):
        # Store sorted list of countries for autocomplete suggestions
        self.autocomplete_list = sorted(items, key=str.lower)
        self.matches = []
        self.position = 0
        self.bind('<KeyRelease>', self.on_key_release)
        self['values'] = self.autocomplete_list

    def autocomplete(self, delta=0):
        if delta:
            self.position += delta
        else:
            self.position = len(self.get())

        text_entered = self.get()
        self.matches = [item for item in self.autocomplete_list if item.lower().startswith(text_entered.lower())]

        if self.matches != self['values']:
            if self.matches:
                self['values'] = self.matches
            else:
                self['values'] = self.autocomplete_list

    def on_key_release(self, event):
        if event.keysym in ("BackSpace", "Left", "Right", "Delete"):
            self.position = self.index(tk.END)
        self.autocomplete()

def load_country_names():
    """Fetch list of all country names from REST Countries API."""
    try:
        response = requests.get("https://restcountries.com/v3.1/all")
        response.raise_for_status()
        country_data = response.json()
        country_names = sorted([country["name"]["common"] for country in country_data])
        print(f"Fetched {len(country_names)} countries")
        return country_names
    except Exception as error:
        print("Failed to fetch countries:", error)
        # fallback list if API fails
        return ["Bangladesh", "United States", "India", "Japan", "United Kingdom", "Canada"]

def fetch_currency_details(country_name):
    """Given a country name, fetch its currency code and symbol."""
    try:
        url = f"https://restcountries.com/v3.1/name/{country_name}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        currencies = data[0].get("currencies", {})
        currency_code = list(currencies.keys())[0]
        symbol = currencies[currency_code].get("symbol", "")
        return currency_code, symbol
    except Exception:
        return None, ""

def fetch_conversion_rate(from_currency, to_currency):
    """Call ExchangeRate API to get conversion rate between two currencies."""
    try:
        url = f"{EXCHANGE_API_BASE_URL}/pair/{from_currency}/{to_currency}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data.get("conversion_rate")
        else:
            return None
    except Exception:
        return None

def perform_conversion():
    from_country = from_country_combo.get().strip()
    to_country = to_country_combo.get().strip()
    amount_text = amount_entry.get().strip()

    if not from_country or not to_country or not amount_text:
        messagebox.showwarning("Input Error", "Please fill all fields before converting.")
        return

    try:
        amount_value = float(amount_text)
    except ValueError:
        messagebox.showwarning("Input Error", "Please enter a valid number for amount.")
        return

    from_currency, from_symbol = fetch_currency_details(from_country)
    to_currency, to_symbol = fetch_currency_details(to_country)

    if not from_currency or not to_currency:
        messagebox.showerror("Error", "Could not find currency information for one or both countries.")
        return

    rate = fetch_conversion_rate(from_currency, to_currency)
    if rate is None:
        messagebox.showerror("Error", "Failed to retrieve conversion rate. Try again later.")
        return

    converted_amount = amount_value * rate
    result_text = f"{amount_value} {from_currency} ({from_symbol}) = {converted_amount:.2f} {to_currency} ({to_symbol})"
    result_label.config(text=result_text)

    # Save conversion to history and update display
    conversion_records.append(result_text)
    update_history_display()

def update_history_display():
    history_listbox.delete(0, tk.END)
    for record in conversion_records[-10:]:
        history_listbox.insert(tk.END, record)

# Load country list at program start
all_countries = load_country_names()

# Setup main window
app = tk.Tk()
app.title("Currency Converter")
app.geometry("520x520")
app.resizable(False, False)

tk.Label(app, text="Select From Country:").pack(pady=(10, 0))
from_country_combo = AutocompleteCombobox(app, width=40)
from_country_combo.set_list_of_items(all_countries)
from_country_combo.pack()

tk.Label(app, text="Select To Country:").pack(pady=(10, 0))
to_country_combo = AutocompleteCombobox(app, width=40)
to_country_combo.set_list_of_items(all_countries)
to_country_combo.pack()

tk.Label(app, text="Amount to Convert:").pack(pady=(10, 0))
amount_entry = tk.Entry(app, width=42)
amount_entry.pack()

convert_button = tk.Button(app, text="Convert", command=perform_conversion)
convert_button.pack(pady=10)

result_label = tk.Label(app, text="", font=("Arial", 12, "bold"))
result_label.pack(pady=5)

tk.Label(app, text="Conversion History (last 10):").pack(pady=(15, 0))
history_frame = tk.Frame(app)
history_frame.pack()

scrollbar = tk.Scrollbar(history_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

history_listbox = tk.Listbox(history_frame, height=7, width=65, yscrollcommand=scrollbar.set)
history_listbox.pack(side=tk.LEFT)
scrollbar.config(command=history_listbox.yview)

app.mainloop()
