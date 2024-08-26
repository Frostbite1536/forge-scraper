# Forge Data Scraper

## Overview

The **Forge Data Scraper** is a GUI-based tool designed to interact with the Evmos blockchain subgraph and retrieve detailed data on decentralized exchange (DEX) activities, tokens, pools, and wallet overviews. This tool allows users to query, visualize, and export data from the blockchain in various formats such as CSV, Excel, JSON, and Google Sheets.

## Features

- **Custom Queries**: Easily select entities such as Factory, Token, Pool, PoolDayData, WalletOverview, or Swap, and specify the fields you want to retrieve.
- **Google Sheets Integration**: Export your data directly to Google Sheets by configuring your Google API credentials.
- **Flexible Export Options**: Export your query results in CSV, Excel, or JSON format.
- **User-Friendly Interface**: Built with Tkinter, the interface is designed to be intuitive and easy to use, with options for browsing files, running queries, and exporting data.
- **Field Descriptions**: Hover over field names to see detailed descriptions of what each field represents, ensuring clarity when building queries.
- **Query Configuration Management**: Save and load your query configurations, allowing for quick reuse of frequently used queries.

## Getting Started

### Prerequisites

- **Python 3.x**
- Required Python packages:
  - tkinter
  - requests
  - json
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - googleapiclient
  - pandas

You can install the required packages using pip:

bash
pip install requests google-auth google-auth-oauthlib google-auth-httplib2 googleapiclient pandas


### Installation

1. **Clone the repository:**

   
bash
   git clone https://github.com/yourusername/forge-data-scraper.git
   cd forge-data-scraper


2. **Run the application:**

   
bash
   python forge_data_scraper.py


### Google Sheets Setup

To export data to Google Sheets, you'll need to set up Google API credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the Google Sheets API.
4. Create OAuth 2.0 credentials and download the client_secret.json file.
5. In the application, provide the path to the client_secret.json file and the Google Sheet ID where you want to export the data.

### Usage

1. **Select an Entity**: Choose an entity such as Factory, Token, Pool, PoolDayData, WalletOverview, or Swap.
2. **Configure Fields**: Select the fields you want to query. You can hover over the fields to see their descriptions.
3. **Run Query**: Click the "Run Query" button to execute your query and retrieve the data.
4. **View Results**: The results will be displayed in a scrollable text area within the application.
5. **Export Data**: Use the export options to save the results in your desired format (CSV, Excel, JSON, or Google Sheets).

### Logging

All actions and errors are logged to a file named forge_data_app.log, which is created in the application directory.

### Help

You can access detailed help within the application by clicking the "Help" button. This will open a new window containing descriptions of all entities and fields available for querying.

## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. You can view the full license here: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

You are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- NonCommercial — You may not use the material for commercial purposes without explicit permission from the original author.

## Contributing

Feel free to fork this repository and submit pull requests. Any contributions are welcome and appreciated.

## Contact

For any questions or support, please create an issue on the [GitHub repository](https://github.com/frostbite1536/forge-scraper) or contact the author directly.

