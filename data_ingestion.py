import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyDataIngestion:
    """Enhanced policy documentation ingestion from real Apigee docs"""
    
    def __init__(self):
        self.policy_docs_path = "./processed_docs/policy_docs.json"
        # Real Apigee policy documentation URLs
        self.apigee_policy_urls = [
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/verify-api-key-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/oauth-v20-policy", 
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/javascript-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/service-callout-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/cors-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/spike-arrest-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/quota-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/assign-message-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/extract-variables-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/raise-fault-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/json-to-xml-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/xml-to-json-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/json-threat-protection-policy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/regular-expression-protection",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies/response-cache-policy"
        ]
    
    def scrape_policy_documentation(self) -> List[Document]:
        """Scrape real policy documentation from Apigee docs"""
        logger.info("🔧 Scraping real Apigee policy documentation...")
        
        policy_documents = []
        
        for i, url in enumerate(self.apigee_policy_urls):
            try:
                logger.info(f"Scraping policy {i+1}/{len(self.apigee_policy_urls)}: {url}")
                
                # Add delay to be respectful
                if i > 0:
                    time.sleep(2)
                
                # Load the policy page
                loader = WebBaseLoader([url])
                docs = loader.load()
                
                for doc in docs:
                    if doc.page_content and len(doc.page_content.strip()) > 100:
                        # Extract policy name from URL
                        policy_name = self._extract_policy_name_from_url(url)
                        
                        doc.metadata.update({
                            'source': url,
                            'category': 'policy_reference',
                            'type': 'policy_doc',
                            'title': f'{policy_name} Policy Reference',
                            'policy_name': policy_name,
                            'scraped_from': 'apigee_docs'
                        })
                        policy_documents.append(doc)
                        logger.info(f"Added policy doc: {policy_name}")
                
            except Exception as e:
                logger.error(f"Error scraping policy {url}: {str(e)}")
                continue
        
        logger.info(f"✅ Scraped {len(policy_documents)} policy documents from real Apigee docs")
        return policy_documents
    
    def _extract_policy_name_from_url(self, url: str) -> str:
        """Extract policy name from Apigee documentation URL"""
        try:
            # Extract from URL pattern like: .../policies/verify-api-key-policy
            path_parts = url.split('/')
            policy_slug = path_parts[-1]  # e.g., "verify-api-key-policy"
            
            # Convert to policy name
            name_mapping = {
                "verify-api-key-policy": "VerifyAPIKey",
                "oauth-v20-policy": "OAuthV2", 
                "javascript-policy": "JavaScript",
                "service-callout-policy": "ServiceCallout",
                "cors-policy": "CORS",
                "spike-arrest-policy": "SpikeArrest",
                "quota-policy": "Quota",
                "assign-message-policy": "AssignMessage",
                "extract-variables-policy": "ExtractVariables",
                "raise-fault-policy": "RaiseFault",
                "json-to-xml-policy": "JSONToXML",
                "xml-to-json-policy": "XMLToJSON",
                "json-threat-protection-policy": "JSONThreatProtection",
                "regular-expression-protection": "RegularExpressionProtection",
                "response-cache-policy": "ResponseCache"
            }
            
            return name_mapping.get(policy_slug, policy_slug.replace('-', '').title())
            
        except:
            return "UnknownPolicy"
    
    def create_minimal_policy_catalog(self) -> Dict[str, Any]:
        """Create minimal policy catalog with just essentials"""
        
        # Minimal policy info for keyword matching - no long XML templates
        minimal_policies = {
            "VerifyAPIKey": {
                "category": "security",
                "keywords": ["api key", "apikey", "key auth", "verify key", "authentication"]
            },
            "OAuthV2": {
                "category": "security", 
                "keywords": ["oauth", "oauth2", "access token", "bearer token", "authorization"]
            },
            "JavaScript": {
                "category": "logic",
                "keywords": ["javascript", "js", "custom logic", "script", "code execution"]
            },
            "ServiceCallout": {
                "category": "external",
                "keywords": ["service callout", "http callout", "external api", "backend call"]
            },
            "CORS": {
                "category": "headers",
                "keywords": ["cors", "cross origin", "browser", "frontend", "web app"]
            },
            "SpikeArrest": {
                "category": "traffic",
                "keywords": ["spike", "traffic spike", "ddos", "burst protection"]
            },
            "Quota": {
                "category": "traffic",
                "keywords": ["rate limit", "throttle", "quota", "usage limit"]
            },
            "AssignMessage": {
                "category": "headers",
                "keywords": ["add header", "set header", "modify request", "assign message"]
            },
            "ExtractVariables": {
                "category": "headers",
                "keywords": ["extract", "parse", "get value", "json path", "xpath"]
            },
            "RaiseFault": {
                "category": "error_handling",
                "keywords": ["error", "fault", "raise error", "custom error", "exception"]
            },
            "JSONToXML": {
                "category": "transformation",
                "keywords": ["json to xml", "xml transform", "convert json", "transformation"]
            },
            "XMLToJSON": {
                "category": "transformation",
                "keywords": ["xml to json", "json transform", "convert xml"]
            },
            "JSONThreatProtection": {
                "category": "validation",
                "keywords": ["validate json", "json validation", "json threat", "security"]
            },
            "RegularExpressionProtection": {
                "category": "validation",
                "keywords": ["regex", "regular expression", "pattern validation", "input validation"]
            },
            "ResponseCache": {
                "category": "caching",
                "keywords": ["cache", "caching", "response cache", "performance"]
            }
        }
        
        policy_catalog = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "source": "minimal_catalog_with_scraped_docs",
                "total_policies": len(minimal_policies)
            },
            "policies": minimal_policies
        }
        
        # Save minimal catalog
        os.makedirs(os.path.dirname(self.policy_docs_path), exist_ok=True)
        with open(self.policy_docs_path, 'w', encoding='utf-8') as f:
            json.dump(policy_catalog, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Created minimal policy catalog with {len(minimal_policies)} policies")
        return policy_catalog

class ApigeeDocsIngestion:
    def __init__(self):
        self.base_urls = [
            "https://cloud.google.com/apigee/docs/api-platform/fundamentals/what-is-apigee",
            "https://cloud.google.com/apigee/docs/api-platform/get-started/what-you-need-to-get-started",
            "https://cloud.google.com/apigee/docs/api-platform/fundamentals/understanding-apis-and-api-proxies",
            "https://cloud.google.com/apigee/docs/api-platform/develop/creating-an-api-proxy",
            "https://cloud.google.com/apigee/docs/api-platform/reference/policies",
            "https://cloud.google.com/apigee/docs/api-platform/security/api-security",
            "https://cloud.google.com/apigee/docs/api-platform/develop/deploying-proxies-ui"
        ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create directories
        os.makedirs("./processed_docs", exist_ok=True)
        os.makedirs("./raw_docs", exist_ok=True)
    
    def scrape_apigee_docs(self):
        """Scrape Apigee documentation"""
        documents = []
        
        logger.info("Starting Apigee documentation scraping...")
        
        for i, url in enumerate(self.base_urls):
            try:
                logger.info(f"Processing {i+1}/{len(self.base_urls)}: {url}")
                
                # Add delay to be respectful to the server
                if i > 0:
                    time.sleep(2)
                
                # Load the webpage
                loader = WebBaseLoader([url])
                docs = loader.load()
                
                for doc in docs:
                    # Clean and enrich the document
                    if doc.page_content and len(doc.page_content.strip()) > 100:
                        doc.metadata.update({
                            'source': url,
                            'category': self._categorize_url(url),
                            'type': 'web_doc',
                            'title': self._extract_title_from_url(url)
                        })
                        documents.append(doc)
                        logger.info(f"Added document: {doc.metadata.get('title', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                continue
        
        logger.info(f"Successfully loaded {len(documents)} web documents")
        return documents
    
    def load_pdf_docs(self):
        """Load PDF documents from raw_docs directory"""
        documents = []
        pdf_dir = "./raw_docs"
        
        if not os.path.exists(pdf_dir):
            logger.warning(f"PDF directory {pdf_dir} not found, skipping PDF loading")
            return documents
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.info("No PDF files found in raw_docs directory")
            return documents
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(pdf_dir, pdf_file)
                loader = PyPDFLoader(pdf_path)
                docs = loader.load()
                
                for doc in docs:
                    doc.metadata.update({
                        'source': pdf_file,
                        'category': 'reference',
                        'type': 'pdf_doc'
                    })
                    documents.append(doc)
                
                logger.info(f"Loaded PDF: {pdf_file} ({len(docs)} pages)")
                
            except Exception as e:
                logger.error(f"Error loading PDF {pdf_file}: {str(e)}")
        
        return documents
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL based on content"""
        url_lower = url.lower()
        
        if 'fundamentals' in url_lower or 'what-is' in url_lower:
            return 'fundamentals'
        elif 'get-started' in url_lower:
            return 'getting_started'
        elif 'develop' in url_lower or 'creating' in url_lower:
            return 'development'
        elif 'security' in url_lower:
            return 'security'
        elif 'policies' in url_lower or 'reference' in url_lower:
            return 'reference'
        elif 'deploy' in url_lower:
            return 'deployment'
        else:
            return 'general'
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL"""
        try:
            path = urlparse(url).path
            title = path.split('/')[-1].replace('-', ' ').title()
            return title if title else "Apigee Documentation"
        except:
            return "Apigee Documentation"
    
    def process_documents(self, documents):
        """Process documents into chunks"""
        if not documents:
            logger.warning("No documents to process!")
            return []
        
        logger.info(f"Processing {len(documents)} documents into chunks...")
        
        all_texts = []
        for doc in documents:
            try:
                # Split the document into chunks
                chunks = self.text_splitter.split_documents([doc])
                
                for i, chunk in enumerate(chunks):
                    # Add chunk metadata
                    chunk.metadata.update({
                        'chunk_id': f"{doc.metadata.get('source', 'unknown')}_{i}",
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    })
                    all_texts.append(chunk)
                    
            except Exception as e:
                logger.error(f"Error processing document {doc.metadata.get('source', 'unknown')}: {str(e)}")
        
        logger.info(f"Created {len(all_texts)} text chunks")
        return all_texts
    
    def save_processed_docs(self, texts, output_path=None):
        """Save processed documents to JSON"""
        if output_path is None:
            output_path = "./processed_docs/processed_docs.json"
        
        if not texts:
            logger.warning("No texts to save!")
            return
        
        # Convert to serializable format
        doc_data = []
        for text in texts:
            doc_data.append({
                'content': text.page_content,
                'metadata': text.metadata
            })
        
        # Save to JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(doc_data)} processed documents to {output_path}")
        
        # Also save by category
        self._save_by_category(doc_data)
    
    def _save_by_category(self, doc_data):
        """Save documents organized by category"""
        categories = {}
        
        for doc in doc_data:
            category = doc['metadata'].get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(doc)
        
        # Save each category
        for category, docs in categories.items():
            category_path = f"./processed_docs/{category}_docs.json"
            with open(category_path, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(docs)} documents to {category}_docs.json")
    
    def create_documentation_index(self, texts):
        """Create an index of all documentation"""
        if not texts:
            return {}
        
        index = {
            'total_documents': len(texts),
            'categories': {},
            'sources': {},
            'types': {}
        }
        
        for text in texts:
            metadata = text.metadata
            
            # Count by category
            category = metadata.get('category', 'unknown')
            index['categories'][category] = index['categories'].get(category, 0) + 1
            
            # Count by source
            source = metadata.get('source', 'unknown')
            index['sources'][source] = index['sources'].get(source, 0) + 1
            
            # Count by type
            doc_type = metadata.get('type', 'unknown')
            index['types'][doc_type] = index['types'].get(doc_type, 0) + 1
        
        # Save index
        with open('./processed_docs/documentation_index.json', 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        logger.info("Documentation index created")
        return index
    
    def run_full_ingestion(self):
        """Run the complete ingestion process including policies"""
        logger.info("=== Starting Full Documentation Ingestion (with Real Policy Docs) ===")
        
        # Load all documents
        all_documents = []
        
        # 1. Load web documents
        web_docs = self.scrape_apigee_docs()
        all_documents.extend(web_docs)
        
        # 2. Load PDF documents  
        pdf_docs = self.load_pdf_docs()
        all_documents.extend(pdf_docs)
        
        # 3. **NEW: Scrape real policy documentation**
        policy_ingestion = PolicyDataIngestion()
        policy_docs = policy_ingestion.scrape_policy_documentation()
        all_documents.extend(policy_docs)  # Add scraped policy docs
        
        # 4. Create minimal policy catalog for keyword matching
        policy_ingestion.create_minimal_policy_catalog()
        
        if not all_documents:
            logger.error("No documents were loaded!")
            self._create_fallback_docs()
            return self._load_fallback_docs()
        
        # 5. Process documents
        processed_texts = self.process_documents(all_documents)
        
        if not processed_texts:
            logger.error("No texts were processed!")
            return self._load_fallback_docs()
        
        # 6. Save processed documents
        self.save_processed_docs(processed_texts)
        
        # 7. Create index
        index = self.create_documentation_index(processed_texts)
        
        logger.info("=== Ingestion Complete (with Real Policy Documentation) ===")
        return processed_texts, index
    
    def _create_fallback_docs(self):
        """Create minimal fallback documentation"""
        logger.info("Creating fallback documentation...")
        
        fallback_content = [
            {
                "content": """
Apigee is Google Cloud's API management platform that provides a comprehensive set of capabilities to design, secure, deploy, monitor, and scale APIs.

Key Features:
- API Proxy creation and management
- Security policies (OAuth, API Keys, JWT)
- Rate limiting and quota management
- Analytics and monitoring
- Developer portal
- API monetization

Basic Proxy Creation Steps:
1. Create a new API proxy
2. Define the target endpoint
3. Configure security policies
4. Set up rate limiting
5. Deploy to environment
6. Test the proxy
                """,
                "metadata": {
                    "source": "fallback_overview",
                    "category": "fundamentals",
                    "type": "fallback",
                    "title": "Apigee Overview"
                }
            },
            {
                "content": """
Common Apigee Policies:

1. API Key Verification
   - Validates API keys sent by client applications
   - Can extract developer and application information

2. OAuth v2.0
   - Implements OAuth 2.0 authentication flows
   - Supports various grant types

3. CORS (Cross-Origin Resource Sharing)
   - Handles browser cross-origin requests
   - Configurable origins, methods, headers

4. Spike Arrest
   - Protects against traffic spikes
   - Smooths out request bursts

5. Rate Limiting
   - Controls request rate per time period
   - Can be applied per developer/app

6. JSON to XML Transform
   - Converts between JSON and XML formats
   - Useful for legacy system integration
                """,
                "metadata": {
                    "source": "fallback_policies",
                    "category": "reference",
                    "type": "fallback",
                    "title": "Apigee Policies Reference"
                }
            }
        ]
        
        os.makedirs("./processed_docs", exist_ok=True)
        with open("./processed_docs/processed_docs.json", 'w', encoding='utf-8') as f:
            json.dump(fallback_content, f, indent=2, ensure_ascii=False)
        
        logger.info("Fallback documentation created")
    
    def _load_fallback_docs(self):
        """Load fallback documentation"""
        try:
            with open("./processed_docs/processed_docs.json", 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            texts = []
            for item in doc_data:
                doc = Document(
                    page_content=item['content'],
                    metadata=item['metadata']
                )
                texts.append(doc)
            
            index = self.create_documentation_index(texts)
            return texts, index
            
        except Exception as e:
            logger.error(f"Error loading fallback docs: {str(e)}")
            return [], {}

if __name__ == "__main__":
    ingestion = ApigeeDocsIngestion()
    
    try:
        texts, index = ingestion.run_full_ingestion()
        
        print(f"\n=== Documentation Ingestion Summary ===")
        print(f"Total chunks created: {len(texts)}")
        
        if index and 'categories' in index:
            print(f"Categories: {list(index['categories'].keys())}")
            print(f"Documents by category:")
            for category, count in index['categories'].items():
                print(f"  - {category}: {count} chunks")
        
        print(f"\nFiles created:")
        print(f"  - ./processed_docs/processed_docs.json")
        print(f"  - ./processed_docs/documentation_index.json")
        print(f"  - Category-specific JSON files")
        
        if texts:
            print(f"\n✅ Ingestion successful! Ready to run main.py")
        else:
            print(f"\n⚠️ No documents processed, but fallback created")
            
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        print(f"\n❌ Ingestion failed: {str(e)}")