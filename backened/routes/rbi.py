from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.cache import cache

router = APIRouter()

@router.get("/rates")
async def get_rbi_rates():

    rates = {
        "source": "RBI Monetary Policy Committee",
        "last_updated": "April 9, 2026",
        "next_mpc": "June 4-6, 2026",
        "policy_stance": "Neutral",
        "rates": {
            "repo_rate": {
                "value": 6.00,
                "unit": "%",
                "description": "Rate at which RBI lends to commercial banks",
                "last_change": "Cut by 25 bps on April 9, 2026"
            },
            "reverse_repo_rate": {
                "value": 3.35,
                "unit": "%",
                "description": "Rate at which RBI borrows from commercial banks"
            },
            "crr": {
                "value": 4.00,
                "unit": "%",
                "description": "Cash Reserve Ratio — % of deposits banks must keep with RBI",
                "last_change": "Cut by 50 bps in Dec 2024"
            },
            "slr": {
                "value": 18.00,
                "unit": "%",
                "description": "Statutory Liquidity Ratio — % held in govt securities"
            },
            "msf_rate": {
                "value": 6.25,
                "unit": "%",
                "description": "Marginal Standing Facility rate (Repo + 25 bps)"
            },
            "bank_rate": {
                "value": 6.25,
                "unit": "%",
                "description": "Rate at which RBI provides long-term funds"
            },
        },
        "forex_reserves": {
            "total_usd_billion": 688.3,
            "as_of": "April 11, 2026"
        },
        "inflation": {
            "cpi_yoy_pct": 3.34,
            "rbi_target_band": "2% - 6%",
            "as_of": "March 2026"
        },
        "gdp_growth": {
            "fy2025_26_estimate": "6.7%",
            "source": "RBI Annual Report"
        }
    }
    return rates

@router.get("/bonds")
async def get_gsec_bonds():
    bonds = {
        "source": "RBI / CCIL (simulated — integrate CCIL API for live data)",
        "timestamp": datetime.now().isoformat(),
        "gsec": [
            {"maturity": "91-Day T-Bill",  "yield": 6.28, "type": "T-Bill",  "face_value": 100},
            {"maturity": "182-Day T-Bill", "yield": 6.42, "type": "T-Bill",  "face_value": 100},
            {"maturity": "364-Day T-Bill", "yield": 6.55, "type": "T-Bill",  "face_value": 100},
            {"maturity": "2-Year G-SEC",   "yield": 6.67, "type": "G-SEC",   "face_value": 100},
            {"maturity": "5-Year G-SEC",   "yield": 6.82, "type": "G-SEC",   "face_value": 100},
            {"maturity": "10-Year G-SEC",  "yield": 6.98, "type": "G-SEC",   "face_value": 100, "benchmark": True},
            {"maturity": "30-Year G-SEC",  "yield": 7.15, "type": "G-SEC",   "face_value": 100},
        ],
        "sgb": {
            "name": "Sovereign Gold Bond",
            "interest_rate": "2.50% per annum (semi-annual)",
            "tenure": "8 years (exit after 5 years)",
            "tax": "Capital gains tax exempt on maturity",
            "how_to_buy": "Through banks, Post Office, NSE/BSE, RBI Retail Direct"
        },
        "rbi_retail_direct": {
            "url": "https://rbiretaildirect.org.in",
            "min_investment": "₹10,000",
            "description": "Buy G-SEC directly from RBI — no broker needed"
        },
        "yield_curve_note": "Inverted/flat curve signals market expects rate cuts."
    }
    return bonds

