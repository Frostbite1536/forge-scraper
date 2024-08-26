import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import csv
import pandas as pd
import logging
from datetime import datetime, timedelta
import os

# Set up logging
logging.basicConfig(filename='forge_data_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# GraphQL endpoint
URL = "https://subgraph.evmos.org/subgraphs/name/forge-subgraph"

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Enhanced schema with more options and descriptions
SCHEMA = {
    "Factory": {
        "description": "Overall statistics for the entire DEX",
        "fields": {
            "id": "Factory address",
            "poolCount": "Total number of pools",
            "txCount": "Total number of transactions",
            "totalVolumeUSD": "Total volume in USD",
            "totalFeesUSD": "Total fees collected in USD",
            "totalValueLockedUSD": "Total value locked in USD"
        }
    },
    "Token": {
        "description": "Information about individual tokens",
        "fields": {
            "id": "Token address",
            "symbol": "Token symbol",
            "name": "Token name",
            "decimals": "Token decimals",
            "totalSupply": "Total supply of the token",
            "volume": "Trading volume in token units",
            "volumeUSD": "Trading volume in USD",
            "feesUSD": "Fees generated in USD",
            "txCount": "Number of transactions involving this token"
        }
    },
    "Pool": {
        "description": "Information about liquidity pools",
        "fields": {
            "id": "Pool address",
            "token0": "Address of the first token in the pair",
            "token1": "Address of the second token in the pair",
            "feeTier": "Fee tier of the pool",
            "liquidity": "Current liquidity in the pool",
            "sqrtPrice": "Square root of the current price",
            "token0Price": "Price of token0 in terms of token1",
            "token1Price": "Price of token1 in terms of token0",
            "volumeUSD": "Total volume in USD",
            "feesUSD": "Total fees collected in USD",
            "txCount": "Total number of transactions"
        }
    },
    "PoolDayData": {
        "description": "Daily data for a specific pool",
        "fields": {
            "id": "Unique identifier for the day's data",
            "date": "Date of the data point",
            "pool": "Address of the pool",
            "liquidity": "Liquidity at the end of the day",
            "sqrtPrice": "Square root of the price at the end of the day",
            "token0Price": "Price of token0 at the end of the day",
            "token1Price": "Price of token1 at the end of the day",
            "volumeUSD": "Volume in USD for the day",
            "feesUSD": "Fees collected in USD for the day",
            "txCount": "Number of transactions for the day",
            "open": "Opening price of token0 for the day",
            "high": "Highest price of token0 for the day",
            "low": "Lowest price of token0 for the day",
            "close": "Closing price of token0 for the day"
        }
    },
    "WalletOverview": {
        "description": "Comprehensive overview of a wallet's activities",
        "fields": {
            "swaps": "Swap transactions made by the wallet",
            "positions": "Liquidity positions owned by the wallet"
        }
    },    
    "Swap": {
        "description": "Individual swap transactions",
        "fields": {
            "id": "Unique identifier for the swap",
            "timestamp": "Timestamp of the swap",
            "pool": "Address of the pool where the swap occurred",
            "token0": "Address of the first token in the pair",
            "token1": "Address of the second token in the pair",
            "amount0": "Amount of token0 swapped",
            "amount1": "Amount of token1 swapped",
            "amountUSD": "USD value of the swap"
        }
    }
}

class ForgeDataApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Forge Data Scraper")
        self.geometry("900x800")  # Increased height to accommodate new fields

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.query_frame, text="Custom Query")

        self.setup_query_frame()

    def setup_query_frame(self):
        # Configuration Section
        config_frame = ttk.LabelFrame(self.query_frame, text="Google Sheets Configuration")
        config_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(config_frame, text="Client Secret Path:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.client_secret_path = tk.StringVar()
        self.client_secret_entry = ttk.Entry(config_frame, textvariable=self.client_secret_path, width=40)
        self.client_secret_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_client_secret).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(config_frame, text="Google Sheet ID:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sheet_id = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.sheet_id, width=40).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Query Section
        self.entity_var = tk.StringVar()
        entity_label = ttk.Label(self.query_frame, text="Select Entity:")
        entity_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        entity_dropdown = ttk.Combobox(self.query_frame, textvariable=self.entity_var, values=list(SCHEMA.keys()))
        entity_dropdown.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        entity_dropdown.bind("<<ComboboxSelected>>", self.update_fields)

        help_button = ttk.Button(self.query_frame, text="Help", command=self.show_help)
        help_button.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        self.fields_frame = ttk.Frame(self.query_frame)
        self.fields_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.address_label = ttk.Label(self.query_frame, text="Address (Pool/Token/Wallet):")
        self.address_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.address_entry = ttk.Entry(self.query_frame, width=50)
        self.address_entry.grid(row=3, column=1, columnspan=2, sticky="we", padx=5, pady=5)

        self.limit_var = tk.StringVar(value="100")
        limit_label = ttk.Label(self.query_frame, text="Limit:")
        limit_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        limit_entry = ttk.Entry(self.query_frame, textvariable=self.limit_var, width=10)
        limit_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Button Section with even spacing
        button_frame = ttk.Frame(self.query_frame)
        button_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        export_button = ttk.Button(button_frame, text="Export to Google Sheets", command=self.export_to_sheets)
        export_button.grid(row=0, column=0, padx=5, pady=5)

        export_csv_button = ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv)
        export_csv_button.grid(row=0, column=1, padx=5, pady=5)

        export_excel_button = ttk.Button(button_frame, text="Export to Excel", command=self.export_to_excel)
        export_excel_button.grid(row=0, column=2, padx=5, pady=5)

        export_json_button = ttk.Button(button_frame, text="Export to JSON", command=self.export_to_json)
        export_json_button.grid(row=0, column=3, padx=5, pady=5)

        query_button = ttk.Button(button_frame, text="Run Query", command=self.run_query)
        query_button.grid(row=0, column=4, padx=5, pady=5)

        # Expand the buttons to take equal space
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        button_frame.grid_columnconfigure(4, weight=1)

        self.result_text = scrolledtext.ScrolledText(self.query_frame, height=20)
        self.result_text.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.query_frame.grid_rowconfigure(6, weight=1)
        self.query_frame.grid_columnconfigure(1, weight=1)

        # Add Export menu
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Export to CSV", command=self.export_to_csv)
        self.file_menu.add_command(label="Export to Excel", command=self.export_to_excel)
        self.file_menu.add_command(label="Export to JSON", command=self.export_to_json)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save Query Configuration", command=self.save_query_config)
        self.file_menu.add_command(label="Load Query Configuration", command=self.load_query_config)


    def export_to_csv(self):
        data = self.get_query_results()
        if data:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv")
            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(data)
                messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
                logging.info(f"Data exported to CSV: {file_path}")

    def export_to_excel(self):
        data = self.get_query_results()
        if data:
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if file_path:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
                logging.info(f"Data exported to Excel: {file_path}")

    def export_to_json(self):
        data = json.loads(self.result_text.get('1.0', tk.END))
        if data:
            file_path = filedialog.asksaveasfilename(defaultextension=".json")
            if file_path:
                with open(file_path, 'w') as jsonfile:
                    json.dump(data, jsonfile, indent=2)
                messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
                logging.info(f"Data exported to JSON: {file_path}")

    def get_query_results(self):
        data = json.loads(self.result_text.get('1.0', tk.END))
        if not data:
            messagebox.showwarning("No Data", "Please run a query first.")
            return None

        entity = self.entity_var.get()
        if entity == "WalletOverview":
            rows = []
            if 'swaps' in data:
                rows.append(["Swaps"])
                rows.append(list(data['swaps'][0].keys()))
                rows.extend([list(swap.values()) for swap in data['swaps']])
                rows.append([])
            if 'positions' in data:
                rows.append(["Positions"])
                rows.append(list(data['positions'][0].keys()))
                rows.extend([list(position.values()) for position in data['positions']])
        else:
            key = entity.lower() + 's'
            if key not in data:
                messagebox.showwarning("No Data", "No data found for the selected entity.")
                return None
            rows = [list(data[key][0].keys())]
            rows.extend([list(item.values()) for item in data[key]])
        return rows

    def save_query_config(self):
        config = {
            'entity': self.entity_var.get(),
            'address': self.address_entry.get(),
            'limit': self.limit_var.get(),
            'fields': {field: getattr(self, f"{self.entity_var.get()}_{field}_var").get() 
                       for field in SCHEMA[self.entity_var.get()]['fields']}
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("Save Successful", f"Query configuration saved to {file_path}")
            logging.info(f"Query configuration saved: {file_path}")

    def load_query_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                config = json.load(f)
            self.entity_var.set(config['entity'])
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, config['address'])
            self.limit_var.set(config['limit'])
            self.update_fields(None)  # Update fields for the loaded entity
            for field, value in config['fields'].items():
                if hasattr(self, f"{config['entity']}_{field}_var"):
                    getattr(self, f"{config['entity']}_{field}_var").set(value)
            messagebox.showinfo("Load Successful", f"Query configuration loaded from {file_path}")
            logging.info(f"Query configuration loaded: {file_path}")

    def show_field_description(self, event, description):
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=description, justify='left',
                          background="#ffffff", relief='solid', borderwidth=1)
        label.pack(ipadx=1)

        self.tooltip.bind("<Leave>", self.hide_field_description)
        self.tooltip.bind("<Button-1>", self.hide_field_description)

    def hide_field_description(self, event):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

    def query_subgraph(self, query):
        logging.info(f"Sending query: {query}")
        try:
            response = requests.post(URL, json={'query': query})
            response.raise_for_status()
            json_response = response.json()
            
            if 'errors' in json_response:
                error_message = json_response['errors'][0]['message']
                logging.error(f"Query error: {error_message}")
                messagebox.showerror("Query Error", f"The subgraph returned an error: {error_message}")
                return None
            
            if 'data' not in json_response:
                logging.warning("Query returned no data")
                messagebox.showwarning("No Data", "The query did not return any data. This could mean there's no matching data for your query.")
                return None
            
            logging.info("Query successful")
            return json_response['data']
        except requests.RequestException as e:
            logging.error(f"Request error: {str(e)}")
            messagebox.showerror("Request Error", f"An error occurred while querying the subgraph: {str(e)}")
            return None

    def build_query(self, entity, fields, wallet_address=None):
        limit = self.limit_var.get()
        address = wallet_address or self.address_entry.get().strip()
        
        filter_condition = ''
        if address:
            if entity in ['Pool', 'Token']:
                filter_condition = f'where: {{ id: "{address}" }}'
            elif entity == 'Swap':
                filter_condition = f'where: {{ origin: "{address}" }}'
            elif entity == 'Position':
                filter_condition = f'where: {{ owner: "{address}" }}'
            elif entity == 'PoolDayData':
                filter_condition = f'where: {{ pool: "{address}" }}'

        query = f"""
          query {{
            {entity.lower()}s(first: {limit}, {filter_condition}) {{
              {' '.join(fields)}
            }}
          }}
        """
        return query

    def browse_client_secret(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.client_secret_path.set(filename)

    def update_fields(self, event):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()

        entity = self.entity_var.get()
        if entity == "WalletOverview":
            self.setup_wallet_overview_fields()
        elif entity in SCHEMA:
            for i, (field, description) in enumerate(SCHEMA[entity]['fields'].items()):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(self.fields_frame, text=field, variable=var)
                chk.grid(row=i//3, column=i%3, sticky="w")
                chk.configure(cursor="question_arrow")
                chk.bind("<Enter>", lambda e, desc=description: self.show_field_description(e, desc))
                chk.bind("<Leave>", self.hide_field_description)
                setattr(self, f"{entity}_{field}_var", var)

        # Update address label based on selected entity
        if entity == "Pool":
            self.address_label.config(text="Pool Address:")
        elif entity == "Token":
            self.address_label.config(text="Token Address:")
        elif entity in ["Swap", "Position", "WalletOverview"]:
            self.address_label.config(text="Wallet Address:")
        else:
            self.address_label.config(text="Address (optional):")

    def setup_wallet_overview_fields(self):
        entities = ["Swap", "Position"]
        for i, entity in enumerate(entities):
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.fields_frame, text=entity, variable=var)
            chk.grid(row=0, column=i, sticky="w")
            setattr(self, f"WalletOverview_{entity}_var", var)
    
    def show_help(self):
        help_window = tk.Toplevel(self)
        help_window.title("Help")
        help_window.geometry("600x400")

        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text.pack(expand=True, fill='both')

        help_content = "Forge Data Scraper Help\n\n"
        for entity, details in SCHEMA.items():
            help_content += f"{entity}:\n{details['description']}\n\n"
            help_content += "Fields:\n"
            for field, description in details['fields'].items():
                help_content += f"  - {field}: {description}\n"
            help_content += "\n"

        help_text.insert(tk.END, help_content)
        help_text.configure(state='disabled')

    def show_field_description(self, event, description):
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=description, justify='left',
                          background="#ffffff", relief='solid', borderwidth=1)
        label.pack(ipadx=1)

    def hide_field_description(self, event):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()
    
    def run_query(self):
        entity = self.entity_var.get()
        if entity == "WalletOverview":
            self.run_wallet_overview_query()
        else:
            selected_fields = [field for field, desc in SCHEMA[entity]['fields'].items() if getattr(self, f"{entity}_{field}_var").get()]

            if not selected_fields:
                messagebox.showwarning("No Fields Selected", "Please select at least one field to query.")
                return

            query = self.build_query(entity, selected_fields)
            data = self.query_subgraph(query)
            if data is not None:
                self.display_results(data)
            else:
                messagebox.showerror("Query Error", "Failed to retrieve data. Please check your query and try again.")

    def run_wallet_overview_query(self):
        wallet_address = self.address_entry.get().strip()
        if not wallet_address:
            messagebox.showwarning("No Wallet Address", "Please enter a wallet address.")
            return

        queries = []
        if getattr(self, "WalletOverview_Swap_var").get():
            swap_fields = ['id', 'timestamp', 'pool', 'token0', 'token1', 'amount0', 'amount1', 'amountUSD']
            queries.append(self.build_query("Swap", swap_fields, wallet_address))
        if getattr(self, "WalletOverview_Position_var").get():
            position_fields = ['id', 'owner', 'pool', 'token0', 'token1', 'liquidity', 'depositedToken0', 'depositedToken1', 'withdrawnToken0', 'withdrawnToken1', 'collectedFeesToken0', 'collectedFeesToken1']
            queries.append(self.build_query("Position", position_fields, wallet_address))

        combined_query = "query {" + " ".join(queries) + "}"
        data = self.query_subgraph(combined_query)
        if data is not None:
            self.display_results(data)
            self.entity_var.set("WalletOverview")  # Set the entity to WalletOverview

    def build_query(self, entity, fields, wallet_address=None):
        limit = self.limit_var.get()
        address = wallet_address or self.address_entry.get().strip()
        
        filter_condition = ''
        if address:
            if entity in ['Pool', 'Token']:
                filter_condition = f'where: {{ id: "{address}" }}'
            elif entity == 'Swap':
                filter_condition = f'where: {{ origin: "{address}" }}'
            elif entity == 'Position':
                filter_condition = f'where: {{ owner: "{address}" }}'

        query = f"""
          {entity.lower()}s(first: {limit}, {filter_condition}) {{
            {' '.join(fields)}
          }}
        """
        return query

    def display_results(self, data):
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, json.dumps(data, indent=2))

    def export_to_sheets(self):
        if not self.client_secret_path.get() or not self.sheet_id.get():
            messagebox.showwarning("Missing Information", "Please provide both the client secret path and Google Sheet ID.")
            return

        creds = self.get_credentials()
        service = build('sheets', 'v4', credentials=creds)

        sheet_id = self.sheet_id.get()
        entity = self.entity_var.get()
        
        data = json.loads(self.result_text.get('1.0', tk.END))
        if not data:
            messagebox.showwarning("No Data", "Please run a query first.")
            return

        if entity == "WalletOverview":
            # Handle WalletOverview separately
            rows = []
            if 'swaps' in data:
                rows.append(["Swaps"])
                rows.append(list(data['swaps'][0].keys()))  # Headers
                for swap in data['swaps']:
                    rows.append(list(swap.values()))
                rows.append([])  # Empty row for separation
            if 'positions' in data:
                rows.append(["Positions"])
                rows.append(list(data['positions'][0].keys()))  # Headers
                for position in data['positions']:
                    rows.append(list(position.values()))
        else:
            # Handle other entities
            if entity.lower() + 's' not in data:
                messagebox.showwarning("No Data", "Please run a query first.")
                return
            rows = [list(data[entity.lower() + 's'][0].keys())]  # Headers
            for item in data[entity.lower() + 's']:
                rows.append(list(item.values()))

        self.update_sheet(service, sheet_id, entity, rows)

    def get_credentials(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_path.get(), SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return creds

    def update_sheet(self, service, spreadsheet_id, sheet_name, data):
        try:
            service.spreadsheets().get(spreadsheetId=spreadsheet_id, ranges=sheet_name).execute()
        except:
            request = {'addSheet': {'properties': {'title': sheet_name}}}
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': [request]}).execute()

        range_name = f"{sheet_name}!A1"
        body = {'values': data}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        
        messagebox.showinfo("Export Successful", f"{result.get('updatedCells')} cells updated in Google Sheets.")

if __name__ == "__main__":
    app = ForgeDataApp()
    app.mainloop()
