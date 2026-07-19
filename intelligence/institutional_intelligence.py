"""
Institutional Intelligence Service

Purpose
-------
Runs 24/7 and continuously builds market intelligence.

Responsibilities
----------------
- Collect News
- Process News
- Update Market Memory
- Update Market Catalyst
- Build Evidence

Does NOT
--------
- Trade
- Connect to Dhan
- Execute Orders
- Manage Positions
"""

import time
import logging

from intelligence.intelligence_bootstrap import IntelligenceBootstrap


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# --------------------------------------------------
# Bootstrap
# --------------------------------------------------

def create_intelligence_service():

    logging.info(
        "Initializing Institutional Intelligence Service..."
    )

    bootstrap = IntelligenceBootstrap()

    logging.info(
        "Institutional Intelligence initialized."
    )

    return bootstrap

    # --------------------------------------------------
    # Main
    # --------------------------------------------------

if __name__ == "__main__":
             
        bootstrap = create_intelligence_service()

        logging.info(
             "Institutional Intelligence Service Started."
        )

        while True:
              
              try:
                    
                    total_news = bootstrap.news_engine.collect()

                    if total_news:
                        evidence_list = bootstrap.news_engine.process()

                        logging.info(
                              "Evidence Generated: %d",
                              len(evidence_list)
                        )

                        if evidence_list:
                                print(evidence_list[0])

                    time.sleep(10)

              except Exception as e:

                    logging.exception(e)

                    time.sleep(30)



                          
                          
            

        

    
        