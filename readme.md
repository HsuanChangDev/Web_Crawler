# Web Scraper

This project is a web scraper that scrapes product data from a website and saves it to a local MongoDB database.
The exaple website is OBDesign.

## Installation

This project uses Docker and docker compose to manage the environment and dependencies. Make sure Docker and docker compose is installed on your system.

## Usage

1. Clone this repository:

   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Build the Docker image using docker compose:

   ```
   docker compose build webcrawler
   ```

3. Run the Docker container:

   ```
    docker compose up -d 
   ```

4. The script will scrape the product data from the website and save it to the MongoDB database.


