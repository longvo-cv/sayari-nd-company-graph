import scrapy
import networkx as nx
import os
import pandas as pd
import plotly.graph_objects as go
import json
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

class NDSpider(scrapy.Spider):
    name = "nd_spider"
    allowed_domains = ["firststop.sos.nd.gov"]
    start_urls = ["https://firststop.sos.nd.gov/api/Records/businesssearch"]

    custom_settings = {
        "FEEDS": {
            "sayari_task/data/companies_detailed.json": {"format": "json", "encoding": "utf8"}
        }
    }

    def start_requests(self):
        payload = {
            "SEARCH_VALUE": "X",
            "STARTS_WITH_YN": True,
            "ACTIVE_ONLY_YN": True
        }
        yield scrapy.Request(
            url=self.start_urls[0],
            method="POST",
            body=json.dumps(payload),
            headers=self.get_headers(),
            callback=self.parse
        )

    def parse(self, response):
        session_id = response.headers.get('Set-Cookie', b'').decode().split("ASP.NET_SessionId=")[1].split(";")[0]
        self.session_cookie = f"ASP.NET_SessionId={session_id}"
        data = json.loads(response.text)
        for record in data.get("rows", {}).values():
            basic_info = {
                "name": record["TITLE"][0],
                "type": record["TITLE"][1],
                "record_num": record["RECORD_NUM"],
                "status": record["STATUS"],
                "standing": record["STANDING"],
                "filing_date": record["FILING_DATE"],
                "id": record["ID"]
            }
            url = f"https://firststop.sos.nd.gov/api/FilingDetail/business/{record['ID']}/false"
            yield scrapy.Request(
                url=url,
                headers=self.get_headers(),
                callback=self.parse_detail,
                meta={"basic_info": basic_info},
                dont_filter=True
            )

    def parse_detail(self, response):
        basic_info = response.meta["basic_info"]
        drawer = json.loads(response.text).get("DRAWER_DETAIL_LIST", [])
        filtered_info = {
            item["LABEL"].strip().lower().replace(" ", "_"): item["VALUE"]
            for item in drawer
            if item["LABEL"].strip().lower() in ["commercial registered agent", "registered agent", "owners"]
        }
        if filtered_info:
            yield {**basic_info, **filtered_info}

    def get_headers(self):
        headers = {
            "accept": "*/*",
            "authorization": "undefined",
            "content-type": "application/json",
            "origin": "https://firststop.sos.nd.gov",
            "priority": "u=1, i",
            "referer": "https://firststop.sos.nd.gov/search/business",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36"
        }
        if hasattr(self, "session_cookie"):
            headers["Cookie"] = self.session_cookie
        return headers
    
def construct_graph(json_path="sayari_task/data/companies_detailed.json"):
    df = pd.json_normalize(json.load(open(json_path)))
    df["agent"] = df["commercial_registered_agent"].fillna(df["registered_agent"]).dropna()
    df_edges = df[["name", "agent"]].dropna()
    G = nx.from_pandas_edgelist(df_edges, source="name", target="agent")
    pos = nx.spring_layout(G, seed=42)
    node_info = {
        row["name"]: {
            "type": row["type"],
            "status": row["status"],
            "standing": row["standing"],
            "filing_date": row["filing_date"],
            "record_num": row["record_num"]
        }
        for _, row in df.iterrows() if row["name"] in G.nodes
    }
    node_trace = go.Scatter(
        x=[pos[n][0] for n in G.nodes],
        y=[pos[n][1] for n in G.nodes],
        mode="markers",
        hoverinfo="text",
        text=[
            (
                f"<b>Company:</b> {n}<br>"
                f"<b>Type:</b> {node_info[n]['type']}<br>"
                f"<b>Status:</b> {node_info[n]['status']}<br>"
                f"<b>Standing:</b> {node_info[n]['standing']}<br>"
                f"<b>Filing Date:</b> {node_info[n]['filing_date']}<br>"
                f"<b>Record #:</b> {node_info[n]['record_num']}"
            ) if n in node_info else f"<b>Agent:</b><br>{n.replace(chr(10), '<br>')}" for n in G.nodes],
        marker=dict(color=["skyblue" if n in node_info else "lightgreen" for n in G.nodes], size=14, line_width=1.5),
    )
    edge_trace = go.Scatter(
        x=[coord for u, v in G.edges for coord in (pos[u][0], pos[v][0], None)],
        y=[coord for u, v in G.edges for coord in (pos[u][1], pos[v][1], None)],
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(title="ND Companies and Registered Agents Graph", showlegend=False,
                                    hovermode="closest", margin=dict(b=20, l=5, r=5, t=40),
                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    fig.show()

def run_spider_and_graph():
    output_path = "sayari_task/data/companies_detailed.json"
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Deleted existing file: {output_path}")
    process = CrawlerProcess(get_project_settings())  
    process.crawl(NDSpider)  
    process.start()  
    print("Spider finished crawling. Now generating graph...")
    construct_graph() 
    print("Graph generation complete.")
    print("hello")

if __name__ == "__main__":
    run_spider_and_graph()    

