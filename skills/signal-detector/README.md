# Skill: signal-detector

## Description
LLM-powered signal extraction from job descriptions. Identifies technical signals, domain alignment, career value indicators, and cultural fit markers. Uses semantic analysis to go beyond keyword matching.

## Capabilities
- `exec` - Run Python/LLM analysis scripts
- `browser` - Navigate company websites for context
- Semantic keyword extraction with weighted importance
- Career value scoring (growth potential, team scale, impact scope)
- Technical stack signal detection
- Domain expertise alignment scoring

## Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY="sk-..."
# or
ANTHROPIC_API_KEY="sk-ant-..."
```

### Detection Categories

#### ML Architecture Signals (weight: 25%)
- Foundation models, transformers, attention mechanisms
- LLMs, GPT, BERT, T5, diffusion models
- GenRec (Generative Recommendation)
- Multi-modal models, embeddings
- Distributed training, ML infrastructure

#### Domain Alignment Signals (weight: 25%)
- Virtual cell, digital twin, biology
- Drug discovery, pharma, biotech
- RecSys, personalization, recommendation systems
- Search, ranking, information retrieval
- MLOps, ML platform, ML infrastructure

#### Career Impact Signals (weight: 20%)
- Staff/Principal level scope
- Team leadership, mentoring
- Cross-functional influence
- Technical strategy involvement
- Published research, patents

#### Infrastructure Signals (weight: 15%)
- Kubernetes, Docker, cloud-native
- MLflow, Kubeflow, Tecton
- Feature store, vector database
- Real-time serving, online learning

#### Culture Signals (weight: 10%)
- Remote-first, async communication
- Open source contributions
- Academic/industry collaboration
- Diversity initiatives

## Usage

### From OpenClaw
```
Use signal-detector to analyze this job description for ML architecture signals
```

### Direct Command
```bash
cd skills/signal-detector
python detect.py --input "job_description.txt" --output "signals.json"
```

## Input Format
```json
{
  "job_description_raw": "Full JD text...",
  "company": "CZI",
  "role_title": "Staff ML Engineer"
}
```

## Output Format
```json
{
  "detected_signals": {
    "ml_architecture": {
      "transformers": true,
      "foundation_models": true,
      "genrec": false,
      "distributed_training": true,
      "confidence": 0.85
    },
    "domain_alignment": {
      "virtual_cell": true,
      "drug_discovery": true,
      "recsys": false,
      "mlops": false,
      "confidence": 0.78
    },
    "career_impact": {
      "staff_level": true,
      "technical_leadership": true,
      "research_opportunities": true,
      "confidence": 0.92
    }
  },
  "signal_strength": {
    "overall": 0.82,
    "technical": 0.85,
    "domain": 0.78,
    "career": 0.92
  },
  "recommendation": "strong_match",
  "reasoning": "High alignment with virtual cell and foundation model work. Strong technical leadership component."
}
```

## Signal Keywords Reference

### Bio-AI / Virtual Cell
```
virtual_cell, digital_twin, biological_systems, cell_simulation,
drug_discovery, molecule_design, protein_folding, genomics,
computational_biology, systems_biology, bio_ai, ai_biology,
drug_target, clinical_trial, precision_medicine, phenotyping
```

### Advanced RecSys / GenRec
```
generative_recommendation, genrec, transformer_recsys,
sequential_recommendation, two_tower, semantic_search,
embedding_store, vector_search, neural_search, ranking,
personalization, collaborative_filtering, content_filtering,
hybrid_recommender, reinforcement_learning_recs
```

### ML Infrastructure
```
ml_platform, ml_infrastructure, feature_store, vector_database,
ml_pipeline, data_pipeline, etl, data_engineering,
kubernetes, kubeflow, mlflow, tensorflow, pytorch,
serving, inference, online_learning, batch_inference
```

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API failure | Retry 3x with exponential backoff |
| Invalid input | Return empty signals, log error |
| Rate limited | Queue and retry after cooldown |

## Dependencies
- openai or anthropic
- python3.10+
- rich (for logging)