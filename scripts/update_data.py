#!/usr/bin/env python3
"""
ATLAS Terminal — robot de datos diario.
Descarga precios reales (yfinance), noticias (RSS) y, opcionalmente,
enriquece con IA (API de Anthropic si existe ANTHROPIC_API_KEY).
Escribe: data/market.json, data/news.json
Se ejecuta desde GitHub Actions (ver .github/workflows/update.yml).
"""
import json, os, re, sys, html
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

INDICES = {
    "US": [("S&P 500", "^GSPC"), ("Nasdaq 100", "^NDX"), ("Dow Jones", "^DJI"), ("Russell 2000", "^RUT")],
    "ES": [("IBEX 35", "^IBEX")],
    "DE": [("DAX 40", "^GDAXI")],
    "FR": [("CAC 40", "^FCHI")],
    "GB": [("FTSE 100", "^FTSE")],
    "IT": [("FTSE MIB", "FTSEMIB.MI")],
    "JP": [("Nikkei 225", "^N225")],
    "CN": [("CSI 300", "000300.SS"), ("Hang Seng", "^HSI")],
    "IN": [("Nifty 50", "^NSEI"), ("Sensex", "^BSESN")],
    "BR": [("Bovespa", "^BVSP")],
    "MX": [("IPC México", "^MXX")],
    "CA": [("S&P/TSX", "^GSPTSE")],
    "AU": [("ASX 200", "^AXJO")],
    "KR": [("KOSPI", "^KS11")],
    "CH": [("SMI", "^SSMI")],
    "SA": [("Tadawul", "^TASI.SR")],
    "ZA": [("JSE Top 40", "^J203.JO")],
    "TR": [("BIST 100", "XU100.IS")],
}
FX = {
    "US": "DX-Y.NYB", "ES": "EURUSD=X", "DE": "EURUSD=X", "FR": "EURUSD=X", "IT": "EURUSD=X",
    "GB": "GBPUSD=X", "JP": "JPY=X", "CN": "CNY=X", "IN": "INR=X", "BR": "BRL=X",
    "MX": "MXN=X", "CA": "CAD=X", "AU": "AUDUSD=X", "KR": "KRW=X", "CH": "CHF=X",
    "SA": "SAR=X", "ZA": "ZAR=X", "TR": "TRY=X",
}
COMPANIES = {
    "AAPL": "AAPL", "MSFT": "MSFT", "NVDA": "NVDA", "AMZN": "AMZN", "GOOGL": "GOOGL",
    "META": "META", "JPM": "JPM", "TSLA": "TSLA",
    "ITX": "ITX.MC", "IBE": "IBE.MC", "SAN": "SAN.MC", "BBVA": "BBVA.MC",
    "REP": "REP.MC", "FER": "FER.MC", "CLNX": "CLNX.MC",
    "SAP": "SAP.DE", "SIE": "SIE.DE", "ALV": "ALV.DE",
    "MC": "MC.PA", "TTE": "TTE.PA", "AZN": "AZN.L", "SHEL": "SHEL.L",
    "7203": "7203.T", "6758": "6758.T", "700": "0700.HK", "9988": "9988.HK",
}
FEEDS = [
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("WSJ Markets", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"),
    ("Financial Times", "https://www.ft.com/rss/home"),
    ("Expansión", "https://e00-expansion.uecdn.es/rss/mercados.xml"),
    ("El Economista", "https://www.eleconomista.es/rss/rss-mercados.php"),
]
CTY_KW = {
    "US": r"fed\b|fomc|powell|wall street|u\.s\.|us stocks|treasur|nasdaq|s&p ?500|dow jones|estados unidos|ee\.? ?uu",
    "ES": r"spain|españa|ibex|santander|bbva|iberdrola|inditex|repsol|ferrovial|cellnex|madrid",
    "DE": r"german|alemania|alemán|dax\b|bund\b|bundesbank|siemens|sap\b",
    "FR": r"france|francia|french|cac ?40|oat\b|macron|lvmh|totalenergies",
    "GB": r"\buk\b|britain|reino unido|británic|ftse|gilt|bank of england|\bboe\b|sterling|libra",
    "IT": r"\bital|btp\b|milan|meloni",
    "JP": r"japan|japón|nikkei|\bboj\b|yen\b|tokyo|tokio|toyota|sony",
    "CN": r"china|chino|beijing|pekín|yuan|hang seng|alibaba|tencent|taiwan|taiwán",
    "IN": r"india\b|rupee|rupia|nifty|sensex|mumbai|\brbi\b",
    "BR": r"brazil|brasil|bovespa|selic|copom",
    "MX": r"mexico|méxico|banxico|usmca|t-mec|peso mexicano",
    "CA": r"canada|canadá|loonie|toronto",
    "AU": r"australia|aussie|\brba\b|sydney",
    "KR": r"korea|corea|kospi|\bwon\b|samsung|sk hynix|seoul|seúl",
    "CH": r"switzerland|suiza|swiss|\bsnb\b|franco suizo|zurich",
    "SA": r"saudi|saudí|opec|opep|aramco|riyadh",
    "ZA": r"south africa|sudáfrica|\brand\b|johannesburg",
    "TR": r"turkey|turquía|turkish|erdogan|cbrt|istanbul|estambul",
}
CAT_KW = [
    ("cb", r"fed\b|fomc|ecb\b|bce\b|boj\b|boe\b|central bank|banco central|rate cut|rate hike|tipos de interés|monetary|powell|lagarde"),
    ("inf", r"inflation|inflación|cpi\b|ipc\b|deflation"),
    ("bd", r"bond|bono|yield|treasur|gilt|bund\b|deuda|auction|spread"),
    ("er", r"earnings|results|resultados|profit|beneficio|guidance|revenue|quarterly"),
    ("ma", r"merger|acquisition|adquisición|takeover|opa\b|buyout|deal\b|fusión"),
    ("en_", r"oil|crude|petróleo|brent|opec|opep|gas natural|energy|energía|barril"),
    ("cm", r"gold|oro\b|copper|cobre|commodit|materias primas|wheat|trigo"),
    ("fx", r"dollar|dólar|euro\b|yen\b|currency|divisa|forex|exchange rate|tipo de cambio"),
    ("gp", r"war|guerra|sanction|sanciones|tariff|arancel|geopolit|conflict|military|militar|ukraine|ucrania|taiwan|taiwán"),
    ("rg", r"regulat|antitrust|competencia|fine|multa|lawsuit|sec\b|probe|investigation"),
    ("tc", r"\bai\b|artificial intelligence|inteligencia artificial|chip|semiconductor|tech|tecnolog|software|nvidia|apple|microsoft|google"),
]
IMP_KW = r"crash|plunge|desplome|surge|soar|se dispara|emergency|downgrade|rebaja de rating|default|impago|crisis|recession|recesión|war|guerra|rate cut|rate hike|record high|máximo histórico|tumble|collapse"


def pct_change(hist):
    closes = hist["Close"].dropna()
    if len(closes) < 2:
        return None, None
    last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
    return last, round((last / prev - 1) * 100, 2)


def fetch_market():
    tickers = set()
    for lst in INDICES.values():
        tickers |= {tk for _, tk in lst}
    tickers |= set(FX.values()) | set(COMPANIES.values()) | {"^TNX"}
    print(f"Descargando {len(tickers)} tickers…")
    df = yf.download(list(tickers), period="1mo", interval="1d",
                     group_by="ticker", threads=True, progress=False, auto_adjust=True)

    def series(tk):
        try:
            return df[tk] if tk in df.columns.get_level_values(0) else None
        except Exception:
            return None

    out = {"updated": datetime.now(timezone.utc).isoformat(),
           "indices": {}, "fx": {}, "companies": {}, "us10y": None}

    for code, lst in INDICES.items():
        arr = []
        for name, tk in lst:
            s = series(tk)
            if s is None:
                continue
            last, chg = pct_change(s)
            if last is not None:
                arr.append({"n": name, "v": round(last), "chg": chg})
        if arr:
            out["indices"][code] = arr

    for code, tk in FX.items():
        s = series(tk)
        if s is None:
            continue
        last, chg = pct_change(s)
        if last is not None:
            out["fx"][code] = {"v": f"{last:,.3f}" if last < 100 else f"{last:,.1f}", "chg": chg}

    for web_tk, yf_tk in COMPANIES.items():
        s = series(yf_tk)
        if s is None:
            continue
        closes = s["Close"].dropna()
        if len(closes) < 2:
            continue
        last = float(closes.iloc[-1])
        d = round((last / float(closes.iloc[-2]) - 1) * 100, 2)
        w = round((last / float(closes.iloc[-6]) - 1) * 100, 2) if len(closes) >= 6 else None
        m = round((last / float(closes.iloc[0]) - 1) * 100, 2)
        out["companies"][web_tk] = {"px": round(last, 2), "d": d, "w": w, "m": m}

    s = series("^TNX")  # rendimiento 10Y de EE. UU. x10
    if s is not None:
        last, _ = pct_change(s)
        if last is not None:
            out["us10y"] = round(last / 10, 2)
    return out


def classify(text):
    tl = text.lower()
    ccs = [c for c, rx in CTY_KW.items() if re.search(rx, tl)]
    cat = next((c for c, rx in CAT_KW if re.search(rx, tl)), "eq")
    imp = "high" if re.search(IMP_KW, tl) else ("medium" if cat != "eq" else "low")
    return ccs, cat, imp


def fetch_news(limit=45):
    items, seen = [], set()
    for src, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:12]:
                title = html.unescape(getattr(e, "title", "")).strip()
                if not title:
                    continue
                key = title.lower()[:60]
                if key in seen:
                    continue
                seen.add(key)
                desc = re.sub(r"<[^>]+>", "", html.unescape(getattr(e, "summary", "")))[:220].strip()
                try:
                    date = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    date = datetime.now(timezone.utc).isoformat()
                ccs, cat, imp = classify(title + " " + desc)
                items.append({"title": title, "link": getattr(e, "link", ""), "source": src,
                              "date": date, "desc": desc, "ccs": ccs, "cat": cat, "imp": imp})
        except Exception as ex:
            print(f"  [warn] feed {src}: {ex}", file=sys.stderr)
    items.sort(key=lambda i: i["date"], reverse=True)
    return items[:limit]


