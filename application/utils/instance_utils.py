import yfinance as yf
import pandas as pd
import numpy as np
import os


def get_financial_assets(num_of_asset_types=4):
    # Set date range
    start_range = ["2024-01-01", "2025-01-01"]

    # Get assets
    assets_dict = _get_assets_dict(num_of_asset_types)

    return {asset_type: _get_assets_instances(asset_type, assets, start_range) for asset_type, assets in assets_dict.items()}


def _get_assets_dict(num_of_asset_types=4):
    bonds = [
        "AGG", "BND", "LQD", "TLT", "IEF", "SHY", "BSV", "BIV", "BLV", "JNK",
        "HYG", "SPAB", "SCHZ", "GOVT", "VGSH", "VGIT", "VGLT", "IGSB", "IGIB", "IGLB",
        "SHYG", "SPSB", "SPIB", "SPLB", "TFLO", "BIL", "SHV", "MINT", "JPST", "GBIL",
        "TIPX", "TIP", "SCHP", "VTIP", "STIP", "IGOV", "BWX", "BNDX", "EMB",
        "EMLC", "LEMB", "EBND", "TOTL", "FBND", "NUBD", "GVI", "SMMU", "VCSH", "VCLT",
        "VCIT", "VMBS", "MBSD", "SRLN", "HYLB", "HYGH", "IHY", "ISHG", "WIP", "CWB",
        "ANGL", "FALN", "FLOT", "FLTR", "BOND", "FIBR", "GNMA", "TFI", "HYD", "PZA",
        "MUB", "SUB", "SHM", "CMF", "NYF", "VTEB", "PAB", "VUSB", "ICSH", "NEAR",
        "FTSD", "ULST", "SPSK", "IBND", "HYS", "HYXU", "VWOB", "CEMB", "IAGG", "QLTA",
        "PLW", "EDV", "ZROZ", "GOVZ", "USFR", "RIGS", "FLRN", "VRIG", "TUA", "FTGC"
    ]

    stocks = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA","AVGO",
        "LLY", "JPM", "UNH", "V", "JNJ", "XOM", "WMT", "MA", "PG", "HD",
        "CVX", "COST", "MRK", "ABBV", "PEP", "PFE", "KO", "INTC", "CSCO", "TMO",
        "ORCL", "ACN", "ADBE", "CRM", "CMCSA", "MCD", "TXN", "DHR", "NKE", "BMY",
        "NEE", "RTX", "LMT", "GE", "INTU", "QCOM", "SBUX", "AMGN", "LOW", "CAT",
        "AXP", "CVS", "CHTR", "GILD", "BA", "MDT", "GM", "HON", "MMM", "CL",
        "MDLZ", "MO", "SO", "GS", "DIS", "IBM", "SCHW", "BK", "MS", "C",
        "WFC", "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "TRV", "PGR",
        "ALL", "CB", "AON", "MMC", "CI", "HUM", "CNC", "UPS", "FDX",
        "UNP", "NSC", "CSX", "AMT", "CCI", "EQIX", "DLR", "SPG", "PSA", "O"
    ]

    commodities = [
        "DBC", "PDBC", "USCI", "GSG", "COMT", "BCI", "DJP", "CMDY", "USO", "BNO",
        "UCO", "SCO", "UNG", "BOIL", "KOLD", "GLD", "IAU", "SGOL", "BAR",
        "SLV", "SIVR", "PLTM", "PPLT", "PALL", "CPER", "CORN", "WEAT", "SOYB",
        "CANE", "UGA", "DBB", "FTGC", "XOP", "XME", "PICK", "REMX", "URA"
    ]

    cryptos = [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "TON11419-USD", "SHIB-USD",
        "DOT-USD", "TRX-USD", "LINK-USD", "MATIC-USD", "BCH-USD", "LTC-USD", "UNI7083-USD", "ICP-USD", "NEAR-USD", "ETC-USD",
        "XLM-USD", "APT21794-USD", "IMX10603-USD", "FIL-USD", "INJ-USD", "HBAR-USD", "VET-USD", "MKR-USD", "ARB11841-USD",
        "QNT-USD", "RUNE-USD", "LDO-USD", "AAVE-USD", "EGLD-USD", "STX-USD", "SAND-USD", "AXS-USD", "XTZ-USD",
        "KAS-USD", "XMR-USD", "THETA-USD", "SNX-USD", "MANA-USD", "CRV-USD", "CHZ-USD", "ZEC-USD", "ENS-USD", "DYDX-USD"
    ]

    assets_dict = {
        "bonds": bonds,
        "stocks": stocks,
        "commodities": commodities,
        "cryptos": cryptos
    }

    return dict(list(assets_dict.items())[:num_of_asset_types])


def _get_assets_instances(asset_type, assets, start_range):
    """
    Return instance of asset list
    """
    n = len(assets)

    # Load from dataset or download and save
    datasets_path = "datasets/yahoo_finance"
    cache_path = datasets_path + "/" + asset_type + ".csv"
    os.makedirs(datasets_path, exist_ok=True)
    if os.path.exists(cache_path):
        price_data = pd.read_csv(cache_path, index_col=0, parse_dates=True)
    else:
        price_data = yf.download(assets, start=start_range[0], end=start_range[1])["Close"]
        price_data.to_csv(cache_path)

    # Compute parameters for instance
    daily_returns = price_data.pct_change().dropna()
    mean = daily_returns.mean().values
    correlation_matrix = daily_returns.corr().values
    sigma = np.cov(daily_returns.to_numpy().T)
    asset_pairs = {(i, j) for i in range(n) for j in range(i + 1, n)}

    return assets, mean, correlation_matrix, sigma, asset_pairs