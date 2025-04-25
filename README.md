# Running the Scrapy Spider and Generating the Graph

Sayari programming task by Long Vo
## Prerequisites

* **Python 3.x** is installed.
* **Scrapy** is installed.
* **Pandas** is installed.
* **NetworkX** is installed.
* **Plotly** is installed.

If not
```bash
pip install scrapy networkx pandas plotly
```

## Installation

1.  **Navigate to the `sayari_task` directory:**

    Open your terminal and use the `cd` command to navigate to the `sayari_task` directory.  The exact path may vary depending on your system and where you've placed the project.  It will be similar to:

    ```bash
    cd /path/to/your/project/main/sayari_task/spiders
    ```

2.  **Install the required Python packages if not installed already:**


    ```bash
    pip install scrapy pandas networkx plotly  # Install the packages globally
    ```

## Running the Spider and Generating the Graph

1.  **Run the Python script:**

    

    ```bash
    python nd_search_spider.py
    ```

    This will:

    * Run the Scrapy spider (`NDSpider`).
    * Save the scraped data to `sayari_task/data/companies_detailed.json`.
    * Generate the interactive graph using the data from the JSON file.
    * Display the graph in your default web browser.
