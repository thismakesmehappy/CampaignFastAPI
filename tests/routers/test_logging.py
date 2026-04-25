import logging

class TestRequestLogging:
    async def test_successful_request_logs_at_info(self, client, caplog):
        with caplog.at_level(logging.INFO, logger="app.middleware"):
            await client.get("/campaigns/")
        assert any("REQUEST GET /campaigns/" in r.message for r in caplog.records)
        assert any(r.levelname == "INFO" and r.name == "app.middleware" for r in caplog.records)
        assert not any(r.levelname == "WARNING" and r.name == "app.middleware" for r in caplog.records)
        assert not any(r.levelname == "ERROR" and r.name == "app.middleware" for r in caplog.records)

    async def test_not_found_logs_at_warning(self, client, caplog):
        with caplog.at_level(logging.WARNING, logger="app.middleware"):
            await client.get("/campaigns/999999")
        assert any("REQUEST GET /campaigns/999999" in r.message for r in caplog.records)
        assert any(r.levelname == "WARNING" and r.name == "app.middleware" for r in caplog.records)
        assert not any(r.levelname == "INFO" and r.name == "app.middleware" for r in caplog.records)
        assert not any(r.levelname == "ERROR" and r.name == "app.middleware" for r in caplog.records)