def enrich_with_ai(news):
    """Opcional: si existe ANTHROPIC_API_KEY, pide a Claude resúmenes en español."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not news:
        return news
    try:
        import urllib.request
        heads = "\n".join(f"{i}. {n['title']}" for i, n in enumerate(news[:25]))
        body = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content":
                "Para cada titular numerado, devuelve SOLO un JSON array de objetos "
                '{"i":n,"resumen":"1 frase en español con el porqué importa para mercados",'
                '"impacto":"pos|neg|neu"}. Titulares:\n' + heads}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = json.loads(r.read())["content"][0]["text"]
        m = re.search(r"\[.*\]", txt, re.S)
        for row in json.loads(m.group(0)) if m else []:
            i = row.get("i")
            if isinstance(i, int) and i < len(news):
                news[i]["desc"] = row.get("resumen", news[i]["desc"])
                news[i]["ai_impact"] = row.get("impacto", "neu")
        print("IA: resúmenes añadidos.")
    except Exception as ex:
        print(f"  [warn] IA no disponible: {ex}", file=sys.stderr)
    return news


def main():
    market = fetch_market()
    (DATA / "market.json").write_text(json.dumps(market, ensure_ascii=False, indent=1))
    print(f"market.json: {len(market['indices'])} países, {len(market['companies'])} empresas")
    news = enrich_with_ai(fetch_news())
    (DATA / "news.json").write_text(json.dumps(news, ensure_ascii=False, indent=1))
    print(f"news.json: {len(news)} titulares")


if __name__ == "__main__":
    main()
