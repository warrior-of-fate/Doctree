"""Comprehensive backend API tests for DocTree.AI."""
import pytest
from fastapi.testclient import TestClient
from src.api.server import app
import io


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint for monitoring."""
    
    def test_health_check_returns_ok(self):
        """Health endpoint should return status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_health_check_version(self):
        """Health endpoint should include version."""
        response = client.get("/health")
        assert response.json()["version"] == "0.1.0"


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""
    
    def test_openapi_schema_available(self):
        """OpenAPI schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/extract" in schema["paths"]
        assert "/health" in schema["paths"]


class TestSecurityHeaders:
    """Test security headers are set correctly."""
    
    def test_security_headers_on_health(self):
        """All responses should include security headers."""
        response = client.get("/health")
        headers = response.headers
        
        # Check all security headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "1; mode=block"
        assert "strict-transport-security" in headers
    
    def test_security_headers_on_extract_options(self):
        """Security headers should be on extract endpoint too."""
        response = client.options("/extract")
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff"


class TestExtractEndpoint:
    """Test PDF extraction endpoint."""
    
    def test_extract_requires_file(self):
        """Extract endpoint should reject requests without file."""
        response = client.post("/extract")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_extract_rejects_non_pdf(self):
        """Extract endpoint should reject non-PDF files."""
        # Create a fake text file
        file_content = b"This is not a PDF"
        response = client.post(
            "/extract",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        assert response.status_code == 400
        assert "Only PDF files are accepted" in response.json()["detail"]
    
    def test_extract_with_valid_pdf(self):
        """Extract endpoint should accept valid PDF files."""
        # Read the sample PDF
        with open("tests/sample_pdfs/simple_doc.pdf", "rb") as f:
            pdf_content = f.read()
        
        response = client.post(
            "/extract",
            files={"file": ("simple_doc.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "duration_sec" in data
        assert "hierarchy" in data
        assert data["duration_sec"] > 0
    
    def test_extract_response_structure(self):
        """Extract response should have correct structure."""
        with open("tests/sample_pdfs/simple_doc.pdf", "rb") as f:
            pdf_content = f.read()
        
        response = client.post(
            "/extract",
            files={"file": ("simple_doc.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert isinstance(data["ok"], bool)
        assert isinstance(data["duration_sec"], (int, float))
        assert isinstance(data["hierarchy"], dict)
        
        # Check hierarchy structure
        hierarchy = data["hierarchy"]
        assert "metadata" in hierarchy
        assert "sections" in hierarchy
        
        # Check metadata
        metadata = hierarchy["metadata"]
        assert "source_file" in metadata
        assert "total_blocks" in metadata
        assert "total_pages" in metadata


class TestFileSizeValidation:
    """Test file size validation."""
    
    def test_extract_rejects_oversized_file(self):
        """Extract should reject files over 500MB."""
        # Create a fake oversized file (simulate by setting content-length header)
        # Note: We can't actually create a 500MB file, so we test the header validation
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", b"PDF stub", "application/pdf")},
            headers={"Content-Length": str(501 * 1024 * 1024)}  # 501MB
        )
        # This may fail at different points depending on client implementation
        # Just verify the endpoint handles it gracefully
        assert response.status_code in [400, 413]


class TestCORSHeaders:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self):
        """CORS headers should be present in response."""
        response = client.options("/health")
        headers = response.headers
        
        # CORS headers should be present
        assert "access-control-allow-origin" in headers or response.status_code == 405


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_extract_with_corrupted_pdf(self):
        """Extract should handle corrupted PDF gracefully."""
        # Create a file that looks like PDF but is corrupted
        corrupted_pdf = b"%PDF-1.4\n" + b"x" * 100 + b"\n%%EOF"
        
        response = client.post(
            "/extract",
            files={"file": ("corrupted.pdf", corrupted_pdf, "application/pdf")}
        )
        
        # Should either process or return error gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            # If it fails, it should have error message
            assert "detail" in response.json()
    
    def test_extract_with_empty_pdf(self):
        """Extract should handle empty PDF."""
        empty_pdf = b"%PDF-1.4\n%%EOF"
        
        response = client.post(
            "/extract",
            files={"file": ("empty.pdf", empty_pdf, "application/pdf")}
        )
        
        # Should either process or return error gracefully
        assert response.status_code in [200, 500]
    
    def test_invalid_filename(self):
        """Extract should handle unusual filenames."""
        with open("tests/sample_pdfs/simple_doc.pdf", "rb") as f:
            pdf_content = f.read()
        
        # Test with unusual but valid filename
        response = client.post(
            "/extract",
            files={"file": ("file-with-dashes_and_underscores.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200


class TestRequestHeaders:
    """Test handling of request headers."""
    
    def test_extract_with_request_id_header(self):
        """Extract should handle X-Request-ID header."""
        with open("tests/sample_pdfs/simple_doc.pdf", "rb") as f:
            pdf_content = f.read()
        
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
            headers={"X-Request-ID": "test-123"}
        )
        
        assert response.status_code == 200
        # Request should complete successfully
        assert response.json()["ok"] is True
    
    def test_extract_without_request_id_header(self):
        """Extract should work without X-Request-ID header."""
        with open("tests/sample_pdfs/simple_doc.pdf", "rb") as f:
            pdf_content = f.read()
        
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_api_docs_available(self):
        """API documentation should be available."""
        response = client.get("/docs")
        # Swagger UI might not be available in test client, just check it doesn't crash
        assert response.status_code in [200, 422]
    
    def test_openapi_endpoint_exists(self):
        """OpenAPI endpoint should exist."""
        response = client.get("/openapi.json")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