@router.get("/msme-schemes")
async def get_msme_schemes():
    schemes = {
        "title": "Government MSME Financing Schemes",
        "schemes": [
            {
                "name": "MUDRA Loan (PM Mudra Yojana)",
                "categories": {
                    "Shishu": "Up to ₹50,000",
                    "Kishore": "₹50,001 – ₹5 Lakh",
                    "Tarun": "₹5 Lakh – ₹10 Lakh",
                    "Tarun Plus": "₹10 Lakh – ₹20 Lakh (new FY25)",
                },
                "collateral": "None required",
                "eligibility": "Any non-farm business enterprise",
                "apply_at": "Banks, MFIs, NBFCs",
                "portal": "https://www.mudra.org.in"
            },
            {
                "name": "CGTMSE (Credit Guarantee Fund Trust for MSEs)",
                "loan_limit": "Up to ₹5 Crore",
                "collateral": "None (guarantee covers up to 85% of loan)",
                "eligibility": "Micro and Small enterprises",
                "note": "Banks lend freely as RBI-backed guarantee covers default risk",
                "portal": "https://www.cgtmse.in"
            },
            {
                "name": "Stand-Up India",
                "loan_range": "₹10 Lakh – ₹1 Crore",
                "target": "SC/ST entrepreneurs and women",
                "purpose": "Greenfield enterprise in manufacturing/services/trading",
                "portal": "https://www.standupmitra.in"
            },
            {
                "name": "PM SVANidhi (Street Vendors)",
                "loan_tiers": {
                    "1st loan": "₹10,000",
                    "2nd loan": "₹20,000",
                    "3rd loan": "₹50,000"
                },
                "interest_subsidy": "7% per annum",
                "portal": "https://pmsvanidhi.mohua.gov.in"
            },
            {
                "name": "SIDBI Loans",
                "description": "Small Industries Development Bank of India — direct MSME loans",
                "loan_range": "₹10 Lakh – ₹25 Crore",
                "interest_rate": "Starting ~8.5% p.a.",
                "portal": "https://www.sidbi.in"
            },
            {
                "name": "Emergency Credit Line Guarantee Scheme (ECLGS)",
                "description": "Covid-era scheme, check current status on portal",
                "portal": "https://www.ncgtc.in/eclgs"
            },
            {
                "name": "Udyam Registration",
                "description": "FREE MSME registration — mandatory to access all schemes",
                "portal": "https://udyamregistration.gov.in",
                "note": "Register first before applying for any scheme"
            }
        ],
        "definition": {
            "Micro": "Investment < ₹1 Cr, Turnover < ₹5 Cr",
            "Small": "Investment < ₹10 Cr, Turnover < ₹50 Cr",
            "Medium": "Investment < ₹50 Cr, Turnover < ₹250 Cr"
        }
    }
    return schemes

@router.get("/fd-rates")
async def get_fd_rates():
    return {
        "title": "Bank FD Rates — Senior Citizen rates are 0.25-0.50% higher",
        "last_updated": "April 2026",
        "note": "Rates change frequently. Verify with respective bank.",
        "banks": [
            {"bank": "SBI",          "1yr": 6.80, "3yr": 6.75, "5yr": 6.50, "type": "PSU"},
            {"bank": "HDFC Bank",    "1yr": 7.10, "3yr": 7.00, "5yr": 7.00, "type": "Private"},
            {"bank": "ICICI Bank",   "1yr": 7.10, "3yr": 7.00, "5yr": 7.00, "type": "Private"},
            {"bank": "Axis Bank",    "1yr": 7.10, "3yr": 7.10, "5yr": 7.00, "type": "Private"},
            {"bank": "Kotak Bank",   "1yr": 7.10, "3yr": 7.00, "5yr": 6.90, "type": "Private"},
            {"bank": "IDFC First",   "1yr": 7.25, "3yr": 7.25, "5yr": 7.00, "type": "Private"},
            {"bank": "IndusInd",     "1yr": 7.75, "3yr": 7.50, "5yr": 7.25, "type": "Private"},
            {"bank": "Small Finance Banks", "1yr": "8.50-9.00", "3yr": "8.00-9.00", "5yr": "7.50-8.50", "type": "SFB"},
        ],
        "tax_note": "FD interest fully taxable as per your income slab. TDS at 10% if interest > ₹40,000/year (₹50,000 for seniors)."
    }
