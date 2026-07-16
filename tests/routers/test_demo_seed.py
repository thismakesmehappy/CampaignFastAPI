class TestSeedDemoData:
    async def test_seed_demo_data_defaults(self, client, existing_client):
        response = await client.post(f"/clients/{existing_client.id}/seed-demo-data", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["seeded"] is True
        assert data["campaigns_created"] == 3
        assert data["metrics_created"] > 0
        assert data["ranges_filled"] == [7, 30, 60, 90, 180]

    async def test_seed_demo_data_custom_params(self, client, existing_client):
        response = await client.post(
            f"/clients/{existing_client.id}/seed-demo-data",
            json={"campaign_count": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["campaigns_created"] == 1

    async def test_seed_demo_data_second_call_noop(self, client, existing_client):
        await client.post(f"/clients/{existing_client.id}/seed-demo-data", json={})
        response = await client.post(f"/clients/{existing_client.id}/seed-demo-data", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["seeded"] is False
        assert data["ranges_filled"] == []

    async def test_seed_demo_data_client_not_found(self, client):
        response = await client.post("/clients/999999999999/seed-demo-data", json={})
        assert response.status_code == 404

    async def test_seed_demo_data_no_body_uses_defaults(self, client, existing_client):
        """The endpoint has a default SeedDemoDataRequest() so an empty/omitted body is valid."""
        response = await client.post(f"/clients/{existing_client.id}/seed-demo-data")
        assert response.status_code == 200
        assert response.json()["campaigns_created"] == 3