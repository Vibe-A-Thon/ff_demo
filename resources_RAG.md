# Resources for Building Multi-Type RAG

## 📚 Academic Foundation (Papers)
* **Self-RAG:** [Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511) - *Essential for the Code Generation Agent.*
* **CRAG:** [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) - *Essential for the XAI Agent's robustness.*
* **GraphRAG:** [From Local to Global: A Graph RAG Approach](https://arxiv.org/abs/2404.16130) - *Microsoft Research paper on combining Knowledge Graphs with LLMs.*

## 🛠️ Software & Libraries
* **Orchestration:** [LangChain](https://python.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/) - *For building the Agentic state machines.*
* **Vector Database:** [ChromaDB](https://www.trychroma.com/) - *Open-source, embeddable vector store.*
* **Graph Database:** [Neo4j](https://neo4j.com/) - *Standard for Knowledge Graphs.*
* **Hybrid Search:** [Rank_BM25](https://github.com/dorianbrown/rank_bm25) - *Python implementation of Okapi BM25.*
* **Evaluation:** [Ragas](https://github.com/explodinggradients/ragas) - *Framework for evaluating RAG pipelines.*

## 💾 Datasets for Training & Testing
* **IEEE-CIS Fraud Detection:** [Kaggle Dataset](https://www.kaggle.com/c/ieee-fraud-detection) - *The gold standard for payment fraud detection. Includes transaction and identity tables.*
* **Synthetic Financial Datasets:** [FraudAmmo](https://ieeexplore.ieee.org/document/10191990/) - *Large-scale synthetic dataset for payment fraud.*
* **Credit Card Fraud Detection:** [Kaggle Dataset](https://www.kaggle.com/mlg-ulb/creditcardfraud) - *Anonymized credit card transactions labeled as fraudulent or genuine.*

## 📘 Implementation Guides & Tutorials
* **Agentic RAG with LangChain:** [KDnuggets Guide](https://www.kdnuggets.com/how-to-implement-agentic-rag-using-langchain-part-1) - *Step-by-step tutorial on building autonomous RAG agents.*
* **GraphRAG in Action:** [Towards Data Science](https://towardsdatascience.com/graphrag-in-action/) - *Guide on building a KYC fraud detection agent using Neo4j and LangChain.*
* **Hybrid RAG (Vector + BM25):** [Analytics Vidhya Guide](https://www.analyticsvidhya.com/blog/2024/12/contextual-rag-systems-with-hybrid-search-and-reranking/) - *Detailed code for setting up hybrid search.*
* **Corrective RAG Implementation:** [LangChain Cookbook](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_crag.ipynb) - *Official notebook for implementing CRAG.*