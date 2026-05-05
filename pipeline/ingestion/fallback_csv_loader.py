from pathlib import Path
import pandas as pd
import logging

def load_or_create_fallback(base_dir: Path) -> pd.DataFrame:
    """
    Loads existing raw CSV if available.
    Otherwise creates fallback dataset.
    """

    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_file = raw_dir / "sample_raw.csv"

    # ==============================
    # 3. Initial Dataset (Fallback if no raw CSV exists)
    # ==============================
    fallback_data = [
        {
            "name": "Flock Safety",
            "website": "https://www.flocksafety.com/",
            "description": "Provides the first public safety operating system.",
            "location": "Atlanta, GA, USA",
            "batch": "S2017",
            "industries": "hardware, saas, machine-learning"
        },
        {
            "name": "Deel",
            "website": "https://www.deel.com/",
            "description": "All-in-one payroll and HR platform.",
            "location": "San Francisco, CA, USA",
            "batch": "W2019",
            "industries": "hr-tech, b2b, saas, payroll, fintech"
        },
        {
            "name": "Podium",
            "website": "https://www.podium.com/",
            "description": "AI-powered lead management and communication platform.",
            "location": "Lehi, UT, USA",
            "batch": "W2016",
            "industries": "ai, saas, b2b, fintech"
        },
        {
            "name": "Algolia",
            "website": "https://www.algolia.com/",
            "description": "Leading Search & Discovery API for websites and mobile apps.",
            "location": "San Francisco, CA, USA",
            "batch": "W2014",
            "industries": "developer-tools, saas, b2b"
        },
        {
            "name": "Weave",
            "website": "https://www.getweave.com/",
            "description": "Threads together data, software, and communication platforms.",
            "location": "Lehi, UT, USA",
            "batch": "W2014",
            "industries": "saas"
        },
        {
            "name": "Flexport",
            "website": "https://www.flexport.com/",
            "description": "Platform for global logistics.",
            "location": "San Francisco, CA, USA",
            "batch": "W2014",
            "industries": "supply-chain, saas, logistics"
        },
        {
            "name": "Webflow",
            "website": "https://webflow.com/",
            "description": "No-code visual web development platform.",
            "location": "San Francisco, CA, USA",
            "batch": "S2013",
            "industries": "saas, marketing, design"
        },
        {
            "name": "Fivetran",
            "website": "https://fivetran.com/",
            "description": "Automates data movement across cloud data platforms.",
            "location": "Oakland, CA, USA",
            "batch": "W2013",
            "industries": "data-engineering, saas, analytics, b2b"
        },
        {
            "name": "Benchling",
            "website": "https://www.benchling.com/",
            "description": "R&D Cloud to power biotechnology development.",
            "location": "San Francisco, CA, USA",
            "batch": "S2012",
            "industries": "b2b, saas, biotech"
        },
        {
            "name": "Zapier",
            "website": "https://zapier.com/",
            "description": "Workflow automation platform connecting over 6,000 apps.",
            "location": "Mountain View, CA, USA",
            "batch": "S2012",
            "industries": "saas, b2b, automation"
        },
        {
            "name": "Stripe",
            "website": "https://stripe.com/",
            "description": "Builds economic infrastructure for the internet.",
            "location": "San Francisco, CA, USA",
            "batch": "S2009",
            "industries": "fintech, banking-as-a-service, saas"
        },
        {
            "name": "Ashr",
            "website": None,
            "description": "Test and evals platform that improves AI agents.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "developer-tools, data-engineering, devops, artificial-intelligence, saas"
        },
        {
            "name": "End Close",
            "website": None,
            "description": "Automatic reconciliation for payments companies.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "ai, payments, b2b, saas, fintech"
        },
        {
            "name": "Proximitty",
            "website": None,
            "description": "AI-native loan management system.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "finops, lending, b2b, fintech, saas"
        },
        {
            "name": "Wideframe",
            "website": None,
            "description": "AI agent that speeds up video work.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "artificial-intelligence, saas"
        },
        {
            "name": "Polymorph",
            "website": None,
            "description": "Helps products feel 1:1 at scale.",
            "location": None,
            "batch": "W2026",
            "industries": "marketing, analytics, artificial-intelligence, saas, b2b"
        },
        {
            "name": "Sponge",
            "website": None,
            "description": "Platform for agents to hold and spend money.",
            "location": None,
            "batch": "W2026",
            "industries": "payments, crypto-web3, fintech, artificial-intelligence, saas"
        },
        {
            "name": "Canary",
            "website": None,
            "description": "AI QA engineer that reads source code.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "b2b, saas, artificial-intelligence, developer-tools"
        },
        {
            "name": "Crosslayer Labs",
            "website": None,
            "description": "Detects impersonation attacks on websites and APIs.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "saas, b2b, cybersecurity"
        },
        {
            "name": "Maven",
            "website": None,
            "description": "Enables AI agents to collect payments over the phone.",
            "location": "San Francisco, CA, USA",
            "batch": "W2026",
            "industries": "infrastructure, conversational-ai, saas, developer-tools, fintech"
        }
    ]

    # ==============================
    # 4. Create DataFrame (Indented inside the function)
    # ==============================
    if raw_file.exists():
        df = pd.read_csv(raw_file)
        logging.info(f"Loaded raw CSV: {raw_file}")
    else:
        df = pd.DataFrame(fallback_data)
        df.to_csv(raw_file, index=False)
        logging.info(f"Created fallback CSV: {raw_file}")
    
    return df