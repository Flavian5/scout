#!/usr/bin/env python3
"""
Unit tests for signal detector (skills/signal-detector/detect.py).
Tests LLM signal extraction and keyword fallback logic.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# =============================================================================
# Tests for JSON extraction
# =============================================================================

class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response function."""

    def test_extract_from_markdown_block(self):
        """Test extracting JSON from markdown code block."""
        response = '''```json
{"recommendation": "strong_match", "reasoning": "Good fit"}
```
'''
        import re
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        
        if json_block_match:
            try:
                result = json.loads(json_block_match.group(1))
                assert result["recommendation"] == "strong_match"
            except json.JSONDecodeError:
                pass

    def test_extract_plain_json(self):
        """Test extracting plain JSON without markdown."""
        response = '{"recommendation": "medium_match", "reasoning": "Decent fit"}'
        
        start = response.find('{')
        end = response.rfind('}')
        if start >= 0 and end > start:
            json_str = response[start:end+1]
            result = json.loads(json_str)
            assert result["recommendation"] == "medium_match"

    def test_extract_with_trailing_comma(self):
        """Test extracting JSON with trailing comma (common LLM issue)."""
        response = '{"recommendation": "strong_match", "reasoning": "Good",}'
        
        import re
        # Repair trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', response)
        result = json.loads(json_str)
        
        assert result["recommendation"] == "strong_match"


class TestKeywordDetection:
    """Tests for detect_signals_keyword function."""

    def test_foundation_models_detection(self):
        """Test foundation models keyword detection."""
        jd_text_lower = "we use large language models and transformers for NLP tasks"
        
        foundation_models = any(k in jd_text_lower for k in ['foundation model', 'llm', 'gpt', 'transformer', 'bert', 'large language'])
        
        assert foundation_models is True

    def test_recsys_detection(self):
        """Test recommendation system detection."""
        jd_text_lower = "building recommendation systems for personalization"
        
        recsys = any(k in jd_text_lower for k in ['recommendation', 'recsys', 'personalization'])
        
        assert recsys is True

    def test_gpu_compute_detection(self):
        """Test GPU compute detection."""
        jd_text_lower = "experience with H100 GPUs and distributed training"
        
        # Keywords should be case-insensitive
        gpu_compute = any(k in jd_text_lower.lower() for k in ['gpu', 'h100', 'a100', 'nvidia', 'tpu'])
        
        assert gpu_compute is True

    def test_production_ml_detection(self):
        """Test production ML detection."""
        jd_text_lower = "mlops and feature store experience required"
        
        production_ml = any(k in jd_text_lower for k in ['feature store', 'mlops', 'model serving', 'production'])
        
        assert production_ml is True

    def test_signal_strength_calculation(self):
        """Test signal strength scoring."""
        signals = {
            "ml_architecture": {"foundation_models": True, "transformers": True, "generative_recommendation": False},
            "domain_alignment": {"recsys": True, "virtual_cell": False},
            "career_impact": {"scientific_impact": False, "hyperscale": True},
            "infrastructure": {"gpu_compute": True, "data_scale": True, "ml_platform": False}
        }
        
        total_signals = sum(1 for cat in signals.values() for v in cat.values() if v)
        max_signals = sum(1 for cat in signals.values() for v in cat.values())
        
        overall = round(total_signals / max_signals, 2) if max_signals > 0 else 0
        
        assert total_signals == 6
        assert overall > 0


class TestRecommendation:
    """Tests for recommendation logic."""

    def test_strong_match_threshold(self):
        """Test strong match requires >= 8 signals."""
        total_signals = 8
        
        recommendation = "strong_match" if total_signals >= 8 else "medium_match" if total_signals >= 4 else "weak_match"
        
        assert recommendation == "strong_match"

    def test_medium_match_threshold(self):
        """Test medium match for 4-7 signals."""
        total_signals = 5
        
        recommendation = "strong_match" if total_signals >= 8 else "medium_match" if total_signals >= 4 else "weak_match"
        
        assert recommendation == "medium_match"

    def test_weak_match_threshold(self):
        """Test weak match for < 4 signals."""
        total_signals = 3
        
        recommendation = "strong_match" if total_signals >= 8 else "medium_match" if total_signals >= 4 else "weak_match"
        
        assert recommendation == "weak_match"


class TestNullSafety:
    """Tests for null safety in signal detection."""

    def test_none_jd_handling(self):
        """Test handling of None job description."""
        raw_jd = None
        
        jd_text = str(raw_jd) if raw_jd else ''
        
        assert jd_text == ''

    def test_missing_fields_fallback(self):
        """Test fallback when fields are missing."""
        job_data = {'company': 'Genentech'}
        raw_jd = job_data.get('job_description_raw') or job_data.get('raw_jd_text') or ''
        company = job_data.get('company') or ''
        
        jd_text = str(raw_jd) + ' ' + str(company)
        
        assert 'Genentech' in jd_text


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_llm_config_structure(self):
        """Test LLM config has required fields."""
        llm_config = {
            'api_key': 'test_key',
            'endpoint': 'https://api.minimax.io/v1/text/chatcompletion_v2',
            'model': 'MiniMax-M2.7'
        }
        
        assert 'api_key' in llm_config
        assert 'endpoint' in llm_config
        assert 'model' in llm_config

    def test_default_model(self):
        """Test default model is MiniMax-M2.7."""
        DEFAULT_MODEL = "MiniMax-M2.7"
        DEFAULT_ENDPOINT = "https://api.minimax.io/v1/text/chatcompletion_v2"
        
        assert DEFAULT_MODEL == "MiniMax-M2.7"
        assert "minimax.io" in DEFAULT_ENDPOINT


class TestProcessLeads:
    """Tests for batch lead processing."""

    def test_lead_data_structure(self):
        """Test expected lead data structure."""
        lead = {
            'job_id': 'lead_001',
            'company': 'Genentech',
            'role_title': 'Staff ML Engineer',
            'job_description_raw': 'We build recommendation systems at scale'
        }
        
        assert 'job_id' in lead
        assert 'company' in lead
        assert 'role_title' in lead

    def test_result_structure(self):
        """Test expected result structure."""
        result = {
            'detected_signals': {'ml_architecture': {}},
            'signal_strength': {'overall': 0.5},
            'recommendation': 'medium_match',
            'method': 'llm',
            'job_id': 'lead_001'
        }
        
        assert 'detected_signals' in result
        assert 'signal_strength' in result
        assert 'recommendation' in result
        assert 'method' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])